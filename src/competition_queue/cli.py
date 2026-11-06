# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Command line: validate, order, render, schedule and tick."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .model import load_register, parse_utc, validate
from .render import private_list, public_list, schedule_table
from .schedule import Pin, lane, ordered, simulate
from .tick import audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="competition-queue", description=__doc__)
    parser.add_argument("--register", default="data/competitions.json")
    parser.add_argument("--overlay", help="private overlay JSON, merged by id")
    parser.add_argument("--now", help="ISO-8601 UTC instant, defaults to the clock")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="check the register schema")
    sub.add_parser("order", help="print open work by nearest deadline")
    render = sub.add_parser("render", help="write a Markdown list")
    render.add_argument("--private", action="store_true", help="Spanish working list with overlay fields")
    render.add_argument("--out", required=True)
    schedule = sub.add_parser("schedule", help="simulate GPU delivery")
    schedule.add_argument("--gpus", type=int, default=2)
    schedule.add_argument(
        "--pin", action="append", default=[],
        help="id,start,end,gpus with ISO-8601 instants; repeatable",
    )
    tick = sub.add_parser("tick", help="read-only audit against a queue listing")
    tick.add_argument("--queue", required=True, help="JSON from `client.py cola listar`")
    tick.add_argument("--out", help="write the report here as well as to stdout")
    return parser


def parse_pin(text: str) -> Pin:
    pid, start, end, gpus = text.split(",")
    return Pin(pid, parse_utc(start), parse_utc(end), int(gpus))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
    items = load_register(args.register, args.overlay)

    errors = validate(items)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if args.command == "validate":
        print(f"ok: {len(items)} competitions")
    elif args.command == "order":
        for due, c in ordered(items, now):
            print(f"{due:%Y-%m-%d %H:%M}Z  {lane(c):8} {c.stage:11} {c.id}")
    elif args.command == "render":
        text = private_list(items, now) if args.private else public_list(items, now)
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    elif args.command == "schedule":
        pins = tuple(parse_pin(p) for p in args.pin)
        print(schedule_table(simulate(items, now, gpus=args.gpus, pins=pins)), end="")
    elif args.command == "tick":
        queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
        report = json.dumps(audit(items, queue, now), ensure_ascii=False, indent=1)
        if args.out:
            Path(args.out).write_text(report + "\n", encoding="utf-8", newline="\n")
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
