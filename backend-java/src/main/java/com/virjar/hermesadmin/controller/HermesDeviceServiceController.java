package com.virjar.hermesadmin.controller;


import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.virjar.hermesadmin.entity.CommonRes;
import com.virjar.hermesadmin.entity.HermesDevice;
import com.virjar.hermesadmin.entity.HermesTargetApp;
import com.virjar.hermesadmin.service.HermesDeviceService;
import com.virjar.hermesadmin.service.HermesDeviceServiceService;
import com.virjar.hermesadmin.service.HermesTargetAppService;
import com.virjar.hermesadmin.util.CommonUtil;
import com.virjar.hermesadmin.util.ReturnUtil;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;

/**
 * <p>
 * 设备上面安装的服务 前端控制器
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
@RestController
@Slf4j
@RequestMapping("//hermes/service")
public class HermesDeviceServiceController {

    @Resource
    private HermesDeviceServiceService hermesDeviceServiceService;

    @Resource
    private HermesTargetAppService hermesTargetAppService;

    @Resource
    private HermesDeviceService hermesDeviceService;

    @GetMapping("list")
    @ApiOperation(value = "列表,分页显示所有已经安装的服务")
    @ResponseBody
    public CommonRes<Page<com.virjar.hermesadmin.entity.HermesDeviceService>> list(
            @PageableDefault Pageable pageable,
            @RequestParam(value = "servicePackage", required = false) String servicePackage
            , @RequestParam("deviceMac") String deviceMac) {
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<com.virjar.hermesadmin.entity.HermesDeviceService> pageWrapper = CommonUtil.wrapperPage(pageable);
        QueryWrapper<com.virjar.hermesadmin.entity.HermesDeviceService> queryWrapper = new QueryWrapper<>();
        if (StringUtils.isNotBlank(servicePackage)) {
            queryWrapper = queryWrapper.eq("app_package", servicePackage);
        }
        if (StringUtils.isNotBlank(deviceMac)) {
            queryWrapper = queryWrapper.eq("device_mac", deviceMac);
        }
        return ReturnUtil.returnPage(hermesDeviceServiceService.page(pageWrapper, queryWrapper), pageable);
    }

    @GetMapping("/deployAllDevice")
    @ApiOperation(value = "某个app,安装到所有的设备上面")
    @ResponseBody
    public CommonRes<?> installAllDevice(@RequestParam("servicePackage") String servicePackage) {
        HermesTargetApp hermesTargetApp = hermesTargetAppService.findByPackage(servicePackage);
        if (hermesTargetApp == null) {
            return ReturnUtil.failed("can not find service:" + servicePackage);
        }
        return ReturnUtil.success(hermesDeviceServiceService.installAllDevice(hermesTargetApp));
    }

    @GetMapping("/deployAllService")
    @ApiOperation(value = "某个app,安装到所有的设备上面")
    @ResponseBody
    public CommonRes<?> installAllService(@RequestParam("deviceMac") String deviceMac) {
        HermesDevice hermesDevice = hermesDeviceService.findByMac(deviceMac);
        if (hermesDevice == null) {
            return ReturnUtil.failed("record not found for device:" + deviceMac);
        }
        return ReturnUtil.success(hermesDeviceServiceService.installAllService(hermesDevice));
    }

    @GetMapping("/installOne")
    @ApiOperation(value = "在某个设备上面安装指定的单个App")
    @ResponseBody
    public CommonRes<?> installOne(String deviceMac, String targetService,
                                   boolean enabled) {
        HermesDevice hermesDevice = hermesDeviceService.getOne(new QueryWrapper<HermesDevice>().eq("app_package", targetService)
                .eq("device_mac", deviceMac));
        if (hermesDevice != null) {
            if (hermesDevice.getStatus() == enabled) {
                return ReturnUtil.success("installed already");
            }
            hermesDevice.setStatus(enabled);
            hermesDeviceService.updateById(hermesDevice);
            return ReturnUtil.success("ok");
        }
        HermesDevice byMac = hermesDeviceService.findByMac(deviceMac);
        if (byMac == null) {
            return ReturnUtil.failed("no device :" + deviceMac + " fond");
        }
        HermesTargetApp byPackage = hermesTargetAppService.findByPackage(targetService);
        if (byPackage == null) {
            return ReturnUtil.failed("no service: " + targetService + " defined");
        }
        hermesDeviceServiceService.create(byMac, byPackage, enabled);
        return ReturnUtil.success("ok");
    }

    @GetMapping("/installServiceForDevice")
    @ApiOperation(value = "在一个设备上面,安装多个app,提供app列表")
    @ResponseBody
    public CommonRes<?> installServiceForDevice() {
        return null;
    }

    @GetMapping("/installServiceForTargetApp")
    @ApiOperation(value = "一个app,安装待多个设备上面,提供设备列表")
    @ResponseBody
    public CommonRes<?> installServcieForTargetApp() {
        return null;
    }
}
