#!/usr/bin/env python3
"""compare_scope_flow.py

Utility script that aligns Tektronix‑scope captures (CSV export + metadata) with
CSV flow‑sensor logs so you can spot correlations between I²C ‘singing’ events
and anomalies in flow‑rate data.

---
INPUT FOLDERS
=============

• **Scope folder** – contains files like::

      F0001CH1.CSV  ← SCL   (or any channel)
      F0001CH2.CSV  ← SDA
      F0001TEK.SET  ← acquisition settings (optional)
      F0001TEK.JPG  ← screenshot (optional)

  The script scans *all* `*CH*.CSV` files it finds and parses the Tek header to
  obtain absolute wall‑clock times for every sample.

• **Data folder** – your project layout, e.g.::

      demo_1_…/raw/data/raw_demo_…_20250509_170211.csv

  The script globs for `raw/data/*.csv` and treats the first column as an
  ISO‑8601 timestamp (or epoch seconds) and the rest as numeric features.

USAGE
=====

    python compare_scope_flow.py \
        --scope E:/ALL0001 \
        --data  C:/…/demo_1_RodePeters_20250509_170211 \
        --out   analysis_output

Outputs a merged CSV, a PNG overlay plot, and a simple cross‑correlation
print‑out.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

###############################################################################
# Tektronix helpers
###############################################################################

_TEK_DATE_FMT = "%d-%b-%y %H:%M:%S"  # example: 10-May-25 04:38:12


def _parse_tek_csv(csv_path: Path) -> pd.DataFrame:
    """Return a DataFrame with absolute timestamps and the voltage column.

    The CSV header gives:
    • Date, Time (wall‑clock of *save*)
    • Sample Interval (∆t)
    • Trigger Point (index of trigger sample)

    We use those to recover an approximate absolute timestamp for *every* sample
    even though Tek CSV stores only relative times.
    """
    hdr: dict[str, str] = {}
    numeric_lines: list[list[str]] = []

    with csv_path.open(newline="", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]:  # header
                key, *vals = row
                hdr[key.strip()] = vals[0].strip() if vals else ""
            else:
                # first blank – numeric table starts
                numeric_lines.append(row)
                numeric_lines.extend(reader)  # rest of file
                break

    try:
        save_dt = dt.datetime.strptime(f"{hdr['Date']} {hdr['Time']}", _TEK_DATE_FMT)
        sample_int = float(hdr['Sample Interval'])  # seconds
        trig_idx = int(float(hdr['Trigger Point']))
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{csv_path} missing Tek header fields: {exc}") from None

    first_sample_time = save_dt - dt.timedelta(seconds=trig_idx * sample_int)

    # Now read numeric part into ndarray, ignoring blanks
    data = [r for r in numeric_lines if len(r) >= 5 and not any(c.strip() for c in r[:3])]
    rel_t = np.asarray([float(r[3]) for r in data])  # seconds rel. to trigger
    volt = np.asarray([float(r[4]) for r in data])

    abs_t = first_sample_time + pd.to_timedelta(rel_t, unit="s")
    return pd.DataFrame({"timestamp": abs_t, csv_path.stem: volt})


###############################################################################
# Flow‑data helpers
###############################################################################

_TS_COL_RE = re.compile(r"^(time|timestamp|date[_ ]?time)$", re.I)


def _parse_flow_csv(csv_path: Path) -> pd.DataFrame:
    """Return DataFrame with a proper datetime index + numeric columns."""
    df = pd.read_csv(csv_path)

    # guess time column
    time_col = next((c for c in df.columns if _TS_COL_RE.match(c)), df.columns[0])
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
    if df[time_col].isna().all():
        # maybe epoch seconds
        df[time_col] = pd.to_datetime(df[time_col].astype(float), unit="s", utc=True)

    df = df.set_index(time_col).rename_axis("timestamp")
    return df.sort_index()


###############################################################################
# Main processing pipeline
###############################################################################

def load_scope_folder(folder: Path) -> pd.DataFrame:
    """Concatenate all channel CSVs into a single time‑aligned table."""
    dfs = [_parse_tek_csv(p) for p in folder.glob("*CH*.CSV")]
    if not dfs:
        raise FileNotFoundError("No *CH*.CSV files in scope folder")
    # outer join on timestamp to keep union of times
    df = dfs[0].set_index("timestamp")
    for d in dfs[1:]:
        df = df.join(d.set_index("timestamp"), how="outer")
    return df.sort_index()


def load_flow_folder(folder: Path) -> pd.DataFrame:
    """Locate raw/data/*.csv and return DataFrame."""
    raw_files = list((folder / "raw" / "data").glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError("No raw/data/*.csv found in data folder")
    # If multiple logs, concat with source tag
    dfs = []
    for p in raw_files:
        df = _parse_flow_csv(p)
        df.columns = [f"{p.stem}_{c}" if df.shape[1] > 1 else p.stem for c in df.columns]
        dfs.append(df)
    df_merged = pd.concat(dfs, axis=1).sort_index()
    return df_merged


def align_and_analyse(scope_df: pd.DataFrame, flow_df: pd.DataFrame, out: Path):
    out.mkdir(parents=True, exist_ok=True)

    # Resample both to 1 ms for easy plotting
    s_resamp = scope_df.interpolate().resample("1ms").mean()
    f_resamp = flow_df.interpolate().resample("1ms").mean()

    combined = s_resamp.join(f_resamp, how="outer")
    combined.to_csv(out / "aligned_data.csv")

    # quick visual overlay
    plt.figure(figsize=(10, 6))
    ax1 = combined.iloc[:, 0].plot(label=combined.columns[0])
    if combined.shape[1] > 1:
        ax2 = ax1.twinx()
        combined.iloc[:, 1].plot(ax=ax2, color="C1", label=combined.columns[1])
        ax2.set_ylabel(combined.columns[1])
    ax1.set_xlabel("Time (UTC)")
    ax1.set_ylabel(combined.columns[0])
    plt.title("Scope vs Flow overlay (1 ms samples)")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(out / "overlay.png", dpi=150)

    # crude cross‑correlation example (first two columns)
    if combined.shape[1] >= 2:
        a = combined.iloc[:, 0].fillna(method="ffill").values
        b = combined.iloc[:, 1].fillna(method="ffill").values
        corr = np.correlate(a - np.nanmean(a), b - np.nanmean(b), mode="full")
        lags = np.arange(-len(a) + 1, len(a))
        lag_ms = lags * 1  # because 1 ms per sample
        best_idx = np.argmax(np.abs(corr))
        print(
            f"Peak correlation at {lag_ms[best_idx]} ms (corr={corr[best_idx]:.2e})"
        )


###############################################################################
# CLI
###############################################################################

def main(argv=None):
    p = argparse.ArgumentParser(description="Correlate Tek scope captures with flow logs")
    p.add_argument("--scope", type=Path, required=True, help="Folder containing FxxxxCH*.CSV")
    p.add_argument("--data", type=Path, required=True, help="Root folder of demo_xxx run")
    p.add_argument("--out", type=Path, default=Path("analysis_output"), help="Output directory")
    args = p.parse_args(argv)

    scope_df = load_scope_folder(args.scope)
    flow_df = load_flow_folder(args.data)
    align_and_analyse(scope_df, flow_df, args.out)
    print("✅ Done. Aligned CSV and overlay plot written to", args.out)


if __name__ == "__main__":
    main()
