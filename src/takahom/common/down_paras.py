from __future__ import annotations

from dataclasses import dataclass

from .common_etc import AT2


@dataclass
class DownloadParas:
    """
    该类后续会废弃

    """
    epoch: int = 0  # epoch ms
    salt: int = 0
    fid: int = 0
    hash: str = ""

    def join_str(self) -> str:
        sa = f"epoch={self.epoch}&salt={self.salt}&fid={self.fid}"
        if self.hash:
            sa += f"&hash={self.hash}"
        return sa

    def gen_hash(self, secret: str) -> None:
        def _h(s: str) -> str:
            return AT2.md5_hex(bytes(s, "utf-8"))

        self.hash = ""
        self.hash = _h(_h(self.join_str()) + secret)[:6]
