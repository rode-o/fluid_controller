import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class TimeAxisItem(pg.AxisItem):
    """
    A custom AxisItem that formats numeric X values (seconds) into mm:ss strings.
    """
    def __init__(self, orientation, *args, **kwargs):
        super().__init__(orientation=orientation, *args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        """Convert each numeric 'value' (seconds) into mm:ss."""
        return [self._sec_to_mmss(v) for v in values]

    def _sec_to_mmss(self, secs):
        minutes = int(secs // 60)
        seconds = int(secs % 60)
        return f"{minutes:02d}:{seconds:02d}"


class TuningPlotManager:
    """
    Plots with double x-axis, transparent background, 10pt fonts, 
    and fully saturated or near-pure colors for high contrast:
      Plot 1: 
        Flow => white (255,255,255)
        Setpt => green (0,255,0)
        FilteredErr => magenta (255,0,255)

      Plot 2: 
        Volt => yellow (255,255,0)
        Temp => red    (255,0,0)

      Plot 3 (left => P & D, right => I): 
        P => blue (0,0,255)
        D => orange (255,128,0)
        I => cyan (0,255,255)

      Plot 4 (left => pGain & dGain, right => iGain):
        pGain => same as P => (0,0,255)
        dGain => same as D => (255,128,0)
        iGain => same as I => (0,255,255)
    """

    def __init__(self, parent_layout):
        self.time_window = 0.0  # 0 => unbounded
        self.t_s = []

        # Plot 1
        self.flow_data         = []
        self.setpt_data        = []
        self.filtered_err_data = []

        # Plot 2
        self.volt_data = []
        self.temp_data = []

        # Plot 3
        self.p_data = []
        self.i_data = []
        self.d_data = []

        # Plot 4
        self.pGain_data = []
        self.iGain_data = []
        self.dGain_data = []

        # ---------- PLOT 1 (Flow / Setpt / fErr) ----------
        self.plot1 = self._create_plot_widget(parent_layout, left_label="Flow / Setpt / fErr")

        # Flow => white
        self.flow_curve = self.plot1.plot(
            [], pen=pg.mkPen(color=(255,255,255), width=4), name='Flow'
        )
        # Setpt => green
        self.setpt_curve = self.plot1.plot(
            [], pen=pg.mkPen(color=(0,255,0), width=4), name='Setpt'
        )
        # FilteredErr => magenta
        self.filtered_err_curve = self.plot1.plot(
            [], pen=pg.mkPen(color=(255,0,255), width=4), name='fErr'
        )

        # Mirror axis on the right
        self._mirror_axis_same_scale(self.plot1, axis_name="right", label_text="Flow/Setpt/fErr")

        # ---------- PLOT 2 (Voltage vs. Temp) ----------
        self.plot2 = self._create_plot_widget(parent_layout, left_label="Voltage")
        # Volt => yellow
        self.volt_curve = self.plot2.plot(
            [], pen=pg.mkPen(color=(255,255,0), width=4), name='Volt'
        )

        # Right axis => Temp => red
        self.vb_right_2 = pg.ViewBox()
        self.temp_curve = pg.PlotCurveItem(
            pen=pg.mkPen(color=(255,0,0), width=4), name='Temp'
        )
        self.vb_right_2.addItem(self.temp_curve)

        self._mirror_axis_same_scale(
            plot_wid=self.plot2,
            axis_name="right",
            label_text="Temp (°C)",
            vbox=self.vb_right_2
        )
        if self.plot2.plotItem.legend is not None:
            self.plot2.plotItem.legend.addItem(self.temp_curve, "Temp")

        def updateViews2():
            self.vb_right_2.setGeometry(self.plot2.getViewBox().sceneBoundingRect())
        self.plot2.getViewBox().sigResized.connect(updateViews2)

        # ---------- PLOT 3 (P & D vs. I) ----------
        self.plot3 = self._create_plot_widget(parent_layout, left_label="P / D")

        # P => blue
        self.p_curve = self.plot3.plot(
            [], pen=pg.mkPen(color=(0,0,255), width=4), name='P'
        )
        # D => orange
        self.d_curve = self.plot3.plot(
            [], pen=pg.mkPen(color=(255,128,0), width=4), name='D'
        )

        self.vb_right_3 = pg.ViewBox()
        # I => cyan
        self.i_curve = pg.PlotCurveItem(
            pen=pg.mkPen(color=(0,255,255), width=4), name='I'
        )
        self.vb_right_3.addItem(self.i_curve)

        self._mirror_axis_same_scale(
            plot_wid=self.plot3,
            axis_name="right",
            label_text="I",
            vbox=self.vb_right_3
        )
        if self.plot3.plotItem.legend is not None:
            self.plot3.plotItem.legend.addItem(self.i_curve, "I")

        def updateViews3():
            self.vb_right_3.setGeometry(self.plot3.getViewBox().sceneBoundingRect())
        self.plot3.getViewBox().sigResized.connect(updateViews3)

        # ---------- PLOT 4 (pGain & dGain vs. iGain) ----------
        self.plot4 = self._create_plot_widget(parent_layout, left_label="pGain / dGain")

        # pGain => same as P => (0,0,255)
        self.pGain_curve = self.plot4.plot(
            [], pen=pg.mkPen(color=(0,0,255), width=4), name='pGain'
        )
        # dGain => same as D => (255,128,0)
        self.dGain_curve = self.plot4.plot(
            [], pen=pg.mkPen(color=(255,128,0), width=4), name='dGain'
        )

        self.vb_right_4 = pg.ViewBox()
        # iGain => same as I => (0,255,255)
        self.iGain_curve = pg.PlotCurveItem(
            pen=pg.mkPen(color=(0,255,255), width=4), name='iGain'
        )
        self.vb_right_4.addItem(self.iGain_curve)

        self._mirror_axis_same_scale(
            plot_wid=self.plot4,
            axis_name="right",
            label_text="iGain",
            vbox=self.vb_right_4
        )
        if self.plot4.plotItem.legend is not None:
            self.plot4.plotItem.legend.addItem(self.iGain_curve, "iGain")

        def updateViews4():
            self.vb_right_4.setGeometry(self.plot4.getViewBox().sceneBoundingRect())
        self.plot4.getViewBox().sigResized.connect(updateViews4)

    def _create_plot_widget(self, parent_layout, left_label: str):
        """
        Creates a PlotWidget with:
          - transparent background
          - 10pt for tick labels and axis labels
          - lines are at width=4 for bright, high-contrast visuals
        """
        plot_wid = pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        parent_layout.addWidget(plot_wid)

        # Transparent
        plot_wid.setBackground(None)
        plot_wid.setAttribute(Qt.WA_TranslucentBackground, True)
        plot_wid.setStyleSheet("background: transparent;")

        # Tick font => 10pt
        tick_font = QFont()
        tick_font.setPointSize(10)

        # Axis label font => 10pt
        label_font = QFont()
        label_font.setPointSize(10)

        plot_item = plot_wid.getPlotItem()

        # Apply tickFont + white color
        for ax_name in ('left', 'bottom', 'top', 'right'):
            axis = plot_item.getAxis(ax_name)
            axis.setStyle(tickFont=tick_font)
            axis.setPen(pg.mkPen(color='white', width=1))
            axis.setTextPen('white')

        # Left axis label
        plot_wid.setLabel('left', left_label, color='white')
        left_axis = plot_item.getAxis('left')
        left_axis.label.setFont(label_font)

        # Bottom axis label
        plot_wid.setLabel('bottom', 'Time (mm:ss)', color='white')
        bot_axis = plot_item.getAxis('bottom')
        bot_axis.label.setFont(label_font)

        # Top axis label
        plot_wid.setLabel('top', 'Time (Top)', color='white')
        top_axis = plot_item.getAxis('top')
        top_axis.label.setFont(label_font)

        # Grid + legend
        plot_wid.showGrid(x=True, y=True, alpha=0.6)
        plot_wid.addLegend()

        # Show top axis
        plot_wid.showAxis('top', show=True)
        top_axis_item = TimeAxisItem(orientation='top')
        plot_wid.setAxisItems({'top': top_axis_item})
        top_axis_item.linkToView(plot_wid.getViewBox())

        return plot_wid

    def _mirror_axis_same_scale(self, plot_wid, axis_name="right", label_text="", vbox=None):
        """
        Mirror the main view's scale to 'axis_name', set the label to 10pt white,
        optionally link a separate ViewBox for that axis.
        """
        plot_wid.showAxis(axis_name, show=True)
        plot_wid.getAxis(axis_name).setLabel(label_text, color='white')

        # Force label to 10pt
        label_font = QFont()
        label_font.setPointSize(10)
        plot_wid.getAxis(axis_name).label.setFont(label_font)

        if vbox is not None:
            plot_wid.scene().addItem(vbox)
            plot_wid.getAxis(axis_name).linkToView(vbox)
            vbox.setXLink(plot_wid)
        else:
            plot_wid.getAxis(axis_name).linkToView(plot_wid.getViewBox())

    def set_time_window(self, tw: float):
        self.time_window = tw

    def start_run(self):
        self.t_s.clear()

        self.flow_data.clear()
        self.setpt_data.clear()
        self.filtered_err_data.clear()

        self.volt_data.clear()
        self.temp_data.clear()

        self.p_data.clear()
        self.i_data.clear()
        self.d_data.clear()

        self.pGain_data.clear()
        self.iGain_data.clear()
        self.dGain_data.clear()

        # Clear data from each curve
        self.flow_curve.setData([], [])
        self.setpt_curve.setData([], [])
        self.filtered_err_curve.setData([], [])

        self.volt_curve.setData([], [])
        self.temp_curve.setData([], [])

        self.p_curve.setData([], [])
        self.d_curve.setData([], [])
        self.i_curve.setData([], [])

        self.pGain_curve.setData([], [])
        self.dGain_curve.setData([], [])
        self.iGain_curve.setData([], [])

    def update_data(self, data_dict, elapsed_s):
        flow_val        = float(data_dict.get("flow", 0.0))
        setpt_val       = float(data_dict.get("setpt", 0.0))
        raw_filtered_err= float(data_dict.get("filteredErr", 0.0))
        shifted_filtered_err = setpt_val + raw_filtered_err

        volt_val = float(data_dict.get("volt", 0.0))
        temp_val = float(data_dict.get("temp", 0.0))

        p_val = float(data_dict.get("P", 0.0))
        i_val = float(data_dict.get("I", 0.0))
        d_val = float(data_dict.get("D", 0.0))

        pGain_val = float(data_dict.get("pGain", 0.0))
        iGain_val = float(data_dict.get("iGain", 0.0))
        dGain_val = float(data_dict.get("dGain", 0.0))

        self.t_s.append(elapsed_s)

        self.flow_data.append(flow_val)
        self.setpt_data.append(setpt_val)
        self.filtered_err_data.append(shifted_filtered_err)

        self.volt_data.append(volt_val)
        self.temp_data.append(temp_val)

        self.p_data.append(p_val)
        self.i_data.append(i_val)
        self.d_data.append(d_val)

        self.pGain_data.append(pGain_val)
        self.iGain_data.append(iGain_val)
        self.dGain_data.append(dGain_val)

        # Sliding window
        if self.time_window > 0.0:
            min_time = elapsed_s - self.time_window
            while len(self.t_s) > 1 and self.t_s[0] < min_time:
                self.t_s.pop(0)

                self.flow_data.pop(0)
                self.setpt_data.pop(0)
                self.filtered_err_data.pop(0)

                self.volt_data.pop(0)
                self.temp_data.pop(0)

                self.p_data.pop(0)
                self.i_data.pop(0)
                self.d_data.pop(0)

                self.pGain_data.pop(0)
                self.iGain_data.pop(0)
                self.dGain_data.pop(0)

        # Update each curve
        self.flow_curve.setData(self.t_s, self.flow_data)
        self.setpt_curve.setData(self.t_s, self.setpt_data)
        self.filtered_err_curve.setData(self.t_s, self.filtered_err_data)

        self.volt_curve.setData(self.t_s, self.volt_data)
        self.temp_curve.setData(self.t_s, self.temp_data)

        self.p_curve.setData(self.t_s, self.p_data)
        self.d_curve.setData(self.t_s, self.d_data)
        self.i_curve.setData(self.t_s, self.i_data)

        self.pGain_curve.setData(self.t_s, self.pGain_data)
        self.dGain_curve.setData(self.t_s, self.dGain_data)
        self.iGain_curve.setData(self.t_s, self.iGain_data)
