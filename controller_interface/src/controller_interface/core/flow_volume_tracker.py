import os
import json
import time

class FlowVolumeTracker:
    """
    Tracks the total volume of liquid that passes through the system, in milliliters (mL).

    If desired, can persist the total to disk (data_file).
    """

    def __init__(self, data_file=None):
        """
        :param data_file: Optional path to a JSON file for persisting total volume.
        """
        self._data_file = data_file
        self._total_volume_ml = 0.0  # Store total volume in mL
        self._last_update_time = time.time()

        # If a file is specified, try loading existing data
        if self._data_file and os.path.exists(self._data_file):
            self._load_data()

    def _load_data(self):
        with open(self._data_file, 'r') as f:
            data = json.load(f)
        self._total_volume_ml = data.get("total_volume_ml", 0.0)

    def _save_data(self):
        data = {"total_volume_ml": self._total_volume_ml}
        with open(self._data_file, 'w') as f:
            json.dump(data, f)

    def update_volume(self, flow_rate_ml_per_min, current_time=None):
        """
        Adds the volume that passed since the last update.

        :param flow_rate_ml_per_min: Flow rate in mL/min.
        :param current_time: An optional timestamp (defaults to time.time()).
        """
        if current_time is None:
            current_time = time.time()

        elapsed_sec = current_time - self._last_update_time
        elapsed_min = elapsed_sec / 60.0

        # Calculate the volume passed in this interval
        volume_passed = flow_rate_ml_per_min * elapsed_min
        self._total_volume_ml += volume_passed

        # Update the last update time
        self._last_update_time = current_time

        # Persist if desired
        if self._data_file is not None:
            self._save_data()

    def get_total_volume_ml(self):
        """Return the total volume in milliliters."""
        return self._total_volume_ml

    def reset_volume(self):
        """Reset total volume to zero mL and save if a file is used."""
        self._total_volume_ml = 0.0
        self._last_update_time = time.time()
        if self._data_file:
            self._save_data()
