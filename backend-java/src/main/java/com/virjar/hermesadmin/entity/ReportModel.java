package com.virjar.hermesadmin.entity;

import lombok.Data;

import java.util.Set;

/**
 * Created by virjar on 2018/8/25.<br>
 * 设备上报
 */
@Data
public class ReportModel {
    private String agentServerIP;
    private int agentServerPort;
    private double cpuLoader;
    private double memoryInfo;
    private String mac;
    private String brand;
    private String systemVersion;
    private Set<String> onlineServices;
}
