from __future__ import annotations

from takahom.common.common_util import *
from takahom.common.down_paras import DownloadParas
from takahom.common.down_result import DownResult
from takahom.common.common_etc import AT2
from takahom.common.ytb_util import YtbUtil


@dataclass_json
@dataclass
class DLClientState:
    results: List[DownResult] = field(default_factory=list)
    fid: int = 0
    rid: int = 0


class DownloadClient(object):
    def __init__(
            self,
            fkey: str = 'TAK',
            secret: str = 'mysecret',
            host: str = "localhost",
            port: int = 8800,
            client_port: int = 8700,
            work_dir: DkFile = DkFile(r"d:\ytb_download_client"),
    ) -> None:
        self.fkey = fkey

        self.secret = secret

        self.TA = 30
        self.TB = 60

        # self.server_port = server_port

        self.server_host = host
        self.server_port = port
        self.server_url = f"http://{host}:{port}"

        self.client_port = client_port

        # self.test_port = 8000

        # headless模式下 firefox运行会出错 可能使用profile会改变 今后再说
        self.browser_headless = False
        # self.browser_headless = True
        self.sleep_a = 300
        self.sleep_b = 30

        self.empty_postfix = ".empty"

        # 平均网速的下限值
        self.lower_lmt_rate = 10 * 1024

        self.work_dir = work_dir

        self.fid = 10 ** 5

        if True:
            # self.fkey = "SEL"
            self.TA = 3
            self.TB = 10

            self.sleep_a = 30
            self.sleep_b = 5
            self.lower_lmt_rate = 3 * 1024

        AT.assert_(
            self.work_dir.exists() and self.work_dir.is_dir(),
            f"err51563 dir not exists {self.work_dir.path}",
        )

        for d in ["cresp", "cdownload", "ctest", "c7z"]:
            os.makedirs(join(self.work_dir.path, d), exist_ok=True)

        # 用目录下的文件 扫描 然后初始化
        fids = [
            int(self.br_parse_filename(DkFile(fname))["fid"])
            for fname in os.listdir(join(self.work_dir.path, "cresp"))
        ]
        if fids:
            self.fid = max(fids) + 1
            AT.assert_(self.fid > 0, "err30212")

        if True:
            self.f_check_hello()

    def f_check_hello(self) -> None:
        start = AT.fepochSecs()

        def fhello() -> None:
            status, data = self.f_http_get(self.server_host, self.server_port, "/hello")
            AT.assert_(status == 200 and "ALLOK" in data)

        ts = []
        for i in range(100):
            thread = threading.Thread(target=fhello, args=())
            thread.start()
            ts.append(thread)

        for t in ts:
            t.join()

        end = AT.fepochSecs()
        iprint_info(f"f_test_hello end {end - start}")

    def f_http_get(self, host: str, port: int, url: str) -> Tuple[int, str]:
        import http.client

        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", url)
        r1 = conn.getresponse()
        # print(r1.status, r1.reason)
        # 200 OK
        data1 = r1.read()  # This will return entire content.
        # print(data1)
        # The following example demonstrates reading data in chunks.
        conn.close()
        return r1.status, str(data1, "utf-8")

    def start(self) -> None:
        thread = threading.Thread(target=self.log_job, args=(), daemon=True)
        thread.start()

        if False:
            thread = threading.Thread(target=self.main_job, args=(), daemon=False)
            thread.start()

        self.main_job()

        if False:
            self._start_test_server()

        pass

    def br_run(
            self, *, paras: DownloadParas, url: str, headless: bool = False
    ) -> Tuple[DkFile | None, str]:
        path_firefox = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        cmd = f'"{path_firefox}" '
        cmd = f'"{path_firefox}" -p downloader --no-remote '
        cmd = f'"{path_firefox}" -no-remote -P downloader '
        cmd = f'"{path_firefox}" -no-remote -P downloader -new-instance '
        cmd = f'"{path_firefox}" -P downloader '

        #  -no-remote -P downloader -new-instance
        if headless:
            cmd += "-headless "
        cmd += f'-url "{url}" '
        DKProcessUtil.run_simple_a(cmd)

        def fcheck() -> Tuple[DkFile | None, str]:
            TA = self.TA
            TB = self.TB

            start_download = AT.fepochSecs()

            time.sleep(TA)

            while True:
                try:
                    now = AT.fepochSecs()
                    files = self.br_list_all_files()

                    # if files ==[] or not self.br_is_downloading():
                    if files == []:
                        # 下载出错了
                        return None, "err34683 no files"

                    file = self.br_file_downloading(paras)

                    low_rate = 1024 * 5
                    low_rate = self.lower_lmt_rate
                    span_lmt = 60
                    rate速度太低 = (
                        None
                        if file is None
                        else file.filesize / (now - start_download) < low_rate
                    )
                    utime_更新超时 = (
                        None
                        if file is None
                        else now - os.path.getmtime(file.path) > 60 * 3
                    )
                    if (
                            file is not None
                            and now - start_download >= span_lmt
                            and (rate速度太低 or utime_更新超时)
                    ):
                        # 显然firefox已经超时
                        iprint_info(
                            f"err36331 utimebad {utime_更新超时} ratebad {rate速度太低}"
                        )
                        return None, CommonUtil.Err_Timeout

                    if file is not None:
                        continue

                    def f_ok(file: DkFile) -> bool:
                        r = str(paras.epoch) in file.basename
                        r2 = not self.br_is_partial_file(file)
                        return r and r2

                    files = [file for file in files if f_ok(file)]

                    AT.assert_(len(files) == 1, "err54281")
                    file = files[0]
                    dc = self.br_parse_filename(file)

                    dcok = dc["ln"] and dc["md5"] and dc["epoch"]
                    AT.assert_(dcok, "err51148")

                    def md5ok() -> bool:
                        m = dc["md5"]
                        AT.assert_(len(dc["md5"]) == 8, "err12586")
                        r = m == (DkFile.file_md5(file.pathstr)[:8])
                        return r

                    mtime = os.path.getmtime(file.path)
                    ln = int(dc["ln"])
                    # 这个逻辑 取决于mtime是否被firefox正确的设置了
                    if mtime < now - TA and file.filesize == ln and md5ok():
                        # file ok ,return
                        return file, ""
                    elif mtime < now - TB and (file.filesize != ln or not md5ok()):
                        # bad, return 可能是网络中断 或者服务器提前终止传送
                        return None, "err82641 err data"
                    else:
                        pass
                finally:
                    time.sleep(TA)
                    pass

        r = fcheck()

        return r

    def br_list_all_files(self) -> List[DkFile]:
        # 用 fkey 过滤 按照ctime顺序排列 todo
        # 包括 partial文件
        dir = "path/to/dir"
        dir = r"C:\Users\dknova\Downloads"
        fkey = "." + self.fkey + "."
        fs = [DkFile(join(dir, fname)) for fname in os.listdir(dir) if fkey in fname]
        return fs

    def br_is_partial_file(self, df: DkFile) -> bool:
        return df.basename.endswith(".part")

    def br_file_downloading(self, paras: DownloadParas) -> DkFile | None:
        fs = self.br_list_all_files()
        fs = [
            file
            for file in fs
            if str(paras.epoch) in file.basename and self.br_is_partial_file(file)
        ]
        r = len(fs) > 0
        if r:
            return fs[0]
        else:
            return None

    def br_kill_process(self) -> None:
        os.system('wmic process where name="firefox.exe" delete')
        # 查看进程列表  wmic process where name="firefox.exe" list

    def br_parse_filename(self, df: DkFile) -> Dict[str, str]:
        # 解析正常文件名称 以及 partial文件名
        return CommonUtil.parse_filename_dict(df, check=True)

    def log_job(self) -> None:
        pass

    def _subdir(self, d: str) -> DkFile:
        r = DkFile(join(self.work_dir.path, d))
        AT.assert_(r.is_dir() and r.exists(), f"err57249 {r.path}")
        return r
        pass

    def main_job(self) -> None:
        def f_is_test_url(url: str) -> bool:
            return url.startswith(f"{self.server_url}/test")

        def f_is_data_url(url: str) -> bool:
            return url.startswith(f"{self.server_url}/data")

        time.sleep(3)
        cnt_a = 0
        while True:
            if False:
                self.br_kill_process()
                ta = 1.0
                ta = 5.0
                ta = 10.0
                time.sleep(ta)

            def fa() -> None:
                for file in self.br_list_all_files():
                    if not self.br_is_partial_file(file):
                        os.remove(file.pathstr)
                        iprint_debug(f"remove file:{file.pathstr}")

            fa()

            AT.assert_(
                [
                    file
                    for file in self.br_list_all_files()
                    if not self.br_is_partial_file(file)
                ]
                == [],
                "err84362",
            )

            p_mock_limit = 0.2
            vlmt = random.randint(1024, 1024 * 100)
            salt = (
                vlmt if random.uniform(0, 1) < p_mock_limit else random.randint(1, 100)
            )

            paras = DownloadParas(epoch=AT.fepochMillis(), salt=salt, fid=self.fid)

            paras.gen_hash(self.secret)

            # url = f'http://localhost:{self.test_port}/test_100'+'?'+ paras.join_str()

            # url = f'{self.server_url}/test'+'?'+ paras.join_str()
            url = f"{self.server_url}/data" + "?" + paras.join_str()

            rrun = self.br_run(
                paras=paras, url=url, headless=self.browser_headless
            )

            file: DkFile | None = rrun[0]
            err = rrun[1]

            iprint_debug(
                f'get file {cnt_a} {"ok" if file is not None else "err"}. browser file:{file.path if file is not None else None} err:{err}'
            )

            v下载正常 = file is not None
            v数据empty = v下载正常 and file and file.basename.endswith(self.empty_postfix)
            v超时 = file is None and err == CommonUtil.Err_Timeout
            v下载不正常 = file is None

            if v下载正常 and v数据empty:
                # 将empty文件删除 记录日志
                assert file
                os.remove(file.path)
                iprint_debug("empty file removed")

            elif v下载正常 and not v数据empty:
                assert file
                dc = self.br_parse_filename(file)
                dir_ctest = self._subdir("ctest")
                dir_cresp = self._subdir("cresp")
                dir_c7z = self._subdir("c7z")
                dir_cdownload = self._subdir("cdownload")

                if False:
                    AT.never()
                elif f_is_test_url(url):
                    AT.assert_(dc["code"] == "110")
                    # move data to ctest 目录
                    shutil.move(file.pathstr, join(dir_ctest.pathstr, file.basename))

                elif f_is_data_url(url):
                    # 将下载的文件移动到 cresp
                    def fcheck(file: DkFile) -> None:
                        """
                                           v是7z分片压缩的格式 =
                        不是 .empty 扩展名
                        t-7z r-123 n-3 i-1
                        """
                        AT.assert_(
                            dc["code"] == "100"
                            and not file.basename.endswith(".empty")
                            and dc["t"] == "7z"
                            and dc["r"]
                            and dc["n"]
                            and dc["i"]
                            and True,
                            "err26942 bad filename format",
                        )

                    fcheck(file)

                    shutil.move(file.pathstr, join(dir_cresp.pathstr, file.basename))

                    i = int(dc["i"])
                    n = int(dc["n"])
                    rid = int(dc["r"])

                    dest7zname = f"r-{rid}_n-{n}.7z.{str(1000 + i)[1:]}"
                    dest7zpath = join(dir_c7z.pathstr, dest7zname)
                    shutil.copy(join(dir_cresp.pathstr, file.basename), dest7zpath)

                    v获取R中的最后一个7z文件 = n == i
                    if v获取R中的最后一个7z文件:
                        path_7z_exe = r"C:\Program Files\7-Zip\7z.exe"
                        destdir = join(dir_cdownload.pathstr, f"r-{rid}")
                        os.makedirs(destdir, exist_ok=False)
                        S = os.sep
                        pwd = self.secret
                        fname7z = f"r-{rid}_n-{n}.7z.001"
                        cmd = f'"{path_7z_exe}" x '
                        # cmd += f'-p{pwd} -o"{destdir}" "{fname7z}" '
                        cmd += f'-p{pwd} -o"{dir_cdownload.pathstr}" "{fname7z}" '
                        run_simple_a(cmd)

                        fs = DkFile.listdir(destdir)
                        AT.assert_(len(fs) > 0, "err91044")

                    AT.assert_(dc["fid"], "err53720")

                    self.fid = int(dc["fid"]) + 1

                    # 客户端可以根据下载的数据，进行大致的流控 todo

                    pass
                else:
                    AT.never()

                if False:
                    pass

            elif v下载不正常:
                # 记录日志
                iprint_warn(f"err15555 {err}")
                pass

            else:
                AT.never()

            if (v下载正常 and v数据empty) or v下载不正常:
                time.sleep(self.sleep_a)
            else:
                time.sleep(self.sleep_b)

            cnt_a += 1

    def _start_test_server(self) -> None:
        from flask import Flask, request

        app = Flask(__name__)

        @app.route("/hello")
        def f_hello() -> Any:
            return "Hello, World! allok "

        @app.route("/test")
        def f_test() -> Any:
            """
                    ?epoch=123231&salt=23123123&fid=13213123&hash=Vhash
            Vhash = hash(hash('epoch=123231&salt=23123123&id=13213123')+ SECRET)

            """

            demostr = "".join(str(random.randint(1, 9)) for x in range(0, 10 ** 3))
            demostr = demostr * (10 ** 3)
            demobytes = bytes(demostr, "utf-8")
            demomd5 = AT2.md5_hex(demobytes)[:8]

            fidstr = request.args.get("fid", "")
            fid = int(fidstr)

            epoch = int(request.args.get("epoch", ""))

            AT.assert_(fid > 0 and epoch > 0, "err66364")

            filename = f"fid-{fid}_ln-{len(demobytes)}_md5-{demomd5}_epoch-{epoch}.{self.fkey}.data"

            return (YtbUtil.write_http_resp_a(data=demobytes, filename=filename))

        if True:
            _debug = False
            app.run(host="0.0.0.0", port=self.client_port, debug=_debug)

    pass


def main(args: Any) -> None:
    client = DownloadClient(
        host="192.168.0.35", port=8800, work_dir=DkFile(r"d:\ytb_download_client")
    )

    client.start()


if __name__ == "__main__":
    import argparse  # 1

    parser = argparse.ArgumentParser()  # 2

    parser.add_argument("-p", "--profile", type=str, default="dev", help="profile")

    parser.add_argument("--workdir", type=str, help="工作目录")

    parser.add_argument("--port", type=int, default=8800, help="server web port")

    parser.add_argument("--secret", type=str, default="hellobaby", help="7z password")

    parser.add_argument("--location", type=str, default="test", help="location")

    parser.add_argument("--maxcnt", type=int, default=50, help="dircnt")

    parser.add_argument("--reportverbose", type=int, default=30, help="报告的详细程度")

    args = parser.parse_args()  # 4

    main(args)
