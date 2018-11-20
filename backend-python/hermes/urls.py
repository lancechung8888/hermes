# coding: utf8

from django.http import HttpResponseRedirect

try:
    from django.conf.urls.defaults import url # django1.6 or higher has removen defaults
except:
    from django.conf.urls import url  # higher version of django
import backend_python.settings
from hermes.views import TargetAppService, HermesWrapperService, HermesDeviceService, HermesServcieService, \
    ServiceRegistryQueueService
from django.views.generic import TemplateView
from django.conf.urls.static import static


def prod_static_url():
    '''
    prod 模式下的 url 适配
    '''
    from django.views import static
    urlpattern = url(r'^hermes/static/(?P<path>.*)$', static.serve, {'document_root': backend_python.settings.STATIC_ROOT},
                     name='static')
    return urlpattern

# Urls
urlpatterns = [
    url(r'^$', lambda request: HttpResponseRedirect("/hermes/static/index.html")),
    url(r'hermes/$', lambda request: HttpResponseRedirect("/hermes/static/index.html")),
    # 设备相关api
    url(r'hermes/device/list$', HermesDeviceService.ListDeviceView.as_view()),
    url(r'hermes/device/listAvailableDevice$', HermesDeviceService.ListAvailableDeviceView.as_view()),
    url(r'hermes/device/invoke$', HermesDeviceService.InvokeHandlerView.as_view()),
    url(r'hermes/device/report$', HermesDeviceService.DeviceReportView.as_view()),
    url(r'hermes/device/setStatus$', HermesDeviceService.SetDeviceStatusView.as_view()),
    url(r'hermes/device/deviceIpList$', HermesDeviceService.DeviceIpListView.as_view()),

    #  targetAPK相关API
    url(r'hermes/targetApp/upload$', TargetAppService.UploadTargetApkView.as_view()),
    url(r'hermes/targetApp/list$', TargetAppService.ListTargetApkView.as_view()),
    url(r'hermes/targetApp/listAvailableService$', TargetAppService.ListAvailableServiceView.as_view()),
    url(r'hermes/targetApp/download$', TargetAppService.ListTargetApkView.as_view()),
    url(r'hermes/targetApp/setStatus$', TargetAppService.SetTargetAppStatusView.as_view()),

    #  wrapper相关API
    url(r'hermes/wrapperApp/upload$', HermesWrapperService.UploadHermesWrapperApkView.as_view()),
    url(r'hermes/wrapperApp/list$', HermesWrapperService.ListHermesWrapperApkView.as_view()),
    url(r'hermes/wrapperApp/download$', HermesWrapperService.DownloadHermesWrapperApkView.as_view()),
    url(r'hermes/wrapperApp/setStatus$', HermesWrapperService.SetWrapperStatusView.as_view()),
    url(r'hermes/wrapperApp/usedWrapper$', HermesWrapperService.EnabledWrapper.as_view()),

    # service 相关API，service 是app_package 和 device 两者笛卡尔积维度
    url(r'hermes/service/list$', HermesServcieService.ListDeviceServiceView.as_view()),
    url(r'hermes/service/deployAllDevice$', HermesServcieService.DeployServiceToAllDeviceView.as_view()),
    url(r'hermes/service/deployAllService$', HermesServcieService.DeployAllServiceForDeviceView.as_view()),
    url(r'hermes/service/installOne$', HermesServcieService.DeployOneServiceView.as_view()),
    url(r'hermes/service/installServiceForDevice$', HermesServcieService.DeployServiceForDeviceView.as_view()),
    url(r'hermes/service/installServiceForTargetApp$', HermesServcieService.DeployServiceForTargetAppView.as_view()),

    url(r'hermes/queue/queueStatus$', ServiceRegistryQueueService.ServiceQueueListView.as_view()),
    url(r'hermes/queue/reset', ServiceRegistryQueueService.ResetQueueView.as_view()),
    url(r'^hermes/static/?$', TemplateView.as_view(template_name="index.html")),
    prod_static_url(),
]

urlpatterns += static(backend_python.settings.STATIC_URL, document_root=backend_python.settings.STATIC_ROOT)
