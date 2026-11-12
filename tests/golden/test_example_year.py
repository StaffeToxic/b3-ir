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
    assert "saldo de IRRF de R$ 1,07" in jun["warnings"][-1]


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


def test_unreadable_files_exit_incomplete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "extrato.xlsx").write_bytes(b"PK")
    (tmp_path / "quebrada.pdf").write_bytes(b"nao e pdf")
    code = main(["--sem-aviso", "posicoes", str(tmp_path)])
    assert code == EXIT_INCOMPLETE
    err = capsys.readouterr().err
    assert "extrato.xlsx" in err
    assert "quebrada.pdf" in err


def test_missing_input_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--sem-aviso", "posicoes", "nao-existe.csv"]) == 1
    assert "não encontrada" in capsys.readouterr().err


def test_statement_trades_are_deduplicated_against_notes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from openpyxl import Workbook

    (tmp_path / "operacoes.csv").write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(
        ["Data do Negócio", "Tipo de Movimentação", "Mercado", "Instituição",
         "Código de Negociação", "Quantidade", "Preço"]
    )  # fmt: skip
    # Same trade as the CSV's first line (dropped) and a new one (kept, zero costs).
    sheet.append(["05/01/2026", "Compra", "Mercado à Vista", "XP", "ITSA4", 1000, "10,00"])
    sheet.append(["07/01/2026", "Compra", "Mercado à Vista", "XP", "WEGE3", 10, "40,00"])
    workbook.save(tmp_path / "negociacao.xlsx")

    code, report = run_json(capsys, "posicoes", str(tmp_path), "--data", "2026-01-31")
    positions = {p["ticker"]: p for p in report["posicoes"]}
    assert Decimal(positions["ITSA4"]["quantity"]) == Decimal("1000")
    assert Decimal(positions["WEGE3"]["total_cost"]) == Decimal("400")
    assert any("já estavam nas notas" in w for w in report["avisos"])
    assert code == EXIT_OK


def test_annual_report_for_example_year(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # 31/12/2026: ITSA4 660 - 600 = 60 shares at avg 9.55 = 573.00; BOVA11 and PETR4 closed.
    # Exempt stock gains: Feb 796 + Jun 2,667 = 3,463.
    code, report = run_json(capsys, "anual", str(EXAMPLE), "--ano", "2026")
    assert code == EXIT_OK
    assets = {a["ticker"]: a for a in report["assets"]}
    # BOVA11 and PETR4 were bought and sold within 2026: held on neither 31/12, so they
    # are not "Bens e Direitos" lines (their results are in the monthly table).
    assert set(assets) == {"ITSA4"}
    assert Decimal(assets["ITSA4"]["cost"]) == Decimal("573")
    assert Decimal(report["exempt_income"]["ganhos_acoes_ate_20_mil"]) == Decimal("3463")

    main(["--sem-aviso", "anual", str(EXAMPLE), "--ano", "2026"])
    out = capsys.readouterr().out
    assert "ITSA4: 60 ações, preço médio R$ 9,55" in out
    assert "R$ 3.463,00" in out

    main(["--sem-aviso", "anual", str(EXAMPLE), "--ano", "2026", "--formato", "csv",
          "--saida", str(tmp_path)])  # fmt: skip
    rows = (tmp_path / "renda_variavel.csv").read_text(encoding="utf-8-sig").splitlines()
    assert rows[0].startswith("mes;acoes_comum;acoes_day_trade")
    assert rows[3].startswith("2026-05;0,00;490,00")
    assert rows[3].endswith(";91,81")


def test_csv_format_requires_output_folder(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--sem-aviso", "anual", str(EXAMPLE), "--ano", "2026", "--formato", "csv"]) == 1
    assert "--saida" in capsys.readouterr().err
