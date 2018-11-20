package com.virjar.hermes.hermesagent.host.http;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.os.Process;
import android.support.annotation.NonNull;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import com.jaredrummler.android.processes.AndroidProcesses;
import com.jaredrummler.android.processes.models.AndroidAppProcess;
import com.koushikdutta.async.AsyncServer;
import com.koushikdutta.async.http.Multimap;
import com.koushikdutta.async.http.server.AsyncHttpServer;
import com.koushikdutta.async.http.server.AsyncHttpServerRequest;
import com.koushikdutta.async.http.server.AsyncHttpServerResponse;
import com.koushikdutta.async.http.server.HttpServerRequestCallback;
import com.virjar.hermes.hermesagent.BuildConfig;
import com.virjar.hermes.hermesagent.hermes_api.CommonRes;
import com.virjar.hermes.hermesagent.hermes_api.Constant;
import com.virjar.hermes.hermesagent.hermes_api.LogConfigurator;
import com.virjar.hermes.hermesagent.hermes_api.aidl.IHookAgentService;
import com.virjar.hermes.hermesagent.host.manager.StartAppTask;
import com.virjar.hermes.hermesagent.host.service.FontService;
import com.virjar.hermes.hermesagent.host.thread.J2Executor;
import com.virjar.hermes.hermesagent.host.thread.NamedThreadFactory;
import com.virjar.hermes.hermesagent.util.CommonUtils;
import com.virjar.hermes.hermesagent.util.HttpClientUtils;
import com.virjar.hermes.hermesagent.util.ReflectUtil;
import com.virjar.hermes.hermesagent.util.libsuperuser.Shell;

import org.apache.commons.lang3.StringUtils;

import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

import lombok.extern.slf4j.Slf4j;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.Response;
import okhttp3.ResponseBody;

/**
 * Created by virjar on 2018/8/23.<br>
 * http 服务器相关实现
 */

@Slf4j
public class HttpServer {

    private static AsyncHttpServer server = null;
    private static AsyncServer mAsyncServer = null;
    private static HttpServer instance = new HttpServer();
    private int httpServerPort = 0;
    private FontService fontService;
    private RPCInvokeCallback httpServerRequestCallback = null;
    private J2Executor j2Executor;
    private StartServiceHandler handler = new StartServiceHandler(Looper.getMainLooper(), this);
    private volatile boolean started = false;
    private Set<HttpServerStartupEvent> startupEventSet = Sets.newCopyOnWriteArraySet();

    private static class StartServiceHandler extends Handler {
        private HttpServer httpServer;

        StartServiceHandler(Looper looper, HttpServer httpServer) {
            super(looper);
            this.httpServer = httpServer;
        }

        @Override
        public void handleMessage(Message msg) {
            //super.handleMessage(msg);
            httpServer.startServerInternal((Context) msg.obj);
        }
    }

    public void setFontService(FontService fontService) {
        this.fontService = fontService;
    }

    private HttpServer() {
    }

    public static HttpServer getInstance() {
        return instance;
    }

    public int getHttpServerPort() {
        return httpServerPort;
    }

    public J2Executor getJ2Executor() {
        return j2Executor;
    }

    private void startServerInternal(Context context) {
        stopServer();
        started = false;
        server = new AsyncHttpServer();
        mAsyncServer = new AsyncServer(Constant.httpServerLooperThreadName);
        j2Executor = new J2Executor(
                new ThreadPoolExecutor(10, 10, 0L,
                        TimeUnit.MILLISECONDS, new ArrayBlockingQueue<Runnable>(10), new NamedThreadFactory("httpServer-public-pool"))
        );
        httpServerRequestCallback = new RPCInvokeCallback(fontService, j2Executor);
        log.info("register http request handler");
        bindRootCommand();
        bindPingCommand();
        bindStartAppCommand(context);
        bindInvokeCommand();
        bindAliveServiceCommand();
        bindRestartDeviceCommand();
        bindExecuteShellCommand();
        bindRestartADBDCommand();
        bindReloadServiceCommand();
        agentVersionCommand();
        hermesLogCommand();
        killAgent();

        try {
            httpServerPort = Constant.httpServerPort;
            server.listen(mAsyncServer, httpServerPort);
            log.info("start server success...");
            log.info("server running on: " + CommonUtils.localServerBaseURL());
            started = true;
            for (HttpServerStartupEvent callback : startupEventSet) {
                callback.onHttpServerStartUp(this);
                startupEventSet.remove(callback);
            }
        } catch (Exception e) {
            log.error("startServer error", e);
        }
    }


    public void onHttpServerStartUp(HttpServerStartupEvent httpServerStartupEvent) {
        if (started) {
            httpServerStartupEvent.onHttpServerStartUp(this);
        } else {
            startupEventSet.add(httpServerStartupEvent);
        }
    }

