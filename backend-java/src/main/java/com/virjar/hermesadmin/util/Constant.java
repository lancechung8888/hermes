package com.virjar.hermesadmin.util;

/**
 * Created by virjar on 2018/8/25.
 */
public interface Constant {
    int serviceStatusOnline = 0;
    int serviceStatusOffline = 1;
    int serviceStatusInstalling = 3;
    int serviceStatusUnInstall = 4;

    String agentApkPackage = "com.virjar.hermes.hermesagent";

    int status_ok = 0;
    int status_failed = -1;
    int status_service_not_available = -2;
    int status_need_invoke_package_param = -3;
    int status_rate_limited = -4;
}
