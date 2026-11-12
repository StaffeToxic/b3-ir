"""Manual CSV of operations and corporate events (FR-015, contracts/cli.md)."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from b3_ir.domain.models import CorporateEvent, EventKind, Operation, Side
from b3_ir.errors import ParseError
from b3_ir.money import ZERO, parse_brl, to_decimal

REQUIRED_COLUMNS = ("data", "tipo", "ticker", "quantidade")
SETTLEMENT_DAYS = 2

_SIDES = {"compra": Side.BUY, "venda": Side.SELL}
_EVENTS = {
    "desdobramento": EventKind.SPLIT,
    "grupamento": EventKind.REVERSE_SPLIT,
    "bonificacao": EventKind.BONUS,
    "bonificação": EventKind.BONUS,
}


@dataclass
class CsvParseResult:
    operations: list[Operation] = field(default_factory=list)
    events: list[CorporateEvent] = field(default_factory=list)


def _number(text: str | None, default: Decimal | None = None) -> Decimal:
    raw = (text or "").strip()
    if not raw:
        if default is None:
            raise ValueError("valor obrigatório vazio")
        return default
    return parse_brl(raw) if "," in raw else to_decimal(raw)


def _date(text: str) -> date:
    raw = text.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()  # noqa: DTZ007 - dates only
        except ValueError:
            continue
    raise ValueError(f"data inválida: {raw!r}")


def parse_operations_csv(path: Path) -> CsvParseResult:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    delimiter = ";" if lines and ";" in lines[0] else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    columns = {(name or "").strip().lower() for name in reader.fieldnames or []}
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise ParseError(path.name, f"colunas ausentes: {', '.join(missing)}")

    result = CsvParseResult()
    for line_no, raw_row in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw_row.items()}
        if not any(row.values()):
            continue
        source = f"{path.name}#linha{line_no}"
        try:
            _parse_row(row, source, result)
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ParseError(path.name, f"linha {line_no}: {exc}") from exc
    return result


def _parse_row(row: dict[str, str], source: str, result: CsvParseResult) -> None:
    kind = row["tipo"].lower()
    day = _date(row["data"])
    ticker = row["ticker"].upper()
    quantity = _number(row["quantidade"])
    if kind in _SIDES:
        result.operations.append(
            Operation(
                trade_date=day,
                settlement_date=day + timedelta(days=SETTLEMENT_DAYS),
                ticker=ticker,
                side=_SIDES[kind],
                quantity=quantity,
                unit_price=_number(row.get("preco")),
                costs=_number(row.get("custos"), ZERO),
                irrf=_number(row.get("irrf"), ZERO),
                source=source,
            )
        )
    elif kind in _EVENTS:
        event_kind = _EVENTS[kind]
        delta = -quantity if event_kind is EventKind.REVERSE_SPLIT else quantity
        bonus_cost = _number(row.get("preco")) if event_kind is EventKind.BONUS else None
        result.events.append(CorporateEvent(day, ticker, event_kind, delta, bonus_cost, source))
    else:
        raise ValueError(f"tipo desconhecido: {row['tipo']!r}")
