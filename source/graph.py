"""Analyze data and show graphs."""
# TODO
# Add open file menu option
import datetime
from typing import Dict, List, Tuple

import matplotlib.dates as dates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes._subplots import Axes
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.container import BarContainer
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
from PyQt5.QtCore import QCoreApplication, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QFileDialog, QMainWindow, QPushButton,
                             QTabWidget, QVBoxLayout, QWidget, QAction)

from .tools import calc_color_map, extract_json, find_tags, str_to_date
from .types import Dot, Entry, Export


class App(QMainWindow):
    """Manage everything present in the PyQt window.

    The position of the toolbar and canvas are instantiated here.

    Methods
    -------
    ```python
    init_ui(self) -> None:
    open_dialog(self) -> None:
    on_quit_key(self) -> None:
    plot_graphs(self) -> None:
    ```

    Properties
    ----------
    ```python
    title: str
    init_w: int
    init_h: int
    btn_w: int
    btn_h: int
    plot_tabs: PlotTabs
    file_menu: QMenu
    ```
    """

    def __init__(self):
        super().__init__()

        self.title = "Journal Entries"

        self.init_w = 500
        self.init_h = 400

        self.btn_w = 150
        self.btn_h = 75

        self.file_menu = self.menuBar().addMenu("&File")

        self.plot_tabs: PlotTabs = None

        self.init_ui()

    def init_ui(self) -> None:
        """Create the initial window and register event handlers."""
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, self.init_w, self.init_h)

        select_btn = QPushButton("Select Data", self)
        select_btn.move(int(self.init_w / 2) - int(self.btn_w / 2),
                        int(self.init_h / 2) - int(self.btn_h / 2))
        select_btn.resize(self.btn_w, self.btn_h)
        select_btn.clicked.connect(self.open_dialog)

        open_file = QAction(QIcon.fromTheme("fileopen"), "&Open", self)
        open_file.setShortcut("Ctrl+O")
        open_file.setStatusTip("Open Day One JSON file")
        open_file.triggered.connect(self.open_dialog)
        self.file_menu.addAction(open_file)

        quit_app = QAction(QIcon.fromTheme("exit"), "&Quit", self)
        quit_app.setShortcuts(["Ctrl+Q", "Ctrl+W"])
        quit_app.setStatusTip("Quit Application")
        quit_app.triggered.connect(self.on_quit_key)
        self.file_menu.addAction(quit_app)

        self.show()

    @pyqtSlot()
    def open_dialog(self) -> None:
        """Create the file dialog and pass the name to plot_graphs."""
        options = QFileDialog.DontUseNativeDialog

        fname, _ = QFileDialog.getOpenFileName(
            parent=self, caption="Select File to Analyze", directory="",
            filter="JSON Files (*.json)", initialFilter="", options=options)
        if fname:
            self.file = fname

            self.plot_graphs()

    @pyqtSlot()
    def on_quit_key(self):
        """Quit the application."""
        QCoreApplication.instance().quit()

    def plot_graphs(self) -> None:
        """Create the Plot with the opened file data."""
        self.showMaximized()

        if self.plot_tabs is not None:
            self.centralWidget().deleteLater()

            self.plot_tabs = PlotTabs(self, self.file)
        else:
            self.plot_tabs = PlotTabs(self, self.file)

        self.setCentralWidget(self.plot_tabs)

        self.show()


class PlotTabs(QWidget):
    """Manage the tabs that contain all plots.

    Attributes
    ----------
    file: str
    """

    def __init__(self, parent: App, file: str):
        super().__init__(parent=parent)

        self.file = file

        glob_layout = QVBoxLayout()

        tabs = QTabWidget()
        dp_tab = QWidget()
        hg_tab = QWidget()

        tabs.addTab(dp_tab, "Dot Plot")
        tabs.addTab(hg_tab, "Histogram")

        # Dot Plot tab
        dp_layout = QVBoxLayout()

        dp = DotPlot(parent=self, file=self.file)

        dp_toolbar = NavigationToolbar(dp, self)

        dp_layout.addWidget(dp)
        dp_layout.addWidget(dp_toolbar)
        dp_tab.setLayout(dp_layout)

        # Histogram Plot tab
        hg_layout = QVBoxLayout()

        hg = Histogram(parent=self, file=self.file)

        hg_toolbar = NavigationToolbar(hg, self)

        hg_layout.addWidget(hg)
        hg_layout.addWidget(hg_toolbar)
        hg_tab.setLayout(hg_layout)

        # Add to current widget
        glob_layout.addWidget(tabs)

        self.setLayout(glob_layout)


