"""Asset class and day-trade classification (FR-005, FR-006)."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal

from b3_ir.domain.models import AssetClass, Operation, Side, TradeType
from b3_ir.errors import UnsupportedOperationError
from b3_ir.money import ZERO

# Tickers ending in 11 can be FIIs, ETFs or stock units. Known ETFs and units are
# listed here; any other *11 ticker is treated as FII with a warning, and the user
# can override it. Offline source to replace this list: research R4.
KNOWN_ETFS = frozenset(
    {
        "BOVA11", "BOVV11", "BRAX11", "DIVO11", "ECOO11", "FIND11", "GOLD11", "GOVE11",
        "HASH11", "IVVB11", "MATB11", "NASD11", "PIBB11", "SMAL11", "SPXI11", "WRLD11",
        "XINA11",
    }
)  # fmt: skip
KNOWN_UNITS = frozenset(
    {
        "ALUP11", "BPAC11", "BRBI11", "ENGI11", "IGTI11", "KLBN11", "SANB11", "SAPR11",
        "TAEE11",
    }
)  # fmt: skip

_STOCK = re.compile(r"^[A-Z]{4}([3-8])$")
_ELEVEN = re.compile(r"^[A-Z]{4}11$")


def asset_class_of(
    ticker: str, overrides: Mapping[str, AssetClass] | None = None
) -> tuple[AssetClass, str | None]:
    """Return the asset class and, when it came from a heuristic, a warning."""
    if overrides and ticker in overrides:
        return overrides[ticker], None
    if _STOCK.match(ticker) or ticker in KNOWN_UNITS:
        return AssetClass.STOCK, None
    if ticker in KNOWN_ETFS:
        return AssetClass.ETF, None
    if _ELEVEN.match(ticker):
        return AssetClass.FII, f"{ticker} classificado como FII por heurística; confirme"
    raise UnsupportedOperationError(ticker, "classe de ativo fora do escopo (ações, FIIs, ETFs)")


def _split(op: Operation, day_qty: Decimal) -> list[Operation]:
    """Split ``op`` into a day-trade slice of ``day_qty`` and a swing slice with the rest.

    Costs and IRRF are scaled multiplying before dividing, and the swing slice takes
    the exact remainder, so the slices always add up to the original operation.
    """
    if day_qty == op.quantity:
        return [replace(op, trade_type=TradeType.DAY)]
    if day_qty == ZERO:
        return [replace(op, trade_type=TradeType.SWING)]
    day_costs = op.costs * day_qty / op.quantity
    day_irrf = op.irrf * day_qty / op.quantity
    return [
        replace(op, quantity=day_qty, costs=day_costs, irrf=day_irrf, trade_type=TradeType.DAY),
        replace(
            op,
            quantity=op.quantity - day_qty,
            costs=op.costs - day_costs,
            irrf=op.irrf - day_irrf,
            trade_type=TradeType.SWING,
        ),
    ]


def _split_day(ops: list[Operation]) -> list[Operation]:
    """Split one ticker's operations of one day into day-trade and swing slices.

    The matched quantity is min(bought, sold); it is taken from buys and sells in
    the order they appear, the rest is swing trade (research R1).
    """
    bought = sum((op.quantity for op in ops if op.side is Side.BUY), ZERO)
    sold = sum((op.quantity for op in ops if op.side is Side.SELL), ZERO)
    matched = min(bought, sold)
    left = {Side.BUY: matched, Side.SELL: matched}
    result: list[Operation] = []
    for op in ops:
        day_qty = min(op.quantity, left[op.side])
        left[op.side] -= day_qty
        result.extend(_split(op, day_qty))
    return result


def classify(
    operations: Iterable[Operation], overrides: Mapping[str, AssetClass] | None = None
) -> tuple[list[Operation], list[str]]:
    """Fill asset_class and trade_type.

    Returns the operations grouped by (day, ticker) in order of first appearance,
    with day-trade and swing slices split, plus classification warnings.
    """
    warnings: list[str] = []
    seen_warnings: set[str] = set()
    groups: dict[tuple[date, str], list[Operation]] = defaultdict(list)
    order: list[tuple[date, str]] = []
    for op in operations:
        asset_class, warning = asset_class_of(op.ticker, overrides)
        if warning and warning not in seen_warnings:
            seen_warnings.add(warning)
            warnings.append(warning)
        key = (op.trade_date, op.ticker)
        if key not in groups:
            order.append(key)
        groups[key].append(replace(op, asset_class=asset_class))

    classified: list[Operation] = []
    for key in order:
        classified.extend(_split_day(groups[key]))
    return classified, warnings


def require_classified(operations: Sequence[Operation]) -> None:
    for op in operations:
        if op.asset_class is None or op.trade_type is None:
            raise ValueError(f"operação não classificada: {op.ticker} em {op.trade_date}")
