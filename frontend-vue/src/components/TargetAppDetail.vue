<template>
    <div>
        <div class="block">
            <div>
                <Row>
                    <Col>
                        <div>Target APP Detail DashBoard</div>
                    </Col>
                </Row>
                <Divider/>
                <Row>
                    <Col span="4">id</Col>
                    <Col span="4">APP Name</Col>
                    <Col span="4">APP package</Col>
                    <Col span="4">status</Col>
                    <Col span="8">downloadUrl</Col>
                </Row>
                <Row>
                    <Col span="4">{{targetAppModel.id}}</Col>
                    <Col span="4">{{targetAppModel.name}}</Col>
                    <Col span="4">{{targetAppModel.appPackage}}</Col>
                    <Col span="4">{{targetAppModel.enabled}}</Col>
                    <Col span="8">{{targetAppModel.downloadUrl}}</Col>
                </Row>
                <Divider dashed/>
                <Row>
                    <Col span="4">Icon</Col>
                    <Col span="4">version</Col>
                    <Col span="4">versionCode</Col>
                    <Col span="4">savePath</Col>
                </Row>
                <Row>
                    <Col span="4">TODO</Col>
                    <Col span="4">{{targetAppModel.version}}</Col>
                    <Col span="4">{{targetAppModel.versionCode}}</Col>
                    <Col span="4">{{targetAppModel.savePath}}</Col>
                </Row>
                <Divider dashed/>
                <Row>
                    <Col span="4">UsedWrapperPackage</Col>
                    <Col span="4">UsedWrapperVersion</Col>
                    <Col span="4">UsedWrapperVersionCode</Col>
                    <Col span="4">UsedWrapperDownloadUrl</Col>
                </Row>
                <Row v-if="presented">
                    <Col span="4">{{usedWrapper.apkPackage}}</Col>
                    <Col span="4">{{usedWrapper.version}}</Col>
                    <Col span="4">{{usedWrapper.versionCode}}</Col>
                    <Col span="4">{{usedWrapper.downloadUrl}}</Col>
                </Row>
                <Divider dashed/>
            </div>
        </div>
        <div class="block">
            <Tabs>
                <TabPane label="Available Device">
                    <Table ref="availableDeviceSelection"
                           :data="availableDeviceData"
                           :columns="availableDeviceTableHeaders"
                           :loading="availableDevicePage.loading"

                           border
                           style="width: 100%">
                    </Table>
                    <Page v-if="availableDevicePage.total>0" :total="availableDevicePage.total"
                          :page-size="availableDevicePage.pageSize"
                          @on-change="getAvailableList"
                          show-total
                          :current="availableDevicePage.currentPage"/>
                </TabPane>
                <TabPane label="Installed Device">
                    <Table ref="installedDeviceSelection"
                           :data="installedDeviceData"
                           :columns="installedDeviceTableHeaders"
                           :loading="installedDevicePage.loading"

                           border
                           style="width: 100%">
                    </Table>
                    <Page v-if="installedDevicePage.total>0" :total="installedDevicePage.total"
                          :page-size="installedDevicePage.pageSize"
                          @on-change="getInstalledList"
                          show-total
                          :current="installedDevicePage.currentPage"/>
                </TabPane>
                <TabPane label="Online devices">
                    <Table :data="onlineDevices"
                           :columns="onlineDeviceColumn"
                           border
                           style="width: 100%"
                    />
                </TabPane>
                <TabPane label="App Wrappers">
                    <Table
                            :data="wrapperApkData"
                            :columns="wrapperTableHeaders"
                            :loading="wrapperPage.loading"
                            border
                            style="width: 100%">
                    </Table>
                    <Page v-if="wrapperPage.total>0" :total="wrapperPage.total"
                          :page-size="wrapperPage.pageSize"
                          @on-change="getWrapperList"
                          show-total
                          :current="wrapperPage.currentPage"/>
                </TabPane>
            </Tabs>
        </div>
    </div>

</template>

