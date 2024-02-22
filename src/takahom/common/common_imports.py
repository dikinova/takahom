AppVer = '0.6.0'

try:
    # 防止IDE自动删除 或者整理 import内容
    import io

    from dataclasses import dataclass
    import random
    import queue
    import itertools as ite

    import yaml
    from sortedcontainers import SortedDict  # type:ignore
    from dataclasses import field

    from urllib.parse import parse_qsl

    from dataclasses_json import dataclass_json

    from uuid import uuid4

    from pydantic import BaseModel

    from collections import deque
    import json
    from queue import Queue
    from typing import Deque, cast, Protocol, Sequence

    from urllib.parse import urlparse
    from urllib.parse import parse_qs, urlencode

    import html

    import functools
    # import schedule

    import numpy.typing as npt

    import numpy as np
    from typing import TypeAlias

    MyNDArrayInt64: TypeAlias = npt.NDArray[np.int64]
    MyNDArrayInt16: TypeAlias = npt.NDArray[np.int16]
    MyNDArrayInt8: TypeAlias = npt.NDArray[np.int8]
    MyNDArrayFloat64: TypeAlias = npt.NDArray[np.float64]
    MyNDArrayFloat32: TypeAlias = npt.NDArray[np.float32]

    from attr import define, field as afield, asdict

    from dknovautils import *
    from dknovautils import (
        AT,
        iprint_debug,
        iprint_info,
        iprint_warn,
        iprint,
        DkFile,
        join,
        List,
        Dict,
        Tuple,
        Set,
        Iterator,
        time,
        threading,
        Path,
        np,
        os,
        shutil,
        Any,
    )

    from dknovautils.dkprocess import DKProcessUtil

    run_simple_a = DKProcessUtil.run_simple_a
    run_simple_b = DKProcessUtil.run_simple_b

    from .common_ctts_ytb import *

finally:
    pass
