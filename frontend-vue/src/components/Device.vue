<template>
    <div>
        设备列表，这里展示所有注册到系统的Android设备，你可以对设备进行上线下线，以及选择某些服务在执行的设备上面安装。
        <div class="block">
            <Table
                    :data="tableData"
                    :columns="tableHeaders"
                    border
                    style="width: 100%">
                <Spin size="large" fix v-if="loading"/>
            </Table>
            <Page v-if="total>0"
                  :total="total"
                  show-total
                  @on-change="getList"
                  :page-size="pageSize"
                  :current="currentPage"></Page>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'Device',
        methods: {
            enable(row, enabled) {
                const _this = this;
                this.$request.device.setEnable({
                    deviceId: row.id,
                    status: enabled
                }, function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.warning('修改失败，请稍后重试！')
                        return
                    }
                    _this.$Message.info('状态修改成功')
                    // _this.getList(_this.$data.currentPage)
                    row.status = enabled
                })
            },
            getList(currentPage) {
                console.log('get page:'+currentPage);
                this.loading = true;
                const data = this.$data;
                const _this = this;
                this.$request.device.getList({
                    page: currentPage - 1,
                    size: data.pageSize
                }, function (res) {
                    _this.loading = false;
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('请求失败，请稍后重试');
                        return
                    }
                    const resData = res.data.data;
                    data.tableData = _this.$lodash.cloneDeep(resData.content);
                    data.pageSize = resData.size;
                    if (data.tableData.length === 0) {
                        _this.$Message.info('没有查询到数据');
                        // 分页相关
                        data.currentPage = 1;
                        data.total = 0
                    } else {
                        // 分页相关
                        data.currentPage = currentPage;
                        data.total = resData.totalElements
                    }
                })
            }
        },
        mounted() {
            if (this.$route.params.page) {
                this.$data.currentPage = this.$route.params.page
            }
            this.getList(this.$data.currentPage)
        },
        filters: {
            booleanTransferFilter: (val) => {
                return val ? '启用' : '禁用'
            }
        },
        data() {
            return {
                currentPage: 1,
                total: 0,
                pageSize: 10,
                loading: false,
                tableData: [],
                tableHeaders: [
                    {title: 'id', key: 'id'},
                    {title: 'mac', key: 'mac'},
                    {title: 'ip', key: 'ip'},
                    {title: 'port', key: 'port'},
                    {title: 'brand', key: 'brand'},
                    {title: 'systemVersion', key: 'systemVersion'},
                    {title: 'status', key: 'status'},
                    {
                        title: 'Action', key: 'action', fixed: 'right', width: 120,
                        render: (h, param) => {
                            let setStatusText = param.row.status ? "offline" : "online";
                            return h('div', [
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            this.enable(param.row, !param.row.status);
                                        }
                                    }
                                }, setStatusText),
                                h('Button', {
                                    props: {
                                        type: 'text',
                                        size: 'small'
                                    },
                                    on: {
                                        click: () => {
                                            this.$router.push({
                                                name: this.$store.state.deviceDetail,
                                                params: param.row
                                            })
                                        }
                                    }
                                }, 'Detail')
                            ]);
                        }
                    }
                ]
            }
        }
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
    h1, h2 {
        font-weight: normal;
    }

    .popup-font {
        display: inline-block;
        width: 100%;
        text-align: left;
        font-size: 20px;
        line-height: 25px;
        padding: 5px;
        &-title {
            font-weight: 700;
        }
    }
</style>
