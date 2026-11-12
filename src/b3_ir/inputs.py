"""Load every supported input file into one set of operations, events and income.

Shared by the CLI and the local web interface, so both compute the same result.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from b3_ir.catalog import load_catalog
from b3_ir.domain.classify import classify
from b3_ir.domain.models import CorporateEvent, IncomeEntry, Operation
from b3_ir.errors import B3IRError, ParseError
from b3_ir.parsers.b3_statements import parse_b3_statement
from b3_ir.parsers.csv_ops import parse_operations_csv
from b3_ir.parsers.dedup import deduplicate
from b3_ir.parsers.sinacor import parse_sinacor


@dataclass
class Inputs:
    operations: list[Operation] = field(default_factory=list)
    statement_operations: list[Operation] = field(default_factory=list)
    events: list[CorporateEvent] = field(default_factory=list)
    income: list[IncomeEntry] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def classified(self) -> list[Operation]:
        """Operations with asset class and trade type; classification warnings recorded."""
        operations, warnings = classify(self.operations, load_catalog().asset_classes)
        self.warnings.extend(w for w in warnings if w not in self.warnings)
        return operations


def _files(entries: Sequence[str | Path]) -> list[Path]:
    files: list[Path] = []
    for entry in entries:
        path = Path(entry)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.is_file():
            files.append(path)
        else:
            raise B3IRError(f"entrada não encontrada: {entry}")
    return files


def load_inputs(entries: Sequence[str | Path]) -> Inputs:
    inputs = Inputs()
    for path in _files(entries):
        suffix = path.suffix.lower()
        try:
            if suffix == ".csv":
                parsed = parse_operations_csv(path)
                inputs.operations.extend(parsed.operations)
                inputs.events.extend(parsed.events)
                continue
            if suffix == ".pdf":
                # Notes carry no broker id in correpy; the folder name stands for it.
                notes = parse_sinacor(path, broker=path.parent.name)
                inputs.operations.extend(notes.operations)
                inputs.unsupported.extend(notes.unsupported)
                continue
            if suffix == ".xlsx":
                statement = parse_b3_statement(path)
                inputs.statement_operations.extend(statement.operations)
                inputs.events.extend(statement.events)
                inputs.income.extend(statement.income)
                inputs.unsupported.extend(statement.unsupported)
                inputs.warnings.extend(statement.warnings)
                continue
        except ParseError as exc:
            # One bad file must not hide the others (spec, edge cases).
            inputs.unsupported.append(str(exc))
            continue
        inputs.ignored.append(path.name)
    # Notes and the manual CSV carry costs; the statement copy of the same trade goes.
    inputs.operations, report = deduplicate(inputs.operations, inputs.statement_operations)
    inputs.statement_operations = []
    inputs.warnings.extend(report)
    return inputs
