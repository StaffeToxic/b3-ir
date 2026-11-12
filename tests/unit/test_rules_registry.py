"""Constitution I: every rule has a source and is mirrored in docs/regras-fiscais.md."""

import itertools
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from b3_ir import rules
from b3_ir.errors import UnsupportedOperationError

DOCS = Path(__file__).resolve().parents[2] / "docs" / "regras-fiscais.md"


def all_rules() -> list[rules.Rule]:
    return [rule for versions in rules.RULES.values() for rule in versions]


@pytest.mark.parametrize("rule", all_rules(), ids=lambda r: r.id)
def test_every_rule_has_source_and_description(rule: rules.Rule) -> None:
    assert rule.source.strip()
    assert rule.description.strip()


@pytest.mark.parametrize("rule", all_rules(), ids=lambda r: r.id)
def test_every_rule_is_documented_with_its_status(rule: rules.Rule) -> None:
    row = next(
        (line for line in DOCS.read_text(encoding="utf-8").splitlines() if f"`{rule.id}`" in line),
        None,
    )
    assert row is not None, f"{rule.id} ausente em docs/regras-fiscais.md"
    status = "VERIFIED" if rule.verified else rules.UNVERIFIED
    assert row.rstrip(" |").endswith(status)


def test_versions_do_not_overlap() -> None:
    for versions in rules.RULES.values():
        ordered = sorted(versions, key=lambda r: r.valid_from)
        for earlier, later in itertools.pairwise(ordered):
            assert earlier.valid_to is not None
            assert earlier.valid_to < later.valid_from


def test_get_reports_verification_status() -> None:
    value, unverified = rules.decimal_rule("stock_swing_rate", date(2026, 5, 1))
    assert (value, unverified) == (Decimal("0.15"), False)
    assert rules.get("money_rounding", date(2026, 5, 1)).unverified is True


def test_get_refuses_dates_without_rule() -> None:
    with pytest.raises(UnsupportedOperationError):
        rules.get("stock_swing_rate", date(2000, 1, 1))


def test_get_unknown_rule() -> None:
    with pytest.raises(KeyError):
        rules.get("nope", date(2026, 1, 1))


def test_decimal_rule_rejects_text_rule() -> None:
    with pytest.raises(TypeError):
        rules.decimal_rule("darf_code_variable_income", date(2026, 1, 1))
