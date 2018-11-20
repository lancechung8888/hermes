import axios from 'axios'
import lodash from 'lodash'

const getList = function (params, callback) {
    axios.get('/hermes/device/list', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const setEnable = function (params, callback) {
    axios.get('/hermes/device/setStatus', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const getAvailableDevice = function (params, callback) {
    axios.get('/hermes/device/listAvailableDevice', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

export default {
    getList,
    setEnable,
    getAvailableDevice
}
