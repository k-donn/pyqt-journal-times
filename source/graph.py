"""Analyze data and show graphs."""
# TODO
# Add vertical scroll area to show all figures
# refactor long-statements and long parameters

import datetime
from typing import Dict, List, Tuple

import matplotlib.cm as cm
import matplotlib.colors as colors
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
from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QShortcut

from .tools import extract_json, find_tags, str_to_date
from .types import ColorMap, Dict, Dot, Entry, Export, List, Tuple


class App(QMainWindow):
    """Manage everything present in the PyQt window.

    The position of the toolbar and canvas are instantiated here.

    Methods
    -------
    ```python
    initUI(self) -> None:
    on_click(self) -> None:
    on_ctrlq(self) -> None:
    ```

    Properties
    ----------
    ```python
    title: str
    init_w: int
    init_h: int
    btn_w: int
    btn_h: int
    m: Plot
    ```
    """

    def __init__(self):
        super().__init__()
        self.title = "Journal Entries"

        self.init_w = 500
        self.init_h = 400

        self.btn_w = 150
        self.btn_h = 75

        self.dp: DotPlot

        self.initUI()

    def initUI(self) -> None:
        """Create the initial window with button to open file and register event handlers."""
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, self.init_w, self.init_h)

        button = QPushButton("Select Data", self)
        button.move(int(self.init_w / 2) - int(self.btn_w / 2),
                    int(self.init_h / 2) - int(self.btn_h / 2))
        button.resize(self.btn_w, self.btn_h)
        button.clicked.connect(self.on_click)

        self.shortcut_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_w = QShortcut(QKeySequence("Ctrl+W"), self)

        self.shortcut_q.activated.connect(self.on_quit_key)
        self.shortcut_w.activated.connect(self.on_quit_key)

        self.show()

    @pyqtSlot()
    def on_click(self) -> None:
        """Create the file dialog and pass the name to plot_graphs."""
        options = QFileDialog.DontUseNativeDialog
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select File to Analyze", "", "JSON Files (*.json)", "", options)
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

        self.dp = DotPlot(parent=self, file=self.file)

        toolbar = NavigationToolbar(self.dp, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.dp)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()


