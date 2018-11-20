<template>
    <div id="app">
        <Layout>
            <Header v-show="$store.state.navShow" style="padding: unset">
                <Menu :active-name="$store.state.navIndex"
                      mode="horizontal"
                      @on-select="handleSelect"
                      :theme="menu_theme">
                    <MenuItem :name="$store.state.home">{{ $store.state.home }}</MenuItem>
                    <MenuItem :name="$store.state.device">{{ $store.state.device }}</MenuItem>
                    <MenuItem :name="$store.state.targetApp">{{ $store.state.targetApp }}</MenuItem>
                    <MenuItem :name="$store.state.wrapper">{{ $store.state.wrapper }}</MenuItem>
                </Menu>
            </Header>
            <Content>
                <transition name="slide-fade">
                    <router-view/>
                </transition>
            </Content>
        </Layout>
    </div>
</template>

<script>

    export default {
        name: 'App',
        data() {
            return {
                menu_theme: 'light'
            }
        },
        methods: {
            handleSelect(key) {
                this.$router.push(key)
            }
        }
    }
</script>

<style lang="scss">
    #app {
        font-family: 'Avenir', Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-align: center;
        color: #2c3e50;
    }

    .slide-fade {
        // position: absolute;
        left: 0;
        right: 0;
    }

    .slide-fade-enter-active {
        transition: all 1.2s ease;
    }

    .slide-fade-leave-active {
        transition: all .1s cubic-bezier(2.0, 0.5, 0.8, 1.0);
    }

    .slide-fade-enter, .slide-fade-leave-to {
        left: 0;
        right: 0;
        transform: translateX(50px);
        opacity: 0;
    }

    .el-main {
        overflow: hidden;
    }

</style>
