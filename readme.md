

### takahom 油管视频下载工具 youtube video downloader

takahom，是简易版的油管视频下载管理工具，其实际的加载过程是调用强大的 yt-dlp 开源项目等完成的。通过编辑对应的文本文件，可以随时增加或者修改需要下载的视频链接. 

takahom 通常作为后台程序保持长期运行。takahom在后台运行，随时检查文本文件的变化，如果发现新的资源链接，将自动完成视频下载。

takahom 名称的意思是 take-all-home 。开发这个软件的目的，是方便将油管视频批量下载到本地磁盘之后，带回家里离线观看。据说，该蓝色星球上的灵长类，还有至少20%无法与油管服务器正常连接，其外貌特征是黄皮肤黑眼睛。


### 特性列表

- 最小化配置，开箱即用
- 支持下载普通视频，播放列表，短视频
- 可以控制下载视频的分辨率
- 后台运行和无人值守自动下载
- 避免重复下载
- 分时间段的最大网速设置
- 对文件名称中的中文自动的简繁体转换，便于根据文件名检索
- 详细完整的目录文件结构，便于存储，后续处理和分析


### 快速开始


#### 运行环境要求

    ubuntu20+   （仅测试该发行版。其他linux发行版应该也可）
    或者
    windows wsl （仅测试ubuntu. wsl1或者wsl2均可）



#### 安装依赖的开源工具软件

安装方法以ubuntu系统为例。其他linux发行版请自行调整。


安装 python3.10+

    sudo apt install python3.10

    #安装成功后 检查pip 确保能正常使用
    python3.10 --version
    python3.10 -m pip --version


安装 wget git p7zip ffmpeg yt-dlp 等开源工具

    sudo apt install wget p7zip ffmpeg git
    sudo apt install yt-dlp 

    #安装后 检查依赖软件在执行路径中 确保能正常使用
    wget --version
    git --version
    7za --help
    ffmpeg --help
    yt-dlp --version



#### 从网站下载项目和安装 takahom

    #直接下载项目源码
    git clone https://github.com/dikinova/takahom

    #然后使用pip安装python依赖库
    cd ./takahom
    python3.10 -m pip install -r requirements.txt

#### 参数配置文件 env.conf

修改配置文件 ./env.conf 完成参数配置 

工作目录参数 work_dir 必须要用户自行修改。其他配置内容是可选的，可以暂时用缺省值。





```env.conf

#该目录必须已经存在，用户需要对该目录有全部读写权限。初次使用时请创建空目录。
#软件的工作目录。 work_dir目录需要提前创建完成。需要对该目录有全部权限。
#下载的视频会保存在 work_dir/sdownload 目录中.
work_dir=/mnt/work/dir

#连接 youtube等网站的网络代理。如果需要代理 请删除行首#字符取消注释。
#network_proxy=socks5://192.168.0.34:7890

```

#### 启动软件


    #在takahom目录下执行如下命令启动
    #cd ../takahom

    PYTHONPATH=$PYTHONPATH:./src python3.10 -m takahom.server run

    

takahom下载的视频文件，保存在 {work_dir}/sdownload目录中。




### 详细说明


-   所有配置文件和文本文件都是utf-8编码


#### 如何下载单个视频

视频配置文件，在{work_dir}/sinput目录下，文件名匹配 **ytb_*_0720.url.txt** 的形式。视频配置文件可以用多个。其中，'720'是希望下载的视频分辨率的数值，这个分辨率数值r要求: 240 <= r <= 2500


例如，需要以720p分辨率下载视频 https://www.youtube.com/watch?v=at71iHV8QAQ

步骤如下

- 可以新建文件。也可以在{work_dir}/sinput 目录中已有的文件中编辑。
- 如果需要新建文件，在 {work_dir}/sinput 目录下创建文件，命名类似于 ytb_202402_0720.url.txt 。文件名称的“0720”表示文件中的所有视频下载的分辨率是720p。然后用编辑器打开该文件，将url拷贝到文件中即可
- 短视频的url也是同样操作


    ```
    #在 ytb_202402_0720.url.txt 文件中添加
    https://www.youtube.com/watch?v=at71iHV8QAQ

    ```







#### 如何下载播放列表

例如，需要以480p分辨率下载播放列表中的全部视频
https://www.youtube.com/watch?v=XlnmN4BfCxw&list=PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MBo

基本步骤与 下载单个视频 过程大致是一样的。其中有一些细节存在差异，说明如下：

- 如果要下载播放列表，那么url中的参数v和参数list都是必须存在的。您可以在油管网页上，点击播放列表界面上的某一个视频，如此就可以在浏览器地址栏获得这样的url

