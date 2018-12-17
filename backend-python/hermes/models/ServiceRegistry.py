#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
import logging
import threading
import time

import redis

from backend_python.settings import *
from hermes.models.HermesModels import HermesDevice

logger = logging.getLogger(__name__)


# 设置本地连接池
def create_redis_client():
    if disable_redis:
        return None
    redis_param = {}
    if not redis_host or not redis_port:
        raise Exception('redis_host and redis_port config can not be empty')
    redis_param['host'] = redis_host
    redis_param['port'] = redis_port
    if redis_auth:
        # TODO
        redis_auth['auth'] = redis_auth
    redis_param['decode_responses'] = True
    pool = redis.ConnectionPool(redis_param)
    return redis.Redis(connection_pool=pool)


try:
    redis_client = create_redis_client()
except Exception as e:
    redis_client = None
    logger.error("forward to device,network exception %s", e)


class ServiceQueue(object):
    """队列轮训模型，在不同场景下对轮训方式进行的抽象"""

    def __init__(self, service_name):
        self.serviceName = service_name

    def online(self, mac):
        """上线一个服务"""
        pass

    def offline(self, mac):
        """下线一个服务"""
        pass

    def roll_poling(self):
        """轮训动作，头部poll，移至尾部，second->head，head->tail"""
        pass

    def mac_size(self):
        """当前已注册设备总数"""
        pass

    def record_failed(self, mac):
        """记录失败，业务方的feedback调用，由于也无方的失败判定不可信，但是能够反应资源好坏趋势，所以该接口可以对执行资源降权，但不直接下线资源"""
        pass

    def record_success(self, mac):
        """记录成功，这个也必须调用，正向打分用户维持正常的高优先级"""
        pass

    def queue_status(self):
        """显示队列内容"""
        pass

    def reset(self):
        """重制队列"""
        pass


