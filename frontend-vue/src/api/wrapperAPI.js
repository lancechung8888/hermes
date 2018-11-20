import axios from 'axios'
import lodash from 'lodash'

const getList = function (params, callback) {
    axios.get('/hermes/wrapperApp/list', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const download = function (params, callback) {
    axios.get('/hermes/wrapperApp/download', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const setEnable = function (params, callback) {
    axios.get('/hermes/wrapperApp/setStatus', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const queryUsed = function (params, callback) {
    axios.get('/hermes/wrapperApp/usedWrapper', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

export default {
    getList,
    download,
    setEnable,
    queryUsed
}
