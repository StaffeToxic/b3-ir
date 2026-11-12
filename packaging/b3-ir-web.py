"""Entry point of the Windows executable: double-click opens the web interface.

Arguments, when given, go to the regular CLI (e.g. ``b3-ir.exe mensal notas``).
"""

import sys

from b3_ir.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["web"]))
