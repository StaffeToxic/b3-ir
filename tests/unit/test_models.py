from datetime import date
from decimal import Decimal

import pytest

from b3_ir.domain.models import (
    AssetClass,
    CorporateEvent,
    EventKind,
    Operation,
    Position,
    Side,
)


def make_op(**overrides: object) -> Operation:
    fields: dict[str, object] = {
        "trade_date": date(2026, 3, 2),
        "settlement_date": date(2026, 3, 4),
        "ticker": "PETR4",
        "side": Side.BUY,
        "quantity": Decimal("100"),
        "unit_price": Decimal("35.10"),
        "costs": Decimal("1.05"),
        "irrf": Decimal("0"),
        "source": "nota-1.pdf#1",
    }
    fields.update(overrides)
    return Operation(**fields)  # type: ignore[arg-type]


def test_operation_gross_value() -> None:
    assert make_op().gross_value == Decimal("3510.00")


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": Decimal("0")},
        {"unit_price": Decimal("-1")},
        {"costs": Decimal("-0.01")},
        {"ticker": "petr4"},
        {"ticker": ""},
        {"settlement_date": date(2026, 3, 1)},
    ],
)
def test_operation_rejects_invalid(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        make_op(**overrides)


def test_operation_rejects_float() -> None:
    with pytest.raises(TypeError):
        make_op(unit_price=35.1)


def test_position_average_price() -> None:
    pos = Position("ITSA4", AssetClass.STOCK, Decimal("200"), Decimal("2010.00"))
    assert pos.average_price == Decimal("10.05")
    assert Position("ITSA4", AssetClass.STOCK, Decimal("0"), Decimal("0")).average_price == 0


def test_bonus_requires_cost() -> None:
    with pytest.raises(ValueError, match="custo"):
        CorporateEvent(date(2026, 1, 5), "ITSA4", EventKind.BONUS, Decimal("10"), None, "x")


def test_event_requires_nonzero_delta() -> None:
    with pytest.raises(ValueError, match="sem variação"):
        CorporateEvent(date(2026, 1, 5), "ITSA4", EventKind.SPLIT, Decimal("0"), None, "x")


@pytest.mark.parametrize(
    ("kind", "delta"),
    [
        (EventKind.SPLIT, Decimal("-100")),
        (EventKind.REVERSE_SPLIT, Decimal("100")),
    ],
)
def test_event_delta_sign_matches_kind(kind: EventKind, delta: Decimal) -> None:
    with pytest.raises(ValueError, match="sinal"):
        CorporateEvent(date(2026, 1, 5), "ITSA4", kind, delta, None, "x")
