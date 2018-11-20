package com.virjar.hermesadmin.service.servicemanager;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.virjar.hermesadmin.entity.ReportModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentMap;

/**
 * Created by virjar on 2018/9/6.<br>
 */
@Service
public class AppServiceRegistry {
    @Value("${app.registry.useRedis}")
    private boolean useRedis;

    private ConcurrentMap<String, ServiceQueue> serviceQueueConcurrentMap = Maps.newConcurrentMap();

    private ServiceQueue createOrGet(String appPackage) {
        ServiceQueue serviceQueue = serviceQueueConcurrentMap.get(appPackage);
        if (serviceQueue != null) {
            return serviceQueue;
        }
        if (useRedis) {
            serviceQueue = new RedisServiceQueue();
        } else {
            serviceQueue = new RamServiceQueue();
        }
        return serviceQueueConcurrentMap.putIfAbsent(appPackage, serviceQueue);
    }


    public void handleReport(ReportModel reportModel) {
        String mac = reportModel.getMac();
        for (String service : reportModel.getOnlineServices()) {
            createOrGet(service).online(mac);
        }
    }

    public String rollPoling(String service) {
        return createOrGet(service).rollPoling();
    }

    public void offline(String service, String mac) {
        createOrGet(service).offline(mac);
    }

    public List<String> serviceList() {
        List<String> ret = Lists.newArrayList();
        for (Map.Entry<String, ServiceQueue> entry : serviceQueueConcurrentMap.entrySet()) {
            if (entry.getValue().macSize() > 0) {
                ret.add(entry.getKey());
            }
        }
        return ret;
    }
}
