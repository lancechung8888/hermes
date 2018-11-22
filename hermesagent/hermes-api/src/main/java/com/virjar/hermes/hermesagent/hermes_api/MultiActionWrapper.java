package com.virjar.hermes.hermesagent.hermes_api;

import android.support.annotation.Nullable;

import com.google.common.base.Preconditions;
import com.google.common.collect.Maps;
import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeRequest;
import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeResult;
import com.virjar.xposed_extention.SharedObject;

import java.util.Map;

/**
 * 通用的wrapper基类，支持多种action路由功能，屏蔽回调函数中一些为了功能完整性定制的但是实际上很少使用的接口。
 * 提供异步返回场景的封装（Android中大量存在异步回调，导致无法直接拿到返回值，需要通过信号通知的方式）。
 */
public abstract class MultiActionWrapper extends ExternalWrapperAdapter {
    private static final String action = "action";

    /**
     * 存在一个默认的action，为了兼容一些老接口，由于接口刚刚开发的是，只有一个api。那个时候没有使用多action机制。后来多action机制上线之后，不能影响老的接口
     *
     * @return action名字，默认为Null
     */
    @Nullable
    protected String defaultAction() {
        return null;
    }

    /**
     * 在异步场景，等待时间，我们不能无限制的等待异步回调。默认6.5s，为啥6.5。我拍脑门
     *
     * @return 等待时间
     */
    protected long waitTimeout() {
        return 6500L;
    }

    /**
     * action是否忽略大小写，默认忽略
     *
     * @return 是否忽略大小写
     */
    protected boolean actionCaseIgnore() {
        return true;
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
        action = actionCaseIgnore() ? action.toLowerCase() : action;
        RequestHandler requestHandler = requestHandlerMap.get(action);
        if (requestHandler == null) {
            return InvokeResult.failed("unknown action: " + action);
        }
        Object handlerResult = requestHandler.handleRequest(invokeRequest);
        InvokeResult result = tryWrap(invokeRequest, handlerResult);
        if (result != null) {
            return result;
        }
        AsyncResult asyncResult = (AsyncResult) handlerResult;
        asyncResult.waitCallback(waitTimeout());
        if (!asyncResult.isCallbackCalled()) {
            return InvokeResult.failed("Request TimeOut");
        }
        return tryWrap(invokeRequest, asyncResult.finalResult());
    }

    private InvokeResult tryWrap(InvokeRequest invokeRequest, Object handlerResult) {
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
        return null;
    }


    protected void registryHandler(String action, RequestHandler requestHandler) {
        Preconditions.checkNotNull(action);
        action = actionCaseIgnore() ? action.toLowerCase() : action;
        requestHandlerMap.put(action, requestHandler);
    }


    private Map<String, RequestHandler> requestHandlerMap = Maps.newHashMap();

    /**
     * handle处理抽象，正对于不同action的路由处理
     */
    protected interface RequestHandler {
        Object handleRequest(InvokeRequest invokeRequest);
    }


    /**
     * 方便链式
     */
    public abstract class AsyncResultBuilder {
        private AsyncResult asyncResult = new AsyncResult();

        public abstract void bind(AsyncResult asyncResult);

        public AsyncResult build() {
            bind(asyncResult);
            return asyncResult;
        }
    }

    /**
     * 如果返回值是这个类型，那么证明结果是异步的，我将会等待异步结果返回
     */
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

        /**
         * 异步返回，需要主动调用这个接口通知数据到达，唤醒http request线程，进行数据回传
         *
         * @param responseData 异步返回结果，可以是任何类型
         */
        public void notifyDataArrival(Object responseData) {
            Preconditions.checkArgument(!(responseData instanceof AsyncResult), "async response can not be a AsyncResult type");
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
