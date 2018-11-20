package com.virjar.hermesadmin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.virjar.hermesadmin.entity.HermesTargetApp;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * <p>
 * 服务器存储的app Mapper 接口
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
public interface HermesTargetAppMapper extends BaseMapper<HermesTargetApp> {

    List<HermesTargetApp> findAvailableForDevice(@Param("deviceMac") String deviceMac);
}
