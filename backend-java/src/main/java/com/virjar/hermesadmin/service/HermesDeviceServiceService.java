package com.virjar.hermesadmin.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.virjar.hermesadmin.entity.HermesDevice;
import com.virjar.hermesadmin.entity.HermesDeviceService;
import com.virjar.hermesadmin.entity.HermesTargetApp;
import com.virjar.hermesadmin.mapper.HermesDeviceMapper;
import com.virjar.hermesadmin.mapper.HermesDeviceServiceMapper;
import com.virjar.hermesadmin.mapper.HermesTargetAppMapper;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

/**
 * <p>
 * 设备上面安装的服务 服务实现类
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
@Service
public class HermesDeviceServiceService extends ServiceImpl<HermesDeviceServiceMapper, HermesDeviceService> {

    @Resource
    private HermesDeviceMapper hermesDeviceMapper;

    @Resource
    private HermesTargetAppMapper hermesTargetAppMapper;

    public int installAllDevice(HermesTargetApp hermesTargetApp) {
        int installed = 0;
        while (true) {
            List<HermesDevice> availableForPackage = hermesDeviceMapper.findAvailableForPackage(hermesTargetApp.getAppPackage());
            if (availableForPackage.size() == 0) {
                return installed;
            }
            for (HermesDevice hermesDevice : availableForPackage) {
                HermesDeviceService hermesDeviceService = new HermesDeviceService();
                hermesDeviceService.setStatus(true);
                hermesDeviceService.setAppPackage(hermesTargetApp.getAppPackage());
                hermesDeviceService.setDeviceMac(hermesDevice.getMac());
                try {
                    baseMapper.insert(hermesDeviceService);
                    installed++;
                } catch (Exception e) {
                    //ignore
                }
            }
        }
        //TODO need update
    }

    public int installAllService(HermesDevice hermesDevice) {
        int installed = 0;
        while (true) {
            List<HermesTargetApp> availableForDevice = hermesTargetAppMapper.findAvailableForDevice(hermesDevice.getMac());
            if (availableForDevice.size() == 0) {
                return installed;
            }

            for (HermesTargetApp hermesTargetApp : availableForDevice) {
                HermesDeviceService hermesDeviceService = new HermesDeviceService();
                hermesDeviceService.setStatus(true);
                hermesDeviceService.setDeviceMac(hermesDevice.getMac());
                hermesDeviceService.setAppPackage(hermesTargetApp.getAppPackage());
                try {
                    baseMapper.insert(hermesDeviceService);
                    installed++;
                } catch (Exception e) {
                    //ignore
                }
            }
        }
        //TODO need update
    }

    public void create(HermesDevice hermesDevice, HermesTargetApp hermesTargetApp, boolean enabled) {
        com.virjar.hermesadmin.entity.HermesDeviceService hermesDeviceServiceEntity = new com.virjar.hermesadmin.entity.HermesDeviceService();
        hermesDeviceServiceEntity.setAppPackage(hermesTargetApp.getAppPackage());
        hermesDeviceServiceEntity.setDeviceMac(hermesDevice.getMac());
        hermesDeviceServiceEntity.setStatus(enabled);
        baseMapper.insert(hermesDeviceServiceEntity);
    }
}
