#!/usr/bin/env python3
# pyre-strict

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import List, Mapping, Optional, Union


class Format(StrEnum):
    SANS_TIMEZONE = "%Y-%m-%d %H:%M:%S"
    WITH_TIMEZONE = "%Y-%m-%d %H:%M:%S%z"
    TIMESTAMP = "%s"


DOCS = "https://www.gnu.org/software/coreutils/manual/html_node/Date-input-formats.html"
DEFAULT_FORMAT: Format = Format.SANS_TIMEZONE


class Source(Enum):
    CURRENT = 1
    CLIPBOARD = 2
    ARGUMENT = 3


@dataclass(frozen=True)
class Item:
    title: str
    subtitle: str
    arg: str


@dataclass(frozen=True)
class DatetimeItem:
    dt: datetime
    source: Source
    format_: Format

    @property
    def dict(self) -> Mapping[str, Union[str, Mapping[str, "DatetimeItem"]]]:
        cmd = DatetimeItem(self.dt, self.source, Format.TIMESTAMP)
        ctrl = DatetimeItem(self.dt, self.source, Format.WITH_TIMEZONE)
        mods = {}
        if self.format_ == DEFAULT_FORMAT:
            mods = {"cmd": cmd, "ctrl": ctrl}
        return {
            "title": self.dt.strftime(Format.WITH_TIMEZONE.value),
            "subtitle": f"Copy {self.source.name.title()} Time {self.format_.name.replace('_', ' ').title()} To Clipboard ({self.dt.tzinfo})",
            "arg": self.dt.strftime(self.format_.value),
            "mods": {k: v.dict for k, v in mods.items()},
        }


@dataclass(frozen=True)
class Feedback:
    items: List[Union[DatetimeItem, Item]]


def atoi(s: Union[int, str, float]) -> Optional[int]:
    try:
        return int(s)
    except ValueError:
        return None


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
        if arg:
            ts = atoi(arg) or gdate(arg)
            source = Source.ARGUMENT
        else:
            cb = read_from_clipboard()
            ts = atoi(cb) or gdate(cb)
            source = Source.CLIPBOARD
        datetimes = []
        if ts:
            datetimes.append((datetime.fromtimestamp(ts).astimezone(), source))
        datetimes.append((datetime.now().astimezone(), Source.CURRENT))
        for t, source in datetimes:
            items.append(DatetimeItem(t, source, DEFAULT_FORMAT))
            utc = datetime.fromtimestamp(t.timestamp(), timezone.utc)
            items.append(DatetimeItem(utc, source, DEFAULT_FORMAT))
        items.append(Item(DOCS, "Visit `gdate` docs", DOCS))
        print(
            json.dumps(
                Feedback(items), default=lambda x: getattr(x, "dict", x.__dict__)
            )
        )
    except IndexError as e:
        print(f"Invalid input: {e}")
        exit(1)


if __name__ == "__main__":
    main()
