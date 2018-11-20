package com.virjar.hermesadmin.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import java.io.Serializable;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * <p>
 * 设备上面安装的服务
 * </p>
 *
 * @author virjar
 * @since 2018-11-18
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("hermes_device_service")
public class HermesDeviceService implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * 服务id
     */
    private Long targetAppId;

    /**
     * 设备id
     */
    private Long deviceId;

    /**
     * 服务状态，如是否在线
     */
    private Boolean status;

    /**
     * app的包名
     */
    private String appPackage;

    /**
     * 设备唯一标识
     */
    private String deviceMac;


}
