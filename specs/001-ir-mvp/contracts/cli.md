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

`ENTRADAS` are files or folders (recursive). `.pdf` → SINACOR parser;
`.xlsx` → B3 statement parser (type detected from header row). Other extensions
are listed as ignored.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success, no unsupported items |
| 1 | Fatal error (I/O, invalid arguments after parsing) |
| 2 | Usage error (argparse) |
| 3 | Completed, but some inputs/items unsupported or `UNVERIFIED`; affected months flagged `incompleto` |

## JSON shape (`--formato json`)

- `mensal`: `{"ano": int, "meses": [MonthlyAssessment], "avisos": [str], "ignorados": [str]}`
- `anual`: `{"ano": int, "bens_e_direitos": [...], "renda_variavel": [...], "rendimentos_isentos": [...], "tributacao_exclusiva": [...], "avisos": [...]}`
- `posicoes`: `{"data": "AAAA-MM-DD", "posicoes": [Position]}`

Decimals serialize as strings (e.g. `"1234.56"`), dates as ISO 8601.
Field names follow `domain-api.md` in snake_case.

## CSV (`anual --formato csv --saida DIR`)

One file per section: `bens_e_direitos.csv`, `renda_variavel.csv`,
`rendimentos_isentos.csv`, `tributacao_exclusiva.csv`. UTF-8 with BOM, `;`
separator, decimal comma (Excel pt-BR friendly).
