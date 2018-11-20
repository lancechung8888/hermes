
/*
 Hermes后台数据库ddl语句
**/
drop table if exists hermes_device;
drop table if exists hermes_target_app;
drop table if exists hermes_wrapper_apk;
drop table if exists hermes_device_service;


/* 设备表，每一个设备代表一个Android 手机资源*/
CREATE TABLE `hermes_device` (
  `id`  bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` varchar(255) DEFAULT NULL COMMENT '手机设备名称',
  `ip` varchar(255) DEFAULT NULL COMMENT '设备的server ip',
  `port` int(6) DEFAULT NULL COMMENT '设备server的端口',
  `mac` varchar(255) DEFAULT NULL COMMENT '设备硬件地址',
  `brand` varchar(255) DEFAULT NULL COMMENT '设备厂商',
  `system_version` varchar(255) DEFAULT NULL COMMENT '设备系统版本',
  `status` tinyint(1) DEFAULT FALSE COMMENT '设备状态，online | offline',
  `visible_ip` varchar(50) DEFAULT NULL COMMENT '可显ip，当一个手机设备在内网中的时候，记录该手机的出口ip',
  `cpu_usage` varchar (50) default '' COMMENT 'cpu 使用率',
  `memory` varchar (50) default '0' COMMENT '手机的内存使用率',
  `last_report_time` timestamp default '1999-01-01 00:00:00' COMMENT '最后上报时间',
  `last_report_service` TEXT  COMMENT '最后上报的时候，在线服务',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_mac` (`mac`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;


/* 目标app，如微视、抖音等第三方app */
CREATE TABLE `hermes_target_app` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` varchar(255) DEFAULT NULL COMMENT 'app名称',
  `app_package` varchar(100) DEFAULT NULL COMMENT 'app的包名，在Android上面唯一标记一个app',
  `version` varchar(255) DEFAULT NULL COMMENT 'app的版本号码',
  `save_path` varchar(255) DEFAULT NULL COMMENT 'app的存储路径，如果是服务器存储，那么可以将它转化为一个下载链接',
  `download_url` varchar(255) DEFAULT NULL COMMENT 'app的下载链接，如果是第三方存储，那么可以下发这个链接',
  `version_code` int(5) NOT NULL DEFAULT '0' COMMENT 'apk版本号',
  `enabled` tinyint(1) NOT NULL DEFAULT TRUE COMMENT '是否启用',
  PRIMARY KEY (`id`),
  CONSTRAINT `uniq_pv` UNIQUE   (`app_package`,`version_code`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COMMENT='服务器存储的app';


/* wrapper app */
CREATE TABLE `hermes_wrapper_apk` (
  `id` bigint(20) unsigned  NOT NULL AUTO_INCREMENT COMMENT 'agent apk的唯一id',
  `version` varchar(255) NOT NULL COMMENT 'agent 对应版本号',
  `save_path` varchar(255) NOT NULL COMMENT 'apk 存储路径',
  `enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `apk_package` varchar(100) NOT NULL DEFAULT '' COMMENT 'wrapper apk 的包名',
  `version_code` int(11) NOT NULL DEFAULT '0' COMMENT '版本号码，数字形式，后台以数字形式为准',
  `download_url` varchar(255) DEFAULT NULL COMMENT 'app的下载链接，如果是第三方存储，那么可以下发这个链接',
  `target_apk_package` varchar(255) NOT NULL DEFAULT '' COMMENT 'target apk 的包名',
  UNIQUE KEY `uniq_pv` (`apk_package`,`version_code`),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COMMENT='wrapper app,扩展代码书写完成后打包上传，存储到此表';

/* 服务安装表 */
CREATE TABLE `hermes_device_service` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `target_app_id` bigint(20) DEFAULT NULL COMMENT '服务id',
  `device_id` bigint(20) DEFAULT NULL COMMENT '设备id',
  `status` tinyint(1) DEFAULT NULL COMMENT '服务状态，如是否在线',
  `app_package` varchar(100) DEFAULT NULL COMMENT 'app的包名',
  `device_mac` varchar(60) DEFAULT NULL COMMENT '设备唯一标识',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_pm` (`app_package`,`device_mac`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COMMENT='设备上面安装的服务';