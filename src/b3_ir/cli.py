"""Command-line entry point `b3-ir` (contract: specs/001-ir-mvp/contracts/cli.md)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from b3_ir import __version__, rules
from b3_ir.domain.annual import build_annual_report
from b3_ir.domain.assessment import assess_year
from b3_ir.domain.models import MonthlyAssessment
from b3_ir.domain.positions import PositionLedger, build_positions
from b3_ir.errors import B3IRError
from b3_ir.inputs import Inputs, load_inputs
from b3_ir.report import csv_out, json_out, text

DISCLAIMER = (
    "AVISO: o b3-ir não é consultoria tributária. Confira todos os valores; "
    "a responsabilidade pela declaração é sua. Veja DISCLAIMER.md."
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_INCOMPLETE = 3


def _ledger(inputs: Inputs, until: date | None = None) -> PositionLedger:
    return build_positions(inputs.classified(), inputs.events, until)


def _print_notes(inputs: Inputs) -> None:
    for item in inputs.unsupported:
        print(f"não suportado: {item}", file=sys.stderr)
    for item in inputs.warnings:
        print(f"aviso: {item}", file=sys.stderr)
    if inputs.ignored:
        print(f"ignorados: {', '.join(inputs.ignored)}", file=sys.stderr)


def cmd_posicoes(args: argparse.Namespace) -> int:
    inputs = load_inputs(args.entradas)
    until = date.fromisoformat(args.data) if args.data else None
    ledger = _ledger(inputs, until)
    positions = ledger.open_positions()
    if args.formato == "json":
        print(
            json_out.dumps(
                {
                    "data": until,
                    "posicoes": positions,
                    "avisos": inputs.warnings,
                    "ignorados": inputs.ignored,
                }
            )
        )
    else:
        print(text.positions_report(positions))
    _print_notes(inputs)
    return EXIT_INCOMPLETE if inputs.unsupported else EXIT_OK


def cmd_mensal(args: argparse.Namespace) -> int:
    inputs = load_inputs(args.entradas)
    ledger = _ledger(inputs)
    years = sorted({r.date.year for r in ledger.realized})
    year: int | None = args.ano or (years[-1] if years else None)
    assessments: list[MonthlyAssessment] = []
    if year is not None:
        opening = None
        for previous in (y for y in years if y < year):
            _, opening = assess_year(ledger.realized, previous, opening)
        assessments, _ = assess_year(ledger.realized, year, opening)
    if args.formato == "json":
        print(
            json_out.dumps(
                {
                    "ano": year,
                    "meses": assessments,
                    "avisos": inputs.warnings,
                    "ignorados": inputs.ignored,
                }
            )
        )
    else:
        print(text.monthly_report(assessments))
    _print_notes(inputs)
    unverified = any(w.startswith(rules.UNVERIFIED) for a in assessments for w in a.warnings)
    return EXIT_INCOMPLETE if inputs.unsupported or unverified else EXIT_OK


def cmd_anual(args: argparse.Namespace) -> int:
    inputs = load_inputs(args.entradas)
    report = build_annual_report(inputs.classified(), inputs.events, inputs.income, args.ano)
    if args.formato == "csv":
        if not args.saida:
            raise B3IRError("--formato csv exige --saida PASTA")
        for path in csv_out.write_annual_csv(report, Path(args.saida)):
            print(path)
    elif args.formato == "json":
        print(json_out.dumps({**json_out.to_jsonable(report), "avisos_entrada": inputs.warnings}))
    else:
        print(text.annual_report(report))
    _print_notes(inputs)
    unverified = any(
        w.startswith(rules.UNVERIFIED) for m in report.monthly_table for w in m.warnings
    )
    return EXIT_INCOMPLETE if inputs.unsupported or unverified else EXIT_OK


def cmd_web(args: argparse.Namespace) -> int:
    from b3_ir.web.server import serve  # imported lazily: the CLI never opens a socket

    serve(port=args.porta, open_browser=not args.nao_abrir)
    return EXIT_OK


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
    mensal.set_defaults(handler=cmd_mensal)

    anual = sub.add_parser("anual", help="dados para a declaração anual")
    anual.add_argument("entradas", nargs="+", metavar="ENTRADAS")
    anual.add_argument("--ano", type=int, required=True)
    anual.add_argument("--formato", choices=["texto", "json", "csv"], default="texto")
    anual.add_argument("--saida", help="pasta dos arquivos CSV")
    anual.set_defaults(handler=cmd_anual)

    posicoes = sub.add_parser("posicoes", help="posições e preço médio")
    posicoes.add_argument("entradas", nargs="+", metavar="ENTRADAS")
    posicoes.add_argument("--data", help="data de corte AAAA-MM-DD")
    posicoes.add_argument("--formato", choices=["texto", "json"], default="texto")
    posicoes.set_defaults(handler=cmd_posicoes)

    web = sub.add_parser("web", help="abre a interface no navegador (só neste computador)")
    web.add_argument("--porta", type=int, default=0, help="porta local (padrão: livre)")
    web.add_argument("--nao-abrir", action="store_true", help="não abre o navegador")
    web.set_defaults(handler=cmd_web)
    return parser


def _force_utf8() -> None:
    # Windows consoles default to a legacy code page and garble accents.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    _force_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.sem_aviso:
        print(DISCLAIMER, file=sys.stderr)
    if args.command is None:
        parser.print_help()
        return EXIT_USAGE
    handler = getattr(args, "handler", None)
    if handler is None:
        print(f"erro: o comando '{args.command}' ainda não foi implementado", file=sys.stderr)
        return EXIT_ERROR
    try:
        result: int = handler(args)
    except B3IRError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return result


if __name__ == "__main__":
    raise SystemExit(main())
