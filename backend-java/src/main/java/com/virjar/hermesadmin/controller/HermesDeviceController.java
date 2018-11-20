package com.virjar.hermesadmin.controller;


import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.virjar.hermesadmin.entity.CommonRes;
import com.virjar.hermesadmin.entity.HermesDevice;
import com.virjar.hermesadmin.entity.ReportModel;
import com.virjar.hermesadmin.service.HermesDeviceService;
import com.virjar.hermesadmin.util.CommonUtil;
import com.virjar.hermesadmin.util.ReturnUtil;
import io.swagger.annotations.ApiImplicitParam;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.List;

/**
 * <p>
 * 前端控制器
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
@RestController
@RequestMapping("//hermes/device")
@Slf4j
public class HermesDeviceController {

    @Resource
    private HermesDeviceService hermesDeviceService;

    @GetMapping("list")
    @ApiOperation(value = "列表,分页显示所有的设备")
    @ResponseBody
    public CommonRes<Page<HermesDevice>> list(@PageableDefault Pageable pageable, @RequestParam(value = "appPackage", required = false) String appPackage) {
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<HermesDevice> pageWrapper = CommonUtil.wrapperPage(pageable);
        if (StringUtils.isBlank(appPackage)) {
            return ReturnUtil.returnPage(hermesDeviceService.page(pageWrapper, new QueryWrapper<>()), pageable);
        }
        return ReturnUtil.returnPage(hermesDeviceService.selectForConfiguredPackage(pageWrapper, appPackage), pageable);
    }

    @GetMapping("listAvailableDevices")
    @ApiOperation(value = "查询当前app可用的设备资源")
    @ResponseBody
    public CommonRes<Page<HermesDevice>> listAvailable(@PageableDefault Pageable pageable, @RequestParam(value = "appPackage") String appPackage) {
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<HermesDevice> pageWrapper = CommonUtil.wrapperPage(pageable);
        return ReturnUtil.returnPage(hermesDeviceService.selectForConfiguredPackage(pageWrapper, appPackage), pageable);
    }

    @ApiOperation(value = "调用某个服务", notes = "支持get/post,content type支持json和urlencoding,其他方式不支持")
    @ApiImplicitParam(name = "invoke_package", value = "invoke_package,代表一个apk的package,该参数必须存", dataType = "java.lang.String", paramType = "query")
    @RequestMapping(value = "/invoke", method = {RequestMethod.GET, RequestMethod.POST})
    @ResponseBody
    public CommonRes<?> invoke(HttpServletRequest httpServletRequest) throws IOException {
        return hermesDeviceService.invoke(httpServletRequest);
    }

    @ApiOperation(value = "上报设备信息", notes = "Android设备会定时上报存活状态,同时会上报当前在线的服务列表")
    @ApiImplicitParam(name = "reportModel", value = "reportModel", dataType = "com.virjar.hermes.hermesadmin.model.ReportModel", paramType = "body")
    @PostMapping("/report")
    @ResponseBody
    public CommonRes<?> report(@RequestBody ReportModel reportModel, HttpServletRequest httpServletRequest) {
        log.info("report request:" + JSONObject.toJSONString(reportModel));
        if (StringUtils.isBlank(reportModel.getAgentServerIP())
                || reportModel.getAgentServerPort() == 0) {
            return ReturnUtil.failed("agent ip & port not present");
        }
        if (StringUtils.isBlank(reportModel.getMac())) {
            return ReturnUtil.failed("agent device id  present");
        }
        return hermesDeviceService.handleReport(reportModel, httpServletRequest);
    }

    @ApiOperation(value = "启用或者禁用一个设备资源")
    @GetMapping("/setStatus")
    @ResponseBody
    public CommonRes<?> setDeviceStatus(@RequestParam("deviceId") String deviceId, @RequestParam("status") Boolean status) {
        HermesDevice hermesDevice = hermesDeviceService.getById(deviceId);
        hermesDevice.setStatus(status);
        hermesDeviceService.updateById(hermesDevice);
        return ReturnUtil.success("ok");
    }

    @ApiOperation(value = "查询系统中所有的设备,以ip的形式列出", notes = "如果是处于内网中的ip(服务器无法直接通信的设备),将不会出现这这个设备中")
    @GetMapping("/deviceIpList")
    @ResponseBody
    public String deviceIpList() {
        List<HermesDevice> hermesDevices = hermesDeviceService.list(new QueryWrapper<HermesDevice>().eq("status", true));
        StringBuilder stringBuilder = new StringBuilder();
        for (HermesDevice hermesDevice : hermesDevices) {
            if (!StringUtils.equals(hermesDevice.getIp(), hermesDevice.getVisibleIp())) {
                continue;
            }
            stringBuilder.append(hermesDevice.getIp());
        }
        return stringBuilder.toString();
    }
}
