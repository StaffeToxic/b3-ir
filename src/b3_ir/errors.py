"""Exception hierarchy. Messages are user-facing, so they are in Portuguese."""

from __future__ import annotations


class B3IRError(Exception):
    """Base class for every error raised by b3-ir."""


class ParseError(B3IRError):
    """An input file could not be read or does not match a supported layout."""

    def __init__(self, file: str, detail: str) -> None:
        self.file = file
        self.detail = detail
        super().__init__(f"{file}: {detail}")


class UnsupportedOperationError(B3IRError):
    """An input item is outside the supported scope; refusing beats guessing."""

    def __init__(self, item: str, reason: str) -> None:
        self.item = item
        self.reason = reason
        super().__init__(f"não suportado: {item} ({reason})")
