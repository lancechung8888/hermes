package com.virjar.hermesadmin.service.servicemanager;

/**
 * Created by virjar on 2018/9/6.
 */
public class RedisServiceQueue implements ServiceQueue {
    public RedisServiceQueue() {
        throw new UnsupportedOperationException("not implemented");
    }

    @Override
    public void online(String mac) {

    }

    @Override
    public void offline(String mac) {

    }

    @Override
    public String rollPoling() {
        return null;
    }

    @Override
    public int macSize() {
        return 0;
    }
}
