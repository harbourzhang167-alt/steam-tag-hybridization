# -*- coding: utf-8 -*-
"""
Environment check + version fingerprint.

The pipeline notebook originally recorded no library versions, and re-running it
under a different scikit-learn silently changed the KMeans clustering (see
06_tools/CHANGELOG_corrections.md, C6). This script makes the environment an
explicit, checkable artifact.

  * reads requirements.txt and compares it against what is actually installed
  * reports PASS / MISMATCH per package, flagging sklearn and statsmodels as
    version-critical
  * writes a fingerprint (versions + Python + hashes of the key data artifacts)
    to 01_data/processed/environment_fingerprint.json, so any result table can
    be tied to the environment that produced it

Exit code is 0 when every pinned package matches, 1 otherwise, so it can be
used as a gate in a reproduce script.

Usage:  python 06_tools/check_environment.py
"""
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import importlib

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "requirements.txt"
OUT = ROOT / "01_data/processed/environment_fingerprint.json"

CRITICAL = {"scikit-learn", "statsmodels"}
# import name != distribution name for these
IMPORT_NAME = {"scikit-learn": "sklearn"}

FINGERPRINT_FILES = [
    "01_data/processed/games_clustered_meta_export.csv",
    "01_data/processed/game_measures_extension.csv",
    "01_data/processed/tag_space_nodes.csv",
    "01_data/processed/tag_domain_distances.csv",
]


def parse_requirements(path: Path) -> dict:
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "==" not in line:
            continue
        name, ver = line.split("==", 1)
        pins[name.strip()] = ver.strip()
    return pins


def installed_version(dist_name: str):
    mod_name = IMPORT_NAME.get(dist_name, dist_name.replace("-", "_"))
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    return getattr(mod, "__version__", "unknown")


def sha256(path: Path, limit_mb: int = 64) -> str:
    """Hash a file; for very large files hash the first `limit_mb` MiB."""
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    limit = limit_mb * 1024 * 1024
    read = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            read += len(chunk)
            if read >= limit:
                break
    return ("sha256:" + h.hexdigest()) if read < limit else ("sha256[:%dMiB]:%s" % (limit_mb, h.hexdigest()))


def main() -> int:
    pins = parse_requirements(REQ)
    print("# 环境核查")
    print()
    print(f"- 解释器：Python {sys.version.split()[0]}　平台：{platform.platform()}")
    print(f"- pin 文件：`requirements.txt`（{len(pins)} 个包）")
    print()
    print("| 包 | 要求 | 实际 | 判定 | 版本关键性 |")
    print("|---|---|---|---|---|")

    ok = True
    versions = {}
    for name, want in pins.items():
        got = installed_version(name)
        versions[name] = got
        if got is None:
            verdict, mark = "**未安装**", "❌"
            ok = False
        elif got == want:
            verdict, mark = "一致", "✅"
        else:
            verdict, mark = "**不一致**", "❌"
            ok = False
        crit = "**关键**" if name in CRITICAL else "—"
        print(f"| `{name}` | {want} | {got} | {mark} {verdict} | {crit} |")
    print()

    if not ok:
        print("> ⚠️ 存在不一致。**`scikit-learn` 不一致时不要重跑聚类**——")
        print("> 同一份数据、同一 `random_state=42`、同一 `K=8`，在不同版本下会得到不同的簇划分")
        print("> （见 `06_tools/CHANGELOG_corrections.md` C6）。聚类结果应直接使用")
        print("> `01_data/processed/games_clustered_meta_export.csv` 中已落盘的 `Game_Cluster` 列。")
        print()

    fp = {
        "captured_for": "Steam tag hybridization workspace",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pinned_versions": versions,
        "requirements_match": ok,
        "critical_packages": sorted(CRITICAL),
        "artifact_hashes": {rel: sha256(ROOT / rel) for rel in FINGERPRINT_FILES},
        "note": ("Game_Cluster is version-fragile: re-running KMeans under a different "
                 "scikit-learn changes the partition. Prefer the persisted column."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[written] {OUT.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