<script>
    export default {
        name: 'targetAppDetail',
        methods: {
            getInstalledList(currentPage) { // 参数为要查询的页数
                this.installedDevicePage.loading = true;
                const _this = this;
                const data = this.$data;
                this.$request.device.getList(_this.$lodash.assign({
                    page: data.installedDevicePage.currentPage - 1,
                    size: data.installedDevicePage.pageSize,
                    appPackage: _this.$data.targetAppModel.appPackage
                }, _this.$data.params), function (res) {
                    _this.installedDevicePage.loading = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    const resData = res.data.data;
                    data.installedDeviceData = _this.$lodash.cloneDeep(resData.content);
                    data.installedDevicePage.pageSize = resData.size;
                    data.installedDevicePage.currentPage = currentPage;
                    data.installedDevicePage.total = resData.totalElements
                })
            },
            getAvailableList(currentPage) {
                this.availableDevicePage.loading = true;
                const _this = this;
                const data = this.$data;
                this.$request.device.getAvailableDevice({
                    page: data.availableDevicePage.currentPage - 1,
                    size: data.availableDevicePage.pageSize,
                    appPackage: _this.$data.targetAppModel.appPackage
                }, function (res) {
                    _this.availableDevicePage.loading = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    const resData = res.data.data;
                    data.availableDeviceData = _this.$lodash.cloneDeep(resData.content);
                    data.availableDevicePage.pageSize = resData.size;
                    data.availableDevicePage.currentPage = currentPage;
                    data.availableDevicePage.total = resData.totalElements
                })
            },
            getWrapperList(currentPage) {
                this.wrapperPage.loading = true;
                const _this = this;
                const data = this.$data;
                this.$request.wrapper.getList({
                    page: data.wrapperPage.currentPage - 1,
                    size: data.wrapperPage.pageSize,
                    targetAppPackage: _this.$data.targetAppModel.appPackage
                }, function (res) {
                    _this.wrapperPage.loading = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    const resData = res.data.data;
                    data.wrapperApkData = _this.$lodash.cloneDeep(resData.content);
                    data.wrapperPage.pageSize = resData.size;
                    data.wrapperPage.currentPage = currentPage;
                    data.wrapperPage.total = resData.totalElements
                })
            },
            queryUsedWrapper() {
                const _this = this;
                let targetAppPackage = this.$data.targetAppModel.appPackage;
                this.$request.wrapper.queryUsed({
                    targetPackage: targetAppPackage
                }, function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.presented = false;
                        return
                    }
                    _this.$data.usedWrapper = res.data.data;
                    _this.presented = true;
                });

            },
            queryOnlineDevices() {
                const _this = this;
                let targetAppPackage = this.$data.targetAppModel.appPackage;
                this.$request.targetApp.queryQueueStatus({
                    servicePackage: targetAppPackage
                }, function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.presented = false;
                        return
                    }
                    _this.$data.onlineDevices = res.data.data;
                    _this.presented = true;
                });
            }
            ,
            installOneService(targetDeviceModel, enabled) {
                const _this = this;
                if (!enabled) {
                    enabled = false;
                }
                _this.$request.deviceService.installOne({
                    deviceMac: targetDeviceModel.mac,
                    targetService: this.$data.targetAppModel.appPackage,
                    enabled: enabled
                }, function (res) {
                    targetDeviceModel.__is_installing = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    _this.$Message.info(enabled ? 'install success' : "uninstall success");
                    _this.getInstalledList(_this.$data.installedDevicePage.currentPage);
                    _this.getAvailableList(_this.$data.availableDevicePage.currentPage);
                })
            }, enable(row, state) {
                const _this = this;
                this.$request.wrapper.setEnable({
                    wrapperId: row.id,
                    status: state
                }, function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('修改失败，请稍后重试！');
                        return
                    }
                    _this.queryUsedWrapper();
                    _this.$Message.info('状态修改成功');
                    row.enabled = state
                })
            }
        },
        mounted() {
            if (!this.$data.targetAppModel || !this.$data.targetAppModel.id) {
                this.$data.targetAppModel = this.$route.params;
            }
            if (!this.$data.targetAppModel || !this.$data.targetAppModel.id) {
                this.$Message.error("you can not access this page direct");
                setTimeout(() => {
                    this.$router.push({
                        name: this.$store.state.targetApp
                    });
                }, 1400);
                return;
            }
            this.getInstalledList(1);
            this.getAvailableList(1);
            this.getWrapperList(1);
            this.queryUsedWrapper();
            this.queryOnlineDevices();
        },
        data() {
            return {
                targetAppModel: {},
                availableDeviceData: [],
                installedDevicePage: {
                    loading: false,
                    total: 0,
                    pageSize: 10,
                    currentPage: 1
                },
                installedDeviceData: [],
                installedDeviceTableHeaders: [
                    {type: 'selection', width: 60, align: 'center'},
                    {title: 'id', key: 'id'},
                    {title: 'ip', key: 'ip'},
                    {title: 'visibleIp', key: 'visibleIp'},
                    {title: 'port', key: 'port'},
                    {title: 'mac', key: 'mac'},
                    {title: 'brand', key: 'brand'},
                    {title: 'systemVersion', key: 'systemVersion'},
                    {
                        title: 'Action',
                        key: 'action',
                        fixed: 'right',
                        width: 120,
                        render: (h, params) => {
                            return h('div', [
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            if (params.row.__is_installing) {
                                                return;
                                            }
                                            params.row.__is_installing = true;
                                            this.installOneService(params.row, false);
                                        }
                                    }
                                }, 'UnInstall'),
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            this.$router.push({
                                                name: this.$store.state.deviceDetail,
                                                params: params.row
                                            })
                                        }
                                    }
                                }, 'Detail')
                            ]);
                        }
                    }
                ],
                availableDevicePage: {
                    loading: false,
                    total: 0,
                    pageSize: 10,
                    currentPage: 1
                },
                availableDeviceTableHeaders: [
                    {type: 'selection', width: 60, align: 'center'},
                    {title: 'id', key: 'id'},
                    {title: 'ip', key: 'ip'},
                    {title: 'visibleIp', key: 'visibleIp'},
                    {title: 'port', key: 'port'},
                    {title: 'mac', key: 'mac'},
                    {title: 'brand', key: 'brand'},
                    {title: 'systemVersion', key: 'systemVersion'},
                    {
                        title: 'Action',
                        key: 'action',
                        fixed: 'right',
                        width: 120,
                        render: (h, params) => {
                            return h('div', [
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            if (params.row.__is_installing) {
                                                return;
                                            }
                                            params.row.__is_installing = true;
                                            this.installOneService(params.row, true);
                                        }
                                    }
                                }, 'Install'),
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            this.$router.push({
                                                name: this.$store.state.deviceDetail,
                                                params: params.row
                                            })
                                        }
                                    }
                                }, 'Detail')
                            ]);
                        }

                    }

                ],
                wrapperApkData: [],
                wrapperPage: {
                    loading: false,
                    total: 0,
                    pageSize: 10,
                    currentPage: 1
                },
                wrapperTableHeaders: [
                    {title: 'wrapperPackage', key: 'apkPackage'},
                    {title: 'targetApkPackage', key: 'targetApkPackage'},
                    {title: 'version', key: 'version'},
                    {title: 'versionCode', key: 'versionCode'},
                    {title: 'downloadUrl', key: 'downloadUrl'},
                    {title: 'status', key: 'enabled'},
                    {
                        title: 'Action',
                        key: 'action',
                        fixed: 'right',
                        width: 120,
                        render: (h, params) => {
                            let setStatusText = params.row.enabled ? "offline" : "online";
                            return h('div', [
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            this.enable(params.row, !params.row.enabled);
                                        }
                                    }
                                }, setStatusText)
                            ]);
                        }
                    }
                ],
                usedWrapper: {},
                presented: false,
                onlineDevices: [],
                onlineDeviceColumn: [
                    {title: 'ip', key: 'ip'},
                    {title: 'port', key: 'port'},
                    {title: 'mac', key: 'mac'},
                    {title: 'score', key: 'score'},
                    {title: 'lastReportTime', key: 'lastReportTime'}
                ]
            }
        }
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
    h1, h2 {
        font-weight: normal;
    }
</style>
