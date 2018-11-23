package com.virjar.hermes.hermesagent.hermes_api;

import android.util.Log;

import com.google.common.base.Preconditions;
import com.koushikdutta.async.AsyncServer;
import com.koushikdutta.async.http.server.AsyncHttpServer;
import com.koushikdutta.async.http.server.AsyncHttpServerRequest;
import com.koushikdutta.async.http.server.AsyncHttpServerResponse;
import com.koushikdutta.async.http.server.HttpServerRequestCallback;
import com.virjar.xposed_extention.ReflectUtil;
import com.virjar.xposed_extention.SharedObject;

import java.io.File;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.regex.Pattern;

import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import lombok.extern.slf4j.Slf4j;

/**
 * Created by virjar on 2018/10/15.<br>
 * 提供一个嵌入式的hermes模块，实现单个进程启动hermes的能力
 */
@Slf4j
public class EmbedHermes {
    private static AgentCallback agentCallback = null;
    private static int serverPort = 0;


    public static void bootstrap(String basePackage, Class loader) {
        bootstrap(MultiActionWrapperFactory.createWrapperByAction(basePackage, bindApkLocation(loader.getClassLoader())));
    }

    public static void bootstrap(AgentCallback agentCallback) {
        bootstrap(agentCallback, Constant.httpServerPort);
    }

    public static void bootstrap(AgentCallback agentCallback, final int serverPort) {
        if (SharedObject.loadPackageParam == null || SharedObject.context == null) {
            throw new IllegalStateException("com.virjar.xposed_extention.SharedObject must be init first");
        }
        Preconditions.checkNotNull(agentCallback, "agent callback can not be empty");
        if (EmbedHermes.agentCallback != null) {
            throw new IllegalStateException("embed hermes can only start one hermes wrapper");
        }
        synchronized (EmbedHermes.class) {
            if (EmbedHermes.agentCallback != null) {
                throw new IllegalStateException("embed hermes can not start one hermes wrapper");
            }
            EmbedHermes.agentCallback = agentCallback;
        }
        EmbedHermes.serverPort = serverPort;
        final AsyncHttpServer server = new AsyncHttpServer();
        AsyncServer mAsyncServer = new AsyncServer("httpServerLooper");

        initIndexHandler(server);
        bindInvokeHandler(server, agentCallback);
        bindPingHandler(server);

        try {
            server.listen(mAsyncServer, serverPort);
            Log.i("weijia", "start server success...");
            Log.i("weijia", "server running on: " + localServerBaseURL());
        } catch (Exception e) {
            log.error("startServer error", e);
        }
        try {
            agentCallback.onXposedHotLoad();
        } catch (Exception e) {
            log.error("start up agent callback failed", e);
            EmbedHermes.agentCallback = null;
            throw new RuntimeException(e);
        }

    }

    private static void bindPingHandler(final AsyncHttpServer server) {
        server.get(Constant.httpServerPingPath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {
                response.send("true");
            }
        });
    }

    private static void bindInvokeHandler(AsyncHttpServer server, AgentCallback agentCallback) {
        EmbedRPCInvokeCallback embedRPCInvokeCallback = new EmbedRPCInvokeCallback(agentCallback);
        server.get(Constant.invokePath, embedRPCInvokeCallback);
        server.post(Constant.invokePath, embedRPCInvokeCallback);
    }

    private static void initIndexHandler(final AsyncHttpServer server) {
        server.get("/", new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                String baseURL = localServerBaseURL();
                Hashtable<String, ArrayList<Object>> actions = ReflectUtil.getFieldValue(server, "mActions");
                StringBuilder html = new StringBuilder("<html><head><meta charset=\"UTF-8\"><title>Hermes</title></head><body><p>HermesAgent ，项目地址：<a href=\"https://gitee.com/virjar/hermesagent\">https://gitee.com/virjar/hermesagent</a></p>");
                html.append("<p>服务base地址：").append(baseURL).append("</p>");
                for (Hashtable.Entry<String, ArrayList<Object>> entry : actions.entrySet()) {
                    html.append("<p>httpMethod:").append(entry.getKey()).append("</p>");
                    html.append("<ul>");
                    for (Object object : entry.getValue()) {
                        Pattern pattern = ReflectUtil.getFieldValue(object, "regex");
                        html.append("<li>");
                        if ("get".equalsIgnoreCase(entry.getKey())) {
                            html.append("<a href=\"").append(baseURL).append(pattern.pattern().substring(1)).append("\">")
                                    .append(baseURL).append(pattern.pattern().substring(1)).append("</a>");
                        } else {
                            html.append(baseURL).append(pattern.pattern().substring(1));
                        }
                        html.append("</li>");
                    }
                    html.append("</ul>");
                }
                html.append("<p>").append("这是embed hermes，仅为测试设计，功能有限，若要保证服务长期在线，请使用hermesAgent").append("</p>");
                html.append("</body></html>");
                response.send("text/html", html.toString());
            }
        });

    }

    private static String localServerBaseURL() {
        return "http://" + APICommonUtils.getLocalIp() + ":" + serverPort;
    }

    private static File bindApkLocation(ClassLoader pathClassLoader) {
        // 不能使用getResourceAsStream，这是因为classloader双亲委派的影响
//        InputStream stream = pathClassLoader.getResourceAsStream(ANDROID_MANIFEST_FILENAME);
//        if (stream == null) {
//            XposedBridge.log("can not find AndroidManifest.xml in classloader");
//            return null;
//        }

        // we can`t call package parser in android inner api,parse logic implemented with native code
        //this object is dalvik.system.DexPathList,android inner api
        Object pathList = XposedHelpers.getObjectField(pathClassLoader, "pathList");
        if (pathList == null) {
            XposedBridge.log("can not find pathList in pathClassLoader");
            return null;
        }

        //this object is  dalvik.system.DexPathList.Element[]
        Object[] dexElements = (Object[]) XposedHelpers.getObjectField(pathList, "dexElements");
        if (dexElements == null || dexElements.length == 0) {
            XposedBridge.log("can not find dexElements in pathList");
            return null;
        }

        return (File) XposedHelpers.getObjectField(dexElements[0], "zip");
        // Object dexElement = dexElements[0];

        // /data/app/com.virjar.xposedhooktool/base.apk
        // /data/app/com.virjar.xposedhooktool-1/base.apk
        // /data/app/com.virjar.xposedhooktool-2/base.apk
        // return (File) XposedHelpers.getObjectField(dexElement, "zip");
    }
}
