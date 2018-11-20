<template>
    <div>
        <div class="block">
            <div>
                <Row>
                    <Col>
                        <div>Device Detail DashBoard</div>
                    </Col>
                </Row>
                <Divider/>
                <Row>
                    <Col span="4">deviceId</Col>
                    <Col span="4">mac</Col>
                    <Col span="4">ip</Col>
                    <Col span="4">port</Col>
                    <Col span="4">visibleIp</Col>
                    <Col span="4">status</Col>
                </Row>
                <Row>
                    <Col span="4">{{deviceModel.id}}</Col>
                    <Col span="4">{{deviceModel.mac}}</Col>
                    <Col span="4">{{deviceModel.ip}}</Col>
                    <Col span="4">{{deviceModel.port}}</Col>
                    <Col span="4">{{deviceModel.visibleIp}}</Col>
                    <Col span="4">{{deviceModel.status}}</Col>
                </Row>
                <Divider dashed/>
                <Row>
                    <Col span="4">brand</Col>
                    <Col span="4">systemVersion</Col>
                    <Col span="4">cpuUsage</Col>
                    <Col span="4">memoryInfo</Col>
                    <Col span="4">lastReportTime</Col>
                </Row>
                <Row>
                    <Col span="4">{{deviceModel.brand}}</Col>
                    <Col span="4">{{deviceModel.systemVersion}}</Col>
                    <Col span="4">{{deviceModel.cpuUsage}}%</Col>
                    <Col span="4">{{deviceModel.memory}}%</Col>
                    <Col span="4">{{deviceModel.lastReportTime}}</Col>
                </Row>
                <Divider dashed/>
            </div>
        </div>
        <div class="block">
            <Tabs>
                <TabPane label="Installed Service">
                    <Table ref="installedServiceSelection"
                           :data="installedServiceData"
                           :columns="installedServiceTableHeaders"
                           :loading="installedPage.loading"
                           border
                           style="width: 100%">
                    </Table>
                    <Page v-if="installedPage.total>0" :total="installedPage.total" :page-size="installedPage.pageSize"
                          @on-change="getInstalledList"
                          show-total
                          :current="installedPage.currentPage"/>
                </TabPane>
                <TabPane label="Available Service">
                    <Table
                            ref="availableServiceSelection"
                            :data="availableServiceData"
                            :columns="availableServiceTableHeaders"
                            :loading="availablePage.loading"
                            border
                            style="width: 100%">
                    </Table>
                    <Page v-if="availablePage.total>0" :total="availablePage.total" :page-size="availablePage.pageSize"
                          @on-change="getAvailableList"
                          show-total
                          :current="availablePage.currentPage"/>
                    <Row>
                        <Col span="2">
                            <Button @click="installService(false)">install selected service</Button>
                        </Col>
                        <Col span="2">
                            <Button @click="installService(true)">install all service(danger)</Button>
                        </Col>
                    </Row>
                </TabPane>

                <TabPane label="Online Service">
                    <ul>
                        <li v-for="service in onlineServices">
                            {{service}}
                        </li>
                    </ul>
                </TabPane>
                <TabPane label="Hermes Log">display device running log (TODO)</TabPane>
                <TabPane label="Device Terminal">a shell that connected to this device(TODO)</TabPane>
                <TabPane label="Debugger">i give you a debugger,so you can test invoke api on this device(TODO)
                </TabPane>
            </Tabs>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'DeviceDetail',
        methods: {
            getInstalledList(currentPage) { // 参数为要查询的页数
                this.availablePage.loading = true;
                const _this = this;
                const data = this.$data;
                this.$request.targetApp.getList(_this.$lodash.assign({
                    page: data.installedPage.currentPage - 1,
                    size: data.installedPage.pageSize,
                    mac: _this.$data.deviceModel.mac
                }, _this.$data.params), function (res) {
                    _this.installedPage.loading = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    const resData = res.data.data;
                    data.installedServiceData = _this.$lodash.cloneDeep(resData.content);
                    data.installedPage.pageSize = resData.size;
                    data.installedPage.currentPage = currentPage;
                    data.installedPage.total = resData.totalElements
                })
            },
            getAvailableList(currentPage) { // 参数为要查询的页数
                this.availablePage.loading = true;
                const _this = this;
                const data = this.$data;
                this.$request.targetApp.getAvailableService(_this.$lodash.assign({
                    page: data.availablePage.currentPage - 1,
                    size: data.availablePage.pageSize,
                    mac: _this.$data.deviceModel.mac
                }, _this.$data.params), function (res) {
                    _this.availablePage.loading = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    const resData = res.data.data;
                    data.availableServiceData = _this.$lodash.cloneDeep(resData.content);
                    data.availablePage.pageSize = resData.size;
                    data.availablePage.currentPage = currentPage;
                    data.availablePage.total = resData.totalElements
                })
            },
            installOneService(targetAppModel, enabled) {
                const _this = this;
                if (!enabled) {
                    enabled = false;
                }
                _this.$request.deviceService.installOne({
                    deviceMac: this.$data.deviceModel.mac,
                    targetService: targetAppModel.appPackage,
                    enabled: enabled
                }, function (res) {
                    targetAppModel.__is_installing = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    _this.$Message.info(enabled ? 'install success' : "uninstall success");
                    _this.getInstalledList(_this.$data.installedPage.currentPage);
                    _this.getAvailableList(_this.$data.availablePage.currentPage);
                })
            },
            installService(forAllService) {
                const _this = this;
                if (_this.$data.availablePage.total === 0) {
                    _this.$Message.error('there is no available service for install');
                    return
                }
                let installCallback = function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    _this.$Message.info("install success");
                    _this.getInstalledList(_this.$data.installedPage.currentPage);
                    _this.getAvailableList(_this.$data.availablePage.currentPage);
                };
                if (forAllService) {

                    this.$Message.warning({
                            content: "you are install all service on this device ,this maybe caused hi load for device",
                            duration: 10
                        }
                    );
                    _this.$request.deviceService.deployAllService({
                        deviceMac: _this.$data.deviceModel.mac
                    }, installCallback)
                } else {
                    if (_this.$refs.availableServiceSelection.getSelection().length === 0) {
                        _this.$Message.error('please select some service');
                        return
                    }
                    _this.$request.deviceService.installServiceForDevice({
                        deviceMac: _this.$data.deviceModel.mac,
                        targetServiceList: _this.$refs.availableServiceSelection.getSelection().map(function (item) {
                            return item.appPackage;
                        })
                    }, installCallback)
                }


            }
        },
        mounted() {
            if (!this.$data.deviceModel || !this.$data.deviceModel.id) {
                this.$data.deviceModel = this.$route.params;
            }
            if (!this.$data.deviceModel || !this.$data.deviceModel.id) {
                this.$Message.error("you can not access this page direct");
                setTimeout(() => {
                    this.$router.push({
                        name: this.$store.state.device
                    });
                }, 1400);
                return;
            }
            this.onlineServices = JSON.parse(this.deviceModel['lastReportService']);
            if (this.onlineServices.length === 0) {
                this.onlineServices = ['no available service']
            }
            this.getInstalledList(1);
            this.getAvailableList(1);
        },
        data() {
            return {
                deviceModel: {},
                installedServiceTableHeaders: [
                    {type: 'selection', width: 60, align: 'center'},
                    {title: 'id', key: 'id'},
                    {title: 'appPackage', key: 'appPackage'},
                    {title: 'version', key: 'version'},
                    {title: 'versionCode', key: 'versionCode'},
                    {title: 'downloadUrl', key: 'downloadUrl'},
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
                                                name: this.$store.state.targetAppDetail,
                                                params: params.row
                                            })
                                        }
                                    }
                                }, 'Detail')
                            ]);
                        }
                    }
                ],
                installedServiceData: [],
                installedPage: {
                    currentPage: 1,
                    total: 0,
                    pageSize: 10,
                    loading: false,
                    lastPage: 0
                },
                availableServiceTableHeaders: [
                    {type: 'selection', width: 60, align: 'center'},
                    {title: 'id', key: 'id'},
                    {title: 'appPackage', key: 'appPackage'},
                    {title: 'version', key: 'version'},
                    {title: 'versionCode', key: 'versionCode'},
                    {title: 'downloadUrl', key: 'downloadUrl'},
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
                                                name: this.$store.state.targetAppDetail,
                                                params: params.row
                                            })
                                        }
                                    }
                                }, 'Detail')
                            ]);
                        }
                    }
                ],
                availableServiceData: [],
                availablePage: {
                    currentPage: 1,
                    total: 0,
                    pageSize: 10,
                    loading: false,
                    lastPage: 0
                },
                onlineServices: []
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
