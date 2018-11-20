package com.virjar.hermesadmin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.virjar.hermesadmin.entity.HermesDevice;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * <p>
 * Mapper 接口
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
public interface HermesDeviceMapper extends BaseMapper<HermesDevice> {
    IPage<HermesDevice> selectForConfiguredPackage(@Param("pag") Page pag, @Param("appPackage") String appPackage);

    IPage<HermesDevice> availableDeviceForPackage(@Param("pag") Page pag, @Param("appPackage") String appPackage);

    List<HermesDevice> findAvailableForPackage(@Param("appPackage") String packageName);
}
