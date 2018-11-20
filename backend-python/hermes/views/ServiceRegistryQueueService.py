#!/usr/bin/env python
# encoding: utf-8


from django.views.generic import View

from hermes.models.HermesModels import HermesDevice
from hermes.models.ServiceRegistry import registry
from hermes.views.HermesUtil import ResponseContainer, ForceDumpJsonResponse


class ServiceQueueListView(View):
    def get(self, request):
        if 'servicePackage' not in request.GET:
            return ForceDumpJsonResponse(ResponseContainer.failed('parameter :{servicePackage} not presented'))
        queue = registry.queue_status(request.GET.get('servicePackage'))
        queue_status_view = []
        for entry in queue:
            device = HermesDevice.objects.filter(mac=entry.mac).first()
            queue_status_view.append({
                'mac': entry.mac,
                'score': entry.score,
                'lastReportTime': entry.lastReportTime,
                'ip': device.ip,
                'port': device.port
            })
        return ForceDumpJsonResponse(ResponseContainer.success(queue_status_view))


class ResetQueueView(View):
    def get(self, request):
        if 'servicePackage' not in request.GET:
            return ForceDumpJsonResponse(ResponseContainer.failed('parameter :{servicePackage} not presented'))
        registry.reset_queue(request.GET.get('servicePackage'))
        return ForceDumpJsonResponse(ResponseContainer.success("ok"))
