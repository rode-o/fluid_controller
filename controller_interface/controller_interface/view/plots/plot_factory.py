# controller_interface/src/view/plots/plot_factory.py

import pyqtgraph as pg
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from controller_interface.view.plots.time_axis_item import TimeAxisItem

def create_plot_widget(
    left_label: str,
    show_top_axis: bool = True,
    background: str = "transparent"
) -> pg.PlotWidget:
    """
    Creates a PlotWidget with:
     - custom bottom axis => TimeAxisItem
     - optional top axis
     - transparent (or user-chosen) background
     - 10pt fonts for axes
     - grid + legend
    """
    # If you prefer a relative import, do:
    # from .time_axis_item import TimeAxisItem
    # But as you've structured your paths, an absolute import might work better.

    plot_wid = pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})

    # Set background
    if background == "transparent":
        plot_wid.setBackground(None)
        plot_wid.setAttribute(Qt.WA_TranslucentBackground, True)
        plot_wid.setStyleSheet("background: transparent;")
    else:
        plot_wid.setBackground(background)

    # Setup fonts
    tick_font = QFont()
    tick_font.setPointSize(10)
    label_font = QFont()
    label_font.setPointSize(10)

    plot_item = plot_wid.getPlotItem()

    # Style the axes
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
    plot_wid.setLabel('bottom', ' ', color='white')
    bot_axis = plot_item.getAxis('bottom')
    bot_axis.label.setFont(label_font)

    # Optionally show top axis
    if show_top_axis:
        plot_wid.showAxis('top', show=True)
        top_axis_item = TimeAxisItem(orientation='top')
        plot_wid.setAxisItems({'top': top_axis_item})
        top_axis_item.linkToView(plot_wid.getViewBox())

        #plot_wid.setLabel('top', 'Time (Top)', color='white')
        top_axis = plot_item.getAxis('top')
        top_axis.label.setFont(label_font)
    else:
        plot_wid.showAxis('top', show=False)

    # Grid + legend
    plot_wid.showGrid(x=True, y=True, alpha=0.6)
    plot_wid.addLegend()

    return plot_wid


def mirror_axis_same_scale(plot_wid, axis_name="right", label_text="", viewbox=None):
    """
    Mirror the main view's scale to 'axis_name', set the label to 10pt white,
    optionally link a separate ViewBox for that axis.
    """
    plot_wid.showAxis(axis_name, show=True)
    plot_wid.getAxis(axis_name).setLabel(label_text, color='white')

    label_font = QFont()
    label_font.setPointSize(10)
    plot_wid.getAxis(axis_name).label.setFont(label_font)

    if viewbox is not None:
        plot_wid.scene().addItem(viewbox)
        plot_wid.getAxis(axis_name).linkToView(viewbox)
        viewbox.setXLink(plot_wid)
    else:
        plot_wid.getAxis(axis_name).linkToView(plot_wid.getViewBox())
