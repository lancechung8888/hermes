package com.virjar.hermesadmin.entity;


import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Created by virjar on 2018/8/4.<br>
 * 前端返回统一数据结构
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class CommonRes<T> {
    private int status = statusOK;
    private String message;
    private T data;

    public static final int statusOK = 0;

    public boolean success() {
        return status == statusOK;
    }
}
