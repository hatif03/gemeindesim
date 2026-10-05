"""Find Markdown tables whose rows have a different number of cells than the header (GitHub splits on every unescaped pipe,
also inside backticks, so `<|inner_prefix|>` or `a|b` in a cell breaks the table).

    python research/lint_tables.py [--fix]      # --fix escapes pipes inside backtick spans of table rows
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FIX = "--fix" in sys.argv
files = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True).stdout.split()


def cells(line):
    return len(re.split(r"(?<!\\)\|", line.strip().strip("|")))


def escape_code_pipes(line):
    return re.sub(r"`([^`]*)`", lambda m: "`" + re.sub(r"(?<!\\)\|", r"\\|", m.group(1)) + "`", line)


bad = 0
for f in files:
    if "node_modules" in f or "TILESET" in f:
        continue
    path = ROOT / f
    lines = path.read_text(encoding="utf-8").split("\n")
    in_code, header_cells, changed = False, None, False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code, header_cells = not in_code, None
            continue
        if in_code:
            continue
        if line.lstrip().startswith("|"):
            if header_cells is None:
                header_cells = cells(line)
            elif cells(line) != header_cells:
                bad += 1
                print(f"{f}:{i + 1}: {cells(line)} cells, header has {header_cells}")
                if FIX:
                    fixed = escape_code_pipes(line)
                    if cells(fixed) == header_cells:
                        lines[i], changed = fixed, True
        else:
            header_cells = None
    if FIX and changed:
        path.write_text("\n".join(lines), encoding="utf-8")
print("rows with a wrong cell count:", bad)
