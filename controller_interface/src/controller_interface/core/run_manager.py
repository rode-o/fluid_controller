import os
import csv
from datetime import datetime

from controller_interface.core.analysis import analyze_data

class RunManager:
    """
    Manages the subfolder creation, CSV file handling, and post-run analysis.
    """

    def __init__(self, data_root: str):
        self.data_root = data_root
        self.run_folder = None
        self.raw_data_dir = None
        self.raw_plots_dir = None
        self.proc_anal_dir = None
        self.proc_stable_data_dir = None
        self.proc_stable_plots_dir = None

        self.csv_file = None
        self.csv_writer = None
        self.csv_path = None

    def create_run_folders(self, test_name: str, user_name: str, timestamp: str):
        """
        Create the subfolders for a new run under data_root:
         test_{testName}_{userName}_{timestamp}/raw/data, raw/plots, etc.
        """
        self.run_folder = os.path.join(self.data_root, f"{test_name}_{user_name}_{timestamp}")
        self.raw_data_dir = os.path.join(self.run_folder, "raw", "data")
        self.raw_plots_dir = os.path.join(self.run_folder, "raw", "plots")
        self.proc_anal_dir = os.path.join(self.run_folder, "processed", "analysis")
        self.proc_stable_data_dir = os.path.join(self.run_folder, "processed", "stable_data", "data")
        self.proc_stable_plots_dir = os.path.join(self.run_folder, "processed", "stable_data", "plots")

        for d in [
            self.raw_data_dir,
            self.raw_plots_dir,
            self.proc_anal_dir,
            self.proc_stable_data_dir,
            self.proc_stable_plots_dir
        ]:
            os.makedirs(d, exist_ok=True)

    def open_csv(self, test_name: str, user_name: str, timestamp: str):
        """
        Create and open the CSV file in raw_data_dir, write header with all advanced fields.
        """
        csv_name = f"raw_{test_name}_{user_name}_{timestamp}.csv"
        self.csv_path = os.path.join(self.raw_data_dir, csv_name)
        self.csv_file = open(self.csv_path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)

        header = [
            "timeMs",
            "flow",
            "setpt",
            "temp",
            "bubble",
            "volt",
            "on",
            "errorPct",
            "pidOut",
            "P",
            "I",
            "D",
            "pGain",
            "iGain",
            "dGain",
            "filteredErr",
            "currentAlpha",
            "totalVolume",
            "userStable"
        ]
        self.csv_writer.writerow(header)

    def write_csv_row(self, row):
        """
        Append a row (list/tuple) to the CSV. Must match the header in length + order.
        """
        if self.csv_writer:
            self.csv_writer.writerow(row)

    def close_csv(self):
        """
        Close the CSV file.
        """
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
        self.csv_writer = None

    def run_post_analysis(self, fluid_density=None):
        """
        After capture stops, call analyze_data with the relevant subfolders.
        Now accepts 'fluid_density' and passes it to analyze_data so you
        don't get the 'unexpected keyword argument' error.
        """
        raw_csv = None
        if os.path.isdir(self.raw_data_dir):
            for f in os.listdir(self.raw_data_dir):
                if f.endswith(".csv"):
                    raw_csv = os.path.join(self.raw_data_dir, f)
                    break

        if not raw_csv:
            print("[WARN] No raw CSV found for analysis.")
            return

        # Pass fluid_density into analyze_data ONLY if your `analyze_data` signature
        # supports it. For example:
        #
        #   def analyze_data(..., fluid_density=1.0):
        #       ...
        #
        # If your analyze_data is truly "hard-coded" and does not accept fluid_density,
        # simply remove ", fluid_density=fluid_density" below or update analyze_data to match.

        analyze_data(
            csv_path=raw_csv,
            out_analysis_dir=self.proc_anal_dir,
            out_stable_data_dir=self.proc_stable_data_dir,
            out_stable_plots_dir=self.proc_stable_plots_dir,
            out_raw_plots_dir=self.raw_plots_dir,
            fluid_density=fluid_density  # <-- new parameter
        )

    def get_run_folder(self):
        return self.run_folder
