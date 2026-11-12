# Regras fiscais

Espelho legível do registro em [`src/b3_ir/rules.py`](../src/b3_ir/rules.py). Cada
regra tem identificador, valor, fonte legal e status. Um teste garante que esta
tabela e o código estão sincronizados.

> [!IMPORTANT]
> **Status `UNVERIFIED`**: o valor é um candidato ainda não conferido no texto
> oficial (pesquisa R1–R5 em `specs/001-ir-mvp/research.md`). Resultados que
> dependem dele aparecem marcados como `UNVERIFIED` no relatório. Não use esses
> resultados para declarar ou pagar imposto. Veja o
> [Termo de Isenção de Responsabilidade](../DISCLAIMER.md).

| ID | Valor | Fonte | Status |
|---|---|---|---|
| `stock_swing_rate` | 15% | Lei 11.033/2004, art. 2º; IN RFB 1.585/2015 | UNVERIFIED |
| `day_trade_rate` | 20% | Lei 8.981/1995, art. 72; IN RFB 1.585/2015 | UNVERIFIED |
| `fii_rate` | 20% | Lei 8.668/1993, art. 18, II | UNVERIFIED |
| `stock_sale_exemption_limit` | R$ 20.000,00 por mês | Lei 11.033/2004, art. 3º, I | UNVERIFIED |
| `irrf_swing_rate` | 0,005% sobre o valor de venda | Lei 11.033/2004, art. 2º, § 1º | UNVERIFIED |
| `irrf_day_trade_rate` | 1% sobre o resultado | Lei 9.959/2000, art. 8º; IN RFB 1.585/2015 | UNVERIFIED |
| `minimum_darf` | R$ 10,00 | Lei 9.430/1996, art. 68 | UNVERIFIED |
| `darf_code_variable_income` | 6015 | Receita Federal, tabela de códigos de receita (Sicalc) | UNVERIFIED |
| `darf_due_rule` | último dia útil do mês seguinte | Lei 11.033/2004; IN RFB 1.585/2015 | UNVERIFIED |
| `money_rounding` | arredondamento para cima a partir de meio centavo | a confirmar (Sicalc / IN RFB) | UNVERIFIED |

## Regras de cálculo (comportamento)

Estas regras não são constantes, mas também dependem de confirmação na pesquisa:

- **Preço médio**: média ponderada do custo de aquisição, incluindo custos da nota
  rateados proporcionalmente ao valor de cada operação; vendas não alteram o
  preço médio (R3).
- **Desdobramento e grupamento**: alteram a quantidade e preservam o custo total
  (R3; formato da B3 em `research/r6-prior-art.md`).
- **Bonificação**: soma ao custo total o valor atribuído pela empresa por ação
  bonificada (R3, IN RFB 1.585/2015, a confirmar).
- **Compensação de prejuízo**: prejuízos de operações comuns e de day trade são
  controlados separadamente; prejuízo de FII só compensa ganho de FII (R1, R2).
- **Isenção**: aplica-se apenas a vendas de ações no mercado à vista em
  operações comuns; não se aplica a day trade, FIIs ou ETFs (R1, a confirmar).
- **Mudanças de 2025–2026**: MP 1.303/2025 e Lei 15.270/2025 precisam ser
  verificadas quanto ao efeito sobre estas regras e sobre dividendos (R1, R5).
