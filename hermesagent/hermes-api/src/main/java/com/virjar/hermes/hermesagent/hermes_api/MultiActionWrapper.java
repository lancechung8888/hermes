package com.virjar.hermes.hermesagent.hermes_api;

import com.google.common.collect.Maps;
import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeRequest;
import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeResult;
import com.virjar.xposed_extention.SharedObject;

import java.util.Map;

public abstract class MultiActionWrapper extends ExternalWrapperAdapter {
    private static final String action = "action";

    public MultiActionWrapper() {
        this.init();
    }

    protected void init() {

    }

    protected String defaultAction() {
        return null;
    }

    @Override
    public InvokeResult invoke(InvokeRequest invokeRequest) {
        String action = invokeRequest.getString(MultiActionWrapper.action);
        if (action == null || action.trim().isEmpty()) {
            action = defaultAction();
        }
        if (action == null || action.trim().isEmpty()) {
            return InvokeResult.failed("the param:{" + MultiActionWrapper.action + "} not presented");
        }
        RequestHandler requestHandler = requestHandlerMap.get(action.toLowerCase());
        if (requestHandler == null) {
            return InvokeResult.failed("unknown action: " + action);
        }
        Object handlerResult = requestHandler.handleRequest(invokeRequest);
        if (handlerResult == null) {
            return InvokeResult.failed("handler return null, wrapper logic error");
        }
        if (handlerResult instanceof InvokeResult) {
            return (InvokeResult) handlerResult;
        }
        if (handlerResult instanceof Throwable) {
            APICommonUtils.requestLogE(invokeRequest, "handler throw an exception", (Throwable) handlerResult);
            return InvokeResult.failed(APICommonUtils.translateSimpleExceptionMessage((Throwable) handlerResult));
        }

        if (!(handlerResult instanceof AsyncResult)) {
            return InvokeResult.success(handlerResult, SharedObject.context);
        }

        AsyncResult asyncResult = (AsyncResult) handlerResult;
        asyncResult.waitCallback(waitTimeout());
        if (!asyncResult.isCallbackCalled()) {
            return InvokeResult.failed("Request TimeOut");
        }
        return InvokeResult.success(asyncResult.finalResult(), SharedObject.context);
    }


    protected void registryHandler(String action, RequestHandler requestHandler) {
        requestHandlerMap.put(action, requestHandler);
    }

    protected long waitTimeout() {
        return 6500L;
    }

    private Map<String, RequestHandler> requestHandlerMap = Maps.newHashMap();

    protected interface RequestHandler {
        Object handleRequest(InvokeRequest invokeRequest);
    }

    public class AsyncResult {
        private Object data;
        private boolean callbackCalled = false;
        private final Object lock = new Object();


        void waitCallback(long timeOUt) {
            if (callbackCalled) {
                return;
            }
            synchronized (lock) {
                try {
                    lock.wait(timeOUt);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }

        public void notifyDataArrival(Object responseData) {
            data = responseData;
            synchronized (lock) {
                lock.notify();
                callbackCalled = true;
            }
        }

        Object finalResult() {
            if (!callbackCalled) {
                return "timeOut";
            }
            return data;
        }

        boolean isCallbackCalled() {
            return callbackCalled;
        }
    }
}
