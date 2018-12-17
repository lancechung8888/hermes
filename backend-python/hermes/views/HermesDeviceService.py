#!/usr/bin/env python
# encoding: utf-8

import json
import time
import urllib

import requests
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.generic import View

from hermes.models.HermesModels import HermesDevice, HermesDevicePackage, ServiceDetail, HermesWrapperAPK, \
    HermesTargetAPP
from hermes.models.ServiceRegistry import registry
from hermes.views.HermesUtil import ResponseContainer, ForceDumpJsonResponse

import logging

logger = logging.getLogger(__name__)


class ListDeviceView(View):
    """手机列表，带有分页功能"""

    def get(self, request):
        page = request.GET.get('page', 0)
        page = int(page) + 1
        pagesize = request.GET.get('size', 10)
        pagesize = max(0, min(pagesize, 10))

        app_package = request.GET.get('appPackage', None)
        query = HermesDevice.objects
        if app_package is not None:
            query_condition = 'mac in (select device_mac from hermes_device_service where app_package=\'%s\' and status=true)' % app_package
            query = query.extra(where=[query_condition])
        p = Paginator(query.order_by('id').all(), pagesize)
        return ForceDumpJsonResponse(ResponseContainer.success(p.page(page)))


class DeviceIpListView(View):
    def get(self, request):
        ip_list = set()
        for device in HermesDevice.objects.filter(status=True).all():
            ip_list.add(device.ip)
        return HttpResponse('\n'.join(ip_list), content_type='text/plain; charset=utf8')


class ListAvailableDeviceView(View):
    def get(self, request):
        page = request.GET.get('page', 0)
        page = int(page) + 1
        pagesize = request.GET.get('size', 10)
        pagesize = max(0, min(pagesize, 10))

        app_package = request.GET.get('appPackage', None)
        query = HermesDevice.objects
        if app_package is not None:
            query_condition = 'mac not in (select device_mac from hermes_device_service where app_package=\'%s\' and status=true)' % app_package
            query = query.extra(where=[query_condition])
        p = Paginator(query.order_by('id').all(), pagesize)
        return ForceDumpJsonResponse(ResponseContainer.success(p.page(page)))


class DeviceReportView(View):
    """接受手机的上报"""

    def post(self, request):
        logger.info('device report:%s' % request.body)
        try:
            report_model = json.loads(request.body)
        except Exception as e:
            logger.error('request not json format', e)
            return ForceDumpJsonResponse(ResponseContainer.failed("request not json format:%s" % e))
        # now check params
        if 'agentServerIP' not in report_model:
            logger.error('agent ip not present')
            return ForceDumpJsonResponse(ResponseContainer.failed("agent ip not present"))
        if 'agentServerPort' not in report_model:
            report_model['agentServerPort'] = 5597
        if 'mac' not in report_model:
            # mac 作为硬件ID，手机唯一性标记，不能缺失
            logger.error('device mac not present')
            return ForceDumpJsonResponse(ResponseContainer.failed("device mac not present"))
        if 'REMOTE_HOST' in request.META:
            report_model['visibleIp'] = request.META['REMOTE_HOST']
        if 'REMOTE_ADDR' in request.META:
            report_model['visibleIp'] = request.META['REMOTE_ADDR']
        if not hasattr(report_model, 'visibleIp'):
            report_model['visibleIp'] = report_model['agentServerIP']

        # 将这个json，转化为数据库相关字段
        device_model = {
            'brand': report_model['brand'],
            'ip': report_model['agentServerIP'],
            'port': report_model['agentServerPort'],
            'mac': report_model['mac'],
            'systemVersion': report_model['systemVersion'],
            # status 这里不设置，否则会复写管理端对设备的禁用启用配置 'status':0
            'visibleIp': report_model['visibleIp'],
            'cpuUsage': str(report_model['cpuLoader']),
            'memory': str(report_model['memoryInfo']),
            'lastReportTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'lastReportService': json.dumps(report_model['onlineServices'])
        }

        HermesDevice.objects.update_or_create(mac=report_model['mac'], defaults=device_model)
        registry.handle_device_report(report_model)

        # gen device config
        config_services = HermesDevicePackage.objects.filter(deviceMac=report_model['mac']).all()
        service_detail_list = []
        for service in config_services:
            service_detail = ServiceDetail()
            # 基本信息
            service_detail.serviceId = service.id
            service_detail.status = service.status
            service_detail.deviceMac = service.deviceMac
            service_detail.targetAppPackage = service.appPackage

            if service_detail.status:
                # targetApp信息
                hermes_target_app = HermesTargetAPP.objects.filter(appPackage=service.appPackage, enabled=True) \
                    .order_by('-versionCode').first()
                if hermes_target_app is None:
                    service_detail.status = False
                else:
                    service_detail.targetAppVersionCode = hermes_target_app.versionCode
                    service_detail.targetAppDownloadUrl = hermes_target_app.downloadUrl

            if service_detail.status:
                # wrapper 数据
                hermes_wrapper_apk = HermesWrapperAPK.objects.filter(enabled=True, targetApkPackage=service.appPackage) \
                    .order_by('-versionCode').first()
                if hermes_wrapper_apk is None:
                    service_detail.status = False
                else:
                    service_detail.wrapperPackage = hermes_wrapper_apk.apkPackage
                    service_detail.wrapperVersionCode = hermes_wrapper_apk.versionCode
                    service_detail.wrapperAppDownloadUrl = hermes_wrapper_apk.downloadUrl

            service_detail_list.append(service_detail)

        return ForceDumpJsonResponse(ResponseContainer.success(service_detail_list))


