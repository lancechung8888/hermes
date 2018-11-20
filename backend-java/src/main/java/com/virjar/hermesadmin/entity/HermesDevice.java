package com.virjar.hermesadmin.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import java.time.LocalDateTime;
import java.io.Serializable;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * <p>
 * 
 * </p>
 *
 * @author virjar
 * @since 2018-11-18
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("hermes_device")
public class HermesDevice implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * 手机设备名称
     */
    private String name;

    /**
     * 设备的server ip
     */
    private String ip;

    /**
     * 设备server的端口
     */
    private Integer port;

    /**
     * 设备硬件地址
     */
    private String mac;

    /**
     * 设备厂商
     */
    private String brand;

    /**
     * 设备系统版本
     */
    private String systemVersion;

    /**
     * 设备状态，online | offline
     */
    private Boolean status;

    /**
     * 可显ip，当一个手机设备在内网中的时候，记录该手机的出口ip
     */
    private String visibleIp;

    /**
     * cpu 使用率
     */
    private String cpuUsage;

    /**
     * 手机的内存使用率
     */
    private String memory;

    /**
     * 最后上报时间
     */
    private LocalDateTime lastReportTime;

    /**
     * 最后上报的时候，在线服务
     */
    private String lastReportService;


}