class DotPlot(FigureCanvas):

    def __init__(self, parent: App = None, file: str = "") -> None:
        """Display a graph of journal entries from Day One JSON."""
        self.file = file

        self.dot_plot = Figure(figsize=(16, 9), dpi=120)
        super().__init__(self.dot_plot)

        # FigureCanvas.__init__(self, self.dot_plot)
        self.setParent(parent)

        self.full_json: Export = extract_json(self.file)

        self.entries = self.full_json["entries"]

        self.tags = find_tags(self.entries)

        self.color_map = self.calc_color_map()

        self.dots, self.x_0 = self.parse_entries()

        # End of day
        self.bottom = int(self.x_0)
        self.left = int(self.x_0) - 0.02

        # Start of day
        self.top = int(self.x_0) + 1
        self.right = int(self.x_0) + 0.98

        self.format_plt()

        self.dot_axes: Axes = self.dot_plot.add_subplot(111)  # type: ignore

        self.plot_dot_plot()

        self.format_dot_x_axis()
        self.format_dot_y_axis()

        self.add_dot_legend()

        self.format_dot()

    def parse_entries(
            self) -> Tuple[List[Dot], float]:
        """Parse the data from the incoming JSON.

        Calculate datetime info, primary tag, and respective color for each entry
        in the Day One export.

        Returns
        -------
        `Tuple[List[Dot], float]`
            Represents parsed info about entries and earliest date of entry

        """
        parsed_entries: List[Dot] = []

        earliest_entry: Entry = min(
            self.entries, key=lambda entry: entry["creationDate"])
        x_0: float = dates.date2num(  # type: ignore
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
            entry_info = {"color": self.color_map[tag], "tag": tag,  # type: ignore
                          "x_value": x_val, "y_value": y_val}
            parsed_entries.append(entry_info)
        return (parsed_entries, x_0)

    def calc_color_map(self) -> ColorMap:
        """Create a dictionary to map unique tags to unique colors.

        Returns
        -------
        `ColorMap`
            Each tag's respective color

        """
        color_map: ColorMap = {}

        vmin = 0
        vmax = len(self.tags)

        norm = colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        # Intellisense can't find any of the color-map members part of cm
        mapper = cm.ScalarMappable(
            norm=norm, cmap=cm.gist_ncar)  # type: ignore

        # always map none to black, index-map non-none
        color_map = {tag: mapper.to_rgba(index)  # type: ignore
                     for index, tag in enumerate(self.tags) if tag != "none"}

        color_map["none"] = (0.0, 0.0, 0.0, 1.0)

        return color_map

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

    def format_dot_x_axis(self) -> None:
        """Draw the ticks, format the labels, and adjust sizing for the day-axis."""
        self.dot_axes.xaxis_date()
        # Pad the x on the left five in the past and pad the right five in the
        # future
        self.dot_axes.set_xlim(left=(self.x_0 - 5),
                               right=(dates.date2num(datetime.datetime.now().date()) + 5))

        x_loc = DayLocator(interval=10)
        x_formatter = DateFormatter("%m/%d/%y")

        x_axis = self.dot_axes.get_xaxis()

        x_axis.set_major_locator(x_loc)
        x_axis.set_major_formatter(x_formatter)

        self.dot_axes.set_xlabel("Date", fontdict={"fontsize": 15})

    def format_dot_y_axis(self) -> None:
        """Draw the ticks, format the labels, and adjust sizing for the day-axis."""
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

        # Display morning on top and midnight on bottom. This is different than what
        # we did at assigning `y_vals`
        self.dot_axes.invert_yaxis()

        self.dot_axes.set_ylabel("Time of day", fontdict={"fontsize": 15})

    def format_dot(self) -> None:
        """Format dot plot after it had been rendered."""
        self.dot_plot.autofmt_xdate()

        self.dot_axes.set_title("Journal entries date and time of day",
                                fontdict={"fontsize": 18, "family": "Poppins", "fontweight": "bold"}, pad=25)

    def add_dot_legend(self) -> Legend:
        """Add a legend that shows the mapping from unique tags to unqiue colors.

        Returns
        -------
        `Legend`
            Object describing the added legend

        """
        tags = list(self.color_map.keys())

        lines = [Line2D([], [], color=color, label=tag,
                        marker="o", linestyle="none") for tag, color in self.color_map.items()]

        return self.dot_axes.legend(
            lines, tags, loc=7, bbox_to_anchor=(1.12, 0.5))

    def format_plt(self) -> None:
        """Set all top-level attributes of the plot."""
        plt.style.use("ggplot")


class Histogram(FigureCanvas):
    def __init__(self) -> None:
        self.histogram = Figure(figsize=(16, 9), dpi=120)

        self.hist_axes: Axes = self.histogram.add_subplot(111)  # type: ignore

        self.histogram_data = self.gen_hour_histogram_data()

        self.plot_histogram()

        self.format_hist_x_axis()
        self.format_hist_y_axis()

        self.format_hist()

        self.hist_axes.legend()  # type: ignore

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
            day = dates.num2date(self.x_0)
            delta = datetime.timedelta(hours=1)
            for i in range(25):
                tag_freq[i] = 0
            for dot in self.dots:
                date_obj = dates.num2date(dot["y_value"])
                if dot["tag"] == tag:
                    tag_freq[date_obj.hour] += 1
            res: Dict[float, int] = {}
            for hour, length in tag_freq.items():
                time_of_day = dates.date2num(day + (delta * hour))
                res[time_of_day] = length  # type: ignore
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
                    keys, values, width=0.025, label=tag, color=self.color_map[tag], bottom=total_height)
            else:
                tag_bars = self.hist_axes.bar(
                    keys, values, width=0.025, label=tag, color=self.color_map[tag])
                total_height = np.zeros(len(tag_freq.values()))

            total_height += np.array(list(tag_freq.values()))
            bars.append(tag_bars)
        self.hist_axes.xaxis_date()

        return bars

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

    def format_hist(self) -> None:
        """Format graph-wide properties of the hour frequency histogram."""
        self.histogram.autofmt_xdate()

        self.hist_axes.set_title("Frequency of entries throughout the day",
                                 fontdict={"fontsize": 18, "family": "Poppins"}, pad=25)
