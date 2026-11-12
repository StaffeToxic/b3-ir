"""Annual report as CSV files for spreadsheets (contracts/cli.md).

UTF-8 with BOM, ';' separator and decimal comma, so Excel in Portuguese opens the
files with the right columns and numbers.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from b3_ir.domain.models import AnnualReport, Category
from b3_ir.money import quantize_cents

FILES = (
    "bens_e_direitos.csv",
    "renda_variavel.csv",
    "rendimentos_isentos.csv",
    "tributacao_exclusiva.csv",
)


def _brl(value: Decimal) -> str:
    return f"{quantize_cents(value, 'half_up'):f}".replace(".", ",")


def _qty(value: Decimal) -> str:
    return f"{value.normalize():f}".replace(".", ",")


def _write(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_annual_csv(report: AnnualReport, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / name for name in FILES]
    _write(
        paths[0],
        [
            "ticker",
            "classe",
            "quantidade",
            f"situacao_{report.year - 1}",
            f"situacao_{report.year}",
        ],
        [
            [
                a.ticker,
                a.asset_class.value,
                _qty(a.quantity),
                _brl(a.cost_previous_year),
                _brl(a.cost),
            ]
            for a in report.assets
        ],
    )
    categories = list(Category)
    _write(
        paths[1],
        [
            "mes",
            *[c.value for c in categories],
            "isento",
            "prejuizo_comum",
            "prejuizo_day_trade",
            "prejuizo_fii",
            "irrf_deduzido",
            "imposto_devido",
            "darf",
        ],
        [
            [
                m.month,
                *[_brl(m.results[c]) for c in categories],
                _brl(m.exempt),
                *[_brl(m.loss_balances[k]) for k in ("comum", "day_trade", "fii")],
                _brl(m.irrf_used),
                _brl(m.tax_due),
                _brl(m.darf.amount) if m.darf else "",
            ]
            for m in report.monthly_table
        ],
    )
    _write(paths[2], ["tipo", "valor"], [[k, _brl(v)] for k, v in report.exempt_income.items()])
    _write(paths[3], ["tipo", "valor"], [[k, _brl(v)] for k, v in report.exclusive_income.items()])
    return paths
