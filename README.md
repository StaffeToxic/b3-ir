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
| Leitura de notas de corretagem em PDF (padrão SINACOR) | planejado |
| Importação dos extratos da Área do Investidor da B3 | planejado |
| Preço médio com custos, desdobramento, grupamento e bonificação | em andamento |
| Apuração mensal: operações comuns, day trade, FIIs, ETFs | em andamento |
| Compensação de prejuízo, IRRF e DARF | em andamento |
| Dados para a declaração anual (bens e direitos, renda variável) | planejado |

**Fora do escopo do MVP:** opções, futuros, BDRs, renda fixa, criptoativos,
ativos no exterior, aluguel de ações e venda a descoberto. Esses itens são
**recusados explicitamente**, nunca calculados em silêncio.

## Princípios

- **Toda regra fiscal tem fonte legal citada** em [`docs/regras-fiscais.md`](docs/regras-fiscais.md).
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

## Uso (planejado)

```bash
b3-ir mensal ./notas --ano 2026
b3-ir posicoes ./notas --data 2026-12-31
b3-ir anual ./notas ./extratos-b3 --ano 2026 --formato csv --saida ./declaracao
```

O contrato completo da CLI está em
[`specs/001-ir-mvp/contracts/cli.md`](specs/001-ir-mvp/contracts/cli.md).

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
