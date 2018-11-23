package com.virjar.hermes.hermesagent.hermes_api;

import android.util.Log;

import com.google.common.base.Function;
import com.google.common.base.Predicate;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.virjar.xposed_extention.ClassScanner;

import java.io.File;
import java.lang.reflect.Modifier;
import java.util.ArrayList;

import javax.annotation.Nullable;

public class MultiActionWrapperFactory {
    public static MultiActionWrapper createWrapperByAction(String packageName, File apkFilePath) {
        ClassScanner.AnnotationClassVisitor annotationClassVisitor = new ClassScanner.AnnotationClassVisitor(WrapperAction.class);
        ClassScanner.scan(annotationClassVisitor, Sets.newHashSet(packageName), apkFilePath);
        ArrayList<ActionRequestHandler> actionRequestHandlers = Lists.newArrayList(Iterables.filter(Iterables.transform(Iterables.filter(annotationClassVisitor.getClassSet(), new Predicate<Class>() {
            @Override
            public boolean apply(@Nullable Class input) {
                if (input == null) {
                    return false;
                }
                if (Modifier.isAbstract(input.getModifiers()) || input.isInterface()) {
                    return false;
                }
                WrapperAction wrapperAction = (WrapperAction) input.getAnnotation(WrapperAction.class);
                return !wrapperAction.value().trim().isEmpty() && ActionRequestHandler.class.isAssignableFrom(input);
            }
        }), new Function<Class, ActionRequestHandler>() {
            @Nullable
            @Override
            public ActionRequestHandler apply(@Nullable Class input) {
                if (input == null) {
                    return null;
                }
                try {
                    return (ActionRequestHandler) input.newInstance();
                } catch (Exception e) {
                    Log.w("weijia", "failed to load create plugin", e);
                    return null;
                }
            }
        }), new Predicate<ActionRequestHandler>() {
            @Override
            public boolean apply(@Nullable ActionRequestHandler input) {
                return input != null;
            }
        }));
        if (actionRequestHandlers.size() == 0) {
            return null;
        }
        MultiActionWrapper multiActionWrapper = new MultiActionWrapper();
        for (ActionRequestHandler actionRequestHandler : actionRequestHandlers) {
            multiActionWrapper.registryHandler(actionRequestHandler.getClass().getAnnotation(WrapperAction.class).value(), actionRequestHandler);
        }
        return multiActionWrapper;
    }
}
