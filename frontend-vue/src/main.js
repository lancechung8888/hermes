import Vue from 'vue'
import App from './App.vue'
import router from './router'

import store from './store/store'

import iView from 'iview'
import 'iview/dist/styles/iview.css'
import './assets/main.less'

import lodash from 'lodash'
import request from './api/request'

Vue.use(iView);

Vue.config.productionTip = false;
// 挂载loadsh
Vue.prototype.$lodash = lodash;
// 挂载所有请求
Vue.prototype.$request = request;

new Vue({
    el: '#app',
    router,
    store,
    //template: '<App/>',
    render: h => h(App),
    components: {
        App
    }
});
