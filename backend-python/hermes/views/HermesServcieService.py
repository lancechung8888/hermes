#!/usr/bin/env python
# encoding: utf-8
import logging

from django.core.paginator import Paginator
from django.views.generic import View

from hermes.models.HermesModels import HermesDevicePackage, HermesTargetAPP, HermesDevice
from hermes.views.HermesUtil import ForceDumpJsonResponse, ResponseContainer, to_boolean

logger = logging.getLogger(__name__)

class ListDeviceServiceView(View):
    """设备服务，带有分页功能"""

    def get(self, request):
        page = request.GET.get('page', 0)
        page = int(page) + 1
        pagesize = request.GET.get('size', 10)
        pagesize = max(0, min(pagesize, 10))
        query = HermesDevicePackage.objects
        if 'deviceMac' in request.GET:
            query = query.filter(deviceMac=request.GET.get('deviceMac'))
        if 'servicePackage' in request.GET:
            query = query.filter(appPackage=request.GET.get('servicePackage'))

        p = Paginator(query.order_by('-id').all(), pagesize)
        return ForceDumpJsonResponse(ResponseContainer.success(p.page(page)))


class DeployServiceToAllDeviceView(View):
    """安装服务到所有设备上面"""

    def get(self, request):
        if 'servicePackage' not in request.GET:
            return ForceDumpJsonResponse(ResponseContainer.failed('parameter :{servicePackage} not presented'))
        service_package = request.GET.get('servicePackage')
        hermes_target_app = HermesTargetAPP.objects.filter(appPackage=service_package).first()
        if hermes_target_app is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("service %s not exist ,please install first"))
        query_condition = 'mac not in (select device_mac from hermes_device_service where app_package=\'%s\' and status=true)' % service_package
        installed_count = 0
        while True:
            uninstall_devices = HermesDevice.objects.extra(where=[query_condition]).all()[0:1024]
            if len(uninstall_devices) == 0:
                break
            for device in uninstall_devices:
                ob, created = HermesDevicePackage.objects.update_or_create(appPackage=service_package,
                                                                           deviceMac=device.mac,
                                                                           defaults={'status': True})
                if created:
                    installed_count += 1
        return ForceDumpJsonResponse(ResponseContainer.success(installed_count))


class DeployAllServiceForDeviceView(View):
    """在一个设备上面，安装所有的服务"""

    def get(self, request):
        device_mac = request.GET.get('deviceMac', None)
        if device_mac is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{deviceMac} not presented"))
        hermes_device = HermesDevice.objects.filter(mac=device_mac).first()
        if hermes_device is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("device %s not exist") % device_mac)

        query_condition = 'app_package not in (select app_package from hermes_device_service where device_mac=\'%s\')' % device_mac
        installed_count = 0
        while True:
            uninstall_target_appes = HermesTargetAPP.objects.extra(where=[query_condition]).all()[0:1024]
            if len(uninstall_target_appes) == 0:
                break
            for uninstall_target_app in uninstall_target_appes:
                ob, created = HermesDevicePackage.objects.update_or_create(appPackage=uninstall_target_app.appPackage,
                                                                           deviceMac=device_mac,
                                                                           defaults={'status': True})
                if created:
                    installed_count += 1

        while True:
            need_update_services = HermesDevicePackage.objects.filter(deviceMac=device_mac, status=False).all()[0:1024]
            if len(need_update_services) == 0:
                break
            for need_update in need_update_services:
                HermesDevicePackage.objects.filter(appPackage=need_update.appPackage,
                                                   deviceMac=need_update.deviceMac).update(status=True)
                installed_count += 1
        return ForceDumpJsonResponse(ResponseContainer.success(installed_count))


class DeployOneServiceView(View):
    """安装单个服务，指定app和设备"""

    def get(self, request):
        device_mac = request.GET.get('deviceMac', None)
        if device_mac is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{deviceMac} not presented"))
        target_package = request.GET.get('targetService', None)
        if target_package is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{targetService} not presented"))
        enabled = to_boolean(request.GET.get('enabled', None))

        existed = HermesDevicePackage.objects.filter(appPackage=target_package, deviceMac=device_mac).first()
        if existed is not None:
            existed.status = enabled
            existed.save()
            return ForceDumpJsonResponse(ResponseContainer.success("success"))

        hermes_target_app = HermesTargetAPP.objects.filter(appPackage=target_package).first()
        if hermes_target_app is None:
            return ForceDumpJsonResponse(
                ResponseContainer.failed("service %s not exist ,please install first") % hermes_target_app)
        hermes_device = HermesDevice.objects.filter(mac=device_mac).first()
        if hermes_device is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("device %s not exist") % device_mac)
        hermes_device_service, created = HermesDevicePackage.objects.update_or_create(
            appPackage=target_package,
            deviceMac=device_mac,
            defaults={
                'status': enabled
            }
        )
        return ForceDumpJsonResponse(ResponseContainer.success(hermes_device_service))


class DeployServiceForDeviceView(View):
    def get(self, request):
        device_mac = request.GET.get('deviceMac', None)
        if device_mac is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{deviceMac} not presented"))
        target_package_list = request.GET.getlist('targetServiceList', None)
        if target_package_list is None or len(target_package_list) == 0:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{targetServiceList} not presented"))
        hermes_device = HermesDevice.objects.filter(mac=device_mac).first()
        if hermes_device is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("device %s not exist") % device_mac)

        # 检查是不是填写了不合法的service list
        existed_app_list = HermesTargetAPP.objects.extra(where=[
            "app_package  in (" + ",".join(map(lambda package: '\'%s\'' % package, target_package_list)) + ")"]).all()
        existed_app_map = {}
        for target_app_model in existed_app_list:
            existed_app_map[target_app_model.appPackage] = target_app_model

        for target_package in target_package_list:
            if target_package not in existed_app_map:
                return ForceDumpJsonResponse(
                    ResponseContainer.failed(
                        "the service :{%s} not installed, please install service app first" % target_package))

        # 正式安装服务
        for target_package in target_package_list:
            HermesDevicePackage.objects.update_or_create(
                appPackage=target_package,
                deviceMac=device_mac,
                defaults={
                    'status': True
                }
            )
        return ForceDumpJsonResponse(ResponseContainer.success("success"))


class DeployServiceForTargetAppView(View):
    def get(self, request):
        # 参数合法性检查
        target_package = request.GET.get('targetService', None)
        if target_package is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{targetService} not presented"))
        device_mac_list = request.GET.getlist('deviceMacList', None)
        if device_mac_list is None or len(device_mac_list) == 0:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param:{deviceMac} not presented"))

        # 数据存在检查
        hermes_target_app = HermesTargetAPP.objects.filter(appPackage=target_package).first()
        if hermes_target_app is None:
            return ForceDumpJsonResponse(
                ResponseContainer.failed("service %s not exist ,please install first") % hermes_target_app)
        existed_device_list = HermesDevice.objects.extra(
            where=["mac  in (" + ",".join(map(lambda package: '\'%s\'' % package, device_mac_list)) + ")"]).all()
        existed_device_map = {}

        def map_function(device_model):
            existed_device_map[device_model.mac] = device_model

        map(map_function, existed_device_list)
        for device in device_mac_list:
            if device not in existed_device_list:
                return ForceDumpJsonResponse(
                    ResponseContainer.failed(
                        "the device :{%s} not existed ,install failed" % device))
        for device in device_mac_list:
            HermesDevicePackage.objects.update_or_create(
                appPackage=target_package,
                deviceMac=device,
                defaults={
                    'status': True
                }
            )
        return ForceDumpJsonResponse(ResponseContainer.success("success"))
