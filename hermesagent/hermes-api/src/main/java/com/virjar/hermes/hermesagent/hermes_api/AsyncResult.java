package com.virjar.hermes.hermesagent.hermes_api;

import com.google.common.base.Preconditions;

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
}