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
 * wrapper app,扩展代码书写完成后打包上传，存储到此表
 * </p>
 *
 * @author virjar
 * @since 2018-11-18
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("hermes_wrapper_apk")
public class HermesWrapperApk implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * agent apk的唯一id
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * agent 对应版本号
     */
    private String version;

    /**
     * apk 存储路径
     */
    private String savePath;

    /**
     * 是否启用
     */
    private Boolean enabled;

    /**
     * wrapper apk 的包名
     */
    private String apkPackage;

    /**
     * 版本号码，数字形式，后台以数字形式为准
     */
    private Integer versionCode;

    /**
     * app的下载链接，如果是第三方存储，那么可以下发这个链接
     */
    private String downloadUrl;

    /**
     * target apk 的包名
     */
    private String targetApkPackage;


}
