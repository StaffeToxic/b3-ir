from datetime import date
from decimal import Decimal

import pytest

from b3_ir.domain.costs import allocate_costs
from b3_ir.domain.models import Side
from tests.unit.factories import op

D = date(2026, 3, 2)


def test_costs_split_proportionally_to_gross_value() -> None:
    # Gross 3000 and 1000 -> costs 10.00 split 7.50 / 2.50
    ops = [op(D, "PETR4", Side.BUY, "100", "30"), op(D, "VALE3", Side.BUY, "10", "100")]
    allocated = allocate_costs(ops, Decimal("10.00"))
    assert [a.costs for a in allocated] == [Decimal("7.5"), Decimal("2.50")]


def test_allocated_costs_add_up_exactly() -> None:
    # Three equal operations and 10.00: thirds do not terminate, the last takes the rest.
    ops = [op(D, t, Side.BUY, "1", "10") for t in ("AAAA3", "BBBB3", "CCCC3")]
    allocated = allocate_costs(ops, Decimal("10.00"))
    assert sum(a.costs for a in allocated) == Decimal("10.00")


def test_empty_note_with_costs_is_an_error() -> None:
    with pytest.raises(ValueError, match="sem operações"):
        allocate_costs([], Decimal("1"))
    assert allocate_costs([], Decimal("0")) == []


def test_negative_costs_are_rejected() -> None:
    with pytest.raises(ValueError, match="negativos"):
        allocate_costs([op(D, "PETR4", Side.BUY, "1", "1")], Decimal("-1"))
