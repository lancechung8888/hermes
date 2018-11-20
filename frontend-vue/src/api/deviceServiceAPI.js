import axios from 'axios'
import lodash from 'lodash'
import qs from 'qs'

const getList = function (params, callback) {
    axios.get('/hermes/service/list', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};


const deployAllService = function (params, callback) {
    axios.get('/hermes/service/deployAllService', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const installOne = function (params, callback) {
    axios.get('/hermes/service/installOne', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};
const installServiceForDevice = function (params, callback) {
    axios.get('/hermes/service/installServiceForDevice', {
        params: params,
        paramsSerializer: params => {
            return qs.stringify(params, {indices: false})
        }
    }).then(function (response) {
        callback(lodash.cloneDeep(response))
    }).catch(function (error) {
        callback(error)
    })
};


export default {
    getList,
    deployAllService,
    installOne,
    installServiceForDevice
}
