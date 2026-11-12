from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import pytest

from b3_ir.domain.classify import classify
from b3_ir.domain.models import CorporateEvent, EventKind, Operation, Side, TradeType
from b3_ir.domain.positions import PositionLedger, build_positions
from b3_ir.errors import UnsupportedOperationError
from tests.unit.factories import op


def ledger_for(ops: Sequence[Operation], events: Sequence[CorporateEvent] = ()) -> PositionLedger:
    classified, _ = classify(ops)
    return build_positions(classified, events)


def event(
    day: date, ticker: str, kind: EventKind, delta: str, cost: str | None = None
) -> CorporateEvent:
    return CorporateEvent(day, ticker, kind, Decimal(delta), Decimal(cost) if cost else None, "x")


def test_weighted_average_includes_costs() -> None:
    # 100 @ 10 + 5 costs = 1005; 100 @ 12 + 5 costs = 1205 -> 200 shares, cost 2210, avg 11.05
    ledger = ledger_for(
        [
            op(date(2026, 1, 5), "ITSA4", Side.BUY, "100", "10", costs="5"),
            op(date(2026, 1, 6), "ITSA4", Side.BUY, "100", "12", costs="5"),
        ]
    )
    pos = ledger.positions["ITSA4"]
    assert (pos.quantity, pos.total_cost, pos.average_price) == (
        Decimal("200"),
        Decimal("2210"),
        Decimal("11.05"),
    )


def test_sale_keeps_average_and_realizes_result() -> None:
    # avg 11.05; sell 50 @ 13 with 2 costs: 650 - 2 - 552.50 = 95.50
    ledger = ledger_for(
        [
            op(date(2026, 1, 5), "ITSA4", Side.BUY, "100", "10", costs="5"),
            op(date(2026, 1, 6), "ITSA4", Side.BUY, "100", "12", costs="5"),
            op(date(2026, 2, 2), "ITSA4", Side.SELL, "50", "13", costs="2"),
        ]
    )
    pos = ledger.positions["ITSA4"]
    assert pos.average_price == Decimal("11.05")
    assert pos.quantity == Decimal("150")
    (realized,) = ledger.realized
    assert (realized.trade_type, realized.sale_value, realized.result) == (
        TradeType.SWING,
        Decimal("650"),
        Decimal("95.50"),
    )


def test_selling_everything_zeroes_cost() -> None:
    # cost 30.01, sale 27 -> -3.01
    ledger = ledger_for(
        [
            op(date(2026, 1, 5), "WEGE3", Side.BUY, "3", "10", costs="0.01"),
            op(date(2026, 1, 6), "WEGE3", Side.SELL, "3", "9"),
        ]
    )
    assert ledger.positions["WEGE3"].total_cost == 0
    assert ledger.open_positions() == []
    assert ledger.realized[0].result == Decimal("-3.01")


def test_split_preserves_cost_and_reverse_split_too() -> None:
    # 100 @ 20 = 2000; split credits 100 -> 200 @ 10; reverse split debits 150 -> 50 @ 40
    ledger = ledger_for(
        [op(date(2026, 1, 5), "MGLU3", Side.BUY, "100", "20")],
        [
            event(date(2026, 2, 1), "MGLU3", EventKind.SPLIT, "100"),
            event(date(2026, 3, 1), "MGLU3", EventKind.REVERSE_SPLIT, "-150"),
        ],
    )
    pos = ledger.positions["MGLU3"]
    assert (pos.quantity, pos.total_cost, pos.average_price) == (
        Decimal("50"),
        Decimal("2000"),
        Decimal("40"),
    )


def test_bonus_adds_attributed_cost() -> None:
    # 100 @ 10 = 1000; bonus 10 shares at 5.00 -> 110 shares, cost 1050
    ledger = ledger_for(
        [op(date(2026, 1, 5), "ITSA4", Side.BUY, "100", "10")],
        [event(date(2026, 4, 1), "ITSA4", EventKind.BONUS, "10", "5")],
    )
    pos = ledger.positions["ITSA4"]
    assert (pos.quantity, pos.total_cost) == (Decimal("110"), Decimal("1050"))


def test_event_on_same_day_applies_before_sale() -> None:
    # avg after split 10; 200 * 11 - 2000 = 200
    ledger = ledger_for(
        [
            op(date(2026, 1, 5), "MGLU3", Side.BUY, "100", "20"),
            op(date(2026, 2, 1), "MGLU3", Side.SELL, "200", "11"),
        ],
        [event(date(2026, 2, 1), "MGLU3", EventKind.SPLIT, "100")],
    )
    assert ledger.realized[0].result == Decimal("200")


def test_oversold_is_refused() -> None:
    with pytest.raises(UnsupportedOperationError, match="descoberto"):
        ledger_for(
            [
                op(date(2026, 1, 5), "PETR4", Side.BUY, "10", "30"),
                op(date(2026, 1, 6), "PETR4", Side.SELL, "11", "31"),
            ]
        )


def test_event_without_position_is_refused() -> None:
    with pytest.raises(UnsupportedOperationError, match="sem posição"):
        ledger_for([], [event(date(2026, 1, 1), "PETR4", EventKind.SPLIT, "1")])


def test_day_trade_result_does_not_touch_position() -> None:
    # Buy 100 @ 10 (1 cost), sell 100 @ 10.50 (1 cost) same day: 1050 - 1 - 1001 = 48
    ledger = ledger_for(
        [
            op(date(2026, 3, 2), "PETR4", Side.BUY, "100", "10", costs="1"),
            op(date(2026, 3, 2), "PETR4", Side.SELL, "100", "10.50", costs="1", irrf="0.48"),
        ]
    )
    assert ledger.open_positions() == []
    (realized,) = ledger.realized
    assert (realized.trade_type, realized.result, realized.irrf) == (
        TradeType.DAY,
        Decimal("48.00"),
        Decimal("0.48"),
    )


def test_until_filters_later_operations() -> None:
    classified, _ = classify(
        [
            op(date(2026, 1, 5), "PETR4", Side.BUY, "10", "30"),
            op(date(2026, 6, 5), "PETR4", Side.BUY, "10", "40"),
        ]
    )
    ledger = build_positions(classified, until=date(2026, 3, 31))
    assert ledger.positions["PETR4"].quantity == Decimal("10")
