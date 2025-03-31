# controller_interface/src/view/plots/time_axis_item.py

import pyqtgraph as pg

class TimeAxisItem(pg.AxisItem):
    """
    A custom AxisItem that formats numeric X values (seconds) into mm:ss strings.
    """

    def __init__(self, orientation='bottom', *args, **kwargs):
        super().__init__(orientation=orientation, *args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        """Convert each numeric 'value' (seconds) into mm:ss."""
        return [self._sec_to_mmss(v) for v in values]

    def _sec_to_mmss(self, secs):
        minutes = int(secs // 60)
        seconds = int(secs % 60)
        return f"{minutes:02d}:{seconds:02d}"
