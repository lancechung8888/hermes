import Vue from 'vue'
import Router from 'vue-router'
import Home from '@/components/Home'
import Device from '@/components/Device'
import targetApp from '@/components/TargetApp'
import Wrapper from '@/components/Wrapper'
import store from '../store/store'
import common from '../common/common'

import DeviceDetail from '@/components/DeviceDetail'
import TargetAppDetail from '@/components/TargetAppDetail'

const config = common.config;
Vue.use(Router);

const router = new Router({
    routes: [{
        path: '/',
        redirect: '/' + config.homePath
    },
        {
            path: '/' + config.homePath,
            name: config.home,
            component: Home
        },
        {
            path: '/' + config.devicePath,
            name: config.device,
            component: Device
        },
        {
            path: '/' + config.targetAppPath,
            name: config.targetApp,
            component: targetApp
        }, {
            path: '/' + config.wrapperPath,
            name: config.wrapper,
            component: Wrapper
        }, {
            path: '/' + config.deviceDetailPath,
            name: config.deviceDetail,
            component: DeviceDetail
        },
        {
            path: '/' + config.targetAppDetailPath,
            name: config.targetAppDetail,
            component: TargetAppDetail
        }
    ]
});

router.beforeEach((to, from, next) => {
    store.commit('navShowSwitch', {
        navShow: to.name !== config.home
    });
    store.commit('navTabSwitch', {
        index: to.name
    });
    if (Object.keys(to.params).length === 0) {
        // 从store中取出付给params，此处注意路径未必完全吻合，以你的为准
        Object.assign(to.params, store.state.paramMap[to.name] || {})
    }
    // 存储一下params备用
    store.commit('REFRESHPARAM', {key: to.name, value: to.params});
    next()
});

export default router
