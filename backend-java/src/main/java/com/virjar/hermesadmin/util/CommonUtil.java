package com.virjar.hermesadmin.util;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.google.common.collect.Lists;
import lombok.Cleanup;
import lombok.extern.slf4j.Slf4j;
import net.dongliu.apk.parser.ApkFile;
import net.dongliu.apk.parser.bean.ApkMeta;
import org.apache.commons.lang3.StringUtils;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

import java.io.*;
import java.util.List;

/**
 * Created by virjar on 2018/8/4.
 */
@Slf4j
public class CommonUtil {


    public static String getStackTrack(Throwable throwable) {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        PrintWriter printWriter = new PrintWriter(new OutputStreamWriter(byteArrayOutputStream));
        throwable.printStackTrace(printWriter);
        return byteArrayOutputStream.toString();
    }

    public static String translateSimpleExceptionMessage(Exception exception) {
        String message = exception.getMessage();
        if (StringUtils.isBlank(message)) {
            message = exception.getClass().getName();
        }
        return message;
    }


    public static ApkMeta parseApk(File file) {
        //now parse the file
        try {
            @Cleanup ApkFile apkFile = new ApkFile(file);
            return apkFile.getApkMeta();
        } catch (IOException e) {
            file.delete();
            throw new IllegalStateException("the filed not a apk filed format");
        }
    }

    public static <T> Page<T> wrapperPage(Pageable pageable) {
        Page<T> page = new Page<>();
        page.setSize(pageable.getPageSize())
                .setCurrent(pageable.getPageNumber());
        Sort sort = pageable.getSort();
        if (sort != null) {
            List<String> ascs = Lists.newArrayList();
            List<String> descs = Lists.newArrayList();
            for (Sort.Order order : sort) {
                if (order.getDirection() == Sort.Direction.ASC) {
                    ascs.add(order.getProperty());
                } else {
                    descs.add(order.getProperty());
                }
            }
            page.setAscs(ascs);
            page.setDescs(descs);
        }
        return page;
    }
}
