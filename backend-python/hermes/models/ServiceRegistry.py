#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
import logging
import threading
import time
import redis

from hermes.models.HermesModels import HermesDevice
from hermes.models.LinkList import DoublyLinkedList
from backend_python.settings import *

logger = logging.getLogger(__name__)

# 设置本地连接池
if redis_queue_enable:
    if not redis_host or not redis_port:
        logger.warning(
            'redis queue config enabled but redis host or port not configured in backend_python.settings.python')
    else:
        redis_param = {
            'host': redis_host,
            'port': redis_port,
            'decode_responses': True
        }
        if redis_auth:
            redis_param['auth'] = redis_auth

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True)
redis_client = redis.Redis(connection_pool=pool)


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
        # print 'set up poling key for mac:%s' % mac
        last_index = self.judge_index_by_score(score)

        now_index = last_index
        if now_index <= old_score:
            return
        # print 'last index:%d' % last_index
        queue_size = self.mac_size()
        # 考虑设备数量最多在百的量级，投射之后数量级在千。其实数据量很小，所以我们这里把它load到内存中，如果未来管理的手机在几千或者几万的时候，这里可能就会影响性能了
        # 不过那个时候hermesAdmin肯定也是会面临进一步的重构了
        all_polling_key = set(redis_client.lrange(self.queue_polling_key, 0, -1))
        while now_index >= old_max_index:
            poling_key = mac + '__' + str(now_index)
            if poling_key in all_polling_key:
                now_index -= 1
                continue
            # print 'add index :%s' % poling_key
            ref_value = redis_client.lindex(self.queue_polling_key, int(queue_size * now_index / 10))
            now_index -= 1
            if not ref_value:
                redis_client.rpush(self.queue_polling_key, poling_key)
                continue
            # print 'ref_value:%s' % ref_value
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
                if mac_enlarge_index > 2:
                    redis_client.lrem(self.queue_polling_key, 1, resource)
                continue
            if mac_enlarge_index <= 2:
                # 永远保证始终有2个投射是有效的，如此提供自动复原的能力
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
        new_score = float(0.2) if new_score < float(0.2) else float(1) if new_score > float(1) else new_score

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


class RamServiceQueue(ServiceQueue):
    """基于内存的实现,目前已废弃"""

    def __init__(self, service_name):
        super(RamServiceQueue, self).__init__(service_name)
        self.queue = DoublyLinkedList()
        self.leaveDevice = set()
        self.deviceMap = {}
        self.lock = threading.Lock()
        self.avgScore = 1.0

    def online(self, mac):
        resource_entry = self.deviceMap.get(mac)
        if resource_entry is not None:
            resource_entry.lastReportTime = time.time()
            if mac in self.leaveDevice:
                with self.lock:
                    if mac not in self.leaveDevice:
                        return
                    self.queue.append(resource_entry)
                    self.leaveDevice.remove(mac)
            return
        # a new service registry
        resource_entry = ResourceEntry(mac)
        self.deviceMap[mac] = resource_entry
        self.queue.append(resource_entry)
        logger.info('a new device :%s registered for service:%s' % (mac, self.serviceName))

    def offline(self, mac):
        resource_entry = self.deviceMap.get(mac)
        if resource_entry is None:
            return
        # 设置flag，在轮训的时候，发现此标记将其剔除
        resource_entry.lastReportTime = -1

    def roll_poling(self):
        while True:
            with self.lock:
                resource_entry = self.queue.pop()
            if resource_entry is None:
                return None
            if not (resource_entry.mac in self.deviceMap.keys()):
                continue
            if resource_entry.lastReportTime < 0:
                """外部下线调用flag"""
                self.leaveDevice.add(resource_entry.mac)
                continue
            if time.time() - resource_entry.lastReportTime > 600:
                """如果一个资源，10分钟都没有进行上报，那么这个资源下线处理,因为agent两分钟上报一次"""
                self.leaveDevice.add(resource_entry.mac)
                continue

            with self.lock:
                try:
                    self.queue.insert(self.queue.size * self.avgScore, resource_entry)
                except Exception:
                    self.queue.append(resource_entry)
            queue_size = self.queue.size + 1
            self.avgScore = (self.avgScore * (queue_size - 1) + resource_entry.score) / queue_size
            return resource_entry.mac

    def mac_size(self):
        return len(self.deviceMap)

    def record_failed(self, mac):
        resource_entry = self.deviceMap.get(mac)
        if resource_entry is None:
            return
        resource_entry.score = resource_entry.score * 0.9
        if self.queue.size <= 3:
            # 如果队列资源太少，取消反馈下线
            return
        with self.lock:
            if not self.queue.remove(resource_entry):
                """ 不在当前队列中，证明已经处于下线状态"""
                return
        # 根据当前分数，计算得到一个新的偏移位置
        length = self.queue.size
        ratio = self.avgScore
        if ratio >= 1:
            with self.lock:
                self.queue.append(resource_entry)
                return
        index = length * (ratio + (1 - ratio) * (1 - resource_entry.score))
        with self.lock:
            try:
                if index >= length - 1:
                    self.queue.append(resource_entry)
                else:
                    tobe_replaced = self.queue.get(index)
                    if resource_entry.score < tobe_replaced.score:
                        # 增加一个向后增长的趋势，避免由于精度误差问题，是的质量更好的资源资源自动恢复
                        index += 1
                    self.queue.insert(index, resource_entry)
            except Exception:
                self.queue.append(resource_entry)

    def record_success(self, mac):
        resource_entry = self.deviceMap.get(mac)
        if resource_entry is None:
            return
        resource_entry.score = (resource_entry.score * 9 + 1) / 10

    def queue_status(self):
        with self.lock:
            ret = []
            self.queue.travel(lambda (entry): ret.append(entry))
            return ret

    def reset(self):
        """重制队列"""
        self.queue = DoublyLinkedList()
        self.leaveDevice = set()
        self.deviceMap = {}


class ServiceRegistry(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.resource_queue_map = {}
        # if settings.DEBUG:
        #     self.__recovery__()

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
            # if settings.DEBUG:
            #     service_queue = RamServiceQueue(service)
            # else:
            service_queue = RedisServiceQueue(service)
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
