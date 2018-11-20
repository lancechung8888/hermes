<template>
    <div>
        <div>App列表</div>
        <p>
            这里列出所有的目标apk，如微视，微信等将要被破解的app，一个抓取需求上线，需要先在这里上传对应的app文件
        </p>
        <div style="margin-top: 2em"></div>
        <Button type="primary" @click="modal.show = true">点击上传新的TargetApk</Button>
        <Modal
                title="上传targetAPK"
                v-model="modal.show"
                width="30%">
            <Upload action="/hermes/targetApp/upload"
                    name="targetAPK"
                    type="drag"
                    drag accept="application/vnd.android.package-archive"
                    :on-success="onApkUploadSuccess">
                <div style="padding: 20px 0">
                    <i class="el-icon-upload" style="font-size: 52px; color: #3399ff;"></i>
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
            <Page v-if="total>0" :total="total" :page-size="pageSize"
                  @on-change="getList"
                  show-total
                  :current="currentPage"/>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'targetApp',
        methods: {
            setTargetAppStatus(targetAppModel, enabled) {
                const _this = this;
                this.$request.targetApp.setEnable({
                    targetAppId: targetAppModel.id,
                    status: enabled
                }, function (res) {
                    if (!_this.$request.isRequestSuccess(res)) {
                        _this.$Message.warning('修改失败，请稍后重试！');
                        return
                    }
                    _this.$Message.info('状态修改成功');
                    targetAppModel.enabled = enabled
                })
            },
            handleUploadDialogClosed() {
                this.$data.modal.show = false;
                const data = this.$data;
                this.getList(data.currentPage)
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
                this.$request.targetApp.getList({
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
            if (this.$route.params.page) {
                this.$data.currentPage = this.$route.params.page
            }
            this.getList(this.$data.currentPage)
        },
        data() {
            return {
                currentPage: 1,
                total: 0,
                pageSize: 10,
                loading: false,
                tableData: [],
                modal: {
                    show: false
                },
                dataColumns: [
                    {title: 'appPackage', key: 'appPackage'},
                    {title: 'version', key: 'version'},
                    {title: 'versionCode', key: 'versionCode'},
                    {title: 'downloadUrl', key: 'downloadUrl'},
                    {title: 'enabled', key: 'enabled'},
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
                                            this.setTargetAppStatus(params.row, !params.row.enabled);
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
                                                name: this.$store.state.targetAppDetail,
                                                params: params.row
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
<style scoped>
    h1, h2 {
        font-weight: normal;
    }
</style>
