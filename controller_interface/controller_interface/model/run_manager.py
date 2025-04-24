# controller_interface/core/run_manager.py

import os
import csv
import time
from datetime import datetime
from typing import Optional

from controller_interface import analyze_data
from controller_interface.utils.logging_utils import logger


class RunManager:
    """
    Manages creation of subfolders for a run, CSV file handling, and post-run analysis.
    """

    def __init__(self, data_root: str):
        """
        :param data_root: Base directory where run folders are created
        """
        self.data_root: str = data_root
        self.run_folder: Optional[str] = None
        self.raw_data_dir: Optional[str] = None
        self.raw_plots_dir: Optional[str] = None
        self.proc_anal_dir: Optional[str] = None
        self.proc_stable_data_dir: Optional[str] = None
        self.proc_stable_plots_dir: Optional[str] = None

        self.csv_file = None
        self.csv_writer = None
        self.csv_path: Optional[str] = None

    def create_run_folders(self, test_name: str, user_name: str, timestamp: str) -> None:
        """
        Create the subfolders for a new run under data_root:
         {test_name}_{user_name}_{timestamp}/raw/data, raw/plots, etc.
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

        logger.debug(f"Run folders created under: {self.run_folder}")

    def open_csv(self, test_name: str, user_name: str, timestamp: str) -> None:
        """
        Create and open the CSV file in raw_data_dir, write header with advanced fields.
        """
        if not self.raw_data_dir:
            logger.warning("raw_data_dir is not set. Did you call create_run_folders first?")
            return

        csv_name = f"raw_{test_name}_{user_name}_{timestamp}.csv"
        self.csv_path = os.path.join(self.raw_data_dir, csv_name)
        logger.debug(f"CSV path set to: {self.csv_path}")

        self.csv_file = open(self.csv_path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)

        # We add new columns for absolute time + relative times in ms, s, and m
        header = [
            "absTimeISO",     
            "relTimeMs",       
            "relTimeSec",      
            "relTimeMin",     
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
        logger.info(f"CSV header written to {self.csv_path}")

    def write_csv_row(self, row) -> None:
        """
        Append a row (list or tuple) to the CSV. Must match the header in length + order.
        
        """
        if self.csv_writer:
            self.csv_writer.writerow(row)
        else:
            logger.warning("Attempted to write to CSV, but csv_writer is not initialized.")

    def close_csv(self) -> None:
        """
        Close the CSV file if open.
        """
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            logger.info(f"CSV file closed: {self.csv_path}")
        self.csv_writer = None

    def run_post_analysis(self, fluid_density: float = 1.0, total_flow: float = 0.0) -> None:
        """
        After capture stops, call analyze_data with the relevant subfolders.
        Now also accepts 'fluid_density' and 'total_flow' for logging or further analysis.
        """
        if not self.raw_data_dir:
            logger.warning("No raw_data_dir set. Post-analysis aborted.")
            return

        raw_csv = None
        for f in os.listdir(self.raw_data_dir):
            if f.endswith(".csv"):
                raw_csv = os.path.join(self.raw_data_dir, f)
                break

        if not raw_csv:
            logger.warning("No raw CSV found for analysis in raw_data_dir.")
            return

        logger.debug(f"Running post-analysis on {raw_csv}")
        analyze_data(
            csv_path=raw_csv,
            out_analysis_dir=self.proc_anal_dir,
            out_stable_data_dir=self.proc_stable_data_dir,
            out_stable_plots_dir=self.proc_stable_plots_dir,
            out_raw_plots_dir=self.raw_plots_dir,
            fluid_density=fluid_density,
            total_flow=total_flow
        )
        logger.info("Post-analysis completed.")

    def get_run_folder(self) -> str | None:
        """
        :return: The top-level folder for this run, or None if not created yet.
        """
        return self.run_folder
