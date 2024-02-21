from __future__ import annotations

from takahom.common.down_request import DownRequest
from takahom.common.common_etc import limit_memory, AT2
from takahom.server.server_base_a import IServerBaseA
# from takahom.server.server_base_a import tgt_email_log
from takahom.server.server_config import ServerConfig
from takahom.server.server_index import DLServerIndex

from takahom.server.server_ytb_util import *


class IServerBaseWeb(IServerBaseA, Protocol):

    def _f_write_file_simple(self, dkfile: DkFile,
                             file_name: str | None = None,
                             attachment: bool = True,
                             content_type: str | None = None,
                             content_length: bool = True) -> Any:

        v130_limit_break = self.sconf.v130_limit_break

        if file_name:
            filename = file_name
        else:
            req_epoch: int = int(request.args.get("epoch", "0"))
            if not req_epoch:
                AT.logger.warn("err61277 no epoch")

            fid = 0
            code = 120
            ln = dkfile.filesize
            datamd5 = AT2.file_md5_hex(dkfile.pathstr)[:8]
            filename = (f"fid-{fid}_code-{code}_epoch-{req_epoch}"
                        f"_ln-{ln}_md5-{datamd5}.{self.fkey}.data")

        vlmt = None

        time.sleep(0.5)
        return YtbUtil.write_http_resp_a(
            data=dkfile,
            filename=filename,
            content_length=content_length,
            content_type=content_type,
            attachment=attachment,
            mock_limit=vlmt,
            lower_break_limit=v130_limit_break,
        )

    def start_web_server(self) -> None:
        from takahom.server import server_base_d

        dir_sresp = self.subdir("sresp")
        dir_s7z = self.subdir("s7z")
        dir_stmp = self.subdir("stmp")

        file_key = self.sconf.file_key
        v130_limit_break = self.sconf.v130_limit_break

        app = Flask(__name__)

        _hello_cnt = 10 ** 5

        @app.route("/hello")
        def f_hello() -> Any:
            nonlocal _hello_cnt
            _hello_cnt += 1
            cnt = _hello_cnt

            cmd = request.args.get("cmd", "")
            if not cmd:
                r = f"Hello, World! ALLOK start:{self.start_app_epoch_str} cnt:{cnt}"
                time.sleep(0.5)
                return r
            elif cmd == "more":
                jstr = server_base_d.tgt_email_log(self, write_email=False)
                return jstr

            elif cmd == "demo_file":
                dkf = DkFile(join(dir_stmp.pathstr, f"hello-{AT2.gen_uuid_str()}"))
                dkf.path.write_bytes(b"hello")
                return self._f_write_file_simple(dkf)

            elif cmd == "index_csv":
                tmp_file = DkFile(join(dir_stmp.path, f"index_{AT.fepochSecs()}.tmp"))
                with open(tmp_file.path, 'w', encoding='utf-8') as file:
                    file.write('#len,md5,filename\n')
                    for dkf in DkFile2.oswalk_simple_a(self.subdir('s7z')):
                        ln = dkf.filesize
                        datamd5 = '0'
                        # datamd5 = AT2.file_md5_hex(dkfile.pathstr)[:8]
                        s = f"{ln},{datamd5},{dkf.basename}\n"
                        file.write(s)
                return self._f_write_file_simple(tmp_file)
            else:
                AT.never()

        @app.route("/file/<string:fname>")
        def f_file(fname: str) -> Any:
            cmd = ''
            if not fname or fname == 'index.html':
                cmd = 'index_file'
            else:
                cmd = 'single_file'

            if cmd == 'index_file':
                # ?att=True 将以附件的形式发送http响应
                attachment = request.args.get("att", False, type=bool)
                tmpfile = DkFile(join(dir_stmp.path, f"index_{AT.fepochSecs()}.html"))

                with open(tmpfile.path, 'w', encoding='utf-8') as file:
                    title = 'index'
                    pre = f'''
                <!DOCTYPE html>
                <html>
                <head>
                <title>{title}</title>
                </head>
                <body>                 
                <pre>   

                                    '''
                    post = '''

                </pre>                    
                </body>
                </html>                       

                                    '''
                    file.write(pre.strip() + '\n')
                    for dkfile in DkFile2.oswalk_simple_a(self.subdir('s7z')):
                        if dkfile.is_dir():
                            continue
                        fname = html.escape(dkfile.basename)
                        fname = dkfile.basename
                        ln = dkfile.filesize
                        datamd5 = '0'
                        p = f'<a href="{fname}">ln={ln},md5={datamd5},file={fname}</a>\n'
                        file.write(p)
                    file.write(post.strip() + '\n')

                return self._f_write_file_simple(
                    tmpfile,
                    file_name='index.html',
                    content_type=CommonUtil.MIME_text_html,
                    attachment=attachment,
                )

            elif cmd == 'single_file':
                AT.assert_(len(fname) > 10, 'err22688')
                file_name = fname
                iprint_debug(f'file_name:{file_name}')
                assert file_name
                dkfile = DkFile2.join_path(dir_s7z, file_name)
                AT.assert_(dkfile.exists(), f'err99421 file not exists {dkfile}')
                return self._f_write_file_simple(dkfile, file_name=file_name)

            else:
                AT.never(cmd)

        @app.route("/data")
        def f_data() -> Any:
            AT.unsupported()

        @app.route("/test")
        def f_test() -> Any:
            """
                    ?epoch=123231&salt=23123123&fid=13213123&hash=Vhash
            Vhash = hash(hash('epoch=123231&salt=23123123&id=13213123')+ SECRET)

            if salt>=1000的时候 用 salt参数作为限制速度 byte/s


            """

            demostr = "".join(str(random.randint(1, 9)) for x in range(0, 10 ** 3))
            demostr = demostr * (10 ** 3)
            demostr = demostr * 10
            demobytes = bytes(demostr, "utf-8")
            demomd5 = AT2.md5_hex(demobytes)[:8]

            fidstr = request.args.get("fid", "")
            fid = int(fidstr)

            epoch = int(request.args.get("epoch", 0))
            AT.assert_(fid > 0 and epoch > 0, "err66364")

            salt = int(request.args.get("salt", 0))
            vlmt = salt if salt >= 1000 else None

            _fid_dummy = 0
            filename = f"fid-{_fid_dummy}_code-110_epoch-{epoch}_ln-{len(demobytes)}_md5-{demomd5}.{file_key}.data"

            iprint_debug(f"step10372")

            return YtbUtil.write_http_resp_a(
                data=demobytes,
                filename=filename,
                mock_limit=vlmt,
                lower_break_limit=v130_limit_break,
            )

        m = {"port": self.port}
        if self.port > 0:
            _debug = False
            iprint_info(f"start app step5 ok. web server start ok. {m} ")
            iprint_info(f"visit web server url: http://localhost:{self.port}/file/index.html ")
            app.run(host="0.0.0.0", port=self.port, debug=_debug)
        else:
            iprint_info(f"start app step5 ok. web server isn't started. {m}")
