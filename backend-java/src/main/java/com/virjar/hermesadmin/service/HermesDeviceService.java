package com.virjar.hermesadmin.service;

import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.google.common.base.Function;
import com.google.common.base.Joiner;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.virjar.hermesadmin.entity.CommonRes;
import com.virjar.hermesadmin.entity.HermesDevice;
import com.virjar.hermesadmin.entity.ReportModel;
import com.virjar.hermesadmin.mapper.HermesDeviceMapper;
import com.virjar.hermesadmin.service.servicemanager.AppServiceRegistry;
import com.virjar.hermesadmin.util.Constant;
import com.virjar.hermesadmin.util.ReturnUtil;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.math.NumberUtils;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.config.SocketConfig;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.impl.client.LaxRedirectStrategy;
import org.apache.http.util.EntityUtils;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.net.URLEncoder;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * <p>
 * 服务实现类
 * </p>
 *
 * @author virjar
 * @since 2018-11-03
 */
@Service
@Slf4j
public class HermesDeviceService extends ServiceImpl<HermesDeviceMapper, HermesDevice> {

    @Resource
    private AppServiceRegistry appServiceRegistry;

    public IPage<HermesDevice> selectForConfiguredPackage(Page pag, String appPackage) {
        return baseMapper.selectForConfiguredPackage(pag, appPackage);
    }

    public IPage<HermesDevice> availableForTargetApp(Page pag, String appPackage) {
        return baseMapper.availableDeviceForPackage(pag, appPackage);
    }

    public CommonRes<?> invoke(HttpServletRequest httpServletRequest) {
        String contentType = httpServletRequest.getContentType();
        String service = httpServletRequest.getParameter("invoke_package");
        Integer timeOut = NumberUtils.toInt(httpServletRequest.getParameter("invoke_timeOut"));
        String requestBody = joinParam(httpServletRequest.getParameterMap());
        if (httpServletRequest.getMethod().equalsIgnoreCase("post")
                && StringUtils.containsIgnoreCase(contentType, "application/json;charset=utf8")) {
            try {
                requestBody = IOUtils.toString(httpServletRequest.getInputStream());
            } catch (IOException e) {
                log.error("error for decode http request", e);
                return ReturnUtil.failed(e);
            }
            if (StringUtils.isBlank(service)) {
                JSONObject jsonObject = JSONObject.parseObject(requestBody);
                service = jsonObject.getString("invoke_package");
                timeOut = jsonObject.getInteger("invoke_timeOut");
            }
        }
        if (StringUtils.isBlank(service)) {
            return ReturnUtil.failed("param: {invoke_package} not present");
        }
        String mac = appServiceRegistry.rollPoling(service);
        if (StringUtils.isBlank(mac)) {
            return ReturnUtil.failed("no service online");
        }
        HermesDevice hermesDevice = findByMac(mac);
        if (hermesDevice == null) {
            appServiceRegistry.offline(service, mac);
            return ReturnUtil.failed("system error,can not find device mode for choose device id");
        }

        if (timeOut == null || timeOut < 1) {
            //默认5s的超时时间
            timeOut = 5000;
        }
        if (StringUtils.isBlank(contentType)) {
            contentType = "application/x-www-form-urlencoded";
        }

        if (hermesDevice.getIp().equalsIgnoreCase(hermesDevice.getVisibleIp())) {
            //在同一个网络环境下,使用http请求,client->server的模式,对服务器压力小
            return forwardByHttpProtocol(hermesDevice, service, requestBody, timeOut, contentType);
        } else {
            //非同一网段,无法直接请求内网server,考虑长链接方案,由于server会和client一直保持tcp链接,这将会限制
            //server的最大并发数量,当此模式下手机过多,则需要考虑水平扩容
            return forwardByNetty(hermesDevice, service, requestBody, timeOut, contentType);
        }
    }

    public HermesDevice findByMac(String mac) {
        return baseMapper.selectOne(new QueryWrapper<HermesDevice>().eq("mac", mac));
    }

