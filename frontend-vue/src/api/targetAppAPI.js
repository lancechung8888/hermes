import axios from 'axios'
import lodash from 'lodash'

const getList = function (params, callback) {
    axios.get('/hermes/targetApp/list', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const download = function (params, callback) {
    axios.get('/hermes/targetApp/download', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const getAvailableService = function (params, callback) {
    axios.get('/hermes/targetApp/listAvailableService', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const setEnable = function (params, callback) {
    axios.get('/hermes/targetApp/setStatus', {params})
        .then(function (response) {
            callback(lodash.cloneDeep(response))
        })
        .catch(function (error) {
            callback(error)
        })
};

const queryQueueStatus = function (params, callback) {
    axios.get('/hermes/queue/queueStatus', {params})
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
    getAvailableService,
    setEnable,
    queryQueueStatus
}
