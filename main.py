#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import timezone, datetime, timedelta
from typing import List, Optional, Union

DOCS = "https://www.gnu.org/software/coreutils/manual/html_node/Date-input-formats.html"
FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
]


@dataclass(frozen=True)
class Item:
    title: str
    subtitle: str
    arg: str


@dataclass(frozen=True)
class Feedback:
    items: List[Item]


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__


def atoi(s: Union[int, str, float]) -> Optional[int]:
    try:
        return int(s)
    except ValueError:
        return None


def generate_items(t: datetime, desc: str):
    ts = t.timestamp()
    utc = datetime.fromtimestamp(ts, timezone.utc)
    items = [Item(str(int(ts)), f"{desc} Timestamp", str(int(ts)))] + [
        Item(t_.strftime(layout), f"{desc} ({t_.tzinfo})", t_.strftime(layout))
        for t_ in [t, utc]
        for layout in FORMATS
    ]
    return items


def generate_feedback(items: List[Item]):
    return CustomEncoder().encode(Feedback(items))


def read_from_clipboard() -> str:
    return (
        subprocess.check_output(["pbpaste"], env={"LANG": "en_US.UTF-8"})
        .decode("utf-8")
        .strip()
    )


def gdate(date: str) -> Optional[int]:
    try:
        return int(
            (
                subprocess.check_output(
                    ["date", f"--date={date}", "+%s"],
                    env={
                        "LANG": "en_US.UTF-8",
                        "PATH": f"/opt/homebrew/opt/coreutils/libexec/gnubin:{os.environ.get('PATH', '')}",
                    },
                )
                .decode("utf-8")
                .strip()
            )
        )
    except subprocess.CalledProcessError:
        return None


def main():
    try:
        items = list()
        arg = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
        if not arg:
            now = datetime.now().astimezone()
            cb = read_from_clipboard()
            if ts := (atoi(cb) or gdate(cb) or None):
                t = datetime.fromtimestamp(ts).astimezone()
                items.extend(generate_items(t, f"From Clipboard: {cb}"))
            items.extend(generate_items(now, "Current Time"))
        else:
            if ts := (gdate(arg) or gdate(f"@{arg}")):
                t = datetime.fromtimestamp(ts).astimezone()
                items.extend(generate_items(t, "From Arg"))
        items.append(Item(DOCS, "Visit `gdate` docs", DOCS))
        print(generate_feedback(items))
    except IndexError as e:
        print(f"Invalid input: {e}")
        exit(1)


if __name__ == "__main__":
    main()
