package com.virjar.hermesadmin.service.servicemanager;

import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import lombok.Data;

import java.util.Set;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.LinkedBlockingDeque;

/**
 * Created by virjar on 2018/9/6.<br>
 * 基于内存实现的队列
 */
public class RamServiceQueue implements ServiceQueue {
    private LinkedBlockingDeque<ServiceResourceEntry> queue = new LinkedBlockingDeque<>();
    private ConcurrentMap<String, ServiceResourceEntry> resourceMap = Maps.newConcurrentMap();
    private Set<String> leaveDevices = Sets.newConcurrentHashSet();

    @Override

    public void online(String mac) {
        ServiceResourceEntry serviceResourceEntry = resourceMap.get(mac);
        if (serviceResourceEntry != null) {
            serviceResourceEntry.setLastReportTimestamp(System.currentTimeMillis());
            if (leaveDevices.contains(mac)) {
                queue.add(serviceResourceEntry);
            }
            return;
        }
        serviceResourceEntry = new ServiceResourceEntry();
        serviceResourceEntry.setLastReportTimestamp(System.currentTimeMillis());
        serviceResourceEntry.setMac(mac);
        resourceMap.putIfAbsent(mac, serviceResourceEntry);

        serviceResourceEntry = resourceMap.get(mac);
        queue.add(serviceResourceEntry);
    }

    @Override
    public void offline(String mac) {
        ServiceResourceEntry serviceResourceEntry = resourceMap.get(mac);
        if (serviceResourceEntry == null) {
            return;
        }
        serviceResourceEntry.setLastReportTimestamp(-1L);
    }

    @Override
    public String rollPoling() {
        while (true) {
            ServiceResourceEntry serviceResourceEntry = queue.poll();
            if (serviceResourceEntry == null) {
                return null;
            }
            if (!resourceMap.containsKey(serviceResourceEntry.getMac())) {
                continue;
            }
            if (serviceResourceEntry.getLastReportTimestamp() < 0) {
                leaveDevices.add(serviceResourceEntry.getMac());
                continue;
            }
            //两分钟没有上报信息,则认为该服务已经下线
            if (System.currentTimeMillis() - serviceResourceEntry.getLastReportTimestamp() > 120000) {
                continue;
            }
            queue.add(serviceResourceEntry);
            return serviceResourceEntry.getMac();
        }
    }

    @Override
    public int macSize() {
        return queue.size();
    }

    @Data
    private class ServiceResourceEntry {
        private String mac;
        long lastReportTimestamp = 0;

    }
}
