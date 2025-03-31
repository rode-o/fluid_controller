from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

class LiveDataPanel(QGroupBox):
    """
    A QGroupBox that displays real-time data in a single column.
    - The group box title is 16pt and bold, colored rgb(29, 154, 221).
    - All child labels are 16pt, not bold.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Live Data")

        #
        # 1) Set the group box title color and font
        #
        title_color = QColor(29, 154, 221)  # Hard-coded
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.setFont(title_font)

        palette = self.palette()
        palette.setColor(self.foregroundRole(), title_color)
        self.setPalette(palette)

        #
        # 2) Create a child font: 16pt, not bold
        #
        self.child_font = QFont()
        self.child_font.setPointSize(12)
        self.child_font.setBold(False)

        #
        # Layout
        #
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        #
        # Create all the labels
        #
        self.lbl_mode        = QLabel("Mode: ---")
        self.lbl_onState     = QLabel("On?: ---")
        self.lbl_errorPct    = QLabel("Err%: ---")
        self.lbl_setpt       = QLabel("Setpt: ---")
        self.lbl_flow        = QLabel("Flow: ---")  # "mL/min"
        self.lbl_temp        = QLabel("Temp: ---")
        self.lbl_volt        = QLabel("Volt: ---")
        self.lbl_bubble      = QLabel("Bubble: ---")
        self.lbl_totalVolume = QLabel("Total Vol: ---")

        self.lbl_filtErr     = QLabel("FiltErr: ---")
        self.lbl_alpha       = QLabel("Alpha: ---")
        self.lbl_p           = QLabel("P: ---")
        self.lbl_pGain       = QLabel("pGain: ---")
        self.lbl_i           = QLabel("I: ---")
        self.lbl_iGain       = QLabel("iGain: ---")
        self.lbl_d           = QLabel("D: ---")
        self.lbl_dGain       = QLabel("dGain: ---")
        self.lbl_pidOut      = QLabel("PID Out: ---")

        self.labels = [
            self.lbl_mode, self.lbl_onState, self.lbl_errorPct, self.lbl_setpt,
            self.lbl_flow, self.lbl_temp, self.lbl_volt, self.lbl_bubble,
            self.lbl_totalVolume, self.lbl_filtErr, self.lbl_alpha,
            self.lbl_p, self.lbl_pGain, self.lbl_i, self.lbl_iGain,
            self.lbl_d, self.lbl_dGain, self.lbl_pidOut
        ]

        # Apply the child font and add each label to the layout
        for lbl in self.labels:
            lbl.setFont(self.child_font)
            self.main_layout.addWidget(lbl)

        self.main_layout.addStretch(1)


    def update_data(
            self,
            setpt_val,
            flow_val,
            temp_val,
            volt_val,
            bubble_bool,
            p_val=None,
            i_val=None,
            d_val=None,
            pid_out_val=None,
            error_pct=None,
            on_state=None,
            mode_val=None,
            p_gain=None,
            i_gain=None,
            d_gain=None,
            filtered_err=None,
            current_alpha=None,
            total_flow_ml=None
        ):
        """
        Update the UI with new data.
        - flow_val: mL/min
        - total_flow_ml: total volume in mL
        """
        if mode_val is not None:
            self.lbl_mode.setText(f"Mode: {mode_val}")
        else:
            self.lbl_mode.setText("Mode: ---")

        if on_state is not None:
            self.lbl_onState.setText(f"On?: {'Yes' if on_state else 'No'}")
        else:
            self.lbl_onState.setText("On?: ---")

        if error_pct is not None:
            self.lbl_errorPct.setText(f"Err%: {error_pct:.3f}")
        else:
            self.lbl_errorPct.setText("Err%: ---")

        self.lbl_setpt.setText(f"Setpt: {setpt_val:.3f}")
        self.lbl_flow.setText(f"Flow: {flow_val:.3f} mL/min")
        self.lbl_temp.setText(f"Temp: {temp_val:.2f}")
        self.lbl_volt.setText(f"Volt: {volt_val:.2f}")
        self.lbl_bubble.setText(f"Bubble: {'Yes' if bubble_bool else 'No'}")

        if total_flow_ml is not None:
            self.lbl_totalVolume.setText(f"Total Vol: {total_flow_ml:.3f} mL")
        else:
            self.lbl_totalVolume.setText("Total Vol: ---")

        if filtered_err is not None:
            self.lbl_filtErr.setText(f"FiltErr: {filtered_err:.3f}")
        else:
            self.lbl_filtErr.setText("FiltErr: ---")

        if current_alpha is not None:
            self.lbl_alpha.setText(f"Alpha: {current_alpha:.3f}")
        else:
            self.lbl_alpha.setText("Alpha: ---")

        if p_val is not None:
            self.lbl_p.setText(f"P: {p_val:.3f}")
        else:
            self.lbl_p.setText("P: ---")

        if p_gain is not None:
            self.lbl_pGain.setText(f"pGain: {p_gain:.3f}")
        else:
            self.lbl_pGain.setText("pGain: ---")

        if i_val is not None:
            self.lbl_i.setText(f"I: {i_val:.3f}")
        else:
            self.lbl_i.setText("I: ---")

        if i_gain is not None:
            self.lbl_iGain.setText(f"iGain: {i_gain:.3f}")
        else:
            self.lbl_iGain.setText("iGain: ---")

        if d_val is not None:
            self.lbl_d.setText(f"D: {d_val:.3f}")
        else:
            self.lbl_d.setText("D: ---")

        if d_gain is not None:
            self.lbl_dGain.setText(f"dGain: {d_gain:.3f}")
        else:
            self.lbl_dGain.setText("dGain: ---")

        if pid_out_val is not None:
            self.lbl_pidOut.setText(f"PID Out: {pid_out_val:.3f}")
        else:
            self.lbl_pidOut.setText("PID Out: ---")
