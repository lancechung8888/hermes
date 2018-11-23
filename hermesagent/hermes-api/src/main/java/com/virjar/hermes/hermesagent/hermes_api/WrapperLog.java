package com.virjar.hermes.hermesagent.hermes_api;

import android.os.Process;
import android.util.Log;

import com.virjar.hermes.hermesagent.hermes_api.aidl.InvokeRequest;

import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * logger for hermes wrapper,the log content always out of control,so wrapper log use a separate logger
 *
 * @author dengweijia
 * @since 1.4
 */
public class WrapperLog {
    private static final Logger log;

    static {
        if (Process.myPid() < Process.FIRST_APPLICATION_UID) {
            Log.w("weijia", "you a use slf4j for system app, some bad things maybe occur,so i will redirect to logcat");
            log = new LogCatLogger();
        } else {
            log = LoggerFactory.getLogger(Constant.hermesWrapperLogTag);
        }
    }

    public static Logger getWrapperLogger() {
        return log;
    }

    public static void requestLogI(InvokeRequest invokeRequest, String msg) {
        log.info(buildMessageBody(invokeRequest, msg));
    }

    public static void requestLogW(InvokeRequest invokeRequest, String msg, Throwable throwable) {
        log.warn(buildMessageBody(invokeRequest, msg), throwable);
    }

    public static void requestLogW(InvokeRequest invokeRequest, String msg) {
        log.warn(buildMessageBody(invokeRequest, msg));
    }

    public static void requestLogE(InvokeRequest invokeRequest, String msg, Throwable throwable) {
        log.error(buildMessageBody(invokeRequest, msg), throwable);
    }

    public static void requestLogE(InvokeRequest invokeRequest, String msg) {
        log.error(buildMessageBody(invokeRequest, msg));
    }

    private static String buildMessageBody(InvokeRequest invokeRequest, String msg) {
        return invokeRequest.getRequestID() + " " + DateTime.now().toString("yyyy-MM-dd hh:mm:ss") + " " + msg;
    }

}