def join_param(param_map):
    first = True
    ret = ''
    for k, v in param_map.items():
        if len(v) == 0:
            v = ['']
        for multi_value in v:
            if not first:
                ret += "&"
            else:
                first = False
            ret += (urllib.quote(str(k)) + "=" + urllib.quote(str(multi_value)))
    return ret


class InvokeHandlerView(View):
    """外部统一invoke调用接口，将会路由调用到某一台在线手机设备"""

    def forward(self, request):
        if 'CONTENT_TYPE' in request.META:
            content_type = request.META['CONTENT_TYPE']
        else:
            content_type = None

        param_dir = {}
        if request.GET is not None:
            param_dir.update(request.GET)
        if request.POST is not None:
            param_dir.update(request.POST)
        logger.info('request:%s' % param_dir)
        service = request.GET.get('invoke_package')
        time_out = request.GET.get('__hermes_invoke_timeOut')

        if request.method == 'GET' or (
                        content_type is not None and str(content_type).lower().startswith(
                    'application/x-www-form-urlencoded')):
            request_body = join_param(param_dir)
        elif request.method == 'POST' and content_type is not None and str(content_type).lower().startswith(
                'application/json'):
            try:
                json_request_body = json.loads(request.body)
            except Exception as e:
                logger.warning('request body parse failed: %s' % request.body, e)
                return ForceDumpJsonResponse(ResponseContainer.failed('request parse failed %s' % e))
            if service is None:
                service = json_request_body['invoke_package']
            if time_out is None:
                time_out = json_request_body['__hermes_invoke_timeOut']
            request_body = request.body
        else:
            """只支持get或者post（application/x-www-form-urlencoded，application/json）"""
            return ForceDumpJsonResponse(ResponseContainer.failed('content type not support'))
        if service is None or len(service) == 0:
            return ForceDumpJsonResponse(ResponseContainer.failed("param:{invoke_package} not presented"))
        logger.info("accept a invoke request:%s" % request_body)
        #  get 转 post, 需要改变content-type
        if content_type is None or request.method == 'GET':
            content_type = "application/x-www-form-urlencoded;charset=utf8"

        # 根据service选择一个设备
        mac = registry.roll_poling(service)
        if mac is None:
            logger.warning("no device available for service:%s" % service)
            return ForceDumpJsonResponse(ResponseContainer.failed("no available devices online"))
        hermes_device = HermesDevice.objects.filter(mac=mac).first()
        if hermes_device is None:
            logger.error("system error,can not find device for mac:%s" % mac)
            registry.offline(mac, service)
            return ForceDumpJsonResponse(ResponseContainer.failed("system error,can not find device for mac:%s" % mac))

        # forward 到指定设备
        if time_out is None:
            time_out = 5000
        request_url = "http://" + hermes_device.visibleIp + ":" + str(hermes_device.port) + "/invoke"
        logger.info("forward invoke ,url:%s ,contentType:%s data:%s" % (request_url, content_type, request_body))
        try:
            response = requests.post(request_url, data=request_body, headers={'Content-Type': content_type},
                                     timeout=time_out)
        except Exception as e:
            logger.error("forward to device,network exception %s", e)
            # 发生网络异常，那么对该资源进行动态降权
            registry.record_failed(mac, service)
            return ForceDumpJsonResponse(
                ResponseContainer.failed("forward to device,network exception:%s" % e))
        response_json = json.loads(response.text)
        if response_json['status'] == -2:
            logger.info('service offline')
            registry.offline(mac, service)
        elif response_json['status'] != 0:
            # 如果返回结果不正常，那么一定是发生了某种异常，此时无法想起判定是否是机器状态不好或者业务代码存在问题，所以进行降权，但不下线
            registry.record_failed(mac, service)
        else:
            registry.record_success(mac, service)
        logger.info("invoke call result:%s" % response.text)
        return ForceDumpJsonResponse(response_json)

    def post(self, request):
        return self.forward(request)

    def get(self, request):
        return self.forward(request)


class SetDeviceStatusView(View):
    def get(self, request):
        device_id = request.GET.get('deviceId', None)
        if device_id is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the parameter :{deviceId} is not presented"))
        status = request.GET.get('status', None)
        if status is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the parameter :{status} is not presented"))
        hermes_device = HermesDevice.objects.filter(id=device_id).first()
        if hermes_device is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("record not fond"))
        real_status = 'true' == str(status).lower()
        HermesDevice.objects.filter(id=device_id).update(status=real_status)
        return ForceDumpJsonResponse(ResponseContainer.success("ok"))
