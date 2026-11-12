# Regras fiscais

Espelho legível do registro em [`src/b3_ir/rules.py`](../src/b3_ir/rules.py). Cada
regra tem identificador, valor, fonte legal e status. Um teste garante que esta
tabela e o código estão sincronizados.

Os textos citados estão versionados em Markdown na pasta
[`legislacao/`](../legislacao/), baixados das fontes oficiais (Planalto e Receita
Federal) com o SHA-256 do arquivo de origem.

> [!IMPORTANT]
> **VERIFIED** significa que o valor foi conferido no texto oficial vigente na data
> indicada em `legislacao/`. **UNVERIFIED** significa que ainda não foi, e os
> resultados que dependem dele saem marcados no relatório. Mesmo verificadas, as
> regras podem mudar: veja o [Termo de Isenção de Responsabilidade](../DISCLAIMER.md).

| ID | Valor | Fonte | Status |
|---|---|---|---|
| `stock_swing_rate` | 15% | Lei 11.033/2004, art. 2º, II; IN RFB 1.585/2015, art. 57 | VERIFIED |
| `day_trade_rate` | 20% | Lei 11.033/2004, art. 2º, I; IN RFB 1.585/2015, art. 65, § 11, I | VERIFIED |
| `fii_rate` | 20% | Lei 8.668/1993, art. 18 (redação da Lei 9.779/1999); IN RFB 1.585/2015, art. 37 | VERIFIED |
| `stock_sale_exemption_limit` | R$ 20.000,00 de vendas de ações no mês | Lei 11.033/2004, art. 3º, I; IN RFB 1.585/2015, art. 59, I e § 2º | VERIFIED |
| `irrf_swing_rate` | 0,005% sobre o valor de venda | Lei 11.033/2004, art. 2º, § 1º, IV; IN RFB 1.585/2015, art. 63 | VERIFIED |
| `irrf_day_trade_rate` | 1% sobre o resultado positivo | Lei 9.959/2000, art. 8º; IN RFB 1.585/2015, art. 65 | VERIFIED |
| `minimum_darf` | R$ 10,00 | Lei 9.430/1996, art. 68 | VERIFIED |
| `darf_code_variable_income` | 6015 | Receita Federal, Agenda Tributária (IRPF - Ganhos líquidos em operações em bolsa) | VERIFIED |
| `darf_due_rule` | último dia útil do mês seguinte | IN RFB 1.585/2015, art. 56, § 5º | VERIFIED |
| `jcp_withholding_rate` | 15% até 31/12/2025 | Lei 9.249/1995, art. 9º, § 2º (redação anterior à LC 224/2025) | VERIFIED |
| `jcp_withholding_rate` | 17,5% a partir de 1º/1/2026 | Lei 9.249/1995, art. 9º, § 2º (redação da LC 224/2025, art. 8º; efeitos art. 14, III) | VERIFIED |
| `dividend_monthly_threshold` | R$ 50.000,00 por empresa no mês, a partir de 2026 | Lei 9.250/1995, art. 6º-A (incluído pela Lei 15.270/2025) | VERIFIED |
| `dividend_withholding_rate` | 10% sobre o total do mês acima do limite | Lei 9.250/1995, art. 6º-A (incluído pela Lei 15.270/2025) | VERIFIED |
| `money_rounding` | arredondamento para cima a partir de meio centavo | a confirmar (Sicalc / IN RFB) | UNVERIFIED |

## Regras de cálculo

