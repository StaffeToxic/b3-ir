"""JSON output: Decimals as strings, dates as ISO 8601 (contracts/cli.md)."""

from __future__ import annotations

import dataclasses
import json
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, date):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(to_jsonable(k)): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(v) for v in value]
    return value


def dumps(value: Any) -> str:
    return json.dumps(to_jsonable(value), ensure_ascii=False, indent=2)
