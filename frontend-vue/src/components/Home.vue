<template>
    <div class="hello">
        <h1 class="home-title">{{ $store.state.projectName }}</h1>
        <Row type="flex" class="row-bg" justify="center" align="middle">
            <Col :span="6">
                <div class="home-list">
                    <Row :gutter="10">
                        <Col :span="12">
                            <div class="home-list-item home-list-item1">
                                <a target="_blank"
                                   href="https://gitee.com/virjar/hermes">Hermes主页</a>
                            </div>
                        </Col>
                        <Col :span="12">
                            <div v-on:click="routerPush($store.state.devicePath)"
                                 class="home-list-item home-list-item2">{{ $store.state.device }}
                            </div>
                        </Col>
                    </Row>
                    <Row :gutter="10">
                        <Col :span="12">
                            <div v-on:click="routerPush($store.state.targetAppPath)"
                                 class="home-list-item home-list-item3">{{ $store.state.targetApp }}
                            </div>
                        </Col>
                        <Col :span="12">
                            <div v-on:click="routerPush($store.state.wrapperPath)"
                                 class="home-list-item home-list-item4">{{ $store.state.wrapper }}
                            </div>
                        </Col>
                    </Row>
                </div>
            </Col>
        </Row>
    </div>
</template>

<script>
    export default {
        name: 'Home',
        data() {
            return {}
        },
        methods: {
            routerPush(message) {
                this.$router.push(message)
            }
        }
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
    .home-title {
        margin-top: 100px;
        font-size: 50px;
    }

    .home-list {
        height: 450px;
        margin-top: 50px;
        color: #fff;
        font-size: 30px;
        font-weight: 700;
        &-item {
            width: 100%;
            height: 225px;
            float: left;
            line-height: 225px;
            cursor: pointer;
            &1 {
                background-color: aqua;
            }
            &2 {
                background-color: burlywood;
            }
            &3 {
                background-color: chartreuse;
            }
            &4 {
                background-color: crimson;
            }
        }
        .ivu-col {
            padding: 5px;
        }
        .mul-line-center {
            display: inline-block;
            vertical-align: middle;
            line-height: 30px;
        }
    }
</style>
