import pyqtgraph as pg
from PyQt5.QtCore import Qt

from controller_interface.view.plots import color_presets as clr
from controller_interface.view.plots.plot_factory import (
    create_plot_widget,
    mirror_axis_same_scale
)

class TuningPlotManager:
    """
    Manages PlotWidgets for visualizing flow, setpoint, temperature, etc.
    Now excludes P & D, plus pGain & dGain, and instead adds alpha.
    """

    def __init__(self, parent_layout):
        self.time_window = 0.0
        self.t_s = []

        # ------------------------------------------------------------
        # 1) Adjust the data buffers to remove p/d/pGain/dGain
        #    and add alpha (or "currentAlpha").
        # ------------------------------------------------------------
        self.data_buffers = {
            'flow': [],
            'setpt': [],
            'filtered_err': [],
            'volt': [],
            'temp': [],
            'i': [],        # Keep the I term if desired
            'iGain': [],    # Keep the I gain
            'alpha': [],    # <--- new: store filter alpha here
        }

        self.curves = {}

        # We assume you still want 4 plots total:
        #   1) Flow/Setpt/fErr
        #   2) Voltage / Temperature
        #   3) I
        #   4) iGain / alpha
        #
        # If you no longer want Plot 3, you can remove it.
        self._setup_plot1(parent_layout)
        self._setup_plot2(parent_layout)
        self._setup_plot3(parent_layout)
        self._setup_plot4(parent_layout)

    def _setup_plot1(self, parent_layout):
        """Plot 1 => Flow, Setpt, FilteredErr on left axis."""
        self.plot1 = create_plot_widget("Flow/Setpt/fErr", show_top_axis=True)
        parent_layout.addWidget(self.plot1)
        plot_item = self.plot1.getPlotItem()

        self.curves["flow"] = plot_item.plot([], pen=pg.mkPen(color=clr.FLOW_COLOR, width=4), name='Flow')
        self.curves["setpt"] = plot_item.plot([], pen=pg.mkPen(color=clr.SETPT_COLOR, width=4), name='Setpt')
        self.curves["filtered_err"] = plot_item.plot([], pen=pg.mkPen(color=clr.FILTERED_ERR, width=4), name='fErr')

        mirror_axis_same_scale(self.plot1, axis_name="right", label_text="Flow/Setpt/fErr")

    def _setup_plot2(self, parent_layout):
        """Plot 2 => Volt on left axis, Temp on a right ViewBox."""
        self.plot2 = create_plot_widget("Voltage")
        parent_layout.addWidget(self.plot2)
        plot_item = self.plot2.getPlotItem()

        self.curves["volt"] = plot_item.plot([], pen=pg.mkPen(color=clr.VOLT_COLOR, width=4), name='Volt')

        self.vb_right_2 = pg.ViewBox()
        self.curves["temp"] = pg.PlotCurveItem(pen=pg.mkPen(color=clr.TEMP_COLOR, width=4), name='Temp')
        self.vb_right_2.addItem(self.curves["temp"])

        mirror_axis_same_scale(self.plot2, "right", "Temp (°C)", self.vb_right_2)
        if plot_item.legend is not None:
            plot_item.legend.addItem(self.curves["temp"], "Temp")

        def updateViews2():
            self.vb_right_2.setGeometry(self.plot2.getViewBox().sceneBoundingRect())
        self.plot2.getViewBox().sigResized.connect(updateViews2)

    def _setup_plot3(self, parent_layout):
        """
        Plot 3 => Just the I term (if you want to see the integral output).
        We removed p & d curves here.
        """
        self.plot3 = create_plot_widget("I-term")
        parent_layout.addWidget(self.plot3)
        plot_item = self.plot3.getPlotItem()

        # Put i on the left axis
        self.curves["i"] = plot_item.plot([], pen=pg.mkPen(color=clr.I_COLOR, width=4), name='I')

        # If you only have one curve, you might not need a second axis or a legend.
        mirror_axis_same_scale(self.plot3, "right", "I-term")
        if plot_item.legend is not None:
            plot_item.legend.addItem(self.curves["i"], "I")

    def _setup_plot4(self, parent_layout):
        """
        Plot 4 => iGain (left axis) / alpha (right axis).
        We removed pGain/dGain completely and replaced them with alpha.
        """
        self.plot4 = create_plot_widget("iGain / alpha")
        parent_layout.addWidget(self.plot4)
        plot_item = self.plot4.getPlotItem()

        # iGain on the main (left) axis
        self.curves["iGain"] = plot_item.plot([], pen=pg.mkPen(color=clr.I_COLOR, width=4), name='iGain')

        # alpha on the right axis
        self.vb_right_4 = pg.ViewBox()
        # Choose any color for alpha. If you have a color, use it. Otherwise, define one:
        self.curves["alpha"] = pg.PlotCurveItem(pen=pg.mkPen(color='white', width=4), name='alpha')
        self.vb_right_4.addItem(self.curves["alpha"])

        mirror_axis_same_scale(self.plot4, "right", "alpha", self.vb_right_4)
        if plot_item.legend is not None:
            plot_item.legend.addItem(self.curves["alpha"], "alpha")

        def updateViews4():
            self.vb_right_4.setGeometry(self.plot4.getViewBox().sceneBoundingRect())
        self.plot4.getViewBox().sigResized.connect(updateViews4)

    def set_time_window(self, tw: float):
        self.time_window = tw

    def start_run(self):
        """Clears all data buffers + curves."""
        self.t_s.clear()
        for k in self.data_buffers.keys():
            self.data_buffers[k].clear()

        # Clear curve data
        for c_name in self.curves:
            self.curves[c_name].setData([], [])

    def update_data(self, data_dict, elapsed_s: float):
        """
        Updates data buffers and re-plots curves, possibly applying a sliding window
        if self.time_window > 0.
        """
        self.t_s.append(elapsed_s)

        # -------------------------------------------------------
        # 1) Parse data from data_dict
        # -------------------------------------------------------
        flow_val  = float(data_dict.get("flow", 0.0))
        setpt_val = float(data_dict.get("setpt", 0.0))
        # We'll offset filteredErr by setpt to visualize it "on top of" setpt
        fErr_val  = setpt_val + float(data_dict.get("filteredErr", 0.0))

        volt_val  = float(data_dict.get("volt", 0.0))
        temp_val  = float(data_dict.get("temp", 0.0))

        i_val     = float(data_dict.get("I", 0.0))
        iGain_val = float(data_dict.get("iGain", 0.0))

        # The "alpha" key might be "currentAlpha" in your data_dict:
        alpha_val = float(data_dict.get("currentAlpha", 0.0))

        # -------------------------------------------------------
        # 2) Append to buffers
        # -------------------------------------------------------
        self.data_buffers["flow"].append(flow_val)
        self.data_buffers["setpt"].append(setpt_val)
        self.data_buffers["filtered_err"].append(fErr_val)
        self.data_buffers["volt"].append(volt_val)
        self.data_buffers["temp"].append(temp_val)
        self.data_buffers["i"].append(i_val)
        self.data_buffers["iGain"].append(iGain_val)
        self.data_buffers["alpha"].append(alpha_val)

        # -------------------------------------------------------
        # 3) Apply sliding window (if time_window > 0)
        # -------------------------------------------------------
        if self.time_window > 0.0:
            min_time = elapsed_s - self.time_window
            while len(self.t_s) > 1 and self.t_s[0] < min_time:
                self.t_s.pop(0)
                for key in self.data_buffers:
                    self.data_buffers[key].pop(0)

        # -------------------------------------------------------
        # 4) Update each curve
        # -------------------------------------------------------
        # Plot 1
        self.curves["flow"].setData(self.t_s, self.data_buffers["flow"])
        self.curves["setpt"].setData(self.t_s, self.data_buffers["setpt"])
        self.curves["filtered_err"].setData(self.t_s, self.data_buffers["filtered_err"])

        # Plot 2
        self.curves["volt"].setData(self.t_s, self.data_buffers["volt"])
        self.curves["temp"].setData(self.t_s, self.data_buffers["temp"])

        # Plot 3 (only i)
        self.curves["i"].setData(self.t_s, self.data_buffers["i"])

        # Plot 4 (iGain on left, alpha on right)
        self.curves["iGain"].setData(self.t_s, self.data_buffers["iGain"])
        self.curves["alpha"].setData(self.t_s, self.data_buffers["alpha"])
