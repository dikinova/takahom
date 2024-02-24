from __future__ import annotations

from takahom.common.down_request import DownRequest
from takahom.common.common_etc import limit_memory, AT2
from takahom.server.server_base_c_download import IServerBaseC
from takahom.server.server_config import ServerConfig, build_config_from_args
from takahom.server.server_index import DLServerIndex

from takahom.server.server_ytb_util import *

from takahom.server.server_base_a import IServerBaseA, dec_my_log_error_builder, Source_Demo, build_system_info, \
    ytb_parse_input_dir_reqs
from attr import define, field as afield, asdict


def check_ydltest_url(server: IServerBaseA) -> None:
    """
    重要目录 sinput目录等 完成扫描 和检查
    检查scan目录都是存在的
    测试ytb url可以正常下载 ,info log begin end error

    """
    self = server

    if True:
        url = ytb_url_demo_ydltest
        res = 720
        req = build_demo_request(server, url, res)
        iprint_info(f'try to test and download {url} begin')
        res = server.handle_request(req)
        if not res.ok:
            AT.fail(f'err7611 test and download {url} failure')
        iprint_info(f'test and download {url} ok')
        # clear dir
        dir_scache = self.subdir('scache')
        CommonUtil.clear_dir(dir_scache)

    pass


def build_demo_request(appctx: IServerBaseA, url: str, res: int) -> DownRequest:
    ytbitem = YtbUtil.parse_ytbitem_from_url(url)
    assert ytbitem

    req = DownRequest(url=ytbitem.get_url(), ytb_resolution=res)
    req.init()
    req.ytb_item = cast(YtbItem, ytbitem)
    req.ytb_ytbid = cast(YtbId, YtbUtil.parse_ytbid_from_url(url))
    req.domain = ytb_domain_name
    req.resource_key = req.ytb_ytbid.to_str_with_prefix()
    req.proxy = appctx.socks_proxy
    req.cmd = appctx.ytb_cmd_path
    req.source = Source_Demo
    return req


@dec_my_log_error_builder(message="Error on tgt_main: {e!r}")  # type:ignore
def tgt_main_download_queue(self: IServerBaseC) -> None:
    for cnt in ite.count(0):

        while CommonUtil.dir_has_filename(self.input_dir, "exit.cmd"):
            iprint_info("step55341 file exit.cmd found. sleep.")
            time.sleep(60)

        # # 可以用文件让循环主动break 不能exit只好改成continue 这样可以循环打印日志
        # if False and CommonUtil.dir_has_filename(self.input_dir, "exit.cmd"):
        #     # do nothing
        #     iprint_warn("step55341 file exit.cmd found. exit application.")
        #     # 为什么 sys.exit 不能生效?
        #     # sys.exit()
        #     pass
        # else:

        try:
            iprint_debug(f"main read queue begin")
            self.thread_main_download(cnt=cnt)
            iprint_debug(f"main read queue end")
        except Exception as e:
            iprint_error(e)

        sp = 20 if AT2.is_profile_prod() else 3
        time.sleep(sp)


@dec_my_log_error_builder(message="Error on tgt_remove_toomuch_data: {e!r}")  # type:ignore
def tgt_remove_toomuch_data(self: IServerBaseC) -> None:
    SECS = self.s7z_keep_secs
    if not SECS:
        return
    AT.assert_(SECS > 60 * 10, 'err19969')

    for _ in range(1):
        RX = 0
        for dkf in DkFile2.oswalk_simple_a(self.subdir('s7z'), only_file=True):
            rv = int(CommonUtil.parse_filename_dict(dkf).get('r', '0'))
            RX = max(RX, rv)

        if RX:
            from os.path import getmtime
            cnt = 0
            for sdir in ['s7z', 'sresp']:
                for dkf in DkFile2.oswalk_simple_a(self.subdir(sdir), only_file=True):
                    rv = int(CommonUtil.parse_filename_dict(dkf).get('r', '0'))
                    now = AT.fepochSecs()
                    RN = 3
                    if rv and rv + RN < RX and dkf.is_file() \
                            and now - getmtime(dkf.path) > SECS:
                        os.remove(dkf.path)
                        iprint_debug(f'step28568 删除过多数据 {dkf}')
                        cnt += 1
            if cnt:
                iprint_info(f'step45645 remove useless data {cnt}')


@dec_my_log_error_builder(message="Error on tgt_email_log: {e!r}")  # type:ignore
def tgt_email_log(self: IServerBaseA, write_email: bool = True) -> str:
    infodc = tgt_job_log_5mins(self, _print=False)
    infodc['sysinfo'] = asdict(build_system_info(self.work_dir))
    infodc['conf'] = build_config_from_args(self.args).copy_without_secret()

    json_string = json.dumps(infodc, ensure_ascii=False, indent=4)

    if write_email:
        setc_dir = self.subdir("setc")
        fname = f"email_{AT.sdf_logger_format_datetime(noColon=True)}.json"
        Path(join(setc_dir.pathstr, fname)).write_text(json_string)
        iprint_info(f'write email log file {fname}')

    return json_string


_demo_v_state: List[str] = ['ydltest', 'list', 'short']


