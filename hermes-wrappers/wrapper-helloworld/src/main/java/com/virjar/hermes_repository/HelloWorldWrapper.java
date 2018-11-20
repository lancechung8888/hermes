package com.virjar.hermes_repository;

import com.virjar.hermes.hermesagent.hermes_api.AgentCallback;
import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeRequest;
import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeResult;
import com.virjar.xposed_extention.SharedObject;

import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class HelloWorldWrapper implements AgentCallback {
    @Override
    public boolean needHook(XC_LoadPackage.LoadPackageParam loadPackageParam) {
        return true;
    }

    @Override
    public InvokeResult invoke(InvokeRequest invokeRequest) {
        return InvokeResult.success("hello world!", SharedObject.context);
    }

    @Override
    public void onXposedHotLoad() {

    }
}
