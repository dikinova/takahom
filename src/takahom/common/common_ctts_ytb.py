from __future__ import annotations

from typing import cast

from dknovautils import *

from takahom.common.common_etc import DkFile2

ytb_url_prefix_www_youtube_com = "https://www.youtube.com/"
ytb_url_prefix_www_youtube_com_watch = "https://www.youtube.com/watch"

ytb_url_demo_moyun = "https://www.youtube.com/watch?v=gf6v59c5yuY"
ytb_url_demo_ydltest = "https://www.youtube.com/watch?v=BaW_jenozKc"

ytb_url_demo100 = ytb_url_demo_moyun
ytb_url_demo100_len = len(ytb_url_demo100)

ytb_code_len_a_11 = 11
assert ytb_code_len_a_11 == len("La1CTjpoE_8")
assert len(ytb_url_prefix_www_youtube_com) > ytb_code_len_a_11

ytb_reg_simple_code11 = re.compile(r"[0-9a-zA-Z-_]{11,11}")
ytb_reg_simple_id_all = re.compile(r"[0-9a-zA-Z-_]{11,90}")
ytb_reg_simple_id_all_name_part = re.compile(r""".*\[([0-9a-zA-Z-_]{11,90})\]""")
ytb_reg_simple_myid_all = re.compile(r"[0-9a-zA-Z-+]{11,90}")
reg_ytb_url_txt = re.compile(r'ytb_.*_\d{3,4}\.url\.txt')
assert re.fullmatch(reg_ytb_url_txt, 'ytb_erwere_0987.url.txt')
# ytb_xxxx.exd.txt
ytb_reg_exd_files = re.compile(r'ytb_.*\.exd\.txt')
assert re.fullmatch(ytb_reg_exd_files, 'ytb_xxxysfdsf.exd.txt'), 'err342342'

ytb_reg_ytb_txt_files = re.compile(r'ytb_.*\.txt')

ytb_reg_extract_idstr_from_file_a = re.compile(r""".*\-([0-9a-zA-Z-_]{11,11})\..+""")


def f_test() -> None:
    assert len(
        cast(re.Match[str], re.fullmatch(ytb_reg_extract_idstr_from_file_a, '司马南激辩-upQSDcpIm48.webm.mp4'))[1]) == 11

    assert re.fullmatch(ytb_reg_simple_code11, "__xx_-xxxxx")
    ma = re.fullmatch(ytb_reg_simple_id_all_name_part, "xyz[12345678901]")
    assert ma and len(ma[1]) >= 11 and ma[1][:1] == '1'


f_test()

ytb_reg_simple_a = re.compile(
    r"https://www\.youtube\.com/watch\?v=[0-9a-zA-Z-_]{11,11}"
)

assert re.fullmatch(
    ytb_reg_simple_a, "https://www.youtube.com/watch?v=__xx_-xxxxx"
)

ytb_reg_simple_shorts = re.compile(
    r"https://www\.youtube\.com/shorts/[0-9a-zA-Z-_]{11,11}"
)

ytb_cfg_maxsize_str = "10.0G"
ytb_cfg_maxsize_str = "5.0G"
ytb_cfg_maxsize_str = "5000M"  # 不确定是否支持G后缀

ytb_domain_name = "youtube"

ytb_cfg_timeout = 120  # secs


class YtbConf:
    IdPrefix_vcode_ytbid = 'ytbid'
    IdPrefix_short_ytbih = 'ytbih'
    IdPrefix_list_ytbip = 'ytbip'

    IdPrefixList = [IdPrefix_vcode_ytbid,
                    IdPrefix_short_ytbih,
                    IdPrefix_list_ytbip]

    playlist_maxitems_default = 100

    dot_description = '.description'

    url_key_maxitems = '_maxitems_'

    @classproperty
    def media_file_exts(cls) -> Tuple[str, ...]:
        r = ('mp4', 'm4a')
        return r

    @classproperty
    def media_file_exts_with_dot(cls) -> Tuple[str, ...]:
        r = tuple('.' + e for e in cls.media_file_exts)
        return r

    @classproperty
    def media_min_filesize(cls) -> int:
        Min_Filesize = 1024 * 200
        return Min_Filesize

    @classmethod
    def short2vcode_将短视频url转换为普通url(cls) -> bool:
        return True

    @classmethod
    def extract_ytb_idstr_from_basename(cls, dkf: DkFile) -> str | None:
        """
        xxxx[yyyy].mp4
        xxxx[yyyy].eeeee
        xxxx[yyyy].a.b.c

        vcode or playlist

        """
        bname = dkf.basename
        # assert len(dkf.basename.split('.')) <= 10, f'err49304 {dkf.pathstr}'
        name_part = bname.split('.')[0]
        # name_part = DkFile2.basename_part_without_extension(dkf.path)
        ma = re.fullmatch(ytb_reg_simple_id_all_name_part, name_part)
        if not ma:
            return None
        idstr = ma[1]
        assert len(idstr) >= 11
        return idstr
