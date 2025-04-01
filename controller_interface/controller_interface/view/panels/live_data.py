# controller_interface/view/panels/live_data.py

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt

TITLE_COLOR = QColor(29, 154, 221)
TITLE_FONT_SIZE = 12
CHILD_FONT_SIZE = 12

class LiveDataPanel(QGroupBox):
    """
    Displays real-time data in a single column.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Live Data")

        # 1) Customize group box title
        title_font = QFont()
        title_font.setPointSize(TITLE_FONT_SIZE)
        title_font.setBold(True)
        self.setFont(title_font)

        palette = self.palette()
        palette.setColor(self.foregroundRole(), TITLE_COLOR)
        self.setPalette(palette)

        # 2) Child font
        self.child_font = QFont()
        self.child_font.setPointSize(CHILD_FONT_SIZE)
        self.child_font.setBold(False)

        # 3) Layout
        self.main_layout = QVBoxLayout(self)
        # Keep margins and spacing tight
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # Set a size policy so it won't greedily expand horizontally
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Create labels
        self.lbl_mode        = QLabel("Mode: ---")
        self.lbl_onState     = QLabel("On?: ---")
        self.lbl_errorPct    = QLabel("Err%: ---")
        self.lbl_setpt       = QLabel("Setpt: ---")
        self.lbl_flow        = QLabel("Flow: ---")      # "mL/min"
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

        # Apply child font and add each label
        for lbl in self.labels:
            lbl.setFont(self.child_font)
            # Optional: Make each label not expand horizontally
            # lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            self.main_layout.addWidget(lbl)

        # Optional spacer to push labels up, so they stay top-aligned
        self.main_layout.addSpacerItem(
            QSpacerItem(5, 5, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

    def update_data(
        self,
        setpt_val: float,
        flow_val: float,
        temp_val: float,
        volt_val: float,
        bubble_bool: bool,
        p_val: float | None = None,
        i_val: float | None = None,
        d_val: float | None = None,
        pid_out_val: float | None = None,
        error_pct: float | None = None,
        on_state: bool | None = None,
        mode_val: str | None = None,
        p_gain: float | None = None,
        i_gain: float | None = None,
        d_gain: float | None = None,
        filtered_err: float | None = None,
        current_alpha: float | None = None,
        total_flow_ml: float | None = None
    ) -> None:
        """
        Update the UI with new data.
        ...
        """
        # (No changes needed in your update logic)
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
