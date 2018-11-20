#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
import logging
import threading
import time

from hermes.models.HermesModels import HermesDevice
from hermes.models.LinkList import DoublyLinkedList

logger = logging.getLogger(__name__)

# from pyutil import pyredis
import redis
from redis.exceptions import ResponseError
# 设置本地连接池
pool = redis.ConnectionPool(host='127.0.0.1',port=6379,password='123456',decode_responses=True)
redis_client = redis.Redis(connection_pool=pool)
# redis_client = pyredis.make_redis_client('toutiao.redis.crawl_vertical')


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
        self.queue_polling_key = 'hermes_admin_' + self.serviceName + '_redis_polling'
        self.queue_meta_key = 'hermes_admin_' + self.serviceName + '_redis_data'
        self.queue_avg_score_key = 'hermes_admin_' + self.serviceName + '_redis_avg_score'

    def online(self, mac):
        meta_data = redis_client.hget(self.queue_meta_key, mac)
        if meta_data is None:
            meta_data = {
                'mac': mac,
                'score': 1.0,
                'lastReportTime': time.time()
            }
            new_record = True
        else:
            meta_data = json.loads(meta_data)
            meta_data['lastReportTime'] = time.time()
            new_record = False
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))
        if new_record:
            redis_client.lpush(self.queue_polling_key, mac)
            return True
        queue_size = self.mac_size()
        if queue_size < 64:
            all_record = redis_client.lrange(self.queue_polling_key, 0, -1)
            for record in all_record:
                if record == mac:
                    return
            redis_client.lpush(self.queue_polling_key, mac)
            return True
        self.record_failed(mac)
        return True

    def offline(self, mac):
        """下线一个服务"""
        # 元数据不要删，这里记录了历史评估数据
        redis_client.lrem(self.queue_polling_key, 0, mac)

    def get_avg_score(self):
        avg_score = redis_client.get(self.queue_avg_score_key)
        if avg_score is None:
            avg_score = 1
        else:
            avg_score = float(avg_score)
            if avg_score > 1:
                avg_score = 1
            elif avg_score < 0:
                avg_score = 0
        return avg_score

    def roll_poling(self):
        """轮训动作，头部poll，移至尾部，second->head，head->tail"""
        while True:
            mac = redis_client.lpop(self.queue_polling_key)
            if mac is None:
                return None
            meta_data = redis_client.hget(self.queue_meta_key, mac)
            if meta_data is None:
                logger.warning("can not find meta data for mac:%s" % mac)
                continue
            meta_data = json.loads(meta_data)
            if time.time() - meta_data['lastReportTime'] > 600:
                logger.info("the device:%s not report status 10 minute" % mac)
                continue
            queue_size = redis_client.llen(self.queue_polling_key) + 1
            avg_score = self.get_avg_score()
            if queue_size <= 3:
                redis_client.rpush(self.queue_polling_key, mac)
            else:
                target_index = queue_size * avg_score
                try:
                    position = redis_client.lindex(self.queue_polling_key, int(target_index))
                    if position is None:
                        redis_client.rpush(self.queue_polling_key, mac)
                    else:
                        redis_client.linsert(self.queue_polling_key, 'after', position, mac)
                except ResponseError:
                    redis_client.rpush(self.queue_polling_key, mac)

            avg_score = (avg_score * (queue_size - 1) + float(meta_data['score'])) / queue_size
            redis_client.set(self.queue_avg_score_key, str(avg_score))
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
        meta_data['score'] = float(meta_data['score']) * 0.9
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))
        queue_size = self.mac_size()
        if queue_size <= 3:
            return
        redis_client.lrem(self.queue_polling_key, 0, mac)
        # 根据当前分数，计算得到一个新的偏移位置
        ratio = redis_client.get(self.queue_avg_score_key)
        if ratio is None:
            ratio = 1.0
        else:
            ratio = float(ratio)
        if ratio >= 1.0:
            redis_client.rpush(self.queue_polling_key, mac)
            return
        index = queue_size * (ratio + (1 - ratio) * (1 - meta_data['score']))

        if index >= queue_size - 1:
            redis_client.rpush(self.queue_polling_key, mac)
            return

        position = redis_client.lindex(self.queue_polling_key, int(index))
        if position is None:
            redis_client.rpush(self.queue_polling_key, mac)
            return
        tobe_replaced = redis_client.hget(self.queue_meta_key, position)
        if tobe_replaced is not None:
            tobe_replaced = json.loads(tobe_replaced)
            if meta_data['score'] > tobe_replaced['score']:
                index += 1
                position = redis_client.lindex(self.queue_polling_key, int(index))
                if position is None:
                    redis_client.rpush(self.queue_polling_key, mac)
                return
        try:
            redis_client.linsert(self.queue_polling_key, 'after', position, mac)
        except:
            redis_client.rpush(self.queue_polling_key, mac)

    def record_success(self, mac):
        """记录成功，这个也必须调用，正向打分用户维持正常的高优先级"""
        meta_data = redis_client.hget(self.queue_meta_key, mac)
        if meta_data is None:
            logger.warning('can not find meta data for device:%s' % mac)
            return
        meta_data = json.loads(meta_data)
        meta_data['score'] = float(meta_data['score']) * 0.9 + 0.1
        if meta_data['score'] < 0:
            meta_data['score'] = 0
        if meta_data['score'] > 1:
            meta_data['score'] = 1
        redis_client.hset(self.queue_meta_key, mac, json.dumps(meta_data))

    def queue_status(self):
        """显示队列内容"""
        mac_list = redis_client.lrange(self.queue_polling_key, 0, -1)
        all_meta = redis_client.hgetall(self.queue_meta_key)
        ret = []
        for mac in mac_list:
            meta_data = all_meta[mac]
            if meta_data is None:
                continue
            meta_data = json.loads(meta_data)
            resource_entry = ResourceEntry(meta_data['mac'])
            resource_entry.score = meta_data['score']
            resource_entry.lastReportTime = meta_data['lastReportTime']
            ret.append(resource_entry)
        return ret

    def reset(self):
        """重制队列"""
        redis_client.delete(self.queue_polling_key)
        redis_client.delete(self.queue_meta_key)
        redis_client.delete(self.queue_avg_score_key)


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
