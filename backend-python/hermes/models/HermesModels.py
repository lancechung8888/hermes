#!/usr/bin/env python
# encoding: utf-8

from django.db import models


class HermesDevice(models.Model):
    class Meta:
        db_table = 'hermes_device'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, null=False, default='')
    ip = models.CharField(max_length=128, null=False, default='')
    port = models.IntegerField()
    mac = models.CharField(max_length=128, null=False, default='')
    brand = models.CharField(max_length=128, null=False, default='')
    systemVersion = models.CharField(max_length=128, null=False, default='', db_column='system_version')
    status = models.BooleanField(default=False)
    visibleIp = models.CharField(max_length=128, null=False, default='', db_column='visible_ip')
    cpuUsage = models.CharField(max_length=128, null=False, db_column='cpu_usage')
    memory = models.CharField(max_length=128, null=False)
    lastReportTime = models.DateTimeField(null=False, db_column='last_report_time')
    lastReportService = models.TextField(null=False, db_column='last_report_service')


class HermesTargetAPP(models.Model):
    class Meta:
        db_table = 'hermes_target_app'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, null=False, default='')
    appPackage = models.CharField(max_length=128, null=False, default='', db_column='app_package')
    version = models.CharField(max_length=128, null=False, default='')
    savePath = models.CharField(max_length=128, null=False, default='', db_column='save_path')
    downloadUrl = models.CharField(max_length=128, null=False, default='', db_column='download_url')
    versionCode = models.CharField(max_length=128, null=False, default='', db_column='version_code')
    enabled = models.BooleanField(default=True)


class HermesWrapperAPK(models.Model):
    class Meta:
        db_table = 'hermes_wrapper_apk'

    id = models.AutoField(primary_key=True)
    version = models.CharField(max_length=128, null=False, default='')
    savePath = models.CharField(max_length=128, null=False, default='', db_column='save_path')
    enabled = models.BooleanField(default=False)
    apkPackage = models.CharField(max_length=128, null=False, default='', db_column='apk_package')
    versionCode = models.CharField(max_length=128, null=False, default='', db_column='version_code')
    downloadUrl = models.CharField(max_length=128, null=False, default='', db_column='download_url')
    targetApkPackage = models.CharField(max_length=128, null=False, default='', db_column='target_apk_package')


class HermesDevicePackage(models.Model):
    class Meta:
        db_table = 'hermes_device_service'

    id = models.AutoField(primary_key=True)
    targetAppId = models.IntegerField(null=True, db_column='target_app_id')
    deviceId = models.IntegerField(null=True, db_column='device_id')
    status = models.BooleanField(default=True)
    appPackage = models.CharField(max_length=128, null=False, default='', db_column='app_package')
    deviceMac = models.CharField(max_length=128, null=False, default='', db_column='device_mac')


class ServiceDetail(object):
    """下发给设备的配置信息，服务维度，包括apk版本，wrapper版本，以及对应的下载地址"""

    def __init__(self):
        self.serviceId = None
        self.status = False
        self.deviceMac = None
        self.targetAppPackage = None
        self.targetAppVersionCode = -1
        self.targetAppDownloadUrl = None
        self.wrapperPackage = None
        self.wrapperVersionCode = -1
        self.wrapperAppDownloadUrl = None
