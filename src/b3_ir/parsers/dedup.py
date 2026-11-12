"""Cross-source deduplication of trades (FR-004).

A trade can appear in a brokerage note (with costs and IRRF) and again in the B3
trading statement (without them). The note wins; the statement copy is dropped.
Matching is by (trade date, ticker, side, quantity, unit price), counting repeats,
so two identical trades in the note cancel two in the statement, not all of them.
The broker is not part of the key: notes take it from the folder name and the
statement from its own "Instituição" column, which need not be spelled the same.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from b3_ir.domain.models import Operation, Side

TradeKey = tuple[date, str, Side, Decimal, Decimal]


def trade_key(op: Operation) -> TradeKey:
    return (op.trade_date, op.ticker, op.side, op.quantity, op.unit_price)


def deduplicate(
    primary: Sequence[Operation], statement: Sequence[Operation]
) -> tuple[list[Operation], list[str]]:
    """Return primary + statement trades not already in primary, and a report."""
    available = Counter(trade_key(op) for op in primary)
    kept: list[Operation] = list(primary)
    dropped = 0
    for op in statement:
        key = trade_key(op)
        if available[key] > 0:
            available[key] -= 1
            dropped += 1
        else:
            kept.append(op)
    report = (
        [f"{dropped} negócio(s) do extrato da B3 já estavam nas notas e foram ignorados"]
        if dropped
        else []
    )
    return kept, report