class DotPlot(FigureCanvas):
    """Represent the time of day versus date of entries.

    Methods
    -------
    ```python
    add_dot_legend(self) -> Legend:
    format_dot_plt(self) -> None:
    format_dot_x_axis(self) -> None:
    format_dot_y_axis(self) -> None:
    format_plt(self) -> None:
    parse_entries(self) -> None:
    plot_dot_plor(self) -> None:
    setup_plt(self) -> None:
    ```

    Attributes
    ----------
    ```python
    file: str
    dpi: int
    dot_plot: Figure
    full_json: Export
    tags: List[str]
    color_map: ColorMap
    dots: List[Dot]
    x_0: float
    bottom: float
    left: float
    top: float
    right: float
    dot_axes: Axes
    ```
    """

    def __init__(self, parent: QWidget, file: str) -> None:
        """Display a graph of journal entries from Day One JSON."""
        self.file = file

        self.dot_plot = Figure(figsize=(16, 9), dpi=120)

        super().__init__(self.dot_plot)

        self.setParent(parent)

        self.full_json = extract_json(self.file)

        self.entries = self.full_json["entries"]

        self.tags = find_tags(self.entries)

        self.color_map = calc_color_map(self.tags)

        self.dots, self.x_0 = self.parse_entries()

        # End of day
        self.bottom = int(self.x_0)
        self.left = int(self.x_0) - 0.02

        # Start of day
        self.top = int(self.x_0) + 1
        self.right = int(self.x_0) + 0.98

        self.setup_plt()

        self.dot_axes: Axes = self.dot_plot.add_subplot(111)

        self.plot_dot_plot()

        self.format_dot_plot()

        self.format_plt()

    def parse_entries(
            self) -> Tuple[List[Dot], float]:
        """Parse the data from the incoming JSON.

        Calculate datetime info, primary tag, and respective color
        for each entry in the Day One export.

        Returns
        -------
        `Tuple[List[Dot], float]`
            Represents parsed info about entries and earliest date of entry

        """
        parsed_entries: List[Dot] = []

        earliest_entry: Entry = min(
            self.entries, key=lambda entry: entry["creationDate"])
        x_0: float = dates.date2num(
            str_to_date(earliest_entry["creationDate"]))

        for entry in self.entries:
            entry_info: Dot
            date = str_to_date(entry["creationDate"])
            x_val = dates.date2num(date.date())
            y_val = int(x_0) + dates.date2num(date) % 1

            tag: str = ""
            if "tags" in entry:
                tag = entry["tags"][0]
            else:
                tag = "none"
            entry_info = {"color": self.color_map[tag], "tag": tag,
                          "x_value": x_val, "y_value": y_val}
            parsed_entries.append(entry_info)
        return (parsed_entries, x_0)

    def plot_dot_plot(self) -> List[Line2D]:
        """Plot points representing day v. time of day.

        Returns
        -------
        `List[Line2D]`
            The returned objects from the matplotlib plotting function
        """
        lines: List[Line2D] = [
            self.dot_axes.plot_date(
                dot["x_value"],
                dot["y_value"],
                fmt="o", label=dot["color"],
                color=dot["color"]) for dot in self.dots]

        return lines

    def format_dot_plot(self):
        """Format the Axes of the figure."""
        self.format_dot_x_axis()
        self.format_dot_y_axis()

        self.add_dot_legend()

    def format_dot_x_axis(self) -> None:
        """Format x-axis Axes props after rendering."""
        self.dot_axes.xaxis_date()
        # Pad the x on the left five in the past
        # and pad the right five in the future
        self.dot_axes.set_xlim(left=(self.x_0 - 5),
                               right=(dates.date2num(
                                   datetime.datetime.now().date()) + 5))

        x_loc = DayLocator(interval=10)
        x_formatter = DateFormatter("%m/%d/%y")

        x_axis = self.dot_axes.get_xaxis()

        x_axis.set_major_locator(x_loc)
        x_axis.set_major_formatter(x_formatter)

        self.dot_axes.set_xlabel("Date", fontdict={"fontsize": 15})

    def format_dot_y_axis(self) -> None:
        """Format x-axis Axes props after rendering."""
        self.dot_axes.yaxis_date()
        self.dot_axes.set_ylim(bottom=self.bottom, top=self.top)
        self.dot_axes.grid(which="major", axis="y", lw=1)
        self.dot_axes.grid(which="minor", axis="y", lw=0.5)

        y_loc = HourLocator(interval=2)
        y_formatter = DateFormatter("%-I:%M %p")

        y_min_loc = HourLocator(interval=1)

        y_axis = self.dot_axes.get_yaxis()

        y_axis.set_major_locator(y_loc)
        y_axis.set_major_formatter(y_formatter)

        y_axis.set_minor_locator(y_min_loc)

        # Display morning on top and midnight on bottom.
        # This is different than what we did at assigning `y_vals`
        self.dot_axes.invert_yaxis()

        self.dot_axes.set_ylabel("Time of day", fontdict={"fontsize": 15})

    def add_dot_legend(self) -> Legend:
        """Add a legend that shows the mapping from unique tags to unqiue colors.

        Returns
        -------
        `Legend`
            Object describing the added legend

        """
        tags = list(self.color_map.keys())

        lines = [Line2D([], [], color=color, label=tag,
                        marker="o", linestyle="none")
                 for tag, color in self.color_map.items()]

        return self.dot_axes.legend(
            lines, tags, loc=7, bbox_to_anchor=(1.12, 0.5))

    def format_plt(self) -> None:
        """Format the plot after it has been rendered."""
        self.dot_plot.autofmt_xdate()

        self.dot_axes.set_title("Journal entries date and time of day",
                                fontdict={"fontsize": 18, "family": "Poppins"},
                                pad=1)

        self.dot_plot.tight_layout()

    def setup_plt(self) -> None:
        """Format the plot before rendering."""
        plt.style.use("ggplot")


