#!/usr/bin/env python
# encoding: utf-8

import logging
import os
import tempfile
import urllib

from django import http
from django.core.paginator import Paginator
from django.views.generic import View

from apkutils.apk import APK
from backend_python.utils import get_upload_path
from hermes.models.HermesModels import HermesWrapperAPK
from hermes.views.HermesUtil import ResponseContainer, ForceDumpJsonResponse, to_boolean

logger = logging.getLogger(__name__)

no_hermes_target_package_define_error_message = """
error apk file,meta-data{hermes_target_package=wrapper for target app} define in AndroidManifest.xml
"""


class UploadHermesWrapperApkView(View):
    def __init__(self, **kwargs):
        super(UploadHermesWrapperApkView, self).__init__(**kwargs)

    @staticmethod
    def parse_target_package_name(manifest):
        if 'application' not in manifest:
            return ForceDumpJsonResponse(
                ResponseContainer.failed("error apk file,not application node in AndroidManifest.xml"))
        application = manifest['application']
        if 'meta-data' not in application:
            return ForceDumpJsonResponse(
                ResponseContainer.failed(no_hermes_target_package_define_error_message))
        meta_data_nodes = application['meta-data']
        if isinstance(meta_data_nodes, dict):
            meta_data_nodes = [meta_data_nodes]

        for meta_data_node in meta_data_nodes:
            if meta_data_node['@android:name'] == 'hermes_target_package':
                return meta_data_node['@android:value']
        return None

    def post(self, request):
        apk_file = request.FILES['agentAPK']
        temp_apk_file = tempfile.mktemp()
        f = open(temp_apk_file, 'wb')
        try:
            for chunk in apk_file.chunks():
                f.write(chunk)
        finally:
            f.close()

        try:
            apk = APK(temp_apk_file)
            manifest = apk.get_manifest()
        except Exception as e:
            logger.error('the upload file is not a apk format %s', e)
            return ForceDumpJsonResponse(ResponseContainer.failed("the upload file is not a apk format"))

        apk_package = manifest['@package']
        version_name = manifest['@android:versionName']
        version_code = manifest['@android:versionCode']
        hermes_target_package = self.parse_target_package_name(manifest)
        if hermes_target_package is None:
            return ForceDumpJsonResponse(
                ResponseContainer.failed(no_hermes_target_package_define_error_message))
        if isinstance(hermes_target_package, ForceDumpJsonResponse):
            return hermes_target_package

        # todo 这里可能对于某个特定的target package,存在多个不同的wrapper package，这可能导致紊乱，后续考虑拦截
        logger.info(
            'upload a new apk file:%s  version code:%s  version name:%s' % (apk_package, version_code, version_name))
        hermes_target_app = HermesWrapperAPK.objects.filter(apkPackage=apk_package, versionCode=version_code).first()
        if hermes_target_app is not None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the file has upload already"))
        if apk_package == 'com.virjar.hermes.hermesagent':
            error_message = 'you can`not upload hermes agent apk for target app upload api'
            return ForceDumpJsonResponse(ResponseContainer.failed(error_message))

        # now gen a file name id,for tos storage
        tos_id = 'hermes_wrapper_app_' + urllib.quote(apk_package) + '_' + version_code + '_' + urllib.quote(
            version_name) + '.apk'
        file_name = 'hermes_wrapper_app_' + urllib.quote(apk_package) + '_' + version_code + '_' + urllib.quote(
            version_name) + '.apk'
        save_file_path = get_upload_path('wrapper') + '\\' + file_name
        try:
            with open(temp_apk_file, 'rb') as fr:
                with open(save_file_path, "wb") as fw:
                    fw.write(fr.read())
        except Exception as e:
            logger.error('upload to  hermesAdmin failed', exc_info=True)
            return ForceDumpJsonResponse(
                ResponseContainer.failed('upload to tos platform failed %s' % e))
        finally:
            f.close()
        os.remove(temp_apk_file)
        hermes_target_app = {
            'version': version_name,
            'downloadUrl': None,
            'savePath': save_file_path,
            'targetApkPackage': hermes_target_package,
            'enabled': False
        }
        hermes_target_app = HermesWrapperAPK.objects.update_or_create(
            apkPackage=apk_package,
            versionCode=version_code,
            defaults=dict(hermes_target_app)
        )
        return ForceDumpJsonResponse(ResponseContainer.success(hermes_target_app))


class ListHermesWrapperApkView(View):
    """targetAPK列表，带有分页功能"""

    def get(self, request):
        page = request.GET.get('page', 0)
        page = int(page) + 1
        pagesize = request.GET.get('size', 10)
        pagesize = max(0, min(pagesize, 10))
        query = HermesWrapperAPK.objects
        target_app_package = request.GET.get('targetAppPackage', None)
        if target_app_package is not None:
            query = query.filter(targetApkPackage=target_app_package)
        p = Paginator(query.order_by('-id').all(), pagesize)
        return ForceDumpJsonResponse(ResponseContainer.success(p.page(page)))


class DownloadHermesWrapperApkView(View):
    def get(self, request):
        #TODO
        apk_id = request.GET.get('apkId')
        if apk_id is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the parameter :{apkId} is not presented"))
        wrapper_apk = HermesWrapperAPK.objects.filter(id=apk_id).first()
        if wrapper_apk is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("record not fond"))
        return http.HttpResponseRedirect(wrapper_apk.download_url)


class SetWrapperStatusView(View):
    def get(self, request):
        wrapper_id = request.GET.get('wrapperId', None)
        if wrapper_id is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the parameter :{wrapperId} is not presented"))
        status = to_boolean(request.GET.get('status', None))
        wrapper_apk = HermesWrapperAPK.objects.filter(id=wrapper_id).first()
        if wrapper_apk is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("record not fond"))
        # wrapper 永远只能保证一个在线，所以其他的全部给下去
        for need_offline_wrapper in HermesWrapperAPK.objects.filter(targetApkPackage=wrapper_apk.targetApkPackage,
                                                                    enabled=True).all():
            HermesWrapperAPK.objects.filter(id=need_offline_wrapper.id).update(enabled=False)
        # HermesWrapperAPK.objects.filter(targetApkPackage=wrapper_apk.targetApkPackage).update(enabled=False)
        real_status = 'true' == str(status).lower()
        if real_status:
            HermesWrapperAPK.objects.filter(id=wrapper_id).update(enabled=True)
        return ForceDumpJsonResponse(ResponseContainer.success("ok"))


class EnabledWrapper(View):
    def get(self, request):
        target_package = request.GET.get('targetPackage', None)
        if target_package is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("the param :{targetPackage} is not presented"))
        hermes_wrapper_apk = HermesWrapperAPK.objects.filter(targetApkPackage=target_package, enabled=True).first()
        if hermes_wrapper_apk is None:
            return ForceDumpJsonResponse(ResponseContainer.failed("record not found"))
        return ForceDumpJsonResponse(ResponseContainer.success(hermes_wrapper_apk))
