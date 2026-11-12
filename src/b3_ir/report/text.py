"""Human-readable reports in Portuguese."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from b3_ir.domain.models import AnnualReport, Category, MonthlyAssessment, Position
from b3_ir.money import quantize_cents

_CATEGORY_LABELS = {
    Category.STOCK_SWING: "Ações (comum)",
    Category.STOCK_DAY: "Ações (day trade)",
    Category.ETF_SWING: "ETFs (comum)",
    Category.ETF_DAY: "ETFs (day trade)",
    Category.FII: "FIIs",
}


def brl(value: Decimal) -> str:
    """Format as ``R$ 1.234,56`` (display only; half-up to cents)."""
    cents = quantize_cents(value, "half_up")
    sign = "-" if cents < 0 else ""
    integer, _, fraction = f"{abs(cents):.2f}".partition(".")
    grouped = f"{int(integer):,}".replace(",", ".")
    return f"{sign}R$ {grouped},{fraction}"


def _quantity(value: Decimal) -> str:
    return f"{value.normalize():f}"


def positions_report(positions: Sequence[Position]) -> str:
    if not positions:
        return "Nenhuma posição aberta."
    header = (
        f"{'Ativo':<8} {'Classe':<6} {'Quantidade':>12} {'Preço médio':>16} {'Custo total':>18}"
    )
    lines = [header, "-" * len(header)]
    for p in positions:
        lines.append(
            f"{p.ticker:<8} {p.asset_class.value:<6} {_quantity(p.quantity):>12} "
            f"{brl(p.average_price):>16} {brl(p.total_cost):>18}"
        )
    return "\n".join(lines)


def monthly_report(assessments: Sequence[MonthlyAssessment]) -> str:
    if not assessments:
        return "Nenhuma venda no período."
    blocks: list[str] = []
    for a in assessments:
        lines = [f"== {a.month} =="]
        for category, value in a.results.items():
            if value:
                lines.append(f"  {_CATEGORY_LABELS[category]:<20} {brl(value):>16}")
        if a.exempt:
            lines.append(f"  {'Ganho isento':<20} {brl(a.exempt):>16}")
        losses = ", ".join(f"{k}: {brl(v)}" for k, v in a.loss_balances.items() if v)
        if losses:
            lines.append(f"  Prejuízo a compensar: {losses}")
        if a.irrf_used:
            lines.append(f"  {'IRRF deduzido':<20} {brl(a.irrf_used):>16}")
        if a.darf:
            lines.append(
                f"  DARF {a.darf.code}: {brl(a.darf.amount)} "
                f"(período {a.darf.period}, vence {a.darf.due_date:%d/%m/%Y})"
            )
        elif a.carryover:
            lines.append(f"  Sem DARF: {brl(a.carryover)} acumulado para o mês seguinte")
        else:
            lines.append("  Sem imposto a pagar")
        lines.extend(f"  ! {w}" for w in a.warnings)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


_EXEMPT_LABELS = {
    "ganhos_acoes_ate_20_mil": "Ganhos líquidos em ações (vendas até R$ 20 mil no mês)",
    "dividendos": "Lucros e dividendos recebidos",
    "rendimentos_fii": "Rendimentos de fundos imobiliários (FII)",
}
_EXCLUSIVE_LABELS = {"jcp": "Juros sobre capital próprio"}
_CLASS_LABELS = {"acao": "ações", "fii": "cotas de FII", "etf": "cotas de ETF"}


def annual_report(report: AnnualReport) -> str:
    year = report.year
    lines = [f"== Declaração anual {year + 1} (ano-calendário {year}) ==", ""]
    lines.append("Bens e Direitos (custo de aquisição)")
    if not report.assets:
        lines.append("  nenhum ativo em 31/12")
    for a in report.assets:
        lines.append(
            f"  {a.ticker}: {_quantity(a.quantity)} {_CLASS_LABELS[a.asset_class.value]}, "
            f"preço médio {brl(a.average_price)}"
        )
        lines.append(
            f"    situação em 31/12/{year - 1}: {brl(a.cost_previous_year)}  |  "
            f"31/12/{year}: {brl(a.cost)}"
        )
    lines += ["", "Rendimentos isentos e não tributáveis"]
    lines += [f"  {_EXEMPT_LABELS[k]}: {brl(v)}" for k, v in report.exempt_income.items()]
    lines += ["", "Rendimentos sujeitos à tributação exclusiva/definitiva"]
    lines += [f"  {_EXCLUSIVE_LABELS[k]}: {brl(v)}" for k, v in report.exclusive_income.items()]
    lines += ["", "Renda variável (mês a mês)"]
    lines.append(monthly_report(report.monthly_table))
    if report.warnings:
        lines += ["", "Avisos"]
        lines += [f"  ! {w}" for w in report.warnings]
    return "\n".join(lines)