class RedisServiceQueue(ServiceQueue):
    """基于redis的实现"""

    def __init__(self, service_name):
        super(RedisServiceQueue, self).__init__(service_name)
        self.queue_polling_key = 'hermes_admin_' + self.serviceName + '_redis_polling_v3'
        self.queue_meta_key = 'hermes_admin_' + self.serviceName + '_redis_data_v3'
        self.queue_index_key = 'hermes_admin_' + self.serviceName + '_index_v3'

    def online(self, mac):
        meta_data = redis_client.hget(self.queue_meta_key, mac)
        if meta_data is None:
            meta_data = {
                'mac': mac,
                'score': 1.0,
                'lastReportTime': time.time(),
                'online': True
            }
            # print 'new device report:' + json.dumps(meta_data)
        else:
            meta_data = json.loads(meta_data)
            meta_data['lastReportTime'] = time.time()
            meta_data['online'] = True
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))
        self.set_up_poling_key(mac, meta_data['score'])

    def set_up_poling_key(self, mac, score, old_score=0):
        old_max_index = self.judge_index_by_score(old_score)
        last_index = self.judge_index_by_score(score)

        now_index = last_index
        if now_index <= old_score:
            return
        queue_size = self.mac_size()
        all_polling_key = set(redis_client.lrange(self.queue_polling_key, 0, -1))
        while now_index >= old_max_index:
            poling_key = mac + '__' + str(now_index)
            if poling_key in all_polling_key:
                now_index -= 1
                continue
            ref_value = redis_client.lindex(self.queue_polling_key, int(queue_size * now_index / 10))
            now_index -= 1
            if not ref_value:
                redis_client.rpush(self.queue_polling_key, poling_key)
                continue
            insert_result = redis_client.linsert(self.queue_polling_key, 'AFTER', ref_value, poling_key)
            if insert_result <= 0:
                redis_client.rpush(self.queue_polling_key, poling_key)

    @staticmethod
    def judge_index_by_score(score):
        enlarge_score = int(float(score) * 10 + 0.1)
        return 1 if enlarge_score < 1 else 10 if enlarge_score > 10 else enlarge_score

    def offline(self, mac):
        """下线一个服务"""
        # 元数据不要删，这里记录了历史评估数据
        meta_data = redis_client.hget(self.queue_meta_key, mac)
        if not meta_data:
            return
        meta_data = json.loads(meta_data)
        meta_data['online'] = False
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))

    def roll_poling(self):
        total_len = self.mac_size()
        if total_len == 0:
            return None
        retry = 0
        while True:
            # 理论上不会死循环，但是还是要这样做保证，避免代码内部出现逻辑漏洞
            if retry > 5:
                return None
            retry += 1

            now_index = redis_client.incr(self.queue_index_key)
            if now_index > 0x0FFFFFFF:
                # 调用次数很多了，可以清零cursor，避免溢出问题
                redis_client.delete(self.queue_index_key)
                now_index = redis_client.incr(self.queue_index_key)
            # print 'nowIndex:%d' % now_index
            resource = redis_client.lindex(self.queue_polling_key, now_index % total_len)
            if not resource:
                # 这个case是可能发生的，由于中途我们可能删除数据，导致index和实际的不一致
                resource = redis_client.lindex(self.queue_polling_key, -1)
                if not resource:
                    return None
            # print 'resource:%s' % resource
            polling_key_param = str(resource).split('__')
            mac = polling_key_param[0]
            mac_enlarge_index = int(polling_key_param[1])
            meta_data = redis_client.hget(self.queue_meta_key, mac)
            if not meta_data:
                continue
            # print 'metaData:%s' % meta_data
            meta_data = json.loads(meta_data)
            if not meta_data['online']:
                if mac_enlarge_index > 1:
                    redis_client.lrem(self.queue_polling_key, 1, resource)
                continue
            if mac_enlarge_index <= 1:
                # 永远保证始终有1个投射是有效的，如此提供自动复原的能力
                return mac
            # print 'max index for score:%d' % self.judge_index_by_score(meta_data['score'])
            # print 'now_index:%s' % mac_enlarge_index
            if self.judge_index_by_score(meta_data['score']) < mac_enlarge_index:
                redis_client.lrem(self.queue_polling_key, 1, resource)
                continue
            return mac

    def mac_size(self):
        """当前已注册设备总数"""
        # 读取queue，不要读取set，set可能有下线资源
        return redis_client.llen(self.queue_polling_key)

    def record_failed(self, mac):
        """记录失败，业务方的feedback调用，由于也无方的失败判定不可信，但是能够反应资源好坏趋势，所以该接口可以对执行资源降权，但不直接下线资源"""
        meta_data = redis_client.hget(self.queue_meta_key, mac)
        if meta_data is None:
            logger.warning('can not find meta data for device:%s' % mac)
            return
        meta_data = json.loads(meta_data)
        new_score = float(meta_data['score']) * 0.9
        # 不能让分数无限降低，这回导致资源被跑干之后无法恢复
        new_score = float(0.1) if new_score < float(0.1) else float(1) if new_score > float(1) else new_score

        meta_data['score'] = new_score
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))

    def record_success(self, mac):
        """记录成功，这个也必须调用，正向打分用户维持正常的高优先级"""
        meta_data = redis_client.hget(self.queue_meta_key, mac)
        if meta_data is None:
            logger.warning('can not find meta data for device:%s' % mac)
            return
        meta_data = json.loads(meta_data)
        old_score = meta_data['score']
        new_score = float(meta_data['score']) * 0.9 + 0.1
        new_score = float(0) if new_score < float(0) else float(1) if new_score > float(1) else new_score
        meta_data['score'] = new_score
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))
        self.set_up_poling_key(mac, new_score, old_score)

    def queue_status(self):
        """显示队列内容"""
        mac_list = redis_client.lrange(self.queue_polling_key, 0, -1)
        all_meta = redis_client.hgetall(self.queue_meta_key)
        # print json.dumps(all_meta)
        ret = []
        duplicate_set = set()
        # print mac_list
        for mac in mac_list:
            # print mac
            mac = str(mac).split('__')[0]
            meta_data = all_meta[mac]
            if meta_data is None:
                continue
            if mac in duplicate_set:
                continue
            duplicate_set.add(mac)
            meta_data = json.loads(meta_data)
            if not meta_data['online']:
                continue
            resource_entry = ResourceEntry(meta_data['mac'])
            resource_entry.score = meta_data['score']
            resource_entry.lastReportTime = meta_data['lastReportTime']
            ret.append(resource_entry)
        return ret

    def reset(self):
        """重制队列"""
        redis_client.delete(self.queue_polling_key)
        redis_client.delete(self.queue_meta_key)
        redis_client.delete(self.queue_index_key)


class ResourceEntry(object):
    def __init__(self, mac):
        self.mac = mac
        self.score = 1.0
        self.lastReportTime = time.time()
        self.online = True


