package com.virjar.hermesadmin.controller;


import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.google.common.base.Charsets;
import com.virjar.hermesadmin.entity.CommonRes;
import com.virjar.hermesadmin.entity.HermesWrapperApk;
import com.virjar.hermesadmin.service.HermesWrapperApkService;
import com.virjar.hermesadmin.util.CommonUtil;
import com.virjar.hermesadmin.util.Constant;
import com.virjar.hermesadmin.util.ReturnUtil;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import net.dongliu.apk.parser.bean.ApkMeta;
import org.apache.commons.lang3.StringUtils;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.InputStreamResource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.io.File;
import java.io.IOException;

/**
 * <p>
 * wrapper app,扩展代码书写完成后打包上传，存储到此表 前端控制器
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
@RestController
@RequestMapping("//hermes/wrapperApp")
@Slf4j
public class HermesWrapperApkController {

    @Value("${web.upload-path}")
    private String uploadPath;

    @Resource
    private HermesWrapperApkService hermesWrapperApkService;

    /**
     * @param file 上传一个apk
     */
    @ApiOperation(value = "上传apk文件", notes = "这个apk,是目标apk,也就是将要被hook的APK,apk大小限制,不超过500M")
    @PostMapping(value = "/upload")
    @ResponseBody
    public CommonRes<String> upload(@RequestParam("wrapperAPK") MultipartFile file) {
        String srcFileName = file.getOriginalFilename();
        if (!StringUtils.endsWithIgnoreCase(srcFileName, ".apk")) {
            return ReturnUtil.failed("the upload file must has .apk suffix");
        }

        File dir = genAgentApkUploadPath();
        String filedName = DateTime.now().toString("yyyy_MM_dd") + "_" + System.currentTimeMillis() + "_" + Thread.currentThread().getId();
        File targetFile = new File(dir, filedName);
        log.info("save new agent apk file to :{}", targetFile.getAbsoluteFile());
        try {
            file.transferTo(targetFile);
        } catch (IOException e) {
            log.error("failed to save agent apk filed", e);
            return ReturnUtil.failed(e);
        }

        ApkMeta apkMeta = CommonUtil.parseApk(targetFile);

        if (StringUtils.equalsIgnoreCase(Constant.agentApkPackage, apkMeta.getPackageName())) {
            //只能上传agent的apk文件,其他文件,认为是不合法的
            return ReturnUtil.failed("wrapper apk package can not  be: " + Constant.agentApkPackage);
        }

        //check passed ,to rename with package name
        String realFileName = apkMeta.getPackageName() + "_" + apkMeta.getVersionName() + "_" + apkMeta.getVersionCode() + ".apk";
        File realFilePath = new File(dir, realFileName);
        if (realFilePath.exists()) {
            targetFile.deleteOnExit();
            return ReturnUtil.failed("target version existed");
        }
        targetFile.renameTo(realFilePath);

        HermesWrapperApk hermesWrapperApk = new HermesWrapperApk();
        hermesWrapperApk.setVersion(apkMeta.getVersionName());
        hermesWrapperApk.setVersionCode(apkMeta.getVersionCode().intValue());
        hermesWrapperApk.setEnabled(true);
        hermesWrapperApk.setSavePath(realFilePath.getAbsolutePath());

        hermesWrapperApkService.save(hermesWrapperApk);
        return ReturnUtil.success("upload success");
    }


    private File genAgentApkUploadPath() {
        File dir = new File(uploadPath);
        if (!dir.exists()) {
            if (!dir.mkdirs()) {
                throw new RuntimeException("failed to create upload directory: " + dir.getAbsolutePath());
            }
        }

        File agentApk = new File(dir, "wrapper_apk");
        if (agentApk.isDirectory()) {
            return agentApk;
        }
        if (!agentApk.mkdir()) {
            throw new RuntimeException("failed to create wrapper apk file upload directory: " + agentApk.getAbsolutePath());
        }
        return agentApk;
    }

    @GetMapping("list")
    @ApiOperation(value = "列表,分页显示所有的设备")
    @ResponseBody
    public CommonRes<Page<HermesWrapperApk>> list(@PageableDefault Pageable pageable, @RequestParam(value = "targetAppPackage", required = false) String appPackage) {
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<HermesWrapperApk> pageWrapper = CommonUtil.wrapperPage(pageable);
        QueryWrapper<HermesWrapperApk> hermesTargetAppQueryWrapper = new QueryWrapper<>();
        if (StringUtils.isBlank(appPackage)) {
            hermesTargetAppQueryWrapper = hermesTargetAppQueryWrapper.eq("apk_package", appPackage);
        }
        return ReturnUtil.returnPage(hermesWrapperApkService.page(pageWrapper, hermesTargetAppQueryWrapper), pageable);
    }


    @ApiOperation(value = "下载某个wrapperApk", notes = "这个是给Android内的agent访问的,他可以通过这个接口下载到新的apk代码,并完成自更新")
    @GetMapping("/download")
    public ResponseEntity<InputStreamResource> downloadFile(@RequestParam("wrapperId") Long wrapperId)
            throws IOException {

        HermesWrapperApk hermesWrapperApk = hermesWrapperApkService.getById(wrapperId);
        if (hermesWrapperApk == null) {
            throw new RuntimeException("can not find apk for wrapperId: " + wrapperId);
        }

        File savePath = new File(hermesWrapperApk.getSavePath());
        if (!savePath.exists() || !savePath.isFile() || !savePath.canRead()) {
            throw new IllegalStateException("resource can not access");
        }
        FileSystemResource file = new FileSystemResource(savePath);
        HttpHeaders headers = new HttpHeaders();
        headers.setCacheControl("no-cache, no-store, must-revalidate");
        headers.add("Content-Disposition", "attachment; filename=" + new String((hermesWrapperApk.getApkPackage() + "_" + hermesWrapperApk.getVersionCode() + ".apk").getBytes(Charsets.UTF_8), Charsets.ISO_8859_1));
        headers.setPragma("no-cache");
        headers.setExpires(0);
        return ResponseEntity
                .ok()
                .headers(headers)
                .contentLength(file.contentLength())
                .contentType(MediaType.parseMediaType("application/octet-stream"))
                .body(new InputStreamResource(file.getInputStream()));
    }


    @ApiOperation(value = "启用或者禁用一个targetApp")
    @GetMapping("/setStatus")
    @ResponseBody
    public CommonRes<?> setWrapperStatus(@RequestParam("wrapperId") Long targetAppId, @RequestParam("status") Boolean status) {
        HermesWrapperApk hermesWrapperApk = hermesWrapperApkService.getById(targetAppId);
        if (hermesWrapperApk == null) {
            return ReturnUtil.failed("record not found");
        }
        if (status) {
            while (true) {
                HermesWrapperApk one = hermesWrapperApkService.getOne(new QueryWrapper<HermesWrapperApk>()
                        .eq("apk_package", hermesWrapperApk.getApkPackage())
                        .eq("enabled", true));
                if (one == null) {
                    break;
                }
                one.setEnabled(false);
                hermesWrapperApkService.updateById(one);
            }
        }

        hermesWrapperApk.setEnabled(status);
        hermesWrapperApkService.updateById(hermesWrapperApk);
        return ReturnUtil.success("ok");
    }

    @GetMapping("/usedWrapper")
    @ApiOperation(value = "查询某个服务,正在使用的wrapper")
    @ResponseBody
    public CommonRes<HermesWrapperApk> userdWrapper(@RequestParam("targetAppPackage") String appPackage) {
        return ReturnUtil.success(hermesWrapperApkService.getOne(new QueryWrapper<HermesWrapperApk>()
                .eq("apk_package", appPackage)
                .eq("enabled", true)));
    }

}