class Histogram(FigureCanvas):
    """Create a histogram of the frequency of entry tags.

    Methods
    -------
    format_hist(self) -> None:
    format_hist_x_axis(self) -> None:
    format_hist_y_axis(self) -> None:
    format_plt(self) -> None:
    gen_hour_histogram_data(self) -> None:
    parse_entries(self) -> None:
    plot_histogram(self) -> None:

    Attributes
    ----------
    file: str
    dpi: int
    histogram: Figure
    hist_axes: Axes
    full_json: Export
    tags: List[str]
    color_map: ColorMap
    dots: List[Dot]
    bottom: float
    left: float
    top: float
    right: float
    """

    def __init__(self, parent: QWidget, file: str) -> None:
        self.file = file

        self.histogram = Figure(figsize=(16, 9), dpi=120)

        super().__init__(self.histogram)

        self.setParent(parent)

        self.hist_axes: Axes = self.histogram.add_subplot(111)

        self.full_json: Export = extract_json(self.file)

        self.entries = self.full_json["entries"]

        self.tags = find_tags(self.entries)

        self.color_map = calc_color_map(self.tags)

        self.dots, self.x_0 = self.parse_entries()

        # End of day
        self.bottom = int(self.x_0)
        self.left = int(self.x_0) - 0.02

        # Start of day
        self.top = int(self.x_0) + 1
        self.right = int(self.x_0) + 0.98

        self.histogram_data = self.gen_hour_histogram_data()

        self.plot_histogram()

        self.format_hist()

        self.format_plt()

        self.hist_axes.legend()

    def parse_entries(
            self) -> Tuple[List[Dot], float]:
        """Parse the data from the incoming JSON.

        Calculate datetime info, primary tag, and respective color
         for each entry in the Day One export.

        Returns
        -------
        `Tuple[List[Dot], float]`
            Represents parsed info about entries and earliest date of entry

        """
        parsed_entries: List[Dot] = []

        earliest_entry: Entry = min(
            self.entries, key=lambda entry: entry["creationDate"])
        x_0: float = dates.date2num(
            str_to_date(earliest_entry["creationDate"]))

        for entry in self.entries:
            entry_info: Dot
            date = str_to_date(entry["creationDate"])
            x_val = dates.date2num(date.date())
            y_val = int(x_0) + dates.date2num(date)

            tag: str = ""
            if "tags" in entry:
                tag = entry["tags"][0]
            else:
                tag = "none"
            entry_info = {"color": self.color_map[tag], "tag": tag,
                          "x_value": x_val, "y_value": y_val}
            parsed_entries.append(entry_info)
        return (parsed_entries, x_0)

    def gen_hour_histogram_data(self) -> Dict[str, Dict[float, int]]:
        """Extract the frequency of entries throughout the day.

        Returns
        -------
        `Dict[str, Dict[float, int]]`
            A dict of dicts for the frquency of each tag per hour
        """
        freq: Dict[str, Dict[float, int]] = {}
        for tag in self.tags:
            tag_freq: Dict[float, int] = {}
            start_day = dates.num2date(int(self.x_0))
            delta = datetime.timedelta(hours=1)

            for i in range(25):
                tag_freq[i] = 0
            for dot in self.dots:
                date_obj = dates.num2date(dot["y_value"])
                if dot["tag"] == tag:
                    tag_freq[date_obj.hour] += 1
            res: Dict[float, int] = {}
            for hour, length in tag_freq.items():
                time_of_day = dates.date2num(start_day + (delta * hour))
                res[time_of_day] = length
            freq[tag] = res

        return freq

    def plot_histogram(self) -> List[BarContainer]:
        """Plot bars representing frequency of entries throughout the day for each tag.

        Returns
        -------
        `BarContainer`
            Object containing all of the plotted bars
        """
        bars: List[BarContainer] = []
        total_height = None
        for tag, tag_freq in self.histogram_data.items():
            keys = list(tag_freq.keys())
            values = list(tag_freq.values())
            if len(bars) > 0:
                tag_bars = self.hist_axes.bar(
                    keys, values, width=0.025, label=tag,
                    color=self.color_map[tag], bottom=total_height)
            else:
                tag_bars = self.hist_axes.bar(
                    keys, values, width=0.025, label=tag,
                    color=self.color_map[tag])
                total_height = np.zeros(len(tag_freq.values()))

            total_height += np.array(list(tag_freq.values()))
            bars.append(tag_bars)
        self.hist_axes.xaxis_date()

        return bars

    def format_hist(self):
        """Format the Axes after rendering."""
        self.format_hist_x_axis()
        self.format_hist_y_axis()

    def format_hist_x_axis(self) -> None:
        """Format the x-axis of the entry hour frequency histogram."""
        self.hist_axes.set_xlim(left=self.left, right=self.right)

        x_loc = HourLocator(interval=1)
        x_formatter = DateFormatter("%-I:%M %p")

        x_axis = self.hist_axes.get_xaxis()

        x_axis.set_major_locator(x_loc)
        x_axis.set_major_formatter(x_formatter)

        self.hist_axes.set_xlabel("Time of day")

    def format_hist_y_axis(self) -> None:
        """Format the y-axis of the entry hour frequency histogram."""
        self.hist_axes.grid(which="major", axis="y", lw=1)
        self.hist_axes.grid(which="minor", axis="y", lw=0.5)

        y_min_loc = MultipleLocator(5)
        y_maj_loc = MultipleLocator(10)

        y_axis = self.hist_axes.get_yaxis()

        y_axis.set_major_locator(y_maj_loc)
        y_axis.set_minor_locator(y_min_loc)

        self.hist_axes.set_ylabel("Number of entries")

    def format_plt(self) -> None:
        """Format the plot after rendering."""
        self.histogram.autofmt_xdate()

        self.hist_axes.set_title("Frequency of entries throughout the day",
                                 fontdict={
                                     "fontsize": 18, "family": "Poppins"},
                                 pad=1)

        self.histogram.tight_layout()
