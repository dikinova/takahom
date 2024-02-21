from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from dataclasses_json import dataclass_json
from dknovautils import AT

from .common_util import CommonUtil
from .common_ctts_ytb import ytb_reg_simple_code11, ytb_reg_simple_id_all, YtbConf


@dataclass_json
@dataclass(eq=True, frozen=True, slots=True)
class YtbId:
    prefix: str = ''  # ytbid
    id_original: str = ''
    myid: str = ''

    def to_str_with_prefix(self) -> str:
        assert self.prefix in YtbConf.IdPrefixList
        assert re.fullmatch(ytb_reg_simple_id_all, self.id_original), 'err44685'
        assert self.prefix and self.id_original and len(self.myid) >= 11, "err92422"
        return f"{self.prefix}-{self.myid}"

    @staticmethod
    def build_from_vstr(vs: str) -> YtbId | None:
        from takahom.common.ytb_util import YtbUtil

        try:
            # 注意 myid中可能包含-符号
            dc = CommonUtil.parse_filename_dict(vs)
            assert len(dc) == 1
            k = list(dc)[0]
            myid = dc[k]
            assert k in YtbConf.IdPrefixList
            r = YtbId(prefix=k, myid=myid, id_original=YtbUtil.ytb_myid_to_original(myid))
            r.to_str_with_prefix()
            return r
        except Exception as e:
            return None


class IYtbItem(Protocol):
    """
    v list两者只有一个非空

    """

    @property
    def para_vcode(self) -> str | None:
        pass

    @property
    def para_list(self) -> str | None:
        pass

    @property
    def para_short(self) -> str | None:
        pass

    def get_url(self) -> str:
        pass

    def has_vcode(self) -> bool:
        return bool(self.para_vcode)

    def has_list(self) -> bool:
        return bool(self.para_list)

    def has_short(self) -> bool:
        return bool(self.para_short)

    @property
    def para_value(self) -> str:
        """哪个有值就返回哪个"""
        if v := self.para_vcode:
            r = v
        elif v := self.para_list:
            r = v
        elif v := self.para_short:
            r = v
        assert r
        return r

    def para_value_to_ytbid(self) -> YtbId:
        from takahom.common import ytb_util
        id: str = self.para_value
        myid = ytb_util.YtbUtil.ytb_original_to_myid(id)
        prefix = 'ytbid' if self.has_vcode() else 'ytbih' if self.has_short() else 'ytbip'
        return YtbId(myid=myid, prefix=prefix, id_original=id)


@dataclass_json
@dataclass(eq=True, frozen=True, slots=True)
class YtbItem(IYtbItem):
    url: str = ""  # 两个url url_originl可能是不同的。 url可能重组过后的 两者很可能存在差异
    vcode: str | None = None
    playlist: str | None = None
    short: str | None = None
    netloc: str = ""
    url_original: str = ""

    @property
    def para_vcode(self) -> str | None:
        return self.vcode

    @property
    def para_list(self) -> str | None:
        return self.playlist

    @property
    def para_short(self) -> str | None:
        return self.short

    def get_url(self) -> str:
        return self.url

    def is_empty(self) -> bool:
        return self.url == ""
