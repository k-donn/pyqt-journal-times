# Journal Entry Times PyQt

A PyQt app to represent entries in a Day One journal.

## Usage

```bash
usage: run.py [-h]

Display a graph of journal entries from Day One JSON

optional arguments:
  -h, --help            show this help message and exit
```

## Running

To run from the root dir,


```bash
python3.8 run.py
```

## Generate Dummy Data

-   From the root of the foler,

```bash
python3.8 ./data/gen_dummy.py
```

-   Now, select the new `./data/Dummy.json` file from `run.py`

## Exporting Journal JSON

See [Exporting Entries](https://help.dayoneapp.com/en/articles/440668-exporting-entries) for instructions.

Export as JSON and place file in ./data directory.

## Meta

I got the inspiration from seeing [jiuguangw](https://github.com/jiuguangw/)'s [Agenoria](https://github.com/jiuguangw/Agenoria)

## TODO

-   [ ] Create super class that Dot Plot and Histogram inhereit
-   [ ] Add data summary tab
