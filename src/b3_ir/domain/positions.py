"""Average price engine and realized results (FR-007, research R3)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from b3_ir.domain.classify import require_classified
from b3_ir.domain.models import (
    AssetClass,
    CorporateEvent,
    EventKind,
    Operation,
    Position,
    Side,
    TradeType,
)
from b3_ir.errors import UnsupportedOperationError
from b3_ir.money import ZERO


@dataclass(frozen=True, slots=True)
class RealizedResult:
    """Net result of a swing sale or of one day's day-trade on a ticker."""

    date: date
    ticker: str
    asset_class: AssetClass
    trade_type: TradeType
    sale_value: Decimal  # gross sale value, used for the stock exemption test
    result: Decimal  # sale value - sale costs - cost basis
    irrf: Decimal


@dataclass
class PositionLedger:
    positions: dict[str, Position] = field(default_factory=dict)
    realized: list[RealizedResult] = field(default_factory=list)

    def open_positions(self) -> list[Position]:
        return sorted(
            (p for p in self.positions.values() if p.quantity > ZERO), key=lambda p: p.ticker
        )


def _event_rank(item: Operation | CorporateEvent) -> int:
    # Same day: corporate events and buys (credits) before sells (debits).
    if isinstance(item, CorporateEvent):
        return 0
    return 1 if item.side is Side.BUY else 2


def _apply_event(ledger: PositionLedger, event: CorporateEvent) -> None:
    current = ledger.positions.get(event.ticker)
    if current is None or current.quantity == ZERO:
        raise UnsupportedOperationError(
            f"{event.kind} {event.ticker} em {event.date}", "evento sem posição aberta"
        )
    quantity = current.quantity + event.quantity_delta
    if quantity <= ZERO:
        raise UnsupportedOperationError(
            f"{event.kind} {event.ticker} em {event.date}", "evento zeraria a posição"
        )
    total_cost = current.total_cost
    if event.kind is EventKind.BONUS:
        assert event.bonus_unit_cost is not None  # guaranteed by CorporateEvent
        total_cost += event.quantity_delta * event.bonus_unit_cost
    ledger.positions[event.ticker] = Position(
        event.ticker, current.asset_class, quantity, total_cost
    )


def _apply_swing(ledger: PositionLedger, op: Operation) -> None:
    assert op.asset_class is not None
    current = ledger.positions.get(op.ticker) or Position(op.ticker, op.asset_class, ZERO, ZERO)
    if op.side is Side.BUY:
        ledger.positions[op.ticker] = Position(
            op.ticker,
            op.asset_class,
            current.quantity + op.quantity,
            current.total_cost + op.gross_value + op.costs,
        )
        return
    if op.quantity > current.quantity:
        raise UnsupportedOperationError(
            f"venda de {op.quantity} {op.ticker} em {op.trade_date}",
            f"posição de apenas {current.quantity}; venda a descoberto ou nota faltando",
        )
    remaining = current.quantity - op.quantity
    # Selling keeps the average price. Selling everything takes the whole cost, so
    # repeating decimals in the average price never leave a residue.
    if remaining > ZERO:
        cost_basis = current.average_price * op.quantity
        remaining_cost = current.total_cost - cost_basis
    else:
        cost_basis = current.total_cost
        remaining_cost = ZERO
    ledger.positions[op.ticker] = Position(op.ticker, op.asset_class, remaining, remaining_cost)
    ledger.realized.append(
        RealizedResult(
            op.trade_date,
            op.ticker,
            op.asset_class,
            TradeType.SWING,
            op.gross_value,
            op.gross_value - op.costs - cost_basis,
            op.irrf,
        )
    )


def _day_trade_results(operations: Sequence[Operation]) -> list[RealizedResult]:
    groups: dict[tuple[date, str, str], list[Operation]] = defaultdict(list)
    for op in operations:
        if op.trade_type is TradeType.DAY:
            groups[(op.trade_date, op.ticker, op.broker or "")].append(op)
    results: list[RealizedResult] = []
    for (day, ticker, _broker), ops in sorted(groups.items()):
        sells = [op for op in ops if op.side is Side.SELL]
        buys = [op for op in ops if op.side is Side.BUY]
        sale_value = sum((op.gross_value for op in sells), ZERO)
        proceeds = sale_value - sum((op.costs for op in sells), ZERO)
        cost = sum((op.gross_value + op.costs for op in buys), ZERO)
        asset_class = ops[0].asset_class
        assert asset_class is not None
        results.append(
            RealizedResult(
                day,
                ticker,
                asset_class,
                TradeType.DAY,
                sale_value,
                proceeds - cost,
                sum((op.irrf for op in ops), ZERO),
            )
        )
    return results


def build_positions(
    operations: Sequence[Operation],
    events: Iterable[CorporateEvent] = (),
    until: date | None = None,
) -> PositionLedger:
    """Replay classified operations and corporate events in date order."""
    require_classified(operations)
    in_range_ops = [op for op in operations if until is None or op.trade_date <= until]
    timeline: list[Operation | CorporateEvent] = [
        op for op in in_range_ops if op.trade_type is TradeType.SWING
    ]
    timeline.extend(ev for ev in events if until is None or ev.date <= until)
    timeline.sort(
        key=lambda item: (
            item.date if isinstance(item, CorporateEvent) else item.trade_date,
            _event_rank(item),
        )
    )

    ledger = PositionLedger()
    for item in timeline:
        if isinstance(item, CorporateEvent):
            _apply_event(ledger, item)
        else:
            _apply_swing(ledger, item)
    ledger.realized.extend(_day_trade_results(in_range_ops))
    ledger.realized.sort(key=lambda r: (r.date, r.ticker, r.trade_type))
    return ledger
