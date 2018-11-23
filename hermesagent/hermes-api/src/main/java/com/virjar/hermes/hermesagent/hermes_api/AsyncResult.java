package com.virjar.hermes.hermesagent.hermes_api;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONException;
import com.google.common.base.Preconditions;
import com.virjar.xposed_extention.ClassLoadMonitor;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

import de.robv.android.xposed.XposedHelpers;

/**
 * 如果返回值是这个类型，那么证明结果是异步的，我将会等待异步结果返回
 *
 * @author dengweijia
 * @since 1.4
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
            if (callbackCalled) {
                return;
            }
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

    /**
     * 方便链式
     */
    public static abstract class AsyncResultBuilder {
        private AsyncResult asyncResult = new AsyncResult();

        public abstract void bind(AsyncResult asyncResult);

        public AsyncResult build() {
            bind(asyncResult);
            return asyncResult;
        }
    }

    public static AsyncResult wrapRxJava(Object rxJavaObserver) {
        return wrapRxJava(rxJavaObserver, "rx.Observer", "subscribe");
    }

    public static AsyncResult wrapRxJava(final Object rxJavaObserver, final String observerClassName, final String subscribeMethodName) {
        return new AsyncResult.AsyncResultBuilder() {

            @Override
            public void bind(final AsyncResult asyncResult) {
                Object o = Proxy.newProxyInstance(rxJavaObserver.getClass().getClassLoader(), new Class[]{ClassLoadMonitor.tryLoadClass(observerClassName)},
                        new InvocationHandler() {
                            @Override
                            public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                                if (method.getDeclaringClass() != ClassLoadMonitor.tryLoadClass(observerClassName)) {
                                    return method.invoke(this, args);
                                }
                                if (args == null) {
                                    return null;
                                }
                                if (args.length > 0) {
                                    asyncResult.notifyDataArrival(args[0]);
                                }
                                return null;
                            }
                        });
                XposedHelpers.callMethod(rxJavaObserver, subscribeMethodName, o);
            }
        }.build();
    }

    public static Object wrapRetrofit(Object retrofitCall) {
        Object response = XposedHelpers.callMethod(retrofitCall, "execute");
        if (response == null) {
            return null;
        }
        return XposedHelpers.callMethod(response, "body");
    }

    public static Object wrapOkHttp(Object okHttpCall) {
        Object responseBody = wrapRetrofit(okHttpCall);
        if (responseBody == null) {
            return null;
        }
        String response_str = (String) XposedHelpers.callMethod(responseBody, "string");
        if (response_str == null) {
            return null;
        }
        // try encoding
        try {
            return JSON.parse(response_str);
        } catch (JSONException exception) {
            //failed over for plain string
            return response_str;
        }
    }
}