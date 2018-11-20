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
 * 服务器存储的app
 * </p>
 *
 * @author virjar
 * @since 2018-11-18
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("hermes_target_app")
public class HermesTargetApp implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * app名称
     */
    private String name;

    /**
     * app的包名，在Android上面唯一标记一个app
     */
    private String appPackage;

    /**
     * app的版本号码
     */
    private String version;

    /**
     * app的存储路径，如果是服务器存储，那么可以将它转化为一个下载链接
     */
    private String savePath;

    /**
     * app的下载链接，如果是第三方存储，那么可以下发这个链接
     */
    private String downloadUrl;

    /**
     * apk版本号
     */
    private Long versionCode;

    /**
     * 是否启用
     */
    private Boolean enabled;


}
