import time

class FlowVolumeTracker:
    """
    Tracks the total volume of liquid passing through the system, in milliliters (mL).
    This version does NOT persist to a JSON file; it keeps the total only in memory.
    """

    def __init__(self):
        """
        Initialize with total_volume=0 and record the current time for elapsed calculations.
        """
        self._total_volume_ml = 0.0
        self._last_update_time = time.time()

    def update_volume(self, flow_rate_ml_per_min, current_time=None):
        """
        Adds the volume that passed since the last update.

        :param flow_rate_ml_per_min: Flow rate in mL/min.
        :param current_time: Optional custom timestamp; defaults to time.time().
        """
        if current_time is None:
            current_time = time.time()

        elapsed_sec = current_time - self._last_update_time
        elapsed_min = elapsed_sec / 60.0

        # Volume passed in this interval
        volume_passed = flow_rate_ml_per_min * elapsed_min
        self._total_volume_ml += volume_passed

        # Update the last update time
        self._last_update_time = current_time

    def get_total_volume_ml(self):
        """Return the current total volume in milliliters."""
        return self._total_volume_ml

    def reset_volume(self):
        """Reset the total volume to zero and update the reference time."""
        self._total_volume_ml = 0.0
        self._last_update_time = time.time()
