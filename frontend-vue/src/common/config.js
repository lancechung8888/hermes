import lodash from 'lodash'
import util from './util'

const titleConfig = {
    home: 'Home',
    device: 'Device',
    targetApp: 'TargetApp',
    wrapper: 'Wrapper',
    deviceDetail: 'DeviceDetail',
    targetAppDetail: 'targetAppDetail'
};
// 根据配置生成path和name数据
const pathConfig = {};
lodash.keys(titleConfig).forEach(function (value) {
    pathConfig[value + 'Path'] = util.firstLetterLower(titleConfig[value])
});
const config = lodash.assign(titleConfig, pathConfig);

export default lodash.assign({
    projectName: 'Hermes'
}, config)