class RamServiceQueue(ServiceQueue):
    """基于内存的实现"""

    def __init__(self, service_name):
        super(RamServiceQueue, self).__init__(service_name)
        self.queue = list()
        self.metaMap = {}
        self.lock = threading.Lock()
        self.index = -1

    def online(self, mac):
        resource_entry = self.metaMap.get(mac)
        if resource_entry is None:
            with self.lock:
                resource_entry = self.metaMap.get(mac)
                if resource_entry is None:
                    resource_entry = ResourceEntry(mac)
                    self.metaMap[mac] = resource_entry
        else:
            resource_entry.lastReportTime = time.time()
            resource_entry.online = True
        self.set_up_poling_key(mac, resource_entry.score)

    def set_up_poling_key(self, mac, score, old_score=0):
        old_max_index = self.judge_index_by_score(old_score)
        # print 'set up poling key for mac:%s' % mac
        last_index = self.judge_index_by_score(score)

        now_index = last_index
        if now_index <= old_score:
            return
        # print 'last index:%d' % last_index
        queue_size = self.mac_size()
        all_polling_key = set(self.queue)
        while now_index >= old_max_index:
            poling_key = mac + '__' + str(now_index)
            if poling_key in all_polling_key:
                now_index -= 1
                continue
            try:
                self.queue.insert(int(queue_size * now_index / 10), poling_key)
            except:
                self.queue.append(poling_key)

    @staticmethod
    def judge_index_by_score(score):
        enlarge_score = int(float(score) * 10 + 0.1)
        return 1 if enlarge_score < 1 else 10 if enlarge_score > 10 else enlarge_score

    def offline(self, mac):
        resource_entry = self.metaMap.get(mac)
        if resource_entry is None:
            return
        resource_entry.online = False

    def roll_poling(self):
        retry_times = 0
        while True:
            if retry_times > 5:
                return None
            retry_times += 1
            with self.lock:
                self.index += 1
                next_index = self.index
            if next_index > 0x0FFFFFFF:
                # 调用次数很多了，可以清零cursor，避免溢出问题
                self.index = -1
                continue
            try:
                resource = self.queue[next_index % len(self.queue)]
            except:
                continue
            polling_key_param = str(resource).split('__')
            mac = polling_key_param[0]
            mac_enlarge_index = int(polling_key_param[1])
            meta_data = self.metaMap[mac]
            if not meta_data:
                continue
            # print 'metaData:%s' % meta_data
            if not meta_data.online:
                if mac_enlarge_index > 1:
                    self.queue.remove(resource)
                continue
            if mac_enlarge_index <= 1:
                # 永远保证始终有1个投射是有效的，如此提供自动复原的能力
                return mac
            if self.judge_index_by_score(meta_data.score) < mac_enlarge_index:
                self.queue.remove(resource)
                continue
            return mac

    def mac_size(self):
        return len(self.queue)

    def record_failed(self, mac):
        """记录失败，业务方的feedback调用，由于也无方的失败判定不可信，但是能够反应资源好坏趋势，所以该接口可以对执行资源降权，但不直接下线资源"""
        meta_data = self.metaMap[mac]
        if meta_data is None:
            logger.warning('can not find meta data for device:%s' % mac)
            return
        new_score = float(meta_data.score) * 0.9
        # 不能让分数无限降低，这回导致资源被跑干之后无法恢复
        new_score = float(0.1) if new_score < float(0.1) else float(1) if new_score > float(1) else new_score
        meta_data.score = new_score

    def record_success(self, mac):
        """记录成功，这个也必须调用，正向打分用户维持正常的高优先级"""
        meta_data = self.metaMap[mac]
        if meta_data is None:
            logger.warning('can not find meta data for device:%s' % mac)
            return
        meta_data = json.loads(meta_data)
        old_score = meta_data.score
        new_score = float(meta_data.score) * 0.9 + 0.1
        new_score = float(0) if new_score < float(0) else float(1) if new_score > float(1) else new_score
        meta_data.score = new_score
        self.set_up_poling_key(mac, new_score, old_score)

    def queue_status(self):
        """显示队列内容"""
        # print json.dumps(all_meta)
        ret = []
        duplicate_set = set()
        # print mac_list
        for mac in self.queue:
            # print mac
            mac = str(mac).split('__')[0]
            meta_data = self.metaMap[mac]
            if meta_data is None:
                continue
            if mac in duplicate_set:
                continue
            duplicate_set.add(mac)
            if not meta_data.online:
                continue
            ret.append(meta_data)
        return ret

    def reset(self):
        """重制队列"""
        self.queue = list()
        self.metaMap = {}
        self.index = 0


class ServiceRegistry(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.resource_queue_map = {}
        if not redis_client:
            # recovery for ram mode
            self.__recovery__()

    def __recovery__(self):
        now = datetime.datetime.now()
        start = now - datetime.timedelta(minutes=10)
        online_devices = HermesDevice.objects.filter(lastReportTime__gt=start)
        for online_device in online_devices:
            last_online_service = json.loads(online_device.lastReportService)
            for service in last_online_service:
                self.create_or_get_resource_queue(service).online(online_device.mac)

    def create_or_get_resource_queue(self, service):
        service_queue = self.resource_queue_map.get(service)
        if service_queue is not None:
            return service_queue
        with self.lock:
            service_queue = self.resource_queue_map.get(service)
            if service_queue is not None:
                return service_queue
            if redis_client:
                service_queue = RedisServiceQueue(service)
            else:
                service_queue = RamServiceQueue(service)
            self.resource_queue_map[service] = service_queue
            return service_queue

    def handle_device_report(self, report_model):
        mac = report_model['mac']
        online_service = report_model['onlineServices']
        for service in online_service:
            self.create_or_get_resource_queue(service).online(mac)

    def roll_poling(self, service):
        return self.create_or_get_resource_queue(service).roll_poling()

    def record_failed(self, mac, service):
        self.create_or_get_resource_queue(service).record_failed(mac)

    def offline(self, mac, service):
        self.create_or_get_resource_queue(service).offline(mac)

    def record_success(self, mac, service):
        self.create_or_get_resource_queue(service).record_success(mac)

    def queue_status(self, service):
        return self.create_or_get_resource_queue(service).queue_status()

    def reset_queue(self, service):
        self.create_or_get_resource_queue(service).reset()


registry = ServiceRegistry()
