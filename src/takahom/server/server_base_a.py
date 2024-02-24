from __future__ import annotations

from enum import auto
from typing import Final

from takahom.common.down_request import DownRequest
from takahom.common.common_etc import limit_memory, AT2
from takahom.server.server_config import ServerConfig
from takahom.server.server_index import DLServerIndex

from takahom.server.server_ytb_util import *


class KeyEvent(Enum):
    down_begin = auto()
    down_end_good = auto()
    down_end_bad = auto()
    down_error = auto()
    down_end = auto()
    down_allok = auto()
    down_end_demo = auto()

    file_begin = auto()
    file_ok = auto()
    file_error = auto()


Source_Demo = 'demo'


class IServerBaseA(Protocol):
    # readable and writable property
    args: Any
    work_dir: DkFile
    state_index: DLServerIndex
    sconf: ServerConfig
    start_app_epoch_str: str
    port: int
    secret: str
    fkey: str
    p7z_volume: int
    p7z_level: str
    s7z_keep_secs: int
    ytb_cmd_path: str
    socks_proxy: str
    scan_dirs: List[DkFile]
    input_dir: DkFile
    output_dir: DkFile

    req_running: DownRequest | None
    downloading_url: str | None
    downloading_begin: str | None
    scache_size: int

    rate_limits: List[int]
    last_new_urls: int
    downloaded_bytes: int

    req_queue: Queue[DownRequest]
    req_queue_list: List[YtbItem]
    req_size_max: int

    stt_cnts: Dict[str, int]

    def fetch_req(self) -> DownRequest:
        req = self.req_queue.get()
        self.req_queue_list.remove(req.ytb_item)
        return req

    def put_req(self, req: DownRequest) -> None:
        AT.assert_(req.check(), "err59453")
        self.req_queue.put(req)
        self.req_queue_list.append(req.ytb_item)

    def subdir(self, d: str) -> DkFile:
        r = DkFile(join(self.work_dir.path, d))
        AT.assert_(r.is_dir() and r.exists(), f"err57249 {r.path}")
        return r

    def get_index_file(self) -> DkFile:
        idxfile = DkFile(join(self.work_dir.pathstr, "index.json"))
        return idxfile

    def read_index_file(self) -> DLServerIndex | None:
        sfile = self.get_index_file()
        if sfile.exists():
            s = sfile.path.read_text(encoding="utf-8")
            r: DLServerIndex = DLServerIndex.from_json(s)  # type:ignore
            return r
        else:
            return None

    @property
    def chinese_cvt_enum(self) -> ChineseCvt:
        return ChineseCvt(self.sconf.chinese_cvt)

    def f_handle_test(self, req: DownRequest) -> DownResult:
        # 在目录下写入随机文件即可
        start_epoch = AT.fepochSecs()
        resid = random.randint(10 ** 4, 10 ** 4 * 2)
        demostr = "".join(str(i) for i in range(resid))

        demostr = req.to_json()  # type:ignore
        Path(join(req.data_dir, "TEST.json")).write_text(demostr)
        time.sleep(5)
        end_epoch = AT.fepochSecs()
        dr = DownResult(
            req=req,
            ok=True,
            data_dir=req.data_dir,
            url=req.url,
            res_id=str(resid),
            infos=[],
            start_epoch=start_epoch,
            end_epoch=end_epoch,
        )

        dr.after_run()
        return dr

    def f_handle_simple_curl_100(self, req: DownRequest) -> DownResult:
        start_epoch = AT.fepochSecs()
        resid = random.randint(10 ** 4, 10 ** 4 * 2)
        demostr = "".join(str(i) for i in range(resid))

        url = req.url

        # AT.assert_(url.split('?'))

        u2 = url.split("?")[0]

        fname = u2.split("/")[-1]

        cmd = f"curl '{url}' --output '{req.data_dir}/{fname}' "
        rc, out, err = run_simple_b(cmd)

        assert isinstance(err, str)

        end_epoch = AT.fepochSecs()

        dr = DownResult(
            req=req,
            ok=(rc == 0),
            data_dir=req.data_dir,
            url=req.url,
            res_id=str(resid),
            infos=[],
            err=err,
            start_epoch=start_epoch,
            end_epoch=end_epoch,
        )

        dr.after_run()

        dr.infos.append(f"cmd: {cmd}")
        return dr

    def f_dev_100(self) -> None:
        dir_scache = self.subdir("scache")

        req = DownRequest(
            url=CommonUtil.test_random_github_url(),
            data_dir=dir_scache.pathstr,
            uuid=AT2.gen_uuid_str(),
        )
        req.domain = "github"
        req.resource_key = str(hash(req.url))

        req.init()
        res = self.f_handle_simple_curl_100(req)
        AT.assert_(
            res.files_cnt > 0 and res.files_size > 0,
            f"err57447 {res.to_json()}",  # type:ignore
        )

    def log_cnt(self, key: Any, v: int = 1, level: LLevel = LLevel.Debug) -> None:

        match key:
            case KeyEvent():
                k = key.name
            case _:
                k = str(key)

        self.stt_cnts[k] = self.stt_cnts.get(k, 0) + v
        iprint(f'log cnt {k} {v}', level)

    def write_index_file(self) -> None:
        sstate = self.state_index
        s = sstate.to_json(indent=4, ensure_ascii=False)  # type:ignore
        self.get_index_file().path.write_text(s, "utf-8")
        return

    def handle_request_pre_init(self, req: DownRequest) -> None:
        self.req_running = req
        self.downloading_url = req.url
        self.downloading_begin = AT.sdf_logger_format_datetime()

    def handle_request_post(self, req: DownRequest) -> None:
        self.req_running = None
        self.downloading_url = None
        self.downloading_begin = None

    def handle_request(self, req: DownRequest) -> DownResult:

        self.log_cnt(KeyEvent.down_begin)
        iprint_info(f'download url begin: {req.url}')

        r: DownResult | None = None
        try:
            dir_scache = self.subdir("scache")
            # self.handle_request_pre_init(req)

            if True:
                req.data_dir = dir_scache.pathstr
                req.start_epoch = AT.fepochMillis()
                req.rate_limit = CommonUtil.rate_limit(self.rate_limits)
                CommonUtil.clear_dir(dir_scache)

            AT.assert_(req.url and req.data_dir, "err40069")
            url = req.url

            if False:
                AT.never()
            elif req.url.startswith("http://test/"):
                return self.f_handle_test(req)
            elif (url.startswith("https://github.com/")
                  or url.startswith("https://totalcommander.ch/")
                  or f_url_in_special_100(url)
                  or False):
                return self.f_handle_simple_curl_100(req)
            elif YtbUtil.parse_ytbitem_from_url(url):
                r = ytb_dl_run(req)
                AT.assert_(r, "err35277")
                assert r

                AT.assert_(r.start_epoch > 0 and r.end_epoch > 0, "err19241")
                r.after_run()

                return r

            else:
                AT.never()
                assert False
        except Exception as e:
            self.log_cnt(KeyEvent.down_error, level=LLevel.Warn)
            raise e
        else:
            pass

        finally:
            self.log_cnt(KeyEvent.down_end)
            iprint_info(f'download url end: {req.url}')

            if r and r.req.source == Source_Demo:
                self.log_cnt(KeyEvent.down_end_demo)
            if r and r.ok:
                self.log_cnt(KeyEvent.down_end_good)
            elif r and not r.ok:
                self.log_cnt(KeyEvent.down_end_bad)
            else:
                pass


