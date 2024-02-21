


https://github.com/ytdl-org/youtube-dl

基于golang开发的下载工具
https://github.com/kkdai/youtube

A youtube-dl fork with additional features and fixes 
https://github.com/yt-dlp/yt-dlp
    yt-dlp is a youtube-dl fork based on the now inactive youtube-dlc. The main focus of this project is adding new features and patches while also keeping up to date with the original project


能否include其他文件 比如 envconf文件?

防止重复下载
    内部的扫描和判断依据?

启动时 扫描work dir获取rid信息

通过web界面简单查看所有下载的文件资料？

启动阶段的info log的设计？
    启动通过下载测试的错误码？
    列表下载的检测和错误码？

docker发布？
    有一定意义，今后再说。
    意义不大。这个主要时需要及时更新。


发布之前的注意
    修改 common_imports.py upload.sh 中的版本号


有待开发

-   启动时 在多个特定目录下创建文件是否正常？

-   获取有限内容的功能？或者，能否提前终止下载进程？
-   仅仅获取相关信息？meta info？description？之类？

-   下载失败时，探测 youtube.com是否可以连接？以此分辨，究竟是视频url的问题，还是网站的连通性的问题？



