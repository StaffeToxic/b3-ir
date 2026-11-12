"""Allocation of note-level costs to operations (FR-002, research R3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal

from b3_ir.domain.models import Operation
from b3_ir.money import ZERO


def allocate_costs(operations: Sequence[Operation], total_costs: Decimal) -> list[Operation]:
    """Spread ``total_costs`` over ``operations`` proportionally to their gross value.

    Values stay exact (no rounding here); rounding happens only on final amounts.
    The allocated costs add up to ``total_costs`` exactly.
    """
    if total_costs < ZERO:
        raise ValueError(f"custos negativos: {total_costs}")
    if not operations:
        if total_costs != ZERO:
            raise ValueError("custos sem operações para ratear")
        return []
    gross_total = sum((op.gross_value for op in operations), ZERO)
    if gross_total == ZERO:
        raise ValueError("operações sem valor bruto para ratear custos")

    allocated: list[Operation] = []
    remaining = total_costs
    for index, op in enumerate(operations):
        if index == len(operations) - 1:
            share = remaining
        else:
            share = total_costs * op.gross_value / gross_total
            remaining -= share
        allocated.append(replace(op, costs=op.costs + share))
    return allocated
