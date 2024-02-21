from __future__ import annotations

from typing import TypedDict

from attr import define
from dknovautils import *
from takahom.common import *
from takahom.common.common_etc import AT2, DkFile2
from takahom.common.common_util import DirMeta
from takahom.common.entity import YtbId
from takahom.common.ytb_util import YtbUtil


class ManUtil:

    @staticmethod
    def f_check_a(pdir: DkFile) -> None:
        """

    将对应的ytbid-目录中加入适量的中文title
        目录依据
            目录名称keys存在 ct r ok 并获得YtbId
                如果子目录中存在id匹配 扩展名为 description的文件 将此文件的中文部分获取 然后rename该目录

        """

        tprint = AT2.tprint_fun(verbose=True)

        def fa_parse_ytbid_from_filename(dkf: DkFile) -> YtbId | None:
            ytbids = list(YtbUtil.parse_ytbid_from_lines([dkf.basename]))
            return ytbids[0] if ytbids else None

        def fb_find_description_file(dkf: DkFile) -> DkFile | None:
            """
    fb(dkfile,ytbid)
        扫描目录
        匹配文件名 [id].description 返回 该文件dkfile|None
            """
            ytbid = fa_parse_ytbid_from_filename(dkf)
            assert ytbid
            f = [f for f in DkFile.listdir(dkf.pathstr) if
                 f.basename.endswith(f'[{ytbid.id_original}]{YtbConf.dot_description}')]
            f = f[0] if f else None
            if not f:
                iprint_warn(f'err15352 {dkf.pathstr}')
            # assert f, f'err59551 {dkf.pathstr}'
            return f

        def fc_convert(dkf: DkFile) -> None:
            tprint('step23551')
            assert dkf.is_dir()
            dc = CommonUtil.parse_filename_dict(dkf, silent=True)
            if (ytbid := fa_parse_ytbid_from_filename(dkf)) and (sfile := fb_find_description_file(dkf)):
                tprint('step99992')
                endp = f'[{ytbid.id_original}]{YtbConf.dot_description}'
                name_part = sfile.basename[:-len(endp)]
                assert len(name_part) > 0
                lmt_bytes = CommonUtil.MAXbytes_dirname - (len(dkf.basename) + len('_tt-'))
                name_part = YtbUtil.f_cal_chinese_parts_for_directory(name_part, lmt_bytes)
                tprint('step81762')
                dir_meta = DirMeta.from_dirname(dkf)
                if not dir_meta or dir_meta.tt:
                    return
                dir_meta.tt = name_part
                iprint_debug(dir_meta)
                dirname = dir_meta.to_str()

                iprint_debug(f'begin convert {dkf.pathstr}')
                CommonUtil.f_file_cvt_rename(dkf, lambda dkf: dirname)
                iprint_debug(f'end convert {dkf.pathstr}')

        def fd_find_all_ytd_dirs(dkf: DkFile) -> Iterator[DkFile]:
            fs = (f for f in DkFile2.oswalk_simple_a(dkf, topdown=False)
                  if f.is_dir()
                  if (d := CommonUtil.parse_filename_dict(f, silent=True))
                  if {'ct', 'r', 'ok'}.issubset(set(d))
                  if d['ok'] in ('yes', 'y', 'true')
                  )
            return fs

        for dkf in fd_find_all_ytd_dirs(pdir):
            iprint_debug(f"step64223 {dkf}")
            assert DkFile2.count_sub_folders(dkf) == 0, f'err40308 {dkf}'

        for dkf in fd_find_all_ytd_dirs(pdir):
            iprint_debug(f"step12654 {dkf}")
            CommonUtil.dir_replace_filename_comma(dkf)

        for dkf in fd_find_all_ytd_dirs(pdir):
            iprint_debug(f"step22106 {dkf}")
            fc_convert(dkf)


def main(args: Any) -> None:
    pdir = DkFile(r's:\_DISC_S_\ytb_scan')
    # pdir = DkFile(r'q:\tmp\2024')
    # pdir = DkFile(r'e:\tmp\2024')
    assert pdir.exists()

    # CommonUtil.chinese_convert_directory(pdir, cvt=ChineseCvt.zh_cn)

    ManUtil.f_check_a(pdir)


def f_parse_args() -> None:
    import argparse
    parser = argparse.ArgumentParser()

    # parser.add_argument("mode", choices=["demo", "run"], help="subcmd")

    parser.add_argument("--profile", type=str,
                        default="prod", choices=["prod", "dev"], help="profile")

    parser.add_argument("--conf", type=str, default='env.conf', help="config file")

    args = parser.parse_args()

    main(args)


if __name__ == "__main__":
    f_parse_args()
