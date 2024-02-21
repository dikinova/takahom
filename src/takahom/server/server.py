from __future__ import annotations

from takahom.common.common_etc import limit_memory, AT2
from takahom.etc.man_util import ManUtil
from takahom.server.server_base_a import IServerBaseA, copy_ytbtxts_files_to_dest_input_dir
from takahom.server.server_base_web import IServerBaseWeb
from takahom.server.server_base_c_download import IServerBaseC
from takahom.server.server_base_d import build_system_info, check_ydltest_url, build_demo_request, \
    tgt_main_download_queue, \
    tgt_remove_toomuch_data, tgt_email_log, f_try_to_add_demo, \
    f_try_to_add_ytb_scan_dir, \
    tgt_job_log_5mins
from takahom.server.server_base_e import INetCalulator, DirSizeInfo, TimeSpan
from takahom.server.server_config import ServerConfig, build_config_from_args, test001
from takahom.server.server_index import DLServerIndex

from takahom.server.server_base_a import dec_my_log_error_builder

from takahom.server.server_ytb_util import *


class DownloadServer(IServerBaseC, INetCalulator):
    subdirs = ["scache", "sinput", "sdownload", "s7z", "sresp", "stmp", "setc", "slog"]

    def __init__(
            self,
            args: Any,
            *,
            sconf: ServerConfig,
    ) -> None:
        self.start_app_epoch_str = AT.sdf_logger_format_datetime()
        self.is_mode_demo: bool = args.mode == "demo"
        self.is_mode_run: bool = args.mode == "run"

        self.sconf = sconf
        self.args: Any = args

        self.fkey = sconf.file_key
        self.secret = sconf.secret
        self.port = sconf.port

        self.work_dir = DkFile(sconf.work_dir)
        self.p7z_volume = sconf.p7z_volume
        self.p7z_level = sconf.p7z_level

        self.cfg_fid = sconf.cfg_fid
        self.cfg_rid = sconf.cfg_rid

        # 30天之内 同样的url不能重复下载
        self.url_duplicate_check_days = sconf.url_duplicate_check_days

        # 网速检测 低于该网速则主动停止传输
        self.v130_limit_break = sconf.v130_limit_break

        self.rate_limits: List[int] = sconf.cal_rate_limits(sconf.rate_limits)
        CommonUtil.rate_limit(self.rate_limits)
        iprint_info(f'rate limites: {self.rate_limits}')

        self.socks_proxy: str = sconf.network_proxy
        self.ytb_cmd_path: str = sconf.ytb_cmd_path

        self.s7z_keep_secs: int = sconf.s7z_keep_secs

        self.scan_dirs: List[DkFile] = sconf.cal_scan_dirs()
        iprint_info(f'scan_dirs: {[dkf.pathstr for dkf in self.scan_dirs]}')

        if vStep1OK := True:
            AT.assert_(
                self.work_dir.exists() and self.work_dir.is_dir(),
                f"err51563 dir not exists {self.work_dir.path}",
            )

            for d in self.subdirs:
                os.makedirs(join(self.work_dir.path, d), exist_ok=True)

            iprint_info('start app step1 ok')

        self.stt_cnts: Dict[str, int] = dict()
        self.dir_size_infos: List[DirSizeInfo] = []
        self.rate_timespans: List[TimeSpan] = []
        self.downloading_url: str | None = None
        self.downloading_begin: str | None = None
        self.scache_size: int = 0
        self.downloaded_bytes: int = 0

        self._empty_postfix = ".empty"
        self.fid = 10 ** 7
        self.state_index: DLServerIndex
        dir_sinput = self.subdir("sinput")
        dir_sdownload = self.subdir("sdownload")

        self.input_dir = dir_sinput
        self.output_dir = dir_sdownload
        self.sresp_dir = self.subdir("sresp")

        # 没用到 可以删除
        self.allow_duplicate_url = False
        if AT2.is_profile_dev():
            self.allow_duplicate_url = False

        # 保证同时添加和移除
        self.req_queue: Queue[DownRequest] = Queue()
        self.req_queue_list: List[YtbItem] = []
        self.req_size_max: int = 10
        self.req_running: DownRequest | None = None
        self.sresp_fids: MyNDArrayInt64 | None = None
        self.sresp_fnames: Dict[int, str] = {}
        self.last_new_urls: int = 0

        if vStep2OK := True:
            sinfo = build_system_info(self.work_dir)
            iprint_info('start app step2 ok')
            AT.assert_(self.input_dir.exists(), f"dir doesn't exist. {self.input_dir.pathstr}")

            def dirok(d: DkFile) -> bool:
                return d.exists() and d.is_dir()

            dsok = all(dirok(d) for d in self.scan_dirs)
            AT.assert_(dsok, f'err98240 some directory is bad. {self.scan_dirs}')

    @dec_my_log_error_builder(message="Error on thread_scan_input_req_scan_dir: {e!r}")  # type:ignore
    def thread_scan_input_req_scan_dir(self) -> None:
        """
        """
        if self.is_mode_run:
            f_try_to_add_ytb_scan_dir(self)
        elif self.is_mode_demo:
            f_try_to_add_demo(self)
        else:
            AT.never()

    def server_init_stateindex(self) -> None:
        """
        """

        _index_file_data = self.read_index_file()

        if _index_file_data is None:
            ss = DLServerIndex()
            ss.results = []
            _index_file_data = ss
        self.state_index = _index_file_data

        while len(self.state_index.results) > self.sconf.state_res_max_size:
            self.state_index.results.pop(0)

        def f_maxfidfile_sresp(sresp_dir: DkFile) -> DkFile | None:
            fid = 0
            file = None
            for d in os.scandir(sresp_dir.pathstr):
                dkf = DkFile(join(sresp_dir.pathstr, d.name))
                dc = CommonUtil.parse_filename_dict(dkf)
                f = int(dc["fid"])
                assert f > 0
                if fid == 0 or f > fid:
                    fid = f
                    file = dkf

            return file

        _maxfidfile_sresp = f_maxfidfile_sresp(self.sresp_dir)
        _maxfidfile_sresp_dc = (
            None
            if not _maxfidfile_sresp
            else CommonUtil.parse_filename_dict(_maxfidfile_sresp)
        )

        if True:
            AT.assert_(self.cfg_rid >= 10 ** 5)
            if _maxfidfile_sresp:
                assert _maxfidfile_sresp_dc
                file_maxid = int(_maxfidfile_sresp_dc["r"])
            else:
                file_maxid = 0

            if _index_file_data:
                indexfile_id = _index_file_data.rid
            else:
                indexfile_id = 0

            self.state_index.rid = max(self.cfg_fid, file_maxid + 1, indexfile_id)

    def start(self) -> None:

        self.server_init_stateindex()

        copy_ytbtxts_files_to_dest_input_dir(src=DkFile('./docs'),
                                             dest=self.subdir('sinput'))

        if vStep3OK := True:
            # 扫描 sdownload scan_dirs 并完成中文简繁体转换
            for dkf in [self.output_dir]:
                iprint_debug(f"step96498 check dir {dkf}")
                CommonUtil.dir_replace_filename_comma(dkf)
                CommonUtil.chinese_convert_directory(dkf, cvt=self.chinese_cvt_enum)

            for scan_dir in self.scan_dirs:
                if not AT2.is_profile_prod():
                    iprint_debug(f"step37361 check dir {scan_dir}")
                    ManUtil.f_check_a(scan_dir)
                    # CommonUtil.chinese_convert_directory(dkf, cvt=self.chinese_cvt_enum)

            check_ydltest_url(self)
            iprint_info('start app step3 ok')

        f_try_to_add_ytb_scan_dir(self)

        thread = threading.Thread(target=tgt_main_download_queue,
                                  args=(self,),
                                  daemon=False  # main thread may end at once
                                  )
        thread.start()

        schedule.every(10).minutes.do(lambda: self.thread_scan_input_req_scan_dir())

        mins = 60 if AT2.is_profile_prod() else 3
        schedule.every(mins).minutes.do(lambda: tgt_remove_toomuch_data(self))

        mins = 60 if AT2.is_profile_prod() else 3
        schedule.every(mins).minutes.do(lambda: tgt_email_log(self))

        mins = 5 if AT2.is_profile_prod() else 1
        schedule.every(mins).minutes.do(lambda: tgt_job_log_5mins(self))

        dir_scache = self.subdir('scache')
        schedule.every(60).seconds.do(lambda: self.tgt_update_sdownload_size(dkf=dir_scache))

        def th_run_schedule() -> None:
            while True:
                schedule.run_pending()
                time.sleep(1)

        thread = threading.Thread(target=th_run_schedule, args=(), daemon=True)
        thread.start()

        if vStep4OK := True:
            iprint_info(f'start app step4 ok')

        if True:
            self.start_web_server()


def main(args: Any) -> None:
    AT2._app_profile = args.profile
    sc = build_config_from_args(args)

    AT.assert_(AT.is_linux, 'err15238 only support linux os')

    if not AT2.is_profile_prod():
        test001()

    max_memory = 1024 * 1024 * 100
    limit_memory(max_memory)

    server = DownloadServer(args, sconf=sc)
    AT2.init_logging_v1(DkFile('.'), log_dir=server.subdir('slog'))
    iprint_info(f"server start version:{AppVer}")
    iprint_info(f"config file, {sc.conf_file}: {sc.copy_without_secret()}")
    time.sleep(0.5)

    server.start()


"""



"""
