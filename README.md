# b3-ir

[![CI](https://github.com/StaffeToxic/b3-ir/actions/workflows/ci.yml/badge.svg)](https://github.com/StaffeToxic/b3-ir/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

**Biblioteca e CLI em Python para calcular o Imposto de Renda de ações, FIIs e
ETFs negociados na B3**: preço médio, apuração mensal, DARF, day trade, isenção
de vendas de ações e dados para a declaração anual (DIRPF).

> [!WARNING]
> **Em desenvolvimento (pré-alfa).** Ainda não use os resultados para declarar ou
> pagar imposto.
>
> O b3-ir **não é consultoria tributária**. Você é o único responsável por
> conferir os valores e pela sua declaração. Leia o
> [Termo de Isenção de Responsabilidade](DISCLAIMER.md) antes de usar.

## O que ele faz

| Recurso | Status |
|---|---|
| Entrada manual em CSV | ✅ pronto |
| Preço médio com custos, desdobramento, grupamento e bonificação | ✅ pronto |
| Separação de day trade e operações comuns | ✅ pronto |
| Apuração mensal: ações, FIIs, ETFs, isenção, prejuízo, IRRF, DARF mínimo | ✅ pronto |
| Regras conferidas nos textos oficiais, versionados em [`legislacao/`](legislacao/) | ✅ 9 de 10 |
| Leitura de notas de corretagem em PDF (padrão SINACOR) | planejado |
| Importação dos extratos da Área do Investidor da B3 | planejado |
| Dados para a declaração anual (bens e direitos, renda variável) | planejado |

**Fora do escopo do MVP:** opções, futuros, BDRs, renda fixa, criptoativos,
ativos no exterior, aluguel de ações e venda a descoberto. Esses itens são
**recusados explicitamente**, nunca calculados em silêncio.

## Princípios

- **Toda regra fiscal tem fonte legal citada** em [`docs/regras-fiscais.md`](docs/regras-fiscais.md),
  e o texto da lei está versionado em [`legislacao/`](legislacao/) (Planalto e Receita
  Federal, com SHA-256 da fonte). Um teste falha se uma lei citada não estiver lá.
  Regra não confirmada aparece como `UNVERIFIED` no relatório.
- **Valores exatos**: dinheiro em `Decimal`, nunca ponto flutuante.
- **Privacidade**: tudo roda localmente, sem acesso à internet e sem telemetria.

## Instalação

Ainda não publicado no PyPI. Para desenvolvimento:

```bash
git clone https://github.com/StaffeToxic/b3-ir.git
cd b3-ir
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Uso

Por enquanto a entrada é um CSV simples (a leitura de notas em PDF e dos extratos
da B3 vem a seguir). Veja [`examples/operacoes.csv`](examples/operacoes.csv):

```text
data;tipo;ticker;quantidade;preco;custos;irrf
2026-01-05;compra;ITSA4;1000;10,00;5,00;0
2026-02-10;venda;ITSA4;400;12,00;2,00;0,24
2026-04-01;bonificacao;ITSA4;60;5,00;;
```

```bash
b3-ir mensal examples/operacoes.csv
b3-ir posicoes examples/operacoes.csv --data 2026-04-30
b3-ir mensal examples/operacoes.csv --formato json
```

Saída (trecho):

```text
== 2026-05 ==
  Ações (day trade)           R$ 490,00
  Prejuízo a compensar: comum: R$ 4.020,00
  IRRF deduzido                 R$ 6,19
  DARF 6015: R$ 91,81 (período 2026-05, vence 30/06/2026)
  ! UNVERIFIED: regras não confirmadas: day_trade_rate, ...
```

Código de saída `3` indica resultado incompleto: arquivo não suportado ou regra
ainda `UNVERIFIED`. O contrato completo está em
[`specs/001-ir-mvp/contracts/cli.md`](specs/001-ir-mvp/contracts/cli.md).

## Arquitetura

```text
src/b3_ir/
├── domain/      núcleo puro, sem I/O: modelos, classificação, preço médio, apuração
├── parsers/     entradas (CSV manual; PDF SINACOR e XLSX da B3 a seguir)
├── report/      saídas em texto e JSON
├── rules.py     registro único de regras fiscais com fonte legal
└── cli.py       comando b3-ir
```

Testes de arquitetura garantem que o domínio não faz I/O, não acessa a rede e não
usa `float`.

## Projetos parecidos

- [COIR](https://github.com/MarceloPCF/COIR): aplicativo para Windows, mais completo
  (opções, futuros, multa e juros do DARF). Licença AGPL-3.0.
- [correpy](https://github.com/thiagosalvatore/correpy): biblioteca Python que lê
  notas SINACOR, sem cálculo de imposto. Licença Apache-2.0.

O b3-ir é uma **biblioteca + CLI multiplataforma** com licença MIT, para quem quer
integrar o cálculo em scripts, planilhas ou outros sistemas, com cada regra
rastreável até o texto da lei.

## Desenvolvimento

O projeto segue *spec-driven development*: especificação, plano e tarefas ficam em
[`specs/`](specs/) e os princípios do projeto em
[`.specify/memory/constitution.md`](.specify/memory/constitution.md).

```bash
pytest
ruff check .
mypy
```

Veja [CONTRIBUTING.md](CONTRIBUTING.md). **Nunca anexe notas de corretagem ou
dados pessoais em issues.**

## Licença

[MIT](LICENSE) © 2026 Anthony Oliveira. Uso sujeito ao
[Termo de Isenção de Responsabilidade](DISCLAIMER.md).
