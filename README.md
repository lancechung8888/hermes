# hermesadmin

#### 项目介绍
hermes项目，管理端代码。管理端包括两个后端一个前端。
* python后端：使用python+Django实现的后端模块，如果你熟悉python，可以使用这个后台部署HermesAdmin
* java后端：使用SpringBoot+MybatisPlus实现的后端模块，如果你们更加熟悉java，可以使用java后台实现HermesAdmin
* Vue前端，使用Vue实现的前端，Vue前端代码可以同时对接Python后端和Java后端，两个后端语言实现的API接口保持一致，且在未来我也会同步兼容两套语言

请注意：由于java，python，js使用不同的编译器，他们在构建的时候都会产生各自的临时文件。在跨ide的时候，可能一个IDE不识别另一个IDE的临时文件导致对不相干文件建立索引，拖慢项目构建速度。所以我使用各自各自单独的目录放置代码，他们之间在项目关联方面，没有统一的构建工具统一关联（不同语言构建工具生态也不一样）。所以前后关联需要大家自己手动实现

演示地址：[http://www.virjar.com:5598](http://www.virjar.com:5598)

#### 安装教程

1. Vue项目使用Vue-Cli3生成，使用命令Vue标准构建方式即可生成前端代码：   
  a. 安装node：``yum install nodejs``(请注意，需要安装node 8.0以上的node)    
  b. 安装淘宝npm镜像（建议步骤：）``npm install -g cnpm --registry=https://registry.npm.taobao.org``    
  c. 编译项目：``cd frontent-vue & cnpm install``    
  d. build node-sass,``npm rebuild node-sass``好像这一步没有执行的话，跑不起来    
  e. 启动开发模式：``npm run serve`` 注意这里需要配置vue.config.js,将proxy参数forward到后端服务    
  f. 当代码测试没问题之后，可以构建发布版本的前端代码：``npm run build`` 此时，将会在dist目录产生压缩好的前端代码，将他们拷贝到后端服务对应的静态目录，或者放置到你们公司对应的静态资源服务器上面即可    
2. java 后端：TODO
3. pyhton 后端：TODO

#### 合作

开源即免费，我不限制你们拿去搞事情，但是开源并不代表义务解答问题。如果你发现了有意思的bug，或者有建设性意见，我乐意参与讨论。
如果你想寻求解决方案，但是又没有能力驾驭这个项目，欢迎走商务合作通道。联系qq：819154316，或者加群：569543649。
拒绝回答常见问题！！！


#### 捐赠
如果你觉得作者辛苦了，可以的话请我喝杯咖啡
![alipay](img/reward.jpg)
