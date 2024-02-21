from __future__ import annotations

import hashlib
import itertools as ite
import os
import shutil
from os.path import join
from pathlib import Path
from typing import Iterator, Tuple, Callable, Any, Iterable
from uuid import uuid4

import yaml
from dknovautils import classproperty, AT, DkFile, iprint, iprint_warn, LLevel, run_simple_a
from pyrate_limiter import Limiter, Rate, Duration


def eat_for(ps: Iterable[Any]) -> None:
    for p in ps:
        pass


class AT2:
    _profile_prod = "prod"
    _profile_test = "test"
    _profile_dev = "dev"
    _profiles_list = [_profile_prod, _profile_test, _profile_dev]

    _app_profile: str = ""

    @classproperty
    def app_profile(cls) -> str:
        AT.assert_(cls._app_profile in cls._profiles_list, 'err46501 bad app profile')
        return cls._app_profile

    @classmethod
    def is_profile_prod(cls) -> bool:
        return bool(cls._profile_prod == cls.app_profile)

    @classmethod
    def is_profile_dev(cls) -> bool:
        return bool(cls._profile_dev == cls.app_profile)

    @classmethod
    def is_profile_test(cls) -> bool:
        return bool(cls._profile_test == cls.app_profile)

    @staticmethod
    def _dummy_drop_fun(s: Any) -> None:
        return None

    @classmethod
    def tprint_fun(cls, verbose: bool = True,
                   use_print: bool = False) -> Callable[[Any], None]:

        if not verbose:
            return cls._dummy_drop_fun
        else:
            # 这两个函数可以抽离成2个静态函数 不需要创建变量
            def fn(msg: str) -> None:
                if not use_print:
                    iprint(msg, level=LLevel.Debug)
                else:
                    print(msg)

            return fn

    @classmethod
    def gen_uuid_str(cls) -> str:
        r = uuid4()
        r = str(r)
        return r

    @classmethod
    def md5_hex(cls, bs: bytes) -> str:
        md5 = hashlib.md5()
        md5.update(bs)
        r = md5.hexdigest().lower()
        AT.assert_(len(r) == 32)
        return r

    @classmethod
    def file_md5_hex(cls, file_path: str | Path) -> str:
        """
        计算文件的md5
        :param file_name:
        :return:

        https://www.cnblogs.com/xiaodekaixin/p/11203857.html

        """
        m = hashlib.md5()  # 创建md5对象
        with open(file_path, "rb") as fobj:
            while True:
                data = fobj.read(4096)
                if not data:
                    break
                m.update(data)  # 更新md5对象

        return m.hexdigest().lower()  # 返回md5对象

    @classmethod
    def init_logging_v1(cls, conf_dir: DkFile, *, log_dir: DkFile | None = None) -> None:
        """

        conf_dir 配置文件目录 必须存在
            logging_$profile.yaml

        log_dir 日志文件目录 会自动创建
            可以用特殊字符来替换配置文件中的目录 将 _LOGDIR_ 替换为 日志目录

    可以调用 init_logging_v1 进行初始化
        将读取yaml配置文件进行初始化
        将设置 _innerLoggerFun_ 用来作为 iprint的执行函数
        """
        AT.assert_(conf_dir.is_dir() and conf_dir.exists(), 'err69053')

        LOGDIR = 'logs/'
        AT.assert_(AT2.app_profile, 'err21738 bad profile')
        conf_file = DkFile(join(conf_dir.pathstr, f'logging_{AT2.app_profile}.yaml'))
        cstr = conf_file.path.read_text()
        iprint(f'logging conf_file: {conf_file} len:{len(cstr)}')
        if log_dir:
            AT.assert_(LOGDIR in cstr, f'err12912 cannot find {LOGDIR} in yaml ')
            cstr = cstr.replace(LOGDIR, log_dir.pathstr + '/')
            os.makedirs(log_dir.path, exist_ok=True)
        conf = yaml.safe_load(cstr)
        import logging.config as log_config
        log_config.dictConfig(conf)
        AT.log_loggerFun(initInnerLoggerFun=True)

    @classmethod
    def ln_filter(cls, lns: Iterable[str], map_opt: Callable[[str], str | None]) -> Iterator[str]:
        # 返回的是 optional 这是大象符号引入之后 更方便的形式
        for ln in lns:
            r = map_opt(ln.strip())
            if r is not None:
                yield r
            else:
                continue

    @classmethod
    def ln_filter_startswith(cls, lns: Iterable[str], stt: Tuple[str, ...]) -> Iterator[str]:
        return cls.ln_filter(lns, map_opt=lambda ln: ln if any(ln.startswith(e) for e in stt) else None)

    @classmethod
    def ln_filter_not_startswith(cls, lns: Iterable[str], stt: Tuple[str, ...]) -> Iterator[str]:
        return cls.ln_filter(lns, map_opt=lambda ln: ln if not any(ln.startswith(e) for e in stt) else None)


