from __future__ import annotations

import os
from dataclasses import dataclass, field
from os.path import join
from typing import List

from dataclasses_json import dataclass_json
from dknovautils import AT, DkFile

from . import CommonUtil
from .common_ctts_ytb import YtbConf
from .down_request import DownRequest, _f_res_version


@dataclass_json
@dataclass
class DownResult:
    version: str = field(default_factory=_f_res_version)
    ok: bool = False
    rcode: int = -1
    data_dir: str = ""
    err: str = ""
    url: str = ""
    res_id: str = ""
    infos: List[str] = field(default_factory=list)
    req: DownRequest = field(default_factory=DownRequest)
    start_epoch: float = 0
    start_epoch_str: str = ""
    end_epoch: float = 0
    end_epoch_str: str = ""
    files_cnt: int = 0
    files_size: int = 0
    files: List[str] = field(default_factory=list)
    rid: int = 0
    stdout: str = ""
    stderr: str = ""
    netv: int = 0  # 下载网速 byte/s
    last_new_urls: int = -1

    @staticmethod
    def from_req(req: DownRequest) -> DownResult:
        r = DownResult(
            data_dir=req.data_dir,
            url=req.url,
            req=req,
        )
        return r

    def check(self) -> bool:
        AT.assert_(
            self.url and self.data_dir and self.req and self.req.check(),
            "err36475 DownResult format error",
        )

        return True

    def after_run(self) -> None:
        """
        包括获取和计算目录内的文件信息
        可以重复调用 不会重复生成数据

        """
        assert self.start_epoch > 0, 'err16785'

        if self.start_epoch_str == "":
            if self.start_epoch > 0:
                self.start_epoch_str = AT.sdf_logger_format_datetime(
                    int(self.start_epoch * 1000)
                )
            if self.end_epoch > 0:
                self.end_epoch_str = AT.sdf_logger_format_datetime(
                    int(self.end_epoch * 1000)
                )

            # fs=[DkFile(f) for f in os.listdir(self.data_dir)]
            fs = DkFile.listdir(self.data_dir)
            self.files_cnt = len(fs)
            self.files_size = sum(f.filesize for f in fs)
            self.files = []
            for f in fs:
                if f.filesize < YtbConf.media_min_filesize:
                    continue
                mtime = os.path.getmtime(f.pathstr)
                dtstr = AT.sdf_logger_format_datetime(int(mtime * 1000))
                ln = [str(f.filesize), dtstr, f.basename]
                ln = ",".join(ln)
                self.files.append(ln)

            if self.ok:
                self.err = ""

            if self.err:
                self.err = self.err[:100]

            if self.stdout:
                self.stdout = self.stdout[:1000]

            if self.stderr:
                self.stderr = self.stderr[:1000]

            # 计算平均网速
            res = self
            span = res.end_epoch - res.start_epoch
            netv = 0 if not span else int(res.files_size / span)
            res.netv = netv

            self.check()

    def write_json_file(self) -> None:
        # 在目录下写入 result.json 文件 文件名称用下划线开头 可以让文件顺序排在前面
        res = self
        DkFile(join(res.data_dir, "_result.json")).path.write_text(
            res.to_json(indent=4, ensure_ascii=False), encoding="utf-8"  # type:ignore
        )

    def cal_title_parts_size_lmt(self) -> int:
        bsize = len(self.cal_sdownload_dir_name(ctitle=''))
        # = 240
        return CommonUtil.MAXbytes_dirname - bsize
        # astr = f'ct-2023-01-01_r-1111111_ok-yes_ytdip-{self.req.ytb_ytbid.id_original}'

    def cal_sdownload_dir_name(self, ctitle: str | None = None) -> str:
        res = self
        ctstr = AT.sdf_logger_format_datetime(dt=int(self.start_epoch * 1000), precise='d', noColon=True)
        ttp = '' if ctitle is None else f'_tt-{ctitle}'
        dirname = (
            f'ct-{ctstr}'
            f'_r-{self.rid}_ok-{"yes" if res.ok else "no"}'
            f'{ttp}'
            f"_{self.req.ytb_ytbid.to_str_with_prefix()}"
        )
        return dirname

    #             bname_7z = f"r-{self.rid}_{req.ytb_ytbid.to_str_with_prefix()}.{self.fkey}.7z"
    def cal_s7z_partial_name(self, p7z_vn: int, secret: str, fkey: str) -> str:
        assert 0 <= p7z_vn < 1000
        ctstr = AT.sdf_logger_format_datetime(dt=int(self.start_epoch * 1000), precise='d', noColon=True)
        phstr = AT.md5_hex(secret.encode())[:4]
        bname_7z = (
            f"ct-{ctstr}"
            f"_r-{self.rid}_{self.req.ytb_ytbid.to_str_with_prefix()}"
            f"_ph-{phstr}_vn-{str(p7z_vn + 1000)[1:]}"  # 为了方便替换 vn必须在最后一部分
            f".{fkey}.7z"
        )
        return bname_7z

    def replace_s7z_vn(self, oldfilename: str, p7z_vn: int) -> str:
        """replace vn to new value """
        assert 0 <= p7z_vn < 1000
        fnpa, *fnps = oldfilename.split('.')
        *bpa, _ = fnpa.split('_')
        fname2 = '.'.join(['_'.join([*bpa, f'vn-{str(p7z_vn + 1000)[1:]}']), *fnps])
        return fname2

    def to_str_simple(self) -> str:
        self.check()
        m = {
            "ok": self.ok,
            "rcode": self.rcode,
            "err": self.err,
            "url": self.url,
            "req.uuid": self.req.uuid,
        }
        return str(m)