def f_url_in_special_100(url: str) -> bool:
    return any(
        url.startswith(u) for u in CommonUtil.special_check_urls_special_100
    )


def dec_my_log_error_builder(message: str, reraise: bool = False) -> Any:
    # 虽然已经全部函数参数都赋值 但类型仍然是 dec_builder 所以必须eval之后才能返回
    dec_log_on_err_builder = functools.partial(
        log_on_error,
        log_level=logging.ERROR,
        message=message,
        logger=AT.logger,
        on_exceptions=(IOError, Exception),
        reraise=reraise,
    )
    return dec_log_on_err_builder()


def copy_ytbtxts_files_to_dest_input_dir(src: DkFile, dest: DkFile) -> None:
    """
    如果目标目录中没有任何文件
    则将源目录中存在 ytb_*.txt 文件 全部拷贝过去

    """

    copy = dest.exists() and dest.is_dir() and not list(DkFile2.oswalk_simple_a(dest)) \
           and src.exists() and src.is_dir()
    if not copy:
        return

    for dkf in DkFile2.oswalk_simple_a(src, only_file=True):
        if re.fullmatch(ytb_reg_ytb_txt_files, dkf.basename):
            shutil.copyfile(dkf.path, DkFile2.join_path(dest, dkf.basename).path)


# @dataclass_json
@define
class SystemInfo:
    uname: str
    memory: str
    ffmpeg: str
    ytdlp: str
    p7zip: str
    wget: str
    work_du: str


