# controller_interface/src/view/plots/plot_manager.py

import pyqtgraph as pg
from PyQt5.QtCore import Qt

from controller_interface.view.plots import color_presets as clr
from controller_interface.view.plots.plot_factory import (
    create_plot_widget,
    mirror_axis_same_scale
)

class TuningPlotManager:
    """
    Manages 4 stacked PlotWidgets showing flow, setpoint, PID terms, etc.
    Each plot is created with consistent styling, then we store references
    to the curve objects in self.curves, and data buffers in self.data_buffers.
    """

    def __init__(self, parent_layout):
        self.time_window = 0.0
        self.t_s = []

        # Dictionary-of-lists for data
        self.data_buffers = {
            'flow': [], 'setpt': [], 'filtered_err': [],
            'volt': [], 'temp': [],
            'p': [], 'i': [], 'd': [],
            'pGain': [], 'iGain': [], 'dGain': [],
        }

        # Store curve references by name
        self.curves = {}

        # Create each plot
        self._setup_plot1(parent_layout)
        self._setup_plot2(parent_layout)
        self._setup_plot3(parent_layout)
        self._setup_plot4(parent_layout)

    def _setup_plot1(self, parent_layout):
        """Plot 1 => Flow, Setpt, FilteredErr on the left axis."""
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
        """Plot 3 => P & D on left, I on right."""
        self.plot3 = create_plot_widget("P / D")
        parent_layout.addWidget(self.plot3)
        plot_item = self.plot3.getPlotItem()

        self.curves["p"] = plot_item.plot([], pen=pg.mkPen(color=clr.P_COLOR, width=4), name='P')
        self.curves["d"] = plot_item.plot([], pen=pg.mkPen(color=clr.D_COLOR, width=4), name='D')

        self.vb_right_3 = pg.ViewBox()
        self.curves["i"] = pg.PlotCurveItem(pen=pg.mkPen(color=clr.I_COLOR, width=4), name='I')
        self.vb_right_3.addItem(self.curves["i"])

        mirror_axis_same_scale(self.plot3, "right", "I", self.vb_right_3)
        if plot_item.legend is not None:
            plot_item.legend.addItem(self.curves["i"], "I")

        def updateViews3():
            self.vb_right_3.setGeometry(self.plot3.getViewBox().sceneBoundingRect())
        self.plot3.getViewBox().sigResized.connect(updateViews3)

    def _setup_plot4(self, parent_layout):
        """Plot 4 => pGain & dGain on left, iGain on right."""
        self.plot4 = create_plot_widget("pGain / dGain")
        parent_layout.addWidget(self.plot4)
        plot_item = self.plot4.getPlotItem()

        self.curves["pGain"] = plot_item.plot([], pen=pg.mkPen(color=clr.P_COLOR, width=4), name='pGain')
        self.curves["dGain"] = plot_item.plot([], pen=pg.mkPen(color=clr.D_COLOR, width=4), name='dGain')

        self.vb_right_4 = pg.ViewBox()
        self.curves["iGain"] = pg.PlotCurveItem(pen=pg.mkPen(color=clr.I_COLOR, width=4), name='iGain')
        self.vb_right_4.addItem(self.curves["iGain"])

        mirror_axis_same_scale(self.plot4, "right", "iGain", self.vb_right_4)
        if plot_item.legend is not None:
            plot_item.legend.addItem(self.curves["iGain"], "iGain")

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

        # Parse data from data_dict
        flow_val  = float(data_dict.get("flow", 0.0))
        setpt_val = float(data_dict.get("setpt", 0.0))
        # We'll offset filteredErr by setpt to visualize it "on top of" setpt
        fErr_val  = setpt_val + float(data_dict.get("filteredErr", 0.0))

        self.data_buffers["flow"].append(flow_val)
        self.data_buffers["setpt"].append(setpt_val)
        self.data_buffers["filtered_err"].append(fErr_val)

        self.data_buffers["volt"].append( float(data_dict.get("volt", 0.0)) )
        self.data_buffers["temp"].append( float(data_dict.get("temp", 0.0)) )

        self.data_buffers["p"].append( float(data_dict.get("P", 0.0)) )
        self.data_buffers["i"].append( float(data_dict.get("I", 0.0)) )
        self.data_buffers["d"].append( float(data_dict.get("D", 0.0)) )

        self.data_buffers["pGain"].append( float(data_dict.get("pGain", 0.0)) )
        self.data_buffers["iGain"].append( float(data_dict.get("iGain", 0.0)) )
        self.data_buffers["dGain"].append( float(data_dict.get("dGain", 0.0)) )

        # Sliding window
        if self.time_window > 0.0:
            min_time = elapsed_s - self.time_window
            while len(self.t_s) > 1 and self.t_s[0] < min_time:
                self.t_s.pop(0)
                for key in self.data_buffers:
                    self.data_buffers[key].pop(0)

        # Update each curve
        self.curves["flow"].setData(self.t_s, self.data_buffers["flow"])
        self.curves["setpt"].setData(self.t_s, self.data_buffers["setpt"])
        self.curves["filtered_err"].setData(self.t_s, self.data_buffers["filtered_err"])

        self.curves["volt"].setData(self.t_s, self.data_buffers["volt"])
        self.curves["temp"].setData(self.t_s, self.data_buffers["temp"])

        self.curves["p"].setData(self.t_s, self.data_buffers["p"])
        self.curves["i"].setData(self.t_s, self.data_buffers["i"])
        self.curves["d"].setData(self.t_s, self.data_buffers["d"])

        self.curves["pGain"].setData(self.t_s, self.data_buffers["pGain"])
        self.curves["dGain"].setData(self.t_s, self.data_buffers["dGain"])
        self.curves["iGain"].setData(self.t_s, self.data_buffers["iGain"])
