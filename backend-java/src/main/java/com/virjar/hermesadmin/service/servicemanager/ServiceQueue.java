package com.virjar.hermesadmin.service.servicemanager;

/**
 * Created by virjar on 2018/9/6.
 */
public interface ServiceQueue {
    void online(String mac);

    void offline(String mac);

    String rollPoling();

    int macSize();
}
