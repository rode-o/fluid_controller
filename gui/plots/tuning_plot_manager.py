import pyqtgraph as pg
from PyQt5.QtCore import Qt

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
    Creates four plots with double x-axis in mm:ss for each:
      Plot 1 (top): Flow, Setpt, and Filtered Error (shifted to setpoint)
      Plot 2 (middle): P & D (left axis), I (right axis)
      Plot 3: Voltage
      Plot 4: Gains (pGain, dGain on left axis; iGain on right axis)

    Also includes a time_window approach for a sliding window if time_window > 0.
    """

    def __init__(self, parent_layout):
        self.time_window = 0.0  # 0 => unbounded

        # --------------------------------
        # Data arrays
        # --------------------------------
        self.t_s = []

        # (Plot 1) Flow, Setpt, Filtered Error (shifted)
        self.flow_data        = []
        self.setpt_data       = []
        self.filtered_err_data = []

        # (Plot 2) P, I, D
        self.p_data = []
        self.i_data = []
        self.d_data = []

        # (Plot 3) Voltage
        self.volt_data = []

        # (Plot 4) Gains
        self.pGain_data = []
        self.iGain_data = []
        self.dGain_data = []

        # --------------- PLOT 1 (Flow, Setpt, Filtered Error) ---------------
        self.plot1 = self._create_plot_widget(parent_layout, left_label="Flow / Setpt / fErr(shifted)")

        self.flow_curve = self.plot1.plot([], pen=pg.mkPen('white', width=2),   name='Flow')
        self.setpt_curve = self.plot1.plot([], pen=pg.mkPen('cyan', width=2),   name='Setpt')
        self.filtered_err_curve = self.plot1.plot([], pen=pg.mkPen('magenta', width=2), name='fErr(shifted)')

        self._mirror_axis_same_scale(self.plot1, axis_name="right", label_text="Flow/Setpt/fErr(shifted)")

        # --------------- PLOT 2 (P & D on left, I on right) ---------------
        self.plot2 = self._create_plot_widget(parent_layout, left_label="P / D")

        # Left-axis => P, D
        self.p_curve = self.plot2.plot([], pen=pg.mkPen('blue', width=2), name='P')
        self.d_curve = self.plot2.plot([], pen=pg.mkPen('red',  width=2), name='D')

        # Right axis => I
        self.plot2.showAxis('right', show=True)
        self.plot2.getAxis('right').setLabel(text="I", color='white')
        self.vb_right_2 = pg.ViewBox()
        self.plot2.scene().addItem(self.vb_right_2)
        self.plot2.getAxis('right').linkToView(self.vb_right_2)
        self.vb_right_2.setXLink(self.plot2)

        def updateViews2():
            self.vb_right_2.setGeometry(self.plot2.getViewBox().sceneBoundingRect())
        self.plot2.getViewBox().sigResized.connect(updateViews2)

        self.i_curve = pg.PlotCurveItem(pen=pg.mkPen('green', width=2), name='I')
        self.vb_right_2.addItem(self.i_curve)

        # --------------- PLOT 3 (Voltage) ---------------
        self.plot3 = self._create_plot_widget(parent_layout, left_label="Voltage")
        self.volt_curve = self.plot3.plot([], pen=pg.mkPen('yellow', width=2), name='Volt')
        self._mirror_axis_same_scale(self.plot3, axis_name="right", label_text="Voltage")

        # --------------- PLOT 4 (PID Gains) ---------------
        # Left axis => pGain, dGain
        self.plot4 = self._create_plot_widget(parent_layout, left_label="pGain / dGain")
        self.pGain_curve = self.plot4.plot([], pen=pg.mkPen('blue',   width=2), name='pGain')
        self.dGain_curve = self.plot4.plot([], pen=pg.mkPen('red',    width=2), name='dGain')

        # Right axis => iGain
        self.plot4.showAxis('right', show=True)
        self.plot4.getAxis('right').setLabel(text="iGain", color='white')
        self.vb_right_4 = pg.ViewBox()
        self.plot4.scene().addItem(self.vb_right_4)
        self.plot4.getAxis('right').linkToView(self.vb_right_4)
        self.vb_right_4.setXLink(self.plot4)

        def updateViews4():
            self.vb_right_4.setGeometry(self.plot4.getViewBox().sceneBoundingRect())
        self.plot4.getViewBox().sigResized.connect(updateViews4)

        self.iGain_curve = pg.PlotCurveItem(pen=pg.mkPen('green',  width=2), name='iGain')
        self.vb_right_4.addItem(self.iGain_curve)

    def _create_plot_widget(self, parent_layout, left_label: str):
        """
        Create a PlotWidget with:
          - bottom axis = TimeAxisItem (mm:ss)
          - top axis    = TimeAxisItem (mm:ss)
        """
        plot_wid = pg.PlotWidget(
            axisItems={'bottom': TimeAxisItem(orientation='bottom')}
        )
        parent_layout.addWidget(plot_wid)
        plot_wid.setLabel('left', left_label)
        plot_wid.setLabel('bottom', 'Time (mm:ss)')
        plot_wid.showGrid(x=True, y=True, alpha=0.3)
        plot_wid.addLegend()

        # Show & link top axis
        plot_wid.showAxis('top', show=True)
        top_axis = TimeAxisItem(orientation='top')
        plot_wid.setAxisItems({'top': top_axis})
        top_axis.linkToView(plot_wid.getViewBox())

        return plot_wid

    def _mirror_axis_same_scale(self, plot_wid, axis_name="right", label_text=""):
        """
        Mirror the main view's scale onto axis_name.
        """
        plot_wid.showAxis(axis_name, show=True)
        plot_wid.getAxis(axis_name).setLabel(label_text)
        plot_wid.getAxis(axis_name).linkToView(plot_wid.getViewBox())

    def set_time_window(self, tw: float):
        """
        Set the time window in seconds. If > 0, remove older data => sliding window.
        """
        self.time_window = tw

    def start_run(self):
        """Clears data arrays & resets curves for a new run."""
        self.t_s.clear()

        # Plot 1
        self.flow_data.clear()
        self.setpt_data.clear()
        self.filtered_err_data.clear()

        # Plot 2
        self.p_data.clear()
        self.i_data.clear()
        self.d_data.clear()

        # Plot 3
        self.volt_data.clear()

        # Plot 4
        self.pGain_data.clear()
        self.iGain_data.clear()
        self.dGain_data.clear()

        # Clear the actual curves
        self.flow_curve.setData([], [])
        self.setpt_curve.setData([], [])
        self.filtered_err_curve.setData([], [])

        self.p_curve.setData([], [])
        self.d_curve.setData([], [])
        self.i_curve.setData([], [])

        self.volt_curve.setData([], [])

        self.pGain_curve.setData([], [])
        self.iGain_curve.setData([], [])
        self.dGain_curve.setData([], [])

    def update_data(self, data_dict, elapsed_s):
        """
        data_dict might contain keys:
          - flow
          - setpt
          - filteredErr   (the raw or computed error)
          - P, I, D       (the raw PID terms)
          - volt
          - pGain, iGain, dGain (the dynamic PID gains)

        We'll shift the filteredErr by setpt_val => 
        if filteredErr==0 => same as setpoint line.
        """

        flow_val        = float(data_dict.get("flow",        0.0))
        setpt_val       = float(data_dict.get("setpt",       0.0))
        raw_filtered_err= float(data_dict.get("filteredErr", 0.0))

        # SHIFT the filtered error so that 0 lines up with the setpoint
        shifted_filtered_err = setpt_val + raw_filtered_err

        p_val     = float(data_dict.get("P",    0.0))
        i_val     = float(data_dict.get("I",    0.0))
        d_val     = float(data_dict.get("D",    0.0))
        volt_val  = float(data_dict.get("volt", 0.0))

        # Gains
        pGain_val = float(data_dict.get("pGain", 0.0))
        iGain_val = float(data_dict.get("iGain", 0.0))
        dGain_val = float(data_dict.get("dGain", 0.0))

        # Append new time
        self.t_s.append(elapsed_s)

        # Plot 1 data
        self.flow_data.append(flow_val)
        self.setpt_data.append(setpt_val)
        self.filtered_err_data.append(shifted_filtered_err)

        # Plot 2 data
        self.p_data.append(p_val)
        self.i_data.append(i_val)
        self.d_data.append(d_val)

        # Plot 3 data
        self.volt_data.append(volt_val)

        # Plot 4 data
        self.pGain_data.append(pGain_val)
        self.iGain_data.append(iGain_val)
        self.dGain_data.append(dGain_val)

        # ----- Sliding Window Logic -----
        if self.time_window > 0.0:
            min_time = elapsed_s - self.time_window
            while len(self.t_s) > 1 and self.t_s[0] < min_time:
                # Remove the earliest samples
                self.t_s.pop(0)

                self.flow_data.pop(0)
                self.setpt_data.pop(0)
                self.filtered_err_data.pop(0)

                self.p_data.pop(0)
                self.i_data.pop(0)
                self.d_data.pop(0)

                self.volt_data.pop(0)

                self.pGain_data.pop(0)
                self.iGain_data.pop(0)
                self.dGain_data.pop(0)

        # ----- Update the Plots -----
        # Plot 1 => Flow, Setpt, fErr
        self.flow_curve.setData(self.t_s, self.flow_data)
        self.setpt_curve.setData(self.t_s, self.setpt_data)
        self.filtered_err_curve.setData(self.t_s, self.filtered_err_data)

        # Plot 2 => P, D, I
        self.p_curve.setData(self.t_s, self.p_data)
        self.d_curve.setData(self.t_s, self.d_data)
        self.i_curve.setData(self.t_s, self.i_data)

        # Plot 3 => Voltage
        self.volt_curve.setData(self.t_s, self.volt_data)

        # Plot 4 => pGain, dGain (left); iGain (right)
        self.pGain_curve.setData(self.t_s, self.pGain_data)
        self.dGain_curve.setData(self.t_s, self.dGain_data)
        self.iGain_curve.setData(self.t_s, self.iGain_data)