def build_system_info(work_dir: DkFile) -> SystemInfo:
    """

    """
    AT.assert_(AT.is_linux, 'err32791 only support linux')

    _, uname, _ = run_simple_b('uname -a')
    _, memory, _ = run_simple_b('free -mh |head -n 5')
    _, ffmpeg, err = run_simple_b('ffmpeg --version 2>&1 |head -n 5')
    """
ffmpeg version 4.2.7-0ubuntu0.1 Copyright (c) 2000-2022 the FFmpeg developers
  built with gcc 9 (Ubuntu 9.4.0-1ubuntu1~20.04.1)    
    """
    AT.assert_('FFmpeg' in ffmpeg and 'Copyright' in ffmpeg,
               f'err87868 ffmpeg cannot run. {ffmpeg} {err}')

    # yt-dlp --version
    _, ytdlp, err = run_simple_b(f'yt-dlp --version')
    # return: 2023.12.30
    AT.assert_(len(ytdlp) > 4, f'err15694 yt-dlp cannot run. {err}')

    _, p7zip, err = run_simple_b('7za -h|head -n 5')
    """

7-Zip (a) [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=C.UTF-8,Utf16=on,HugeFiles=on,64 bits,12 CPUs Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz (A0652),ASM,AES-NI)

Usage: 7za <command> [<switches>...] <archive_name> [<file_names>...]

    """
    AT.assert_('Copyright' in p7zip, f'err53910 7za cannot run. need to install p7zip. {err}')

    # 也可以用 xxx -h 2>/dev/null | head -n 1 但是这样就没有版本信息
    cmd = 'wget --version | head -n 5'
    _, wget, _ = run_simple_b(cmd)
    """
GNU Wget 1.20.3 built on linux-gnu.

-cares +digest -gpgme +https +ipv6 +iri +large-file -metalink +nls
+ntlm +opie +psl +ssl/openssl
    """
    AT.assert_('Wget' in wget, f'err21171 wget cannot run')

    # 重要目录的磁盘占用
    AT.assert_(work_dir.exists() and work_dir.is_dir(), f'err40659 dir is bad {work_dir}')

    # du . -d1 -h -BG |sort -r
    cmd = f'du "{work_dir.pathstr}" -d1 -h -BG |sort -r'
    _, work_du, _ = run_simple_b(cmd)
    work_du = ' '.join(work_du.splitlines())

    info = SystemInfo(
        uname=uname.strip(),
        memory=memory.strip(),
        ffmpeg=ffmpeg.strip(),
        ytdlp=ytdlp.strip(),
        p7zip=p7zip.strip(),
        wget=wget.strip(),
        work_du=work_du.strip(),
    )

    return info


def ytb_parse_input_dir_reqs(
        server: IServerBaseA | None,
        input_dir: DkFile, socks_proxy: str, cmd_path: str
) -> List[DownRequest]:
    """
    # 返回全部文件中的所有url 有顺序问题

    """
    from .server_base_a import IServerBaseA

    dkfs = [
        dkf
        for dkf in DkFile2.oswalk_simple_a(input_dir, only_file=True)
        if CommonUtil.parse_resolution_of_input_filename(dkf)
    ]
    dkfs = sorted(dkfs, key=lambda dkf: dkf.basename)
    iprint_debug(f"find input files. {len(dkfs)} {[f.basename for f in dkfs]}")

    reqs: List[DownRequest] = []
    ytbids: Set[YtbId] = set()
    line_no = 0
    for dkf in dkfs:
        urls = CommonUtil.parse_urls_from_sinput_text(dkf.path.read_text())
        res = CommonUtil.parse_resolution_of_input_filename(dkf)
        assert res, "err98972"
        AT.assert_(240 <= res <= 2500, f"err66968 bad resolution {res}")
        for urla in urls:
            ytbitem = YtbUtil.parse_ytbitem_from_url(urla)
            if not ytbitem:
                iprint_info(f"err69431 bad url {urla} file:{dkf}")
                continue
            assert ytbitem
            req = DownRequest(url=ytbitem.get_url(), ytb_resolution=res)
            req.init()
            req.ytb_item = cast(YtbItem, ytbitem)
            req.ytb_ytbid = cast(YtbId, YtbUtil.parse_ytbid_from_url(ytbitem.get_url()))
            req.domain = ytb_domain_name
            req.resource_key = req.ytb_ytbid.to_str_with_prefix()
            req.proxy = socks_proxy
            req.cmd = cmd_path
            # req.source = f"file-{dkf.basename}"
            req.source = f"{dkf.basename}"
            req.line_no = line_no
            line_no += 1

            if req.ytb_ytbid not in ytbids:
                ytbids.add(req.ytb_ytbid)
                reqs.append(req)

    # 用tuple实现多属性的级联排序
    if server and server.sconf.download_order_by == DownOrderBy.vcode_first.value:
        reqs.sort(key=lambda x: (x.ytb_ytbid.prefix, x.line_no))
    elif server and server.sconf.download_order_by == DownOrderBy.natural.value:
        reqs.sort(key=lambda x: (x.line_no,))
    else:
        AT.never('err95878')

    return reqs
