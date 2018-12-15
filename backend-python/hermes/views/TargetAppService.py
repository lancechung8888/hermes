#!/usr/bin/env python
# encoding: utf-8

import logging
import os
import tempfile
import urllib

from django.core.paginator import Paginator
from django.views.generic import View

from apkutils.apk import APK
from backend_python import settings
from hermes.models.HermesModels import HermesTargetAPP
from hermes.views.HermesUtil import ResponseContainer, ForceDumpJsonResponse, to_boolean

logger = logging.getLogger(__name__)
from backend_python.settings import upload_path
# from pytos import tos
from django import http


# from pyutil.program.fmtutil import fmt_exception


class UploadTargetApkView(View):
    def __init__(self, **kwargs):
        super(UploadTargetApkView, self).__init__(**kwargs)

    def post(self, request):
        apk_file = request.FILES['agentAPK']
        temp_apk_file = tempfile.mktemp()
        f = open(temp_apk_file, 'wb')
        logger.info("create temp file for write apk:%s" % temp_apk_file)
        try:
            for chunk in apk_file.chunks():
                f.write(chunk)
        finally:
            f.close()

        try:
            apk = APK(temp_apk_file)
            manifest = apk.get_manifest()
        except Exception:
            logger.error('the upload file is not a apk format', exc_info=True)
            return ForceDumpJsonResponse(ResponseContainer.failed("the upload file is not a apk format"))

        apk_package = manifest['@package']
        version_name = manifest['@android:versionName']
        version_code = manifest['@android:versionCode']
        logger.info(
            'upload a new apk file:%s  version code:%s  version name:%s' % (apk_package, version_code, version_name))
        hermes_target_app = HermesTargetAPP.objects.filter(appPackage=apk_package, versionCode=version_code).first()
        if hermes_target_app is not None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the file has upload already"))
        if apk_package == 'com.virjar.hermes.hermesagent':
            error_message = 'you can`not upload hermes agent apk for target app upload api'
            return ForceDumpJsonResponse(ResponseContainer.failed(error_message))

        # now gen a file name id,for tos storage
        file_name = 'hermes_target_app_' + urllib.quote(apk_package) + '_' + version_code + '_' + urllib.quote(
            version_name) + '.apk'
        save_file_path = upload_path + '\\' + file_name
        try:
            with open(temp_apk_file, 'rb') as fr:
                with open(save_file_path, "wb") as fw:
                    fw.write(fr.read())
        except Exception as e:
            logger.error('upload to tos platform failed', exc_info=True)
            return ForceDumpJsonResponse(
                ResponseContainer.failed('upload to tos platform failed %s' % e))
        finally:
            f.close()
        os.remove(temp_apk_file)
        # tos_url = '/hermes/targetApp/download?apkId='
        # logger.info('apk文件上传到tos平台，下载地址为：%s' % tos_url)
        hermes_target_app = {
            'name': apk_package,
            'appPackage': apk_package,
            'versionCode': version_code,
            'version': version_name,
            'savePath':save_file_path,
            'downloadUrl': None,
            'enabled': True
        }
        hermes_target_app = HermesTargetAPP.objects.update_or_create(appPackage=apk_package,
                                                                     versionCode=version_code,
                                                                     defaults=hermes_target_app)
        return ForceDumpJsonResponse(ResponseContainer.success(hermes_target_app))


class ListTargetApkView(View):
    """targetAPK列表，带有分页功能"""

    def get(self, request):
        page = request.GET.get('page', 0)
        page = int(page) + 1
        pagesize = request.GET.get('size', 10)
        pagesize = max(0, min(pagesize, 10))
        query = HermesTargetAPP.objects
        device_mac = request.GET.get("mac", None)
        if device_mac is not None:
            query_condition = 'app_package  in (select app_package from hermes_device_service where device_mac=\'%s\' and status=true)' % device_mac
            query = query.extra(where=[query_condition])
        p = Paginator(query.order_by('-id').all(), pagesize)
        return ForceDumpJsonResponse(ResponseContainer.success(p.page(page)))


class ListAvailableServiceView(View):
    def get(self, request):
        page = request.GET.get('page', 0)
        page = int(page) + 1
        pagesize = request.GET.get('size', 10)
        pagesize = max(0, min(pagesize, 10))
        device_mac = request.GET.get("mac", None)
        if device_mac is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param: {mac} not presented"))
        query_condition = 'app_package not in (select app_package from hermes_device_service where device_mac=\'%s\' and status=true)' % device_mac
        return ForceDumpJsonResponse(ResponseContainer.success(
            Paginator(HermesTargetAPP.objects.extra(where=[query_condition]).order_by('-id').all(), pagesize).page(
                page)))


class DownloadTargetApkView(View):
    def get(self, request):
        apk_id = request.GET.get('apkId')
        if apk_id is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the parameter :{apkId} is not presented"))
        logger.info("download apk is not support for toutiao hermes admin system,forward to tos platform")
        hermes_target_app = HermesTargetAPP.objects.filter(id=apk_id).first()
        if hermes_target_app is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("record not fond"))
        return http.HttpResponseRedirect(hermes_target_app.download_url)


class SetTargetAppStatusView(View):
    def get(self, request):
        wrapper_id = request.GET.get('targetAppId', None)
        if wrapper_id is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the parameter :{wrapperId} is not presented"))
        status = to_boolean(request.GET.get('status', None))

        target_app = HermesTargetAPP.objects.filter(id=wrapper_id).first()
        if target_app is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("record not found"))
        if target_app.enabled == status:
            logger.info("the app:{%s} status is:%s already" % (wrapper_id, status))
            return ForceDumpJsonResponse(ResponseContainer.success("success"))
        HermesTargetAPP.objects.filter(id=wrapper_id).update(enabled=status)
        return ForceDumpJsonResponse(ResponseContainer.success("ok"))
