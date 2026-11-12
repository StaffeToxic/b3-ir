"""Single registry of tax rules (Constitution I).

Every rate, limit, code and date rule used by the domain comes from here, with its
legal source. ``verified=False`` means the value is a candidate that has not been
confirmed against the official text yet (research.md R1-R5): results that depend
on it are flagged ``UNVERIFIED``. Mirrored for humans in docs/regras-fiscais.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from b3_ir.errors import UnsupportedOperationError

UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    value: Decimal | str
    source: str
    valid_from: date
    valid_to: date | None
    verified: bool
    description: str

    def applies_on(self, day: date) -> bool:
        return self.valid_from <= day and (self.valid_to is None or day <= self.valid_to)


_SINCE = date(2005, 1, 1)

_RULES: tuple[Rule, ...] = (
    Rule(
        "stock_swing_rate",
        Decimal("0.15"),
        "Lei 11.033/2004, art. 2º; IN RFB 1.585/2015",
        _SINCE,
        None,
        verified=False,
        description="Alíquota sobre ganho líquido em operações comuns com ações e ETFs.",
    ),
    Rule(
        "day_trade_rate",
        Decimal("0.20"),
        "Lei 8.981/1995, art. 72; IN RFB 1.585/2015",
        _SINCE,
        None,
        verified=False,
        description="Alíquota sobre resultado de day trade.",
    ),
    Rule(
        "fii_rate",
        Decimal("0.20"),
        "Lei 8.668/1993, art. 18, II",
        _SINCE,
        None,
        verified=False,
        description="Alíquota sobre ganho na alienação de cotas de FII.",
    ),
    Rule(
        "stock_sale_exemption_limit",
        Decimal("20000.00"),
        "Lei 11.033/2004, art. 3º, I",
        _SINCE,
        None,
        verified=False,
        description="Limite mensal de vendas de ações no mercado à vista para isenção.",
    ),
    Rule(
        "irrf_swing_rate",
        Decimal("0.00005"),
        "Lei 11.033/2004, art. 2º, § 1º",
        _SINCE,
        None,
        verified=False,
        description="IRRF ('dedo-duro') sobre o valor de alienação em operações comuns.",
    ),
    Rule(
        "irrf_day_trade_rate",
        Decimal("0.01"),
        "Lei 9.959/2000, art. 8º; IN RFB 1.585/2015",
        _SINCE,
        None,
        verified=False,
        description="IRRF sobre o resultado positivo de day trade.",
    ),
    Rule(
        "minimum_darf",
        Decimal("10.00"),
        "Lei 9.430/1996, art. 68",
        _SINCE,
        None,
        verified=False,
        description="Valor mínimo de DARF; abaixo disso o imposto acumula para o mês seguinte.",
    ),
    Rule(
        "darf_code_variable_income",
        "6015",
        "Receita Federal, tabela de códigos de receita (Sicalc)",
        _SINCE,
        None,
        verified=False,
        description="Código de receita do DARF de ganhos líquidos em bolsa (pessoa física).",
    ),
    Rule(
        "darf_due_rule",
        "last_business_day_next_month",
        "Lei 11.033/2004; IN RFB 1.585/2015",
        _SINCE,
        None,
        verified=False,
        description="Vencimento no último dia útil do mês seguinte ao da apuração.",
    ),
    Rule(
        "money_rounding",
        "half_up",
        "a confirmar (Sicalc / IN RFB)",
        _SINCE,
        None,
        verified=False,
        description="Arredondamento de valores finais para centavos.",
    ),
)

RULES: dict[str, tuple[Rule, ...]] = {}
for _rule in _RULES:
    RULES[_rule.id] = (*RULES.get(_rule.id, ()), _rule)


@dataclass(frozen=True, slots=True)
class RuleValue:
    """A rule resolved for a date, with the flag that consumers must propagate."""

    rule: Rule

    @property
    def value(self) -> Decimal | str:
        return self.rule.value

    @property
    def unverified(self) -> bool:
        return not self.rule.verified


def get(rule_id: str, on: date) -> RuleValue:
    """Resolve a rule valid on ``on``; refuse when no version covers that date."""
    candidates = RULES.get(rule_id)
    if candidates is None:
        raise KeyError(f"regra desconhecida: {rule_id}")
    for rule in candidates:
        if rule.applies_on(on):
            return RuleValue(rule)
    raise UnsupportedOperationError(rule_id, f"nenhuma regra vigente em {on.isoformat()}")


def decimal_rule(rule_id: str, on: date) -> tuple[Decimal, bool]:
    """Resolve a numeric rule; returns (value, unverified)."""
    resolved = get(rule_id, on)
    if not isinstance(resolved.value, Decimal):
        raise TypeError(f"regra {rule_id} não é numérica")
    return resolved.value, resolved.unverified
