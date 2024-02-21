from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from dataclasses_json import dataclass_json

from takahom.common.down_result import DownResult


@dataclass_json
@dataclass
class DLServerIndex:
    fid: int = 0
    rid: int = 0
    results: List[DownResult] = field(default_factory=list)