    public void startServer(final Context context) {

        HttpClientUtils.getClient().newCall(CommonUtils.pingServerRequest()).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                Message obtain = Message.obtain();
                obtain.obj = context;
                handler.sendMessage(obtain);
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (response.isSuccessful()) {
                    ResponseBody body = response.body();
                    if (body != null) {
                        if (body.string().equalsIgnoreCase("true")) {
                            log.info("ping http server success,skip restart http server");
                            return;
                        }
                    }
                }
                log.info("ping http server failed ,start http server");
                Message obtain = Message.obtain();
                obtain.obj = context;
                handler.sendMessage(obtain);
            }
        });


    }

    public synchronized void stopServer() {
        if (server == null) {
            return;
        }
        log.info("stop http server");
        server.stop();
        mAsyncServer.stop();
        server = null;
        mAsyncServer = null;
        j2Executor.shutdownAll();
        j2Executor = null;
    }

    private void bindRootCommand() {
        server.get("/", new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                String baseURL = CommonUtils.localServerBaseURL();
                Hashtable<String, ArrayList<Object>> actions = ReflectUtil.getFieldValue(server, "mActions");
                StringBuilder html = new StringBuilder("<html><head><meta charset=\"UTF-8\"><title>Hermes</title></head><body><p>HermesAgent ，项目地址：<a href=\"https://gitee.com/virjar/hermesagent\">https://gitee.com/virjar/hermesagent</a></p>");
                html.append("<p>服务base地址：").append(baseURL).append("</p>");
                html.append("<p>agent版本：").append(BuildConfig.VERSION_CODE).append("</p>");
                html.append("<p>设备ID：").append(CommonUtils.deviceID(HttpServer.this.fontService)).append("</p>");
                for (Hashtable.Entry<String, ArrayList<Object>> entry : actions.entrySet()) {
                    html.append("<p>httpMethod:").append(entry.getKey()).append("</p>");
                    html.append("<ul>");
                    for (Object object : entry.getValue()) {
                        Pattern pattern = ReflectUtil.getFieldValue(object, "regex");
                        html.append("<li>");
                        if (StringUtils.equalsIgnoreCase(entry.getKey(), "get")) {
                            html.append("<a href=\"").append(baseURL).append(pattern.pattern().substring(1)).append("\">")
                                    .append(baseURL).append(pattern.pattern().substring(1)).append("</a>");
                        } else {
                            html.append(baseURL).append(pattern.pattern().substring(1));
                        }
                        html.append("</li>");
                    }
                    html.append("</ul>");
                }
                html.append("</body></html>");
                response.send("text/html", html.toString());
            }
        });
    }

    private void bindReloadServiceCommand() {
        server.get(Constant.reloadService, new HttpServerRequestCallback() {

            @Override
            public void onRequest(final AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                new J2ExecutorWrapper(j2Executor.getOrCreate("shell", 1, 2), new Runnable() {
                    @Override
                    public void run() {
                        if (!CommonUtils.isSuAvailable()) {
                            CommonUtils.sendJSON(response, CommonRes.failed("need root permission"));
                            return;
                        }
                        Multimap query = request.getQuery();
                        final String service = query.getString("service");
                        Map<String, Boolean> killStatus = Maps.newHashMap();
                        if (StringUtils.isNotBlank(service)) {
                            killStatus.put(service, CommonUtils.killService(service));
                        } else {
                            for (String str : fontService.onlineAgentServices()) {
                                killStatus.put(str, CommonUtils.killService(str));
                            }
                        }
                        CommonUtils.sendJSON(response, CommonRes.success(killStatus));
                    }
                }, response).run();


            }
        });
    }

    private void bindExecuteShellCommand() {
        server.get(Constant.executeShellCommandPath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                Multimap query = request.getQuery();
                final String cmd = query.getString("cmd");
                if (StringUtils.isBlank(cmd)) {
                    CommonUtils.sendJSON(response, CommonRes.failed("parameter {cmd} not present!!"));
                    return;
                }
                // org.apache.commons.lang3.BooleanUtils.toBooleanObject(java.lang.String) 在这里对卡死线程，具体原因待分析
                final boolean useRoot = StringUtils.equalsIgnoreCase(query.getString("useRoot"), "true");
                new J2ExecutorWrapper(j2Executor.getOrCreate("shell", 1, 2), new Runnable() {
                    @Override
                    public void run() {
                        CommonUtils.sendPlainText(response, CommonUtils.execCmd(cmd, useRoot));
                    }
                }, response).run();
                if (StringUtils.trimToEmpty(cmd).equalsIgnoreCase("reboot")) {
                    //reboot 命令，需要直接返回响应，因为reboot执行之后，手机已经关机了，请求端无法再收到server的响应了
                    CommonUtils.sendJSON(response, CommonRes.success("reboot command accepted"));
                }
            }
        });
    }

    private void bindRestartDeviceCommand() {
        server.get(Constant.restartDevicePath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                new J2ExecutorWrapper(j2Executor.getOrCreate("shell", 1, 2), new Runnable() {
                    @Override
                    public void run() {
                        //CommonUtils.sendJSON(response, CommonRes.success("command accepted"));
                        //CommonUtils.restartAndroidSystem();
                        //shell无启动权限，adb通过网络直连，adb远程服务默认关闭，目前无法再不获取root权限的情况下重启系统
                        CommonUtils.sendJSON(response, CommonRes.failed("not implement"));
                    }
                }, response).run();
            }
        });
    }

    private void bindRestartADBDCommand() {
        server.get(Constant.restartAdbD, new HttpServerRequestCallback() {
            @Override
            public void onRequest(final AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                new J2ExecutorWrapper(j2Executor.getOrCreate("shell", 1, 2), new Runnable() {
                    @Override
                    public void run() {
                        if (!CommonUtils.isSuAvailable()) {
                            CommonUtils.sendJSON(response, CommonRes.failed("need root permission"));
                            return;
                        }
                        CommonUtils.sendJSON(response, CommonRes.success(Shell.SU.run(Lists.newArrayList("stop adbd", "start adbd"))));
                    }
                }, response).run();
            }
        });
    }

    private void bindAliveServiceCommand() {
        server.get(Constant.aliveServicePath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {
                ArrayList<String> strings = Lists.newArrayList(fontService.onlineAgentServices());
                Collections.sort(strings);
                CommonUtils.sendJSON(response, CommonRes.success(strings));
            }
        });
    }

    private void bindInvokeCommand() {
        server.get(Constant.invokePath, httpServerRequestCallback);
        server.post(Constant.invokePath, httpServerRequestCallback);
    }

    private void bindStartAppCommand(final Context context) {
        server.get(Constant.startAppPath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {
                String app = request.getQuery().getString("app");
                if (StringUtils.isBlank(app)) {
                    CommonUtils.sendJSON(response, CommonRes.failed("the param {app} must exist"));
                    return;
                }
                new StartAppTask(app, context, response).execute();
            }
        });
    }


    private void bindPingCommand() {
        server.get(Constant.httpServerPingPath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {
                String sourcePackage = request.getQuery().getString("source_package");
                if (StringUtils.isBlank(sourcePackage)) {
                    response.send("true");
                    return;
                }
                IHookAgentService hookAgent = fontService.findHookAgent(sourcePackage);
                if (hookAgent == null) {
                    response.send(Constant.rebind);
                    return;
                }
                response.send("true");
            }
        });
    }

    private void agentVersionCommand() {
        server.get(Constant.getAgentVersionCodePath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {
                CommonUtils.sendJSON(response, CommonRes.success(BuildConfig.VERSION_CODE));
            }
        });
    }

    private void hermesLogCommand() {
        server.get(Constant.hermesLogPath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, final AsyncHttpServerResponse response) {
                //日志接口，允许跨域，方便HermesAdmin直接在页面调取日志而不经过hermesAdmin的服务器转发
                response.getHeaders().set("Access-Control-Allow-Origin", "*");
                response.getHeaders().set("Access-Control-Expose-Headers", "Server,Content-Type,Last-Modified,ETag,Accept-Ranges,Content-Length,Date,Transfer-Encoding");
                response.getHeaders().set("Content-Type", "text/plain;charset=utf8");
                final File logDir = LogConfigurator.logDir(HttpServer.this.fontService);
                if (!logDir.isDirectory() || !logDir.canWrite()) {
                    response.send("no available log");
                    return;
                }
                new J2ExecutorWrapper(j2Executor.getOrCreate("shell", 1, 2), new Runnable() {
                    @Override
                    public void run() {
                        File[] hermesLogFiles = logDir.listFiles(new FilenameFilter() {
                            @Override
                            public boolean accept(File dir, String name) {
                                return StringUtils.startsWith(name, "loghermes_system_");
                            }
                        });
                        if (hermesLogFiles == null || hermesLogFiles.length == 0) {
                            response.send("no available log");
                            return;
                        }
                        File theLastFile = null;
                        for (File candidateFile : hermesLogFiles) {
                            if (theLastFile == null) {
                                theLastFile = candidateFile;
                                continue;
                            }
                            if (candidateFile.lastModified() > theLastFile.lastModified()) {
                                theLastFile = candidateFile;
                            }
                        }
                        log.info("get get log content ,use local file:{}", theLastFile.getAbsolutePath());
                        response.sendFile(theLastFile);
                    }
                }, response).run();
            }
        });
    }

    private void killAgent() {
        server.get(Constant.killHermesAgentPath, new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {
                CommonUtils.sendJSON(response, CommonRes.success("command accepted!"));
                new J2ExecutorWrapper(j2Executor.getOrCreate("shell", 1, 2), new Runnable() {
                    @Override
                    public void run() {
                        List<AndroidAppProcess> runningAppProcesses = AndroidProcesses.getRunningAppProcesses();
                        for (AndroidAppProcess androidAppProcess : runningAppProcesses) {
                            if (androidAppProcess.name.equalsIgnoreCase(BuildConfig.APPLICATION_ID + ":daemon")) {
                                Shell.SU.run("kill -9 " + androidAppProcess.pid);
                            }
                        }
                        //先杀后台，再杀前台
                        Shell.SU.run("kill -9 " + Process.myPid());
                    }
                }, response).run();


            }
        });
    }
}