- 在下载播放列表中视频的时候，最多允许下载的视频数量，软件内用参数进行了限制。这样设计，是为了避免播放列表过长，造成下载时间太漫长而难以结束。缺省情况的上限设置是100个视频。有些播放列表的视频数可能超过这个数量，此时如果仍然需要完全下载该列表，可以通过在url尾部附加参数 '\_maxitems_=200' 这样的方式，将该列表中的下载上限数量修改为200个视频。该参数的具体数值可以根据需要设置。


    ```
    #在 ytb_202402_0480.url.txt 文件中添加
    #播放列表的url必须包括list参数和v参数（下同，不再重复）    
    #播放列表的url下载时，缺省限制为最多下载100个视频
    https://www.youtube.com/watch?v=XlnmN4BfCxw&list=PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MBo

    #因为url附加了 _maxitems_=200 的参数 所以该列表最多可下载200个视频
    https://www.youtube.com/watch?v=XlnmN4BfCxw&list=PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MBo&_maxitems_=200
        
    ```


#### 如何防止重复下载

takahom下载的视频存储在 {work_dir}/sdownload目录下。 存储在该目录下的视频不会重复下载。如果需要排除其他的视频url，那么需要编辑排除文件。

排除文件，是指存放在{work_dir}/sinput目录下，文件名称匹配 **ytb_*.exd.txt** 的文本文件。为方便管理，排除文件可以有多个。

通过将url或者文件名称等信息添加到排除文件中，可以让下载程序跳过对应视频资源的下载。


采用如下任何一种方法，都可以达到排除特定视频资源的目的：



-   在排除文件中，写入视频或者播放列表对应的url


    ```
    #比如视频的url
    https://www.youtube.com/watch?v=Ch6Ae9DT6Ko
    
    #比如播放列表的url
    https://www.youtube.com/watch?v=XlnmN4BfCxw&list=PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MBo

    ```


-   在排除文件中，写入视频或者播放列表的编号

    ```
    #比如 视频编号
    Ch6Ae9DT6Ko

    #比如 播放列表的编号
    PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MBo

    ```


-   在排除文件中，写入目录或者文件名称。从takahom已经下载的数据目录中获取目录和文件名称列表的内容，写入到排除文件即可

    ```
    #假设用户保存下载数据的目录是 /work/dir/backup
    cd /work/dir/backup
    find . > tmp.txt

    #此时tmp.txt文件中将包含所有已经下载的目录和文件的名称信息。
    #然后将tmp.txt文件内容拷贝到排除文件中即可
    #cp tmp.txt /work/dir/sinput/ytb_202312.exd.txt 

    ```



-   在env.conf文件中配置 scan_dirs 参数。 如此，将自动的扫描和识别对应目录下已经下载的视频资源，防止重复下载。当然，需要目录和文件的名称保持来自takahom下载和生成的名称，否则是无法从名称中正确提取视频编号的。

    ```
    # scan_dirs 可以配置多个目录
    scan_dirs=/a/b/c/ytb_backup_1,/a/b/c/ytb_backup_2

    ```



#### 如何设置分时段的网络限速


在 env.conf 文件中配置 rate_limits 参数

```
# 配置网速上限 单位 bytes/s
# 可以用,符号分割成多个区段，每个区段:符号左边是时间段，右边是网速限值。 左边的区段优先级更高
# 下面的配置，表示0-8点和22,23点的网速上限为5MB/s 其他所有时间段为300KB/s 
# 数字中的下划线是方便阅读，可以省略
rate_limits=0-8:5000_000,22-23:5000_000,*:300_000

```

#### 如何自动进行文件名称的简体繁体的转换


我们下载的视频，可能来源于不同的中文变体，比如大陆简体和台湾繁体的文字就有差异。 多种中文变体的存在，会导致我们文件搜索的时候很不方便。比如，在fsearch或者Everything中，输入简体的'民国'，就无法搜索到名称包含'民國'的文件。

一个简单的解决办法，就是自动在保存文件的时候将文件名称中的中文进行简体或繁体的转换。在配置文件中进行配置即可。


```
#设置是否自动进行文件名的中文简繁体转换。 0=不转换 1=转换为zh-cn 2=转换为zh-tw 3=转换为zh-hk
chinese_cvt=1
```

### 问题与缺陷


存在少量重复下载的情况。 例如，某个视频A昨天已经下载了，今天添加了一个播放列表B，该列表中包含了视频A。那么，在下载播放列表B的时候，还会重复下载视频A。

播放列表下载之后，不会重复下载。因此，导致的一个问题是，如果下载之后，该播放列表的作者在列表中进行变动，例如增加视频，或者删除调整了某些视频，那么，takahom不会发现或跟踪这种变更。

同理，视频下载之后，也不会重复下载。如果在下载之后，油管作者对该视频进行了变更，那么，takahom不会发现或跟踪这种变更。






### 其他


#### 命令行参数说明


未完成


#### 配置文件说明

未完成

<!---





-->











