"""End-to-end run of the CLI on examples/operacoes.csv with hand-computed results.

Hand calculation (candidate rules: 15% common, 20% day trade, R$ 20,000 exemption):
- Feb: ITSA4 avg (10,000 + 5) / 1,000 = 10.005; sell 400 @ 12: 4,800 - 2 - 4,002 = 796,
  sales 4,800 <= 20,000 -> exempt. IRRF 0.24 carried.
- Mar: PETR4 cost 60,010; sell 2,000 @ 28: 56,000 - 10 - 60,010 = -4,020 loss. IRRF 2.80.
- Apr: bonus 60 ITSA4 @ 5.00 -> 660 shares, cost 6,003 + 300 = 6,303 (avg 9.55).
- May: day trade PETR4: 31,500 - 5 - 31,005 = 490 -> 20% = 98.00; IRRF 0.24 + 2.80 + 3.15
  = 6.19 -> DARF 91.81, due Tue 2026-06-30. Common loss is not used by day trade.
- Jun: ITSA4 600 @ 14: 8,400 - 3 - 5,730 = 2,667 exempt (sales 8,400). BOVA11 (ETF, never
  exempt): 13,000 - 3 - 12,003 = 994, offset by the 4,020 loss -> loss left 3,026.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from b3_ir.cli import EXIT_INCOMPLETE, EXIT_OK, main

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "operacoes.csv"


def run_json(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict]:  # type: ignore[type-arg]
    code = main(["--sem-aviso", *args, "--formato", "json"])
    return code, json.loads(capsys.readouterr().out)


def test_monthly_report(capsys: pytest.CaptureFixture[str]) -> None:
    code, report = run_json(capsys, "mensal", str(EXAMPLE))
    assert code == EXIT_OK  # every rule used here is verified and no rounding happens
    months = {m["month"]: m for m in report["meses"]}
    assert list(months) == ["2026-02", "2026-03", "2026-05", "2026-06"]
    assert Decimal(months["2026-02"]["exempt"]) == Decimal("796")
    assert Decimal(months["2026-03"]["loss_balances"]["comum"]) == Decimal("4020")
    may = months["2026-05"]
    assert may["darf"] == {
        "code": "6015",
        "period": "2026-05",
        "due_date": "2026-06-30",
        "amount": "91.81",
    }
    jun = months["2026-06"]
    assert Decimal(jun["exempt"]) == Decimal("2667")
    assert Decimal(jun["loss_balances"]["comum"]) == Decimal("3026")
    assert jun["darf"] is None
    # June IRRF 0.42 + 0.65 is never used in 2026 and is reported, not carried.
    assert "saldo de IRRF de R$ 1.07" in jun["warnings"][-1]


def test_positions_report(capsys: pytest.CaptureFixture[str]) -> None:
    code, report = run_json(capsys, "posicoes", str(EXAMPLE), "--data", "2026-04-30")
    assert code == EXIT_OK
    positions = {p["ticker"]: p for p in report["posicoes"]}
    assert set(positions) == {"BOVA11", "ITSA4"}
    assert Decimal(positions["ITSA4"]["quantity"]) == Decimal("660")
    assert Decimal(positions["ITSA4"]["total_cost"]) == Decimal("6303")


def test_text_report_mentions_darf(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--sem-aviso", "mensal", str(EXAMPLE)])
    out = capsys.readouterr().out
    assert "DARF 6015: R$ 91,81" in out
    assert "vence 30/06/2026" in out


def test_pending_parsers_exit_incomplete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "nota.pdf").write_bytes(b"%PDF-1.4")
    code = main(["--sem-aviso", "posicoes", str(tmp_path)])
    assert code == EXIT_INCOMPLETE
    assert "ainda não implementada" in capsys.readouterr().err


def test_missing_input_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--sem-aviso", "posicoes", "nao-existe.csv"]) == 1
    assert "não encontrada" in capsys.readouterr().err
