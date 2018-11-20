const BASE_URL = process.env.NODE_ENV === 'production'
    ? '/hermes/static/'
    : '/';


module.exports = {
    baseUrl: BASE_URL,
    productionSourceMap: false,
    devServer: {
        port: 5598,
        // 设置代理
        proxy: {
            "/": {
                target: "http://127.0.0.1:5597", // 域名
                ws: false, // 是否启用websockets
                changOrigin: true,
                secure: false,
                pathRequiresRewrite: {
                    // "^/v1": "/"
                }
            }
        },
        disableHostCheck: true
    }
};
