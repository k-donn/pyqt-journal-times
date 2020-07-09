"""
Display a graph of journal entries from Day One JSON.

usage: python3.8 run.py [-h]

optional arguments:
  -h, --help            show this help message and exit
"""

import sys

from PyQt5.QtWidgets import QApplication

from source import graph

if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        exit(0)

    app = QApplication(sys.argv)

    journal_times = graph.App()
    exit(app.exec_())