class DkFile2:

    @staticmethod
    def clear_dir(tmp_dir: DkFile) -> None:
        # 清空tmp目录
        if AT.is_windows:
            shutil.rmtree(tmp_dir.pathstr)
            os.mkdir(tmp_dir.pathstr)
        else:
            run_simple_a(f'rm -rf "{tmp_dir.pathstr}"/* ')

    @classmethod
    def count_sub_folders(cls, pdir: DkFile) -> int:
        """计算子目录的个数 深度遍历"""
        ia = sum(1 for dkf in cls.oswalk_simple_a(topdir=pdir, include_self=False) if dkf.is_dir())
        return ia

    @classmethod
    def oswalk_simple_a(cls,
                        topdir: DkFile,
                        topdown: bool = True,
                        only_file: bool = False,
                        followlinks: bool = False,
                        include_self: bool = True,
                        ) -> Iterator[DkFile]:
        assert topdir.is_dir(), 'err76794 not dir'
        i = 0
        for _i, (root, dirs, files) in enumerate(os.walk(topdir.path, topdown=topdown, followlinks=followlinks)):
            for d in ite.chain(dirs, files):
                # assert isinstance(d, str) and isinstance(root, Path), f'{d} {root}'
                dkf = DkFile(join(root, d))
                if False:
                    AT.never()
                elif only_file and not dkf.is_file():
                    continue
                elif not include_self and dkf.is_dir() and dkf.path == topdir.path:
                    continue
                else:
                    yield dkf
                    i += 1

    @classmethod
    def join_path(cls, dkf: DkFile, filename: str | Path) -> DkFile:
        return DkFile(join(dkf.path, filename))

    @classmethod
    def basename_part_without_extension(cls, pa: Path) -> str:
        """this includes the leading period"""
        file_extension = pa.suffix
        basename = os.path.basename(pa)
        if file_extension:
            return basename[:-len(file_extension)]
        else:
            return basename


def limit_memory(maxsize: int) -> None:
    # import resource
    # soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    # resource.setrlimit(resource.RLIMIT_AS, (maxsize, hard))
    pass


def f_simple_limiter(vlmt: int) -> Tuple[Limiter, int]:
    """
    v 每秒网速限制 byte 1kb/s = 1000
    因为tksize=v/10 而且一般情况 tksize一般不能太大 比如 不要超过1M
    """
    assert vlmt >= 1000, f"err41849 bad v. vlmt >=1000 "

    def f_n() -> int:
        # 防止 tksize太大 不便于流量控制的效果
        n: float = 10.0
        while True:
            tks = vlmt / n
            if tks < 1000 * 100:
                assert n >= 10
                return int(n)
            else:
                n *= 1.2

    kn = f_n()
    tksize = int(vlmt / kn)
    rate = Rate(kn, Duration.SECOND * 1)
    limiter = Limiter(rate, raise_when_fail=False, max_delay=Duration.SECOND * 10)
    return limiter, tksize
