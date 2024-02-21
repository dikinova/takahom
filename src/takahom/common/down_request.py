from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from dataclasses_json import dataclass_json
from dknovautils import AT

from .entity import YtbId, YtbItem
from .common_etc import AT2

_req_version = "0.2.2"


def _f_req_version() -> str:
    return f'DRQ-{_req_version}'


def _f_res_version() -> str:
    return f'DRS-{_req_version}'


@dataclass_json
@dataclass
class DownRequest:
    version: str = field(default_factory=_f_req_version)
    url: str = ""
    domain: str = ""
    resource_key: str = ""
    data_dir: str = ""
    uuid: str = ""
    start_epoch: float = 0
    rate_limit: int = 1000 * 1000
    ytb_resolution: int = 720
    ytb_format: str = ""
    ytb_ytbid: YtbId = field(default_factory=YtbId)
    cmd: str = ""
    proxy: str = ""
    no_download: bool = False  # 是否dry-run 并不真实的下载数据
    source: str = ""
    ytb_item: YtbItem = field(default_factory=YtbItem)
    line_no: int = 0

    def init(self) -> None:
        self.uuid = AT2.gen_uuid_str()

    def check(self) -> bool:
        AT.assert_(
            self.url and self.uuid and self.start_epoch >= 0,
            f"err40638 {self.to_json()}",  # type:ignore
        )
        AT.assert_(self.domain and self.resource_key, "err57667")
        AT.assert_(not self.ytb_item.is_empty(), "err78243")
        return True


class IDownRequest(Protocol):
    pass
