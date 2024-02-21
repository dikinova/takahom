import collections
from enum import auto
from typing import cast

from dknovautils import *

from takahom.common.common_imports import run_simple_a
from takahom.common.common_util import CommonUtil, ChineseCvt
from takahom.common.common_etc import DkFile2, AT2, limit_memory

from attr import define, field as afield, asdict


def _f_rate_limits() -> str:
    a = [1000 * 1000 * 5] * 8 + [1000 * 300] * 16
    r = ','.join(str(e) for e in a)
    LMT = 1000 * 1000 * 10
    return f'*:{LMT}'


def trim_to_empty(v: str) -> str:
    r = v.strip()
    return r


class DownOrderBy(Enum):
    natural = auto()
    # vcode在前面 list在后面 然后是natural顺序和行顺序
    vcode_first = auto()


@define(kw_only=True, frozen=True)
class ServerConfig:
    work_dir: str = afield(converter=trim_to_empty)
    profile: str = afield(default='')

    port: int = afield(default=0, )  # port>=0 如果是0 表示不启动web server

    secret: str = afield(default='', converter=trim_to_empty)

    # ---------------------------------------------
    # 暂时不手动设置

    scan_dirs: str = afield(default="", converter=trim_to_empty)

    network_proxy: str = afield(default="", converter=trim_to_empty)  # ='socks5://192.168.0.34:7890'

    rate_limits: str = afield(factory=_f_rate_limits, converter=trim_to_empty)

    chinese_cvt: int = afield(default=ChineseCvt.nothing.value)

    download_order_by: int = afield(default=DownOrderBy.vcode_first.value)

    # ------------------------------------

    file_key: str = afield(default="TAK")

    p7z_volume: int = 1024 * 1024 * 10

    p7z_level: str = "-mx1"

    cfg_fid: int = 10 ** 7

    cfg_rid: int = 10 ** 5

    url_duplicate_check_days: int = 30

    # 网速检测 低于该网速则主动停止传输
    v130_limit_break: int = 1000 * 5

    ytb_cmd_path: str = "yt-dlp "

    s7z_keep_secs: int = 60 * 60

    state_res_max_size: int = 5

    # -----------------------------------------------------------
    conf_file: str = afield(default="")

    @work_dir.validator
    def check_workdir(self, attribute: Any, value: str) -> None:
        # 必须是目录 必须存在
        ma = f"work_dir:'{value}' doesn't exists or is not a directory "
        _dummy = value == ''
        if _dummy:
            return
        dkf = DkFile(value)
        if not dkf.exists() or not dkf.is_dir():
            raise ValueError(ma)

        tfile = DkFile2.join_path(dkf, f'tmp{AT.fepochMillis()}.tmp')
        try:
            with open(tfile.path, 'w') as file:
                file.write('hello')
        except Exception as e:
            raise ValueError(f"work_dir:'{value}' has no write permission ")
        finally:
            if tfile.exists():
                os.remove(tfile.path)

    #     secret
    @secret.validator
    def check_secret(self, attribute: Any, value: str) -> None:
        r = re.compile('[0-9a-zA-Z_]{6,30}')
        ok = value == '' or r.fullmatch(value)
        if not ok:
            sc = '*' * len(value)
            raise ValueError(f"secret:'{sc}' is bad. It should only contains 0-9a-zA-Z_ and 6<= len <=30 ")

    @network_proxy.validator
    def check_socksproxy(self, attribute: Any, value: str) -> None:
        r = re.compile('socks5://.*')
        ok = value == '' or r.fullmatch(value)
        if not ok:
            raise ValueError(f"socks_proxy:'{value}' is bad. It should starts with 'socks5://' ")

    @rate_limits.validator
    def check_ratelimits(self, attribute: Any, value: str) -> None:
        self.cal_rate_limits(value)

    # -------------------------------------------------------------------
    def cal_rate_limits(self, value: str) -> List[int]:
        rs = CommonUtil.parse_rate_limits_from_conf(value)
        assert len(rs) == 24
        return rs

    def cal_scan_dirs(self) -> List[DkFile]:
        rs = [e for e in self.scan_dirs.split(',') if e]
        rs = list(collections.Counter(rs))  # 去掉重复
        rs = [DkFile(e) for e in rs]
        return rs

    def copy_without_secret(self) -> Dict[str, Any]:
        osdc: Dict[str, Any] = asdict(self, filter=lambda attr, value: attr.name != "secret")
        return osdc


def test001() -> None:
    AT.logger.debug("hello from here")

    s = AT.md5_hex("".encode())
    assert len(s) > 0
    iprint(s)
    pass


def build_config_from_args(args: Any) -> ServerConfig:
    from dotenv import dotenv_values

    conf_file: str = args.conf
    conf_file = str(DkFile(conf_file).path.resolve())

    AT.assert_((dkf := DkFile(conf_file)).exists() and dkf.is_file(), f'err62869 file {conf_file} cannot be read')
    iprint_debug(f"conf file is '{conf_file}' ")

    cfg: Dict[str, str] = cast(Dict[str, str],
                               dotenv_values(conf_file))
    # config = {"USER": "foo", "EMAIL": "foo@example.org"}

    AT.assert_(all(v is not None for v in cfg.values()),
               f'err12922 some value is bad. check format of file {conf_file}')

    if cfg.get('work_dir', '').strip() == '':
        raise ValueError(f"err36901 work_dir is bad")

    _sc = ServerConfig(work_dir='')

    sc = ServerConfig(
        work_dir=cast(str, cfg.get('work_dir')),
        profile=args.profile,
        conf_file=conf_file,
        secret=cfg.get('secret', _sc.secret),
        port=int(cfg.get('port', _sc.port)),
        rate_limits=cfg.get('rate_limits', _sc.rate_limits),
        network_proxy=cfg.get('network_proxy', _sc.network_proxy),
        scan_dirs=cfg.get('scan_dirs', _sc.scan_dirs),
        chinese_cvt=int(cfg.get('chinese_cvt', _sc.chinese_cvt)),

    )

    CommonUtil.parse_rate_limits_from_conf(sc.rate_limits)

    return sc


"""



"""