| Regra | Como o b3-ir aplica | Fonte |
|---|---|---|
| Custo médio | Média ponderada dos custos unitários | Lei 8.981/1995, art. 72, § 2º, a; IN 1.585, art. 58 |
| Custos da nota | Dedutíveis; rateados entre as operações do dia proporcionalmente ao valor financeiro | IN 1.585, art. 56, §§ 3º e 4º |
| Desdobramento | Ações acrescidas entram com custo zero: custo total preservado | IN 1.585, art. 58, § 7º, II |
| Bonificação | Custo = lucro ou reserva capitalizado por ação (valor informado pela empresa) | IN 1.585, art. 58, § 1º |
| Day trade | Mesmo dia, mesmo ativo, **mesma instituição intermediadora**; casamento pela ordem dos negócios; estoque anterior não conta | Lei 9.959/2000, art. 8º, § 1º; IN 1.585, art. 65, §§ 1º a 3º |
| Isenção de R$ 20 mil | Só ações no mercado à vista; não vale para day trade nem para ETFs (fundos de índice) | IN 1.585, art. 59, § 2º, I e II; art. 65, § 15 |
| Prejuízo comum (ações e ETFs) | Compensa ganhos de operações comuns no mês e nos meses e anos seguintes; não compensa day trade | IN 1.585, art. 64 e parágrafo único |
| Prejuízo de day trade | Só compensa ganhos de day trade, no mês e nos meses seguintes | IN 1.585, art. 65, §§ 10 e 11 |
| Prejuízo de FII | Só compensa ganhos com cotas de FII | IN 1.585, art. 37, § 2º |
| IRRF 0,005% | Deduzido no mês, compensado nos meses seguintes; saldo no fim do ano vai para a declaração de ajuste | Lei 11.033/2004, art. 2º, § 7º |
| IRRF de day trade | Deduzido no mês, compensado nos meses seguintes; saldo no fim do ano só por pedido de restituição | IN 1.585, art. 65, §§ 8º e 9º |
| DARF abaixo de R$ 10 | Não é emitido; o valor soma ao período seguinte até atingir R$ 10 | Lei 9.430/1996, art. 68 |

| Dividendos | Isentos | Lei 9.249/1995, art. 10 |
| Dividendos acima de R$ 50 mil/mês por empresa (a partir de 2026) | Retenção de 10% na fonte; o relatório anual avisa | Lei 9.250/1995, art. 6º-A (Lei 15.270/2025) |
| Rendimentos de FII | Isentos para pessoa física se o fundo tem ≥ 100 cotistas e o investidor < 10% das cotas; o relatório avisa | Lei 11.033/2004, art. 3º, III e § 1º |
| JCP | Tributação exclusiva na fonte: 15% até 2025, 17,5% a partir de 2026 | Lei 9.249/1995, art. 9º, § 2º; LC 224/2025, arts. 8º e 14, III |

### Interpretações adotadas (sem regra expressa)

- **Soma das vendas para a isenção**: o b3-ir soma só as vendas de ações em
  operações comuns, já que a isenção não se aplica ao day trade (IN 1.585, art. 59,
  § 2º, I). Há quem some também as vendas de day trade; confira com um contador
  se você opera os dois no mesmo mês.
- **Códigos das fichas da declaração**: grupo/código de Bens e Direitos e número do
  tipo de rendimento mudam com o programa de cada ano e não constam das normas nem do
  "Perguntas e Respostas IRPF 2026". O relatório anual usa os nomes dos campos.
- **Feriados**: o vencimento usa o último dia de semana do mês; feriados nacionais
  ainda não são considerados. Confira na
  [Agenda Tributária](https://www.gov.br/receitafederal/pt-br/assuntos/agenda-tributaria).

## Mudanças recentes verificadas

- **MP 1.303/2025**: o texto compilado do Planalto marca as alterações dela nas
  Leis 11.033, 9.959, 8.668 e 8.981 como "Vigência encerrada". As regras acima
  continuam valendo.
- **Lei 15.270/2025**: a partir de janeiro de 2026, lucros e dividendos pagos por
  uma mesma empresa a uma mesma pessoa física acima de R$ 50.000,00 no mês têm
  retenção de 10% (art. 6º-A da Lei 9.250/1995, incluído pela Lei 15.270). Afeta o
  relatório anual (proventos), não a apuração mensal de ganhos.