    public CommonRes<?> handleReport(ReportModel reportModel, HttpServletRequest httpServletRequest) {
        HermesDevice device = findByMac(reportModel.getMac());
        boolean newDevice = false;
        if (device == null) {
            newDevice = true;
            device = new HermesDevice();
        }
        device.setName(reportModel.getBrand());
        device.setBrand(reportModel.getBrand());
        device.setIp(reportModel.getAgentServerIP());
        device.setPort(reportModel.getAgentServerPort());
        device.setMac(reportModel.getMac());
        device.setSystemVersion(reportModel.getSystemVersion());
        device.setVisibleIp(httpServletRequest.getRemoteAddr());
        if (newDevice) {
            baseMapper.insert(device);
        } else {
            baseMapper.updateById(device);
        }
        appServiceRegistry.handleReport(reportModel);
        return ReturnUtil.success("");
    }

    private CommonRes<?> forwardByNetty(HermesDevice device, String service, String requestBody, int timeOut, String contentType) {
        //TODO 这里提供netty的方案
        return ReturnUtil.failed("not implemented");
    }

    private CommonRes<?> forwardByHttpProtocol(HermesDevice device, String service, String requestBody, int timeOut, String contentType) {
        //http://192.168.2.55:5597/invoke?invoke_package=com.tencent.weishi&key=%E5%B0%8F%E5%A7%90%E5%A7%90
        String requestURL = buildRequestURL(device, service);
        try {
            HttpPost httpPost = new HttpPost(requestURL);
            RequestConfig.Builder builder = RequestConfig.custom().setSocketTimeout(timeOut)
                    .setConnectTimeout(timeOut)
                    //.setProxy(new HttpHost("127.0.0.1", 8888))
                    .setConnectionRequestTimeout(timeOut);

            httpPost.setConfig(builder.build());
            httpPost.setEntity(new StringEntity(requestBody, contentType));
            if (httpClient == null) {
                createHttpClient();
            }
            HttpResponse httpResponse = httpClient.execute(httpPost);
            JSONObject ret = JSONObject.parseObject(EntityUtils.toString(httpResponse.getEntity()));
            Integer status = ret.getInteger("status");
            if (status == Constant.status_service_not_available) {
                appServiceRegistry.offline(service, device.getMac());
            }
            return ReturnUtil.from(ret);
        } catch (IOException e) {
            log.error("forward failed", e);
            return ReturnUtil.failed("timeOut");
        }
    }

    private HttpClient httpClient = null;

    private synchronized void createHttpClient() {
        if (httpClient != null) {
            return;
        }
        SocketConfig socketConfig = SocketConfig.custom().setSoKeepAlive(true).setSoLinger(-1).setSoReuseAddress(false)
                .setTcpNoDelay(true).build();
        httpClient = HttpClientBuilder.create().setMaxConnTotal(500).setMaxConnPerRoute(25)
                .setDefaultSocketConfig(socketConfig)
                .setRedirectStrategy(new LaxRedirectStrategy())
                .build();
    }

    private String buildRequestURL(HermesDevice device, String targetService) {
        return "http://" + device.getIp() + ":" + device.getPort() + "/invoke?invoke_package=" + targetService;
    }


    private Joiner joiner = Joiner.on('&').skipNulls();

    private String joinParam(Map<String, String[]> params) {
        if (params == null || params.isEmpty()) {
            return null;
        }
        return joiner.join(params.entrySet().stream().map(input -> {
            assert input != null;
            final String name = input.getKey();
            String[] inputValue = input.getValue();
            List<String> encodeItem = Lists.newArrayListWithExpectedSize(inputValue.length);
            for (String value : inputValue) {
                encodeItem.add(URLEncoder.encode(name) + "=" + URLEncoder.encode(value));
            }
            return joiner.join(encodeItem);
        }).collect(Collectors.toList()));

    }
}
