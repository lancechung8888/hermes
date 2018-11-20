import Vue from 'vue'
import Vuex from 'vuex'
import common from '../common/common'
import lodash from 'lodash'

Vue.use(Vuex);

export default new Vuex.Store({
    state: lodash.assign({
        navShow: false,
        navIndex: common.config.home,
        paramMap: {}
    }, common.config),
    mutations: {
        navShowSwitch(state, data) {
            state.navShow = data.navShow
        },
        navTabSwitch(state, data) {
            state.navIndex = data.index
        },
        REFRESHPARAM(state, paramKV) {
            //mutation，应该能看懂做的操作吧？
            Vue.set(state.paramMap, paramKV.key, paramKV.value)
        }
    }
})