def f_try_to_add_demo(self: IServerBaseC) -> None:
    v_state = _demo_v_state
    iprint_debug(f"demo req {v_state}")
    if not v_state:
        return

    if not self.req_queue.empty():
        iprint_debug("queue is not empty. wait awhile.")
        return

    assert self.ytb_cmd_path

    id = v_state[-1]
    if id == 'ydltest':
        url = ytb_url_demo_ydltest
        res = 720
        req = build_demo_request(self, url, res)

        reqs = [req]

    elif id == 'list':
        url = "https://www.youtube.com/watch?v=csebxC-oKn4&list=PLtpBIq5yTxAUrB1-jkE9uNQludEzbhLmL"
        url = "https://www.youtube.com/watch?list=PLtpBIq5yTxAUrB1-jkE9uNQludEzbhLmL"
        # 没有v值的url 是不能下载list的
        url_歌曲30首 = "https://www.youtube.com/watch?list=RDf-Neutoz40g"
        url_songs = "https://www.youtube.com/watch?v=f-Neutoz40g&list=RDf-Neutoz40g&_maxitems_=3"

        url = url_songs
        res = 480
        req = build_demo_request(self, url, res)
        reqs = [req]

    elif id == 'short':
        url_shorta = "https://www.youtube.com/shorts/6fC95hU3puU"

        url = url_shorta
        res = 480
        req = build_demo_request(self, url, res)
        reqs = [req]

    else:
        reqs = []

    if not reqs:
        iprint_debug(f"no new url")
    else:
        iprint_debug(f"find new urls total:{len(reqs)}")
        req = reqs[0]
        self.put_req(req)
        v_state.pop(-1)
        time.sleep(3.0)


def f_try_to_add_ytb_scan_dir(self: IServerBaseC) -> None:
    app_ctx = self
    assert self.req_size_max >= 1, 'err27326'
    # 排除 excludecodes， output_dir中的重复，选择一个url

    exitids: Set[YtbId] = set(ytb_scan_ytbids_excludes_file(app_ctx.input_dir))
    exitids.update(ytb_scan_output_ytbids_scan_dirs(
        scan_dirs=app_ctx.scan_dirs,
        output_dirs=[app_ctx.output_dir]))

    if req_run := self.req_running:
        exitids.add(req_run.ytb_ytbid)

    exitids.update(item.para_value_to_ytbid() for item in self.req_queue_list)

    assert app_ctx.ytb_cmd_path

    reqs = [
        req
        for req in ytb_parse_input_dir_reqs(
            server=self,
            input_dir=app_ctx.input_dir,
            socks_proxy=app_ctx.socks_proxy,
            cmd_path=app_ctx.ytb_cmd_path,
        )
        if req.ytb_ytbid not in exitids
    ]

    self.last_new_urls = len(reqs)

    nps = self.req_size_max - len(self.req_queue_list)
    if nps <= 0:
        iprint_debug("queue is not empty. wait awhile.")
        return

    if not reqs:
        iprint_debug(f"no new url. exitids:{len(exitids)}")
    else:
        iprint_debug(f"find new urls total:{len(reqs)} exitids:{len(exitids)}")
        nps = min(nps, len(reqs))
        for i in range(nps):
            req: DownRequest = reqs[i]
            self.put_req(req)

    time.sleep(3.0)


def thread_auto_req_job(self: IServerBaseC, scnt: int) -> None:
    """
    周期调用delay是60秒 scnt大概60秒增加一次

    """

    dir_scache = self.subdir("scache")

    def f_add_test() -> None:
        r = random.randint(1, 10 ** 5)
        req = DownRequest(
            url=f"http://test/abc?r={r}",
            data_dir=dir_scache.pathstr,
            uuid=AT2.gen_uuid_str(),
            start_epoch=AT.fepochSecs(),
        )
        req.init()

        self.req_queue.put(req)

    def f_add_local(n: int) -> None:
        DownRequest(url="http://test")

        pass

    def f_add_curl() -> None:
        r = random.randint(1, 10 ** 5)
        req = DownRequest(
            url=CommonUtil.test_random_github_url(),
            data_dir=dir_scache.pathstr,
            uuid=AT2.gen_uuid_str(),
            start_epoch=AT.fepochSecs(),
        )
        req.init()

        self.req_queue.put(req)

    def f_add_ytb() -> None:
        r = random.randint(1, 10 ** 5)
        req = DownRequest(
            url=CommonUtil.special_check_urls_ytb[0] + f"&r={r}",
            data_dir=dir_scache.pathstr,
        )
        req.init()

        self.req_queue.put(req)

    base = 60 if AT2.is_profile_prod() else 3
    if scnt % base == 0:
        f_add_test()

    base = 60 if AT2.is_profile_prod() else 3
    if scnt % base == 0:
        f_add_curl()

    base = 60 if AT2.is_profile_prod() else 3
    if scnt % base == 0:
        f_add_ytb()


@dec_my_log_error_builder(message="Error on tgt_job_log_5mins: {e!r}")  # type:ignore
def tgt_job_log_5mins(self: IServerBaseC, _print: bool = True) -> Dict[str, Any]:
    """
    每5分钟调用一次

    info级别 打印一次运行状态
        统计主要路径的运行次数
        异常次数
    报告sdownload目录大小
    """

    rtss = [f'{ts.rate // 1000}' for ts in self.rate_timespans[-13:]]

    source = self.req_running.source if self.req_running else ''
    infodc = {
        'events': SortedDict(self.stt_cnts),
        'downloading_url': self.downloading_url,
        'downloading_begin': self.downloading_begin,
        'downloading_size': f'{self.scache_size:,} bytes',
        'downloading_file': source,
        'appending_urls': ', '.join(x.url for x in self.req_queue_list),
        'downloaded_total_bytes': f'{self.downloaded_bytes:,} bytes',
        'more_urls': self.last_new_urls,
        'log_errs': AT._AstErrorCnt_,
        'log_warns': AT._AstWarnCnt_,
        'network_rates kb/s': ', '.join(rtss),
        'app_start': self.start_app_epoch_str,
        'now': AT.sdf_logger_format_datetime(),

    }

    if _print:
        jstr = json.dumps(infodc, ensure_ascii=False, indent=4)
        iprint_info(jstr)
    return infodc
