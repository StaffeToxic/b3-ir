"""b3-ir: Brazilian income tax calculation for B3 stocks, FIIs and ETFs.

Not tax advice. See DISCLAIMER.md.
"""

from b3_ir.errors import B3IRError, ParseError, UnsupportedOperationError

__version__ = "0.1.0.dev0"

__all__ = [
    "B3IRError",
    "ParseError",
    "UnsupportedOperationError",
    "__version__",
]
