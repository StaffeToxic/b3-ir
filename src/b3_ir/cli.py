"""Command-line entry point `b3-ir` (contract: specs/001-ir-mvp/contracts/cli.md)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from b3_ir import __version__

DISCLAIMER = (
    "AVISO: o b3-ir não é consultoria tributária. Confira todos os valores; "
    "a responsabilidade pela declaração é sua. Veja DISCLAIMER.md."
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_INCOMPLETE = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b3-ir",
        description="Imposto de Renda de ações, FIIs e ETFs da B3.",
    )
    parser.add_argument("--version", action="version", version=f"b3-ir {__version__}")
    parser.add_argument(
        "--sem-aviso", action="store_true", help="não mostra o aviso de responsabilidade"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMANDO")

    mensal = sub.add_parser("mensal", help="apuração mensal e DARF")
    mensal.add_argument("entradas", nargs="+", metavar="ENTRADAS")
    mensal.add_argument("--ano", type=int)
    mensal.add_argument("--formato", choices=["texto", "json"], default="texto")

    anual = sub.add_parser("anual", help="dados para a declaração anual")
    anual.add_argument("entradas", nargs="+", metavar="ENTRADAS")
    anual.add_argument("--ano", type=int, required=True)
    anual.add_argument("--formato", choices=["texto", "json", "csv"], default="texto")
    anual.add_argument("--saida")

    posicoes = sub.add_parser("posicoes", help="posições e preço médio")
    posicoes.add_argument("entradas", nargs="+", metavar="ENTRADAS")
    posicoes.add_argument("--data")
    posicoes.add_argument("--formato", choices=["texto", "json"], default="texto")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.sem_aviso:
        print(DISCLAIMER, file=sys.stderr)
    if args.command is None:
        parser.print_help()
        return EXIT_USAGE
    print(f"erro: o comando '{args.command}' ainda não foi implementado", file=sys.stderr)
    return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
