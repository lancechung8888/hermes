<template>
    <div>
        <div>Wrapper列表</div>
        <p>
            wrapper，wrapper是对于某些需要破解对apk实现的破解逻辑代码，wrapper需要符合hermes定义的接口规范。对于同一个wrapper，如果发生更新，需要升级apk的版本号码
        </p>
        <div style="margin-top: 2em"></div>

        <Button type="primary" @click="modal.show = true">点击上传新的WrapperApk</Button>
        <Modal
                title="上传wrapperAPK"
                v-model="modal.show"
                width="30%">
            <Upload action="/hermes/wrapperApp/upload"
                    type="drag"
                    name="agentAPK"
                    :on-success="onApkUploadSuccess"
                    accept="application/vnd.android.package-archive">
                <div style="padding: 20px 0">
                    <Icon type="ios-cloud-upload" size="52" style="color: #3399ff"></Icon>
                    <p>选择/拖拽 apk 文件上传</p>
                    <div slot="tip" class="el-upload__tip">只能上传apk文件，且不超过500M</div>
                </div>
            </Upload>
            <p slot="footer" style="text-align: center">
                <Button type="primary" @click="handleUploadDialogClosed">完成</Button>
            </p>
        </Modal>
        <div class="block">
            <Table
                    :data="tableData"
                    :columns="dataColumns"
                    border
                    style="width: 100%">
                <Spin size="large" fix v-if="loading"/>
            </Table>
            <Page v-if="total>0" :total="total"
                  :page-size="pageSize"
                  @on-change="getList"
                  show-total
                  :current="currentPage"/>
        </div>
    </div>
</template>

<script>

    export default {
        name: 'Wrapper',
        methods: {
            handleUploadDialogClosed() {
                this.$data.modal.show = false;
                this.getList(currentPage)
            },
            enable(row, state) {
                const _this = this;
                this.$request.wrapper.setEnable({
                    wrapperId: row.id,
                    status: state
                }, function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.error('修改失败，请稍后重试！');
                        return
                    }
                    _this.$Message.info('状态修改成功');
                    row.enabled = state
                })
            },
            download(row) {
                this.$request.wrapper.download({
                    apkId: row.id
                }, function (res) {
                    console.log(res)
                })
            },
            onApkUploadSuccess(response, file, fileList) {
                if (response.status !== 0) {
                    this.$Message.error(response.message);
                    file.status = 'fail';
                    fileList.splice(fileList.indexOf(file), 1)
                }
            },
            getList(currentPage) {
                this.loading = true;
                const _this = this;
                const data = this.$data;
                this.$request.wrapper.getList({
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
                        _this.$Message.warning('没有查询到数据');
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
            this.getList(1)
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
                agentAPK: '',
                modal: {
                    show: false
                },
                dataColumns: [
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

    .upload-demo {
        height: 100px;
        float: left;
        &-tip {
            text-align: left;
            height: 30px;
            line-height: 30px;
            color: red;
        }
    }
</style>
