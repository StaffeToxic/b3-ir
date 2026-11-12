# CLI contract — `b3-ir`

Messages in pt-BR. Every command prints the not-tax-advice disclaimer to stderr
(suppressed with `--sem-aviso`).

## Commands

```text
b3-ir mensal  ENTRADAS... [--ano AAAA] [--formato texto|json]
b3-ir anual   ENTRADAS... --ano AAAA [--formato texto|json|csv] [--saida DIR]
b3-ir posicoes ENTRADAS... [--data AAAA-MM-DD] [--formato texto|json]
b3-ir --version
```

`ENTRADAS` are files or folders (recursive). `.csv` → manual operations CSV
(FR-015); `.pdf` → SINACOR notes via the optional `b3-ir[pdf]` extra (correpy,
research D-R4-1). The PDF's parent folder name is taken as the broker, so keep one
folder per broker for correct day-trade pairing. A file that cannot be read is
listed as unsupported and the others keep processing; `.xlsx` → B3 statement parser (Negociação or
Movimentação, detected from the header row; research D-R4-3). Statement trades
already present in a note or CSV are dropped and reported. Other extensions are listed as ignored. Until a parser exists,
its files are listed as unsupported and the exit code is 3.

## Manual CSV (FR-015)

```text
data;tipo;ticker;quantidade;preco;custos;irrf
2026-01-05;compra;ITSA4;100;10,00;5,00;0
2026-02-02;venda;ITSA4;50;13,00;2,00;0,03
2026-03-01;desdobramento;ITSA4;100;;;
2026-04-01;bonificacao;ITSA4;10;5,00;;
```

- Separator `;` (or `,` when the file has no `;`); header row required.
- `data`: `AAAA-MM-DD` or `DD/MM/AAAA`. Numbers accept `1.234,56` (a comma makes it Brazilian format) or `1234.56`;
  without a comma the dot is the decimal separator, so write `1000`, not `1.000`.
- `tipo`: `compra`, `venda`, `desdobramento`, `grupamento`, `bonificacao`.
  For `grupamento`, `quantidade` is the number of shares removed (positive).
  For `bonificacao`, `preco` is the cost attributed per bonus share.
- `custos`, `irrf` and `corretora` are optional (default 0 / empty). Day trade
  pairs only operations with the same `corretora` (research D-R1-2). Settlement date = trade date + 2
  calendar days (only informative in the MVP).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success, no unsupported items |
| 1 | Fatal error (I/O, invalid arguments after parsing) |
| 2 | Usage error (argparse) |
| 3 | Completed, but some inputs/items unsupported or `UNVERIFIED`; affected months flagged `incompleto` |

## JSON shape (`--formato json`)

- `mensal`: `{"ano": int, "meses": [MonthlyAssessment], "avisos": [str], "ignorados": [str]}`
- `anual`: the `AnnualReport` fields (`year`, `assets`, `monthly_table`,
  `exempt_income`, `exclusive_income`, `warnings`) plus `avisos_entrada` (input warnings)
- `posicoes`: `{"data": "AAAA-MM-DD", "posicoes": [Position]}`

Decimals serialize as strings (e.g. `"1234.56"`), dates as ISO 8601.
Field names follow `domain-api.md` in snake_case.

## CSV (`anual --formato csv --saida DIR`)

One file per section: `bens_e_direitos.csv`, `renda_variavel.csv`,
`rendimentos_isentos.csv`, `tributacao_exclusiva.csv`. UTF-8 with BOM, `;`
separator, decimal comma (Excel pt-BR friendly).
