# controller_interface/core/analysis.py

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

# If you prefer aggregator imports, do:
# from controller_interface import logger
# Otherwise, direct from utils:
from controller_interface.utils.logging_utils import logger

def analyze_data(
    csv_path: str,
    out_analysis_dir: str,
    out_stable_data_dir: str,
    out_stable_plots_dir: str,
    out_raw_plots_dir: str,
    fluid_density: float = 0.977,  # existing default
    total_flow: Optional[float] = None  # optional param from PidTuningView
) -> None:
    """
    Analyzes PID run data:
      - Reads a CSV, sorts by timeMs, adds Time_s column
      - Integrates flow across the entire dataset and a "stable" subset (userStable==True & on==True)
      - Saves stable_data.csv
      - Generates a JSON summary of metrics in out_analysis_dir
      - Plots full-flow vs stable data in out_raw_plots_dir and out_stable_plots_dir
      - Rounds numeric results to 4 decimals
    """

    # 1) If no CSV, bail out
    if not os.path.isfile(csv_path):
        logger.error(f"CSV not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded CSV => {csv_path}, shape={df.shape}")

    # Sort by timeMs and reset index
    df.sort_values("timeMs", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Convert timeMs to seconds
    df["Time_s"] = df["timeMs"] / 1000.0

    analysis_results = {}

    # If we got a final flow volume from the flow tracker, store it
    analysis_results["final_flow_ml"] = float(total_flow) if total_flow is not None else None

    # ---------------- RAW METRICS ----------------
    if len(df) >= 2:
        total_time_raw_s = df["Time_s"].iloc[-1] - df["Time_s"].iloc[0]
    else:
        total_time_raw_s = 0.0
    total_time_raw_min = total_time_raw_s / 60.0

    analysis_results["total_time_raw_s"] = total_time_raw_s
    analysis_results["total_time_raw_min"] = total_time_raw_min

    # Integrate flow across entire dataset
    total_vol_raw_ml = _integrate_flow(df)
    total_mass_raw_g = total_vol_raw_ml * fluid_density

    analysis_results["total_volume_raw_ml"] = total_vol_raw_ml
    analysis_results["total_mass_raw_g"] = total_mass_raw_g

    flow_all = df["flow"]
    analysis_results["avg_flow_raw"] = flow_all.mean()
    analysis_results["max_flow_raw"] = flow_all.max()

    if "temp" in df.columns:
        analysis_results["avg_temp_raw"] = df["temp"].mean()
    else:
        analysis_results["avg_temp_raw"] = None

    # ---------------- STABLE SUBSET ----------------
    if "userStable" in df.columns:
        stable_df = df[(df["on"] == True) & (df["userStable"] == True)].copy()
    else:
        stable_df = df.head(0)
    stable_df.reset_index(drop=True, inplace=True)

    # Save stable_data.csv
    stable_csv_path = os.path.join(out_stable_data_dir, "stable_data.csv")
    stable_df.to_csv(stable_csv_path, index=False)
    logger.info(f"Stable CSV => {stable_csv_path}")

    # ---------------- STABLE METRICS ----------------
    if len(stable_df) < 2:
        analysis_results["total_time_stable_s"] = 0.0
        analysis_results["total_time_stable_min"] = 0.0
        analysis_results["total_volume_stable_ml"] = 0.0
        analysis_results["total_mass_stable_g"] = 0.0
        analysis_results["avg_flow_stable"] = 0.0
        analysis_results["max_flow_stable"] = 0.0
        analysis_results["min_flow_stable"] = 0.0
        analysis_results["std_flow_stable"] = 0.0
        analysis_results["rstd_flow_stable"] = 0.0
        analysis_results["cov_flow_stable"] = 0.0
        analysis_results["avg_temp_stable"] = None
        analysis_results["min_temp_stable"] = None
        analysis_results["max_temp_stable"] = None
    else:
        total_time_stable_s = stable_df["Time_s"].iloc[-1] - stable_df["Time_s"].iloc[0]
        total_time_stable_min = total_time_stable_s / 60.0
        analysis_results["total_time_stable_s"] = total_time_stable_s
        analysis_results["total_time_stable_min"] = total_time_stable_min

        total_vol_stable_ml = _integrate_flow(stable_df)
        total_mass_stable_g = total_vol_stable_ml * fluid_density
        analysis_results["total_volume_stable_ml"] = total_vol_stable_ml
        analysis_results["total_mass_stable_g"] = total_mass_stable_g

        flow_stable = stable_df["flow"]
        mean_flow_stable = flow_stable.mean()
        std_flow_stable = flow_stable.std()
        min_flow_stable = flow_stable.min()
        max_flow_stable = flow_stable.max()

        analysis_results["avg_flow_stable"] = mean_flow_stable
        analysis_results["max_flow_stable"] = max_flow_stable
        analysis_results["min_flow_stable"] = min_flow_stable
        analysis_results["std_flow_stable"] = std_flow_stable

        if mean_flow_stable != 0.0:
            rsd_flow_stable = (std_flow_stable / mean_flow_stable) * 100.0
            cov_flow_stable = std_flow_stable / mean_flow_stable
        else:
            rsd_flow_stable = 0.0
            cov_flow_stable = 0.0

        analysis_results["rstd_flow_stable"] = rsd_flow_stable
        analysis_results["cov_flow_stable"] = cov_flow_stable

        if "temp" in stable_df.columns:
            temp_stable = stable_df["temp"]
            analysis_results["avg_temp_stable"] = temp_stable.mean()
            analysis_results["min_temp_stable"] = temp_stable.min()
            analysis_results["max_temp_stable"] = temp_stable.max()
        else:
            analysis_results["avg_temp_stable"] = None
            analysis_results["min_temp_stable"] = None
            analysis_results["max_temp_stable"] = None

    # ----------- Round numeric fields to 4 decimals -----------
    for key, val in analysis_results.items():
        if isinstance(val, (int, float)):
            analysis_results[key] = round(val, 4)

    # ---------------- SAVE ANALYSIS JSON ----------------
    analysis_json_path = os.path.join(out_analysis_dir, "analysis_results.json")
    with open(analysis_json_path, "w") as f:
        json.dump(analysis_results, f, indent=2)
    logger.info(f"Analysis JSON => {analysis_json_path}")

    # ---------------- Plot: Full flow + stable overlay ---------------
    flow_profile_path = os.path.join(out_raw_plots_dir, "flow_profile.png")
    plt.figure(figsize=(8,4))

    # entire dataset
    plt.plot(df["Time_s"], df["flow"], label="Flow (All)", color="blue", alpha=0.6)
    plt.plot(df["Time_s"], df["setpt"], label="Setpt (All)", color="gray", alpha=0.6)

    # stable overlay
    plt.plot(
        stable_df["Time_s"],
        stable_df["flow"],
        label="Flow (Stable)",
        color="red",
        linewidth=2
    )
    plt.plot(
        stable_df["Time_s"],
        stable_df["setpt"],
        label="Setpt (Stable)",
        color="green",
        linewidth=2
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Flow / Setpt")
    plt.legend()
    plt.title("Flow Profile with Stable Region Overlaid")
    plt.savefig(flow_profile_path)
    plt.close()
    logger.info(f"Full-flow profile => {flow_profile_path}")

    # ---------------- Plot: stable-only ---------------
    stable_plot_path = os.path.join(out_stable_plots_dir, "stable_data_plot.png")
    plt.figure(figsize=(8,4))
    plt.plot(stable_df["Time_s"], stable_df["flow"], label="Flow (Stable)", color="red")
    plt.plot(stable_df["Time_s"], stable_df["setpt"], label="Setpt (Stable)", color="green")

    plt.xlabel("Time (s)")
    plt.ylabel("Flow / Setpt")
    plt.legend()
    plt.title("Stable Flow Region Only")
    plt.savefig(stable_plot_path)
    plt.close()
    logger.info(f"Stable-only plot => {stable_plot_path}")

    logger.info(f"Done analyzing. fluid_density={fluid_density}, total_flow={total_flow}")


def _integrate_flow(df: pd.DataFrame) -> float:
    """
    Integrate flow over time using the trapezoid rule.

    The 'flow' column is in ml/min, 'Time_s' is in seconds.
    We convert flow to ml/s, then integrate piecewise across 'Time_s'.

    :param df: Pandas DataFrame with 'flow' and 'Time_s' columns.
    :return: Total integrated volume in ml.
    """
    if len(df) < 2:
        return 0.0

    df_sorted = df.sort_values("Time_s").reset_index(drop=True)
    total_vol = 0.0

    for i in range(len(df_sorted) - 1):
        t_i   = df_sorted["Time_s"].iloc[i]
        t_ip1 = df_sorted["Time_s"].iloc[i+1]
        dt    = t_ip1 - t_i  # seconds

        flow_i   = df_sorted["flow"].iloc[i]
        flow_ip1 = df_sorted["flow"].iloc[i+1]

        # flow in ml/min => convert to ml/s
        flow_s_i   = flow_i   / 60.0
        flow_s_ip1 = flow_ip1 / 60.0

        # average flow (ml/s) over dt
        avg_flow_s = (flow_s_i + flow_s_ip1) / 2.0
        partial_vol = avg_flow_s * dt
        total_vol += partial_vol

    return total_vol
