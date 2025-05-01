#!/usr/bin/env python3
"""
generate_flow_report.py – Aggregate flow-test metrics into one CSV.

Output
------
<root>/overview/metrics_summary.csv   (includes mass_error_pct column)

Run
---
python generate_flow_report.py              # uses default root
python generate_flow_report.py D:/results   # override root
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_ROOT = (Path(__file__).resolve().parent.parent / "volume_calc_test").resolve()
DENSITY_WATER = 0.977  # g / ml

# ──────────────────────────────────────────────────────────────────────────────
# JSON loader (strips // comments if json5 isn’t installed)
# ──────────────────────────────────────────────────────────────────────────────
try:
    import json5 as _json
except ModuleNotFoundError:
    _json = json
    _WHOLE_COM = re.compile(r"^\s*//.*$", re.MULTILINE)
    _INLINE_COM = re.compile(r"//.*?(?=\r|\n|$)")
    _TRAIL_COM  = re.compile(r",\s*([}\]])")

    def _scrub(txt: str) -> str:
        txt = _WHOLE_COM.sub("", txt)
        txt = _INLINE_COM.sub("", txt)
        txt = _TRAIL_COM.sub(r"\1", txt)
        return txt


def _read_json(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if _json is json:
        raw = _scrub(raw)
    return _json.loads(raw)


# ──────────────────────────────────────────────────────────────────────────────
_MASS_KEYS = {
    "measured_mass_g",
    "measured mass",
    "measured_weight",
    "measured weight",
}


def _load_metrics(jfile: Path) -> Dict[str, Any]:
    data = _read_json(jfile)

    data["test_name"] = jfile.parents[2].name  # folder name two levels up

    # normalise mass key
    for key in _MASS_KEYS:
        if key in data and data[key] not in (None, "", 0):
            data["measured_mass_g"] = float(data[key])
    for key in _MASS_KEYS - {"measured_mass_g"}:
        data.pop(key, None)

    # debug print (path converted to str to avoid TypeError)
    print(
        f"[DEBUG] {str(jfile.relative_to(jfile.parents[2])):35} "
        f"measured_mass_g={data.get('measured_mass_g')} "
        f"total_mass_raw_g={data.get('total_mass_raw_g')}"
    )

    return data


def _collect_json(root: Path) -> Iterable[Path]:
    yield from root.rglob("analysis_results.json")


# ──────────────────────────────────────────────────────────────────────────────
def _save_csv(df: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / "metrics_summary.csv"
    df.to_csv(out_path, index=False)
    print(f"\n✓ CSV saved to {out_path}\n")


# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate flow-test summary CSV.")
    parser.add_argument(
        "root_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Root directory with test folders (default: {DEFAULT_ROOT})",
    )
    root = parser.parse_args().root_dir.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"{root} is not a valid directory")

    files = list(_collect_json(root))
    if not files:
        sys.exit("No analysis_results.json files found.")

    df = pd.DataFrame(_load_metrics(p) for p in files)

    # ensure columns exist
    for col in ("measured_mass_g", "total_mass_raw_g"):
        if col not in df.columns:
            df[col] = pd.NA

    # percent error column
    df["mass_error_pct"] = (
        (pd.to_numeric(df["measured_mass_g"], errors="coerce")
         - pd.to_numeric(df["total_mass_raw_g"], errors="coerce"))
        / pd.to_numeric(df["total_mass_raw_g"], errors="coerce")
    ) * 100.0

    # move test_name first
    if "test_name" in df.columns:
        df = df[["test_name"] + [c for c in df.columns if c != "test_name"]]

    # replace standalone zeros with NA for numerics
    num_cols = df.select_dtypes("number").columns
    df[num_cols] = df[num_cols].replace({0: pd.NA})

    # show final structure
    print("[DEBUG] Columns:", df.columns.tolist())
    print("[DEBUG] First rows:\n", df.head(), "\n")

    _save_csv(df, root / "overview")


if __name__ == "__main__":
    main()
