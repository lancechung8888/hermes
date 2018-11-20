package com.virjar.hermesadmin.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.virjar.hermesadmin.entity.HermesTargetApp;
import com.virjar.hermesadmin.mapper.HermesTargetAppMapper;
import org.springframework.stereotype.Service;

/**
 * <p>
 * 服务器存储的app 服务类
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
@Service
public class HermesTargetAppService extends ServiceImpl<HermesTargetAppMapper, HermesTargetApp> {

    public HermesTargetApp findByPackage(String packageName) {
        return baseMapper.selectOne(new QueryWrapper<HermesTargetApp>().eq("app_package", packageName)
                .eq("enabled", true));
    }
}
