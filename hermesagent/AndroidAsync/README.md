# AndroidAsync
迁移自：https://github.com/koush/AndroidAsync

迁移的原因，主要是发现了bug，并且在最新的发布包中并没有发现被修复了。
目前发现的两个bug如下：
1. http请求的时候，编码内容不识别ContentType
https://github.com/koush/AndroidAsync/issues/624
2. 关于urlEncoding编码规范，可以将空格翻译为"+"，本框架似乎没有反解"+"