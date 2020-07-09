"""Utility functions."""

import json
from datetime import datetime

import pytz
import tzlocal

from .types import Entry, Export, List


def find_tags(entries: List[Entry]) -> List[str]:
    """Find all unique and first tags.

    Parameters
    ----------
    entries: `List[Entry]`
        Entries property of exported JSON

    Returns
    -------
    `List[str]`
        List of tags

    Notes
    -----
    The returned list is sorted in order to get the same mapping every single time given
    the same exported JSON

    """
    avail_tags: List[str] = []

    avail_tags = [entry["tags"][0]
                  for entry in entries if "tags" in entry]

    avail_tags.append("none")

    # Sort them to get the same color-mapping each time
    return sorted(list(set(avail_tags)))


def str_to_date(date_str: str) -> datetime:
    """Convert a string in Day One format to a datetime object.

    Matplotlib isn't compatible with timezone aware datetime objects.
    If one is passed to date2num, it undergoes unpredicted behaviour.
    This calculates the offset (offset from UTC changes based on a lot of things)
    then applies that offset via a timedelta object that doesn't affect/apply
    timezone info.

    Parameters
    ----------
    date_str: `str`
        String from an entry in JSON

    Returns
    -------
    `datetime`
        Parsed datetime object

    """
    utc_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    # This automatically calculates the offset to user's timezone
    # The offset is different throughout the year
    local_timezone = tzlocal.get_localzone()
    local_time_auto = utc_time.replace(tzinfo=pytz.utc)
    local_time_auto = utc_time.astimezone(local_timezone)

    local_time = utc_time + local_time_auto.utcoffset()
    return local_time


def extract_json(file) -> Export:
    """Extract JSON from supplied Day One journal export.

    Parameters
    ----------
    file : `ste`
        Path to file

    Returns
    -------
    `Export`
        Nested dictionary object with Day One JSON properties
    """
    with open(file, "r") as file:
        full_json = json.load(file)
    return full_json
