"""
Display a graph of journal entries from Day One JSON.

usage: run.py [-h] -f FILE [-d]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to exported Day One JSON file
"""

import argparse

from source import graph

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Display a graph of journal entries from Day One JSON")
    parser.add_argument("-f", "--file", required=True,
                        help="Path to exported Day One JSON file")

    args = parser.parse_args()

    graph.App()
