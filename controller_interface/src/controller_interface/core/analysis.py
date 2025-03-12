# app/core/analysis.py

import os
import json
import pandas as pd
import matplotlib.pyplot as plt

def analyze_data(
    csv_path,
    out_analysis_dir,
    out_stable_data_dir,
    out_stable_plots_dir,
    out_raw_plots_dir,
    stable_window=10,
    stable_threshold=0.05,
    fluid_density=1.0
):
    """
    Steps:
      1) Load raw CSV (timeMs, flow, setpt, etc.)
      2) 'on==True' filtering to find stable region:
         a consecutive stable_window where abs(flow - setpt) <= stable_threshold,
         from that index onward is stable.
      3) Save stable_data.csv
      4) Compute:
         - Total time raw, total time stable
         - Integrate flow over raw => total mL, then mass = volume * fluid_density
         - Integrate flow over stable => total mL, then mass = volume * fluid_density
         - stable stats (mean, std, RSD, COV, etc.)
         - raw dataset stats
      5) Save analysis_results.json (including fluid_density)
      6) Generate two plots:
         - full dataset with stable region overlaid
         - stable-only plot
    """

    if not os.path.isfile(csv_path):
        print(f"[ERROR] CSV not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"[INFO] Loaded CSV => {csv_path}, shape={df.shape}")

    # Sort by timeMs just in case
    df.sort_values("timeMs", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Convert timeMs to seconds
    df["Time_s"] = df["timeMs"] / 1000.0

    # We'll store analysis results in a dict
    analysis_results = {}
    # Record the fluid density used (e.g. 1.05 g/mL) for clarity
    analysis_results["fluid_density"] = float(fluid_density)

    # ---------- RAW Data stats -----------
    if len(df) >= 2:
        total_time_raw_s = df["Time_s"].iloc[-1] - df["Time_s"].iloc[0]
    else:
        total_time_raw_s = 0.0
    total_time_raw_min = total_time_raw_s / 60.0

    analysis_results["total_time_raw_s"]   = float(total_time_raw_s)
    analysis_results["total_time_raw_min"] = float(total_time_raw_min)

    # Integrate flow over entire DF => total volume in mL
    total_vol_raw_ml = _integrate_flow(df)
    # Convert to mass by multiplying fluid_density (g/mL)
    total_mass_raw_g = total_vol_raw_ml * fluid_density

    analysis_results["total_volume_raw_ml"] = float(total_vol_raw_ml)
    analysis_results["total_mass_raw_g"]    = float(total_mass_raw_g)

    # Some basic flow stats
    flow_all = df["flow"]
    analysis_results["avg_flow_raw"] = float(flow_all.mean())
    analysis_results["max_flow_raw"] = float(flow_all.max())

    # If temperature column present
    if "temp" in df.columns:
        analysis_results["avg_temp_raw"] = float(df["temp"].mean())
    else:
        analysis_results["avg_temp_raw"] = None

    # ---------- Find stable region -----------
    if "on" not in df.columns:
        print("[WARN] 'on' column not found. No stable region detection possible.")
        stable_df = df.head(0)
    else:
        on_df = df[df["on"] == True].copy()
        on_df.reset_index(drop=True, inplace=True)

        stable_start = None
        for i in range(len(on_df) - stable_window + 1):
            window = on_df.iloc[i : i + stable_window]
            max_diff = (window["flow"] - window["setpt"]).abs().max()
            if max_diff <= stable_threshold:
                stable_start = i
                break

        if stable_start is not None:
            stable_df = on_df.iloc[stable_start:].copy()
        else:
            stable_df = on_df.head(0)

    # Save stable_data.csv
    stable_csv_path = os.path.join(out_stable_data_dir, "stable_data.csv")
    stable_df.to_csv(stable_csv_path, index=False)
    print(f"[INFO] Stable CSV => {stable_csv_path}")

    # ---------- stable region metrics ---------
    if not stable_df.empty:
        # total time stable
        total_time_stable_s = stable_df["Time_s"].iloc[-1] - stable_df["Time_s"].iloc[0]
        total_time_stable_min = total_time_stable_s / 60.0
        analysis_results["total_time_stable_s"]   = float(total_time_stable_s)
        analysis_results["total_time_stable_min"] = float(total_time_stable_min)

        # integrate flow stable => volume in mL
        total_vol_stable_ml = _integrate_flow(stable_df)
        # mass => multiply by fluid_density
        total_mass_stable_g = total_vol_stable_ml * fluid_density

        analysis_results["total_volume_stable_ml"] = float(total_vol_stable_ml)
        analysis_results["total_mass_stable_g"]    = float(total_mass_stable_g)

        # stable flow stats
        flow_stable = stable_df["flow"]
        mean_flow_stable = float(flow_stable.mean())
        std_flow_stable  = float(flow_stable.std())
        min_flow_stable  = float(flow_stable.min())
        max_flow_stable  = float(flow_stable.max())

        analysis_results["avg_flow_stable"] = mean_flow_stable
        analysis_results["max_flow_stable"] = max_flow_stable
        analysis_results["min_flow_stable"] = min_flow_stable
        analysis_results["std_flow_stable"] = std_flow_stable

        if mean_flow_stable != 0.0:
            rsd_flow_stable = (std_flow_stable / mean_flow_stable) * 100.0
            cov_flow_stable = (std_flow_stable / mean_flow_stable)
        else:
            rsd_flow_stable = 0.0
            cov_flow_stable = 0.0

        analysis_results["rstd_flow_stable"] = rsd_flow_stable
        analysis_results["cov_flow_stable"]  = cov_flow_stable

        if "temp" in stable_df.columns:
            temp_stable = stable_df["temp"]
            analysis_results["avg_temp_stable"] = float(temp_stable.mean())
            analysis_results["min_temp_stable"] = float(temp_stable.min())
            analysis_results["max_temp_stable"] = float(temp_stable.max())
        else:
            analysis_results["avg_temp_stable"] = None
            analysis_results["min_temp_stable"] = None
            analysis_results["max_temp_stable"] = None
    else:
        # no stable data
        analysis_results["total_time_stable_s"]   = 0.0
        analysis_results["total_time_stable_min"] = 0.0
        analysis_results["total_volume_stable_ml"] = 0.0
        analysis_results["total_mass_stable_g"]    = 0.0
        analysis_results["avg_flow_stable"]        = 0.0
        analysis_results["max_flow_stable"]        = 0.0
        analysis_results["min_flow_stable"]        = 0.0
        analysis_results["std_flow_stable"]        = 0.0
        analysis_results["rstd_flow_stable"]       = 0.0
        analysis_results["cov_flow_stable"]        = 0.0
        analysis_results["avg_temp_stable"]        = None
        analysis_results["min_temp_stable"]        = None
        analysis_results["max_temp_stable"]        = None

    # ---------- Save analysis JSON -----------
    analysis_json_path = os.path.join(out_analysis_dir, "analysis_results.json")
    with open(analysis_json_path, "w") as f:
        json.dump(analysis_results, f, indent=2)
    print(f"[INFO] Analysis JSON => {analysis_json_path}")

    # ---------- Plot: full flow + stable overlay -----------
    flow_profile_path = os.path.join(out_raw_plots_dir, "flow_profile.png")
    plt.figure(figsize=(8,4))

    # entire dataset
    plt.plot(df["Time_s"], df["flow"], label="Flow (All)", color="blue", alpha=0.6)
    plt.plot(df["Time_s"], df["setpt"], label="Setpt (All)", color="gray", alpha=0.6)

    # stable overlay
    if not stable_df.empty:
        plt.plot(stable_df["Time_s"], stable_df["flow"], label="Flow (Stable)", color="red", linewidth=2)
        plt.plot(stable_df["Time_s"], stable_df["setpt"], label="Setpt (Stable)", color="green", linewidth=2)

    plt.xlabel("Time (s)")
    plt.ylabel("Flow / Setpt")
    plt.legend()
    plt.title("Flow Profile with Stable Region Overlaid")
    plt.savefig(flow_profile_path)
    plt.close()
    print(f"[INFO] Full-flow profile => {flow_profile_path}")

    # ---------- Plot: stable-only -----------
    stable_plot_path = os.path.join(out_stable_plots_dir, "stable_data_plot.png")
    if not stable_df.empty:
        plt.figure(figsize=(8,4))
        plt.plot(stable_df["Time_s"], stable_df["flow"], label="Flow (Stable)", color="red")
        plt.plot(stable_df["Time_s"], stable_df["setpt"], label="Setpt (Stable)", color="green")
        plt.xlabel("Time (s)")
        plt.ylabel("Flow / Setpt")
        plt.legend()
        plt.title("Stable Flow Region Only")
        plt.savefig(stable_plot_path)
        plt.close()
        print(f"[INFO] Stable-only plot => {stable_plot_path}")
    else:
        print("[INFO] No stable data, skipping stable-only plot.")

    print(f"[INFO] Done. stable_window={stable_window}, stable_threshold={stable_threshold}, fluid_density={fluid_density}")


def _integrate_flow(df):
    """
    Helper to integrate flow over time using trapezoid rule.
    flow in ml/min, time in seconds.
    Steps:
      1) Sort df by Time_s
      2) For i in range(len-1):
         dt = Time_s[i+1] - Time_s[i]
         flow_s_i   = flow[i]   / 60 => ml/s
         flow_s_ip1 = flow[i+1] / 60 => ml/s
         partialVol = ((flow_s_i + flow_s_ip1)/2) * dt
         sum
      Return total volume (ml).
    """
    if len(df) < 2:
        return 0.0

    df_sorted = df.sort_values("Time_s").reset_index(drop=True)
    total_vol = 0.0
    for i in range(len(df_sorted) - 1):
        t_i = df_sorted["Time_s"].iloc[i]
        t_ip1 = df_sorted["Time_s"].iloc[i+1]
        dt = t_ip1 - t_i

        flow_i   = df_sorted["flow"].iloc[i]     # ml/min
        flow_ip1 = df_sorted["flow"].iloc[i+1]   # ml/min

        flow_s_i   = flow_i   / 60.0  # ml/s
        flow_s_ip1 = flow_ip1 / 60.0

        avg_flow_s = (flow_s_i + flow_s_ip1) / 2.0
        partial_vol = avg_flow_s * dt
        total_vol += partial_vol

    return total_vol
