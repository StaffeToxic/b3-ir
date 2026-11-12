from dataclasses import replace
from datetime import date
from decimal import Decimal

from b3_ir.domain.models import Side
from b3_ir.parsers.dedup import deduplicate
from tests.unit.factories import op

D = date(2026, 3, 2)


def test_note_wins_over_statement_copy() -> None:
    note = op(D, "PETR4", Side.BUY, "100", "30.5", costs="1.20")
    copy = replace(note, costs=Decimal(0), broker="XP", source="extrato.xlsx#linha2")
    kept, report = deduplicate([note], [copy])
    assert kept == [note]
    assert "1 negócio" in report[0]


def test_repeated_trades_cancel_one_by_one() -> None:
    note = op(D, "PETR4", Side.BUY, "100", "30.5")
    statement = [note, note, op(D, "VALE3", Side.SELL, "1", "60")]
    kept, _ = deduplicate([note], statement)
    assert [(o.ticker, o.side) for o in kept] == [
        ("PETR4", Side.BUY),
        ("PETR4", Side.BUY),
        ("VALE3", Side.SELL),
    ]


def test_nothing_to_dedup() -> None:
    a = op(D, "PETR4", Side.BUY, "1", "1")
    kept, report = deduplicate([], [a])
    assert (kept, report) == ([a], [])
