from __future__ import annotations

import re

from .server_config import DownOrderBy
from .server_imports import *
from takahom.common.down_request import DownRequest
from takahom.common.entity import YtbId, YtbItem
from takahom.common.down_result import DownResult
from takahom.common.common_etc import DkFile2
from takahom.common.ytb_util import YtbUtil, ln_filter_nor_comments_nor_empty


def ytb_dl_run(req: DownRequest) -> DownResult | None:
    return ytb_dl_v100(req=req)



def ytb_scan_output_ytbids_scan_dirs(
        scan_dirs: List[DkFile], output_dirs: List[DkFile]
) -> Iterator[YtbId]:
    """
    深度扫描所有目录
    深度扫描所有文件

    """

    dkfs = (dkf.basename
            for dkdir in (scan_dirs + output_dirs)
            for dkf in DkFile2.oswalk_simple_a(dkdir))

    ids = YtbUtil.parse_ytbid_from_lines(dkfs)
    return ids


def ytb_scan_ytbids_excludes_file(input_dir: DkFile) -> Iterator[YtbId]:
    """

    """
    # ytb_*.exd.txt

    dkfs = (dkf for dkf in DkFile2.oswalk_simple_a(input_dir, only_file=True)
            if re.fullmatch(ytb_reg_exd_files, dkf.basename))

    for dkf in dkfs:
        txt = dkf.path.read_text("utf-8")
        codesa = YtbUtil.parse_ytbid_from_lines(txt.splitlines())
        for id in codesa:
            yield id


