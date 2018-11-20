import device from './deviceAPI'
import deviceService from './deviceServiceAPI'
import targetApp from './targetAppAPI'
import wrapper from './wrapperAPI'

const isRequestSuccess = function (res) {
    return res.data && res.data.status === 0
};

export default {
    device,
    targetApp,
    deviceService,
    wrapper,
    isRequestSuccess
}
