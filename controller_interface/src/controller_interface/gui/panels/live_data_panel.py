from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt
# No direct QFont import needed now because we'll rely on style sheets

class LiveDataPanel(QGroupBox):
    """
    Displays real-time data in two columns, including total volume in mL.
    
    COLUMN 1:
      1) Mode
      2) On?
      3) Err%
      4) Setpt
      5) Flow (mL/min)
      6) Temp
      7) Volt
      8) Bubble
      9) Total Vol (mL)
    
    COLUMN 2:
      1) FiltErr
      2) Alpha
      3) P
      4) pGain
      5) I
      6) iGain
      7) D
      8) dGain
      9) PID Out

    Best‐practice layout:
    - No forced panel sizes or min/max constraints.
    - Uses a style sheet to set the font size for all child labels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Live Data")

        # 1) Apply a style sheet that sets font size to, e.g., 12pt for
        #    this QGroupBox and all its child widgets. 
        #    Adjust 'font-size' to your desired size.
        self.setStyleSheet("""
            QGroupBox, QGroupBox * {
                font-size: 12pt;
            }
        """)

        # 2) Main horizontal layout: two columns
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self.col1 = QVBoxLayout()
        self.col2 = QVBoxLayout()

        # We'll store references to the labels if needed later
        self.labels_col1 = []
        self.labels_col2 = []

        # ---------------- COLUMN 1 ----------------
        self.lbl_mode     = QLabel("Mode: ---")
        self.lbl_onState  = QLabel("On?: ---")
        self.lbl_errorPct = QLabel("Err%: ---")
        self.lbl_setpt    = QLabel("Setpt: ---")
        self.lbl_flow     = QLabel("Flow: ---")  # Will display "mL/min"
        self.lbl_temp     = QLabel("Temp: ---")
        self.lbl_volt     = QLabel("Volt: ---")
        self.lbl_bubble   = QLabel("Bubble: ---")
        self.lbl_totalVolume = QLabel("Total Vol: ---")

        self.labels_col1.extend([
            self.lbl_mode,
            self.lbl_onState,
            self.lbl_errorPct,
            self.lbl_setpt,
            self.lbl_flow,
            self.lbl_temp,
            self.lbl_volt,
            self.lbl_bubble,
            self.lbl_totalVolume
        ])

        for lbl in self.labels_col1:
            self.col1.addWidget(lbl)
        self.col1.addStretch(1)

        # ---------------- COLUMN 2 ----------------
        self.lbl_filtErr  = QLabel("FiltErr: ---")
        self.lbl_alpha    = QLabel("Alpha: ---")
        self.lbl_p        = QLabel("P: ---")
        self.lbl_pGain    = QLabel("pGain: ---")
        self.lbl_i        = QLabel("I: ---")
        self.lbl_iGain    = QLabel("iGain: ---")
        self.lbl_d        = QLabel("D: ---")
        self.lbl_dGain    = QLabel("dGain: ---")
        self.lbl_pidOut   = QLabel("PID Out: ---")

        self.labels_col2.extend([
            self.lbl_filtErr,
            self.lbl_alpha,
            self.lbl_p,
            self.lbl_pGain,
            self.lbl_i,
            self.lbl_iGain,
            self.lbl_d,
            self.lbl_dGain,
            self.lbl_pidOut
        ])

        for lbl in self.labels_col2:
            self.col2.addWidget(lbl)
        self.col2.addStretch(1)

        # 3) Add both columns to the main layout
        self.main_layout.addLayout(self.col1)
        self.main_layout.addLayout(self.col2)

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

        Typically:
        - flow_val: mL/min
        - total_flow_ml: total volume in mL
        """
        # ---------- COLUMN 1 ----------
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

        # ---------- COLUMN 2 ----------
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