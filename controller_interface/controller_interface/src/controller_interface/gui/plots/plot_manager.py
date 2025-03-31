import pyqtgraph as pg
from PyQt5.QtCore import Qt
import math

class TimeAxisItem(pg.AxisItem):
    """
    A custom AxisItem for PyQtGraph that formats numeric X values (in seconds)
    into mm:ss strings.
    """
    def __init__(self, orientation, *args, **kwargs):
        super().__init__(orientation=orientation, *args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        """
        Convert each numeric 'value' (representing seconds) into mm:ss format.
        """
        return [self._sec_to_mmss(v) for v in values]

    def _sec_to_mmss(self, secs):
        minutes = int(secs // 60)
        seconds = int(secs % 60)
        return f"{minutes:02d}:{seconds:02d}"


class PlotManager:
    """
    A PyQtGraph-based manager with three subplots:
      1) top_plot: Flow / Setpt / Bubble
      2) mid_plot: Voltage
      3) bot_plot: Temperature

    Features:
      - Double x-axis (top & bottom) in mm:ss format
      - 'bubble' line placed at setpoint if bubble_bool is True
      - time_window logic for sliding the x-range (only keep the last window's data)
      - Slightly lighter pink for Flow: (255, 105, 180)
    """

    def __init__(self, parent_layout, time_window=2.0):
        """
        :param parent_layout: Layout to which we add our PlotWidgets
        :param time_window: (float) number of seconds to keep on screen (slides).
                            If <=0, it grows unbounded.
        """
        self.time_window = time_window  # store the plot window in seconds

        # Data arrays
        self.t_s = []
        self.flow_vals   = []
        self.setpt_vals  = []
        self.bubble_vals = []
        self.volt_vals   = []
        self.temp_vals   = []

        # ------------ TOP PLOT ------------
        self.top_plot = self._create_plot_widget(parent_layout, "Flow / Setpt / Bubble")

        # Flow: slightly lighter pink => (255, 105, 180)
        self.flow_curve = self.top_plot.plot(
            [], pen=pg.mkPen(color=(247, 146, 203), width=2), name='Flow'
        )

        # Setpt: lighter green => (144, 238, 144)
        self.setpt_curve = self.top_plot.plot(
            [], pen=pg.mkPen(color=(146, 247, 158), width=2), name='Setpt'
        )

        # Bubble: softer gray => (210, 210, 210)
        self.bubble_curve = self.top_plot.plot(
            [], pen=pg.mkPen(color=(210, 210, 210), style=Qt.DotLine, width=2), name='Bubble'
        )

        # ------------ MIDDLE PLOT ------------
        self.mid_plot = self._create_plot_widget(parent_layout, "Voltage")

        # Volt: lighter yellow => (255, 255, 128)
        self.volt_curve = self.mid_plot.plot(
            [], pen=pg.mkPen(color=(255, 255, 128), width=2), name='Volt'
        )

        # ------------ BOTTOM PLOT ------------
        self.bot_plot = self._create_plot_widget(parent_layout, "Temp")

        # Temp: lighter red => (255, 128, 128)
        self.temp_curve = self.bot_plot.plot(
            [], pen=pg.mkPen(color=(255, 128, 128), width=2), name='Temp'
        )

    def _create_plot_widget(self, parent_layout, left_label: str):
        """
        Helper to create a PlotWidget with double X-axis (top & bottom) in mm:ss.
        """
        # A PlotWidget that replaces the default bottom axis with a TimeAxisItem
        plot_wid = pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        parent_layout.addWidget(plot_wid)

        plot_wid.setLabel('left', left_label)
        plot_wid.setLabel('bottom', 'Time (mm:ss)')
        plot_wid.showGrid(x=True, y=True, alpha=0.3)
        plot_wid.addLegend()

        # Show top axis, also using TimeAxisItem
        plot_wid.showAxis('top', show=True)
        top_axis = TimeAxisItem(orientation='top')
        plot_wid.setAxisItems({'top': top_axis})
        top_axis.linkToView(plot_wid.getViewBox())
        # No explicit label for the top axis => just mm:ss tick marks

        return plot_wid

    def set_time_window(self, tw: float):
        """Update the time window at runtime."""
        self.time_window = tw

    def start_run(self):
        """Clears data arrays and resets plots for a new run."""
        self.t_s.clear()
        self.flow_vals.clear()
        self.setpt_vals.clear()
        self.bubble_vals.clear()
        self.volt_vals.clear()
        self.temp_vals.clear()

        self.flow_curve.setData([], [])
        self.setpt_curve.setData([], [])
        self.bubble_curve.setData([], [])
        self.volt_curve.setData([], [])
        self.temp_curve.setData([], [])

    def update_data(self, data_dict, elapsed_s):
        """
        data_dict: { 'flow':..., 'setpt':..., 'bubble':..., 'volt':..., 'temp':..., ... }
        elapsed_s: float, seconds since run start

        1) Place bubble line at setpt if bubble_bool is True, else hide (NaN).
        2) Keep only last 'time_window' seconds of data, so the plot slides.
        3) Update curves.
        """
        flow_val    = float(data_dict.get("flow",  0.0))
        setpt_val   = float(data_dict.get("setpt", 0.0))
        bubble_bool = data_dict.get("bubble", False)
        volt_val    = float(data_dict.get("volt",  0.0))
        temp_val    = float(data_dict.get("temp",  0.0))

        # If bubble_bool => bubble y-value = setpt_val; else => NaN
        bubble_val = setpt_val if bubble_bool else float('nan')

        # Append new data
        self.t_s.append(elapsed_s)
        self.flow_vals.append(flow_val)
        self.setpt_vals.append(setpt_val)
        self.bubble_vals.append(bubble_val)
        self.volt_vals.append(volt_val)
        self.temp_vals.append(temp_val)

        # Remove data older than 'elapsed_s - time_window'
        if self.time_window > 0.0:
            min_time = elapsed_s - self.time_window
            while len(self.t_s) > 1 and self.t_s[0] < min_time:
                self.t_s.pop(0)
                self.flow_vals.pop(0)
                self.setpt_vals.pop(0)
                self.bubble_vals.pop(0)
                self.volt_vals.pop(0)
                self.temp_vals.pop(0)

        # Update curves
        self.flow_curve.setData(self.t_s, self.flow_vals)
        self.setpt_curve.setData(self.t_s, self.setpt_vals)
        self.bubble_curve.setData(self.t_s, self.bubble_vals)
        self.volt_curve.setData(self.t_s, self.volt_vals)
        self.temp_curve.setData(self.t_s, self.temp_vals)

        # Optionally fix the x-range to [elapsed_s - time_window, elapsed_s]
        # if self.time_window > 0:
        #     lastX = self.t_s[-1]
        #     firstX = max(0, lastX - self.time_window)
        #     self.top_plot.setXRange(firstX, lastX)
        #     self.mid_plot.setXRange(firstX, lastX)
        #     self.bot_plot.setXRange(firstX, lastX)
        # else:
        #     pass
