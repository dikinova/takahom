from __future__ import annotations

from takahom.common.down_request import DownRequest
from takahom.common.common_etc import limit_memory, AT2
from takahom.server.server_base_a import KeyEvent
from takahom.server.server_base_web import IServerBaseWeb
from takahom.server.server_base_e import INetCalulator
from takahom.server.server_index import DLServerIndex

from takahom.server.server_ytb_util import *


class IServerBaseC(IServerBaseWeb, INetCalulator, Protocol):
    def thread_main_download(self, cnt: int) -> None:
        """

        """

        dir_scache = self.subdir("scache")
        dir_sinput = self.subdir("sinput")
        dir_sdownload = self.subdir("sdownload")
        dir_s7z = self.subdir("s7z")
        dir_sresp = self.subdir("sresp")
        dir_stmp = self.subdir("stmp")

        req: DownRequest | None = None

        req = self.fetch_req()
        assert req

        iprint_info(f"start download: {req.url}")

        try:

            self.handle_request_pre_init(req)

            res = self.handle_request(req)

            res.last_new_urls = self.last_new_urls
            assert self.state_index
            if vAddRes := False:
                rss = self.state_index.results
                rss.append(res)
                while len(rss) > self.sconf.state_res_max_size:
                    rss.pop(0)

            if res.ok or not res.ok:
                rid = self.state_index.rid
                res.rid = rid

                # 尽早持久化 防止rid重复
                self.state_index.rid += 1
                self.write_index_file()

                res.write_json_file()

                AT.assert_(DkFile2.count_sub_folders(dir_scache) == 0, f'err18144 {dir_scache}')
                # scache中的所有文件名 确保将,替换为-
                CommonUtil.dir_replace_filename_comma(dir_scache)

                iprint_info("will copy to sdownload dir 10secs later")
                time.sleep(10)

                title_part = YtbUtil.cal_title_part_from_description_filename(res, dir_scache)
                if title_part:
                    title_part = CommonUtil.chinese_cvt_str(title_part, cvt=self.chinese_cvt_enum)
                iprint_debug(f'step73261 {title_part}')
                sdownload_dir_name = res.cal_sdownload_dir_name(ctitle=title_part)
                sdownload_dir_path = join(dir_sdownload.pathstr, sdownload_dir_name)
                os.makedirs(sdownload_dir_path)
                AT.assert_((_ := DkFile(sdownload_dir_path)).is_dir() and _.exists(), "err38182")
                shutil.copytree(req.data_dir, sdownload_dir_path, dirs_exist_ok=True)
                # 目录下所有文件都简体和繁体转换
                CommonUtil.chinese_convert_directory(DkFile(sdownload_dir_path), cvt=self.chinese_cvt_enum)

                iprint_info(
                    f"end download. ok:{res.ok} url:{req.url} network: {int(res.netv / 1000)}KB/s"
                )

            if not res.ok:
                self.write_index_file()
                iprint_info(f"err72093 donwlaod error {res.to_str_simple()}")
                self.req_running = None
            else:
                """
                目录内的数据进行移动 sdownload/下面
                    创建 info.json文件
    
                在s7z目录下创建 7z文件
                    s7z/
                    r-123.7z.001
                    r-123.7z.002
    
                在 sresp目录下创建 data 文件
                    fid-123_r-123_n-3_i-1_md5-xxx.data
    
                """
                iprint_debug("step54059")
                # fid = self.state_index.fid
                fid = 10000
                AT.assert_(res.files_cnt > 0 and res.files_size > 0, "err79860")

                run_simple_a(f'ls -l "{sdownload_dir_path}" ')

                # 7za a -p123456 -mhe -mx0 -t7z -v3m directory.7z directory
                # 压缩的文件中是有目录名称的
                pwd = self.secret
                volume = 1024 * 1024
                volume = self.p7z_volume

                def f_vlm(fsize: int, vlm: int) -> int:
                    AT.assert_(fsize > 0 and vlm >= 1000, "err93746")
                    while True:
                        fnum = int(fsize / vlm) + 1
                        if fnum < 300:
                            return vlm
                        else:
                            vlm = int(vlm * 1.2)

                volume = f_vlm(res.files_size, volume)
                # AT.assert_(res.files_size/volume<900,'err67222 too many volumes')
                AT.assert_(req.ytb_ytbid, "err32546")
                # bname_7z = f"r-{self.rid}_{req.ytb_ytbid.to_str_with_prefix()}.{self.fkey}.7z"
                bname_7z = res.cal_s7z_partial_name(p7z_vn=0, secret=self.secret, fkey=self.fkey)
                run_simple_a(f'mkdir "{dir_s7z.pathstr}"/tmp ')
                run_simple_a(f'rm -rf "{dir_s7z.pathstr}"/tmp/* ')
                dest_s7z_file_path = f"{dir_s7z.pathstr}/tmp/{bname_7z}"
                mxn = self.p7z_level
                pwd = pwd.strip()
                _ppwd = f'-p{pwd}' if pwd else ''
                _cmd = (
                    f'7za a {_ppwd} -mhe {mxn} -t7z -v{volume}b "{dest_s7z_file_path}" "{sdownload_dir_path}" '
                )
                run_simple_a(_cmd)
                iprint_debug("step30466")
                # 可能文件size太小 那么就没有分卷 为了统一处理 添加后缀 001
                if DkFile(dest_s7z_file_path).exists():
                    run_simple_a(f'mv "{dest_s7z_file_path}" "{dest_s7z_file_path}.001" ')

                # 验证 rid对应的7z文件 创建成功 ls文件
                fs = [
                    dkf
                    for dkf in DkFile.listdir(join(dir_s7z.pathstr, 'tmp'))
                    if bname_7z in dkf.basename
                ]
                AT.assert_(len(fs) > 0, "err21761")
                iprint_debug(f'step81273 fs {",".join([dkf.basename for dkf in fs[:100]])}')

                # 计算创建的7z的文件个数
                p7z_vn = len(fs)
                AT.assert_(0 < p7z_vn < 900, "err23868")

                # 将文件从tmp mv up 同时重命名
                for i in range(1, p7z_vn + 1):
                    suffix = str(1000 + i)[1:]
                    from_path = f'{dir_s7z.pathstr}/tmp/{bname_7z}.{suffix}'
                    bname_7z_new = res.replace_s7z_vn(bname_7z, p7z_vn=p7z_vn)
                    to_path = f'{dir_s7z.pathstr}/{bname_7z_new}.{suffix}'
                    run_simple_a(f'mv "{from_path}" "{to_path}" ')

                # 尽早持久化 防止fid重复
                # self.state_index.fid += n
                self.write_index_file()

                self.req_running = None
                res.infos.append("step100 save file ok")
                CommonUtil.clear_dir(dir_scache)
                self.log_cnt(KeyEvent.down_allok)

                iprint_debug("step65252")

        finally:
            self.handle_request_post(req)