def ytb_dl_v100(req: DownRequest) -> DownResult | None:
    """


    偶尔存在 极低概率存在 子进程僵化的现象。没有任何反应 下载进程等待10个小时 没有任何下载 也不退出

    本应用中的cmd运行中的 stdout信息被捕获 在控制台或者日志中是不能实时查看的
        有时候运行cmd之后 目录内没有新的数据生成 进程也不返回 这时候应该是cmd出现问题了。
        此时的一个调试方法是 将cmd从日志中拷贝出来，将程序退出，然后单独运行该cmd 看out信息 可以了解具体的过程

        多线程的启动子进程

        while True:
            if 目录内所有普通文件的sum_filesize 超过 N=120s 没有任何变化:
                kill process
                sleep 10s
                确认线程正常退出
                break
            else:
                sleep 30s


    """
    # 说明：
    #     错误的url 必然返回1 而且有一定的原因说明
    #     网络中断 也能返回

    FA = "bestvideo+bestaudio/best"
    FB = "bestvideo[height<=?1080]+bestaudio/best"
    FC = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    FD = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

    # 目前的FH的这种LS的condition 可以保证下载的文件不会太大 但是 也可能因为size的限制而下载较低分辨率的文件
    maxsize = ytb_cfg_maxsize_str
    LS = f"[filesize<={maxsize}]"
    FH = f"bestvideo*[ext=mp4]{LS}+bestaudio[ext=m4a]{LS}/best[ext=mp4]{LS}/bestvideo*{LS}+bestaudio{LS}/best{LS}"
    # FI只下载mp4 m4a两种格式的文件 最终会合并到mp4文件
    FI = f"bestvideo*[ext=mp4]{LS}+bestaudio[ext=m4a]{LS}/best[ext=mp4]{LS}"

    req.check()

    AT.assert_(req.data_dir, "err30672 data_dir is bad")

    datadir = DkFile(req.data_dir)
    dir = datadir.pathstr  # '/path/to/mydata'
    fmt = FI
    tot = ytb_cfg_timeout  # seconds
    if True or req.rate_limit > 0:
        ratei = req.rate_limit
        AT.assert_(ratei >= 1000, "err62121 bad rate_limit")
        ratei = int(ratei / 1000)
        rate = f"{ratei}K"

    url = req.url
    proxy = ""  # 如果proxy是空字符串 将直接网络连接 --proxy ""
    proxy = req.proxy  # for example 'socks5://192.168.0.34:7890'

    AT.assert_(req.proxy is not None, "err35925")

    cmd_ytb = r"d:\yt-dlp2023.exe "
    cmd_ytb = r"yt-dlp "
    AT.assert_(
        req.cmd is not None and len(req.cmd) > 0 and req.cmd.endswith(" "), "err86555"
    )
    cmd_ytb = req.cmd

    LN = 150
    LN = 0

    LTitle = 70

    short_pre = ""
    if False and req.ytb_item.has_short():
        short_pre = "[SH]"

    OPT = f"%(title).{LTitle}B{short_pre}[%(id)s].%(ext)s"

    """
    res:720 prefers larger videos, but no larger than 720p and the smallest video if there are no videos less than 720p.
    
    """
    FMS = f"res:{req.ytb_resolution}"

    print_json = "--print-json "
    print_json = " "

    cmd_ytb += f'--ignore-config --socket-timeout {tot} --limit-rate "{rate}" --proxy "{proxy}" '

    RETRIES = 20
    cmd_ytb += f'--retries {RETRIES} '

    if LN:
        """
        似乎 LN与LTitle可能形成冲突？ 比如将 id 或者id的一部分 被trim掉 所以暂时关闭
        
        ct-2024-01-16T01-15-57_r-10001919_ok-no_ytbid-XGzUw+envy0\
            Blue Swimsuit Fashion Show 2⧸4 [AI룩북] AI ART 룩북(Stable Diffusion lookbook) #aiart #ai룩북 #ailookboo[XGzUw_e.mp4
        """
        cmd_ytb += f"--trim-filenames {LN} "

    # 这个 max-filesize 参数为何没有生效？改成M的单位试试看 似乎还是不行
    cmd_ytb += f"--no-progress --part {print_json} --max-filesize {maxsize} "
    cmd_ytb += f"--write-description --write-info-json --write-annotations  "

    # dump-single-json 这个参数什么意义 好像不能在此使用？不会下载文件？
    # cmd += f'--dump-single-json   '

    # 有些视频的comments好像极多 会导致下载出现问题 例如 https://www.youtube.com/watch?v=kYc7D9qGSAU
    # cmd += f'--write-comments  '

    cmd_ytb += f"--no-cache-dir --windows-filenames  "
    cmd_ytb += f"--write-thumbnail  "
    cmd_ytb += f"--write-all-thumbnails  "

    def parse_items_limit() -> int:
        ur = urlparse(req.ytb_item.url_original)
        qr = dict(parse_qsl(ur.query))
        KEY = YtbConf.url_key_maxitems
        r = YtbConf.playlist_maxitems_default
        if KEY in qr and qr[KEY].isnumeric():
            r = int(qr[KEY])
        r = min(max(r, 2), 500)
        return r

    items_limit = parse_items_limit()
    cmd_ytb += f"--write-playlist-metafiles --yes-playlist --playlist-items 1:{items_limit} "
    cmd_ytb += f"--playlist-random "

    """
    -o --output
    -f --format
    -S --format-sort
    
    """
    cmd_ytb += f'--output "{dir}/{OPT}" --format "{fmt}" --format-sort "{FMS}" '

    cmd_ytb += f' "{url}" '

    # if False:
    #     cmd_ytb = f'd:\\yt-dlp2023.exe --proxy "{proxy}" {url} --format bestaudio'

    req.cmd = cmd_ytb
    req.ytb_format = fmt
    start_epoch = AT.fepochSecs()
    req.start_epoch = start_epoch
    iprint_debug(f"cmd: {cmd_ytb}")

    if req.no_download:
        iprint_debug("step65173 no download")
        return None

    if True:
        # 用下划线开头 可以让文件名称顺序在最前面
        Path(join(req.data_dir, f"_r-request_{req.ytb_ytbid.to_str_with_prefix()}.json")).write_text(
            req.to_json(indent=4, ensure_ascii=False), encoding="utf-8"  # type:ignore
        )

    rc, out, err = run_simple_b(cmd_ytb, _debug=True)
    assert isinstance(out, str) and isinstance(err, str)
    end_epoch = AT.fepochSecs()

    files_path = (join(dir, f) for f in os.listdir(dir))
    files = (DkFile(f) for f in files_path)
    exts = YtbConf.media_file_exts_with_dot
    files = [
        f
        for f in files
        if any(f.basename.endswith(e) for e in exts)
        if f.filesize >= YtbConf.media_min_filesize
    ]

    if files:
        return DownResult(
            ok=True,
            rcode=0,
            err=err,
            data_dir=dir,
            url=url,
            req=req,
            stdout=out,
            stderr=err,
            start_epoch=start_epoch,
            end_epoch=end_epoch,
        )

    else:
        return DownResult(
            ok=False,
            rcode=rc,
            err=f"rc={rc} out={out} err={err}",
            data_dir=dir,
            url=url,
            req=req,
            stdout=out,
            stderr=err,
            start_epoch=start_epoch,
            end_epoch=end_epoch,
        )


"""


"""
