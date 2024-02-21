from __future__ import annotations

from takahom.server.server_base_a import ytb_parse_input_dir_reqs
from takahom.server.server_ytb_util import *


class _DemoAppCtx(object):
    def __init__(self, args: Any) -> None:
        self.rate_limits: List[int] = []
        self.socks_proxy: str = ""  # ='socks5://192.168.0.34:7890'
        self.cmd_path: str = ""
        self.work_dir = args.workdir
        self.scan_dirs: List[DkFile] = []
        self.input_dir = DkFile(join(self.work_dir, "input"))
        self.output_dir = DkFile(join(self.work_dir, "output"))
        self.tmp_dir = DkFile(join(self.work_dir, "tmp"))

        assert self.input_dir.exists(), self.input_dir.pathstr


appCtx: _DemoAppCtx | None = None


def f_download_simple_a(args: Any) -> None:
    """

    循环扫描目录

    ytb_2500.txt
    ytb_720.txt
    ytb_360.txt

    获取1个url 然后下载

    子目录名  r-100_ct-202312T123456_ytbid-312313_c-{ok|err}_url-{url简化的info}


    """
    assert appCtx, "err78385"
    scnt = 0
    while True:
        # 可以用文件让循环主动break
        if CommonUtil.dir_has_filename(appCtx.input_dir, "exit.cmd"):
            iprint_warn("step17239 file exit.cmd found. exit main loop.")
            break

        scnt += 1
        if scnt != 1:
            t = 30 + random.uniform(0, 30)
            iprint_debug(f"sleeping {t}s")
            time.sleep(t)

        # 排除 excludecodes， output_dir中的重复，选择一个url
        exids = set(ytb_scan_ytbids_excludes_file(appCtx.input_dir)) | set(
            ytb_scan_output_ytbids_scan_dirs(
                scan_dirs=appCtx.scan_dirs, output_dirs=[appCtx.output_dir]
            )
        )
        reqs = [
            req
            for req in ytb_parse_input_dir_reqs(
                server=None,
                input_dir=appCtx.input_dir,
                socks_proxy=appCtx.socks_proxy,
                # write_dir=appCtx.tmp_dir,
                cmd_path=appCtx.cmd_path,
            )
            if req.ytb_ytbid not in exids
        ]

        if not reqs:
            iprint_debug(f"no new url {scnt}")
            continue

        iprint_info(f"find new urls {len(reqs)}")
        req: DownRequest = reqs[0]

        iprint_info(f"start download: {req.url}")
        req.data_dir = appCtx.tmp_dir.pathstr
        req.start_epoch = AT.fepochSecs()
        req.rate_limit = CommonUtil.rate_limit(appCtx.rate_limits)

        CommonUtil.clear_dir(appCtx.tmp_dir)
        if not DkFile(req.data_dir).exists():
            os.mkdir(req.data_dir)
        res: DownResult | None = ytb_dl_v100(req)
        assert res
        AT.assert_(res.start_epoch > 0 and res.end_epoch > 0, "err19241")
        res.after_run()

        iprint_info(f"end download: {req.url} network: {int(res.netv / 1000)}KB/s")

        res.write_json_file()

        # 将目录 mv 到output 的子目录中 不会mv的写法 只好copy
        res.rid = 100
        rdirname = res.cal_sdownload_dir_name()
        shutil.copytree(req.data_dir, join(appCtx.output_dir.pathstr, rdirname))

        if res and res.ok:
            # 生成一个完整的7z文件 可以加上密码 定义在 DLCommon 类函数中 todo
            pass

        else:
            # 记录错误日志
            pass

        iprint_info(f"end job. url:{req.url} ok:{res.ok}")


def f_excludecodes20231228() -> str:
    # AT.unimplemented() ytbid-xxxxx
    return """



""".strip()


def _f_learn_dlp_100() -> None:
    import json
    import yt_dlp  # type:ignore

    URL = "https://www.youtube.com/watch?v=BaW_jenozKc"

    # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
    ydl_opts: Dict[Any, Any] = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)

        # ℹ️ ydl.sanitize_info makes the info json-serializable
        print(json.dumps(ydl.sanitize_info(info)))

    pass


if __name__ == "__main__":
    import argparse  # 1

    parser = argparse.ArgumentParser()  # 2

    parser.add_argument("-p", "--profile", type=str, default="dev", help="profile")

    parser.add_argument("--location", type=str, default="test", help="location")

    parser.add_argument("--workdir", type=str, default=r"", help="工作目录")

    # parser.add_argument('--datadir',
    #                     type=str, default=r'q:\webdav_share\hesai_data\raw', help='数据目录')

    # 最多包括目录个数
    parser.add_argument("--maxcnt", type=int, default=50, help="dircnt")

    # 是否运行测试工况。可以用字符串详细描述 例如 1,2,3,4 等等
    parser.add_argument("--testcase", type=str, default="", help="是否运行测试工况")

    parser.add_argument("--reportverbose", type=int, default=30, help="报告的详细程度")

    args = parser.parse_args()  # 4

    if AT.is_windows:
        args.workdir = r"d:\tmp_dl"
    else:
        args.workdir = r"/mnt/ss/_DISC_S_/ytb_download"

    appCtx = _DemoAppCtx(args)

    appCtx.rate_limits = [1000 * 1000 * 3] * 8 + [1000 * 300] * 16

    if AT.is_windows:
        appCtx.rate_limits = [1000 * 300] * 24
    else:
        pass

    CommonUtil.rate_limit(appCtx.rate_limits)

    if AT.is_windows:
        appCtx.cmd_path = r"f:\DIKI\DIKIDEV\ZTools\yt-dlp2023.exe "
    else:
        appCtx.cmd_path = r"yt-dlp "

        appCtx.scan_dirs.append(DkFile("/mnt/ss/_DISC_S_/ytb_scan"))

    appCtx.socks_proxy = "socks5://192.168.0.34:7890"

    f_download_simple_a(args)


def _urlsa() -> str:
    return """


#girl show
https://www.youtube.com/watch?v=nFmmumBB1_4

#古筝 hotel california
https://www.youtube.com/watch?v=gf6v59c5yuY

https://www.youtube.com/watch?v=hgVq-DpCtao
https://www.youtube.com/watch?v=8syimRWomrs
https://www.youtube.com/watch?v=AMakl19CckA
https://www.youtube.com/watch?v=ynQypJe8k2g
https://www.youtube.com/watch?v=t1nlFJV5csM
https://www.youtube.com/watch?v=IOiedWxP5Zw
https://www.youtube.com/watch?v=n4WNxRbYwB4
https://www.youtube.com/watch?v=jqirCnIIKC4
https://www.youtube.com/watch?v=tSGD1AYrZg4&t=42s
https://www.youtube.com/watch?v=SKAkuZpMCPQ
https://www.youtube.com/watch?v=gf6v59c5yuY&list=RDgf6v59c5yuY&start_radio=1
https://www.youtube.com/watch?v=ighkK6pKJng


""".strip()


"""


"""
