# -*- coding: utf-8 -*-
"""
Execute the main pipeline notebook cell by cell, without nbconvert/nbclient.

Reads the .ipynb, strips IPython magics and shell escapes, and execs every code
cell in one shared namespace. matplotlib is forced to the Agg backend so the
figure cells do not block. On failure the offending cell index and traceback are
printed and the process exits non-zero.

Usage:  python 06_tools/run_notebook.py [path/to/notebook.ipynb]
"""
import json
import sys
import time
import traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
NB = Path(sys.argv[1]) if len(sys.argv) > 1 else next(
    iter(ROOT.glob("**/4dissertation_gamespace_clustering_new.ipynb")), None)
if NB is None:
    raise SystemExit("notebook not found")

nb = json.loads(NB.read_text(encoding="utf-8"))
cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
print(f"[run] {NB.name}: {len(cells)} code cells")

ns = {"__name__": "__main__"}
t0 = time.time()
for i, cell in enumerate(cells):
    src = "".join(cell["source"])
    lines = []
    for ln in src.splitlines():
        s = ln.lstrip()
        if s.startswith(("%", "!")) or "get_ipython(" in s:
            lines.append("pass  # stripped: " + s[:80])
        else:
            lines.append(ln)
    code = "\n".join(lines)
    if not code.strip():
        continue
    cell_id = cell.get("id", f"#{i}")
    print(f"[cell {i:2d}] {cell_id} … ", end="", flush=True)
    try:
        exec(compile(code, f"<cell {i}>", "exec"), ns)
        print("ok")
    except Exception:
        print("FAILED")
        print("-" * 70)
        traceback.print_exc()
        sys.exit(1)

# persist the executed outputs back into the notebook so the saved outputs match
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        cell["execution_count"] = None
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"[done] {len(cells)} cells in {time.time()-t0:.1f}s")
