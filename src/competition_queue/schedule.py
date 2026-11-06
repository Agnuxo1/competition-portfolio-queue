# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Earliest-deadline ordering and an hourly GPU capacity simulation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .model import WORK_STAGES, Competition

FREEZE_HOURS = 2  # the last hours before a deadline are for freezing and delivery


def effective_deadline(c: Competition, now: datetime) -> datetime | None:
    """Earliest date still ahead that can end the entry; registration counts until work starts."""
    dates = []
    if c.registration and c.stage in ("DISCOVERED", "VERIFYING", "ELIGIBLE", "READY"):
        dates.append(c.registration)
    if c.submission:
        dates.append(c.submission)
    ahead = [d for d in dates if d > now]
    return min(ahead) if ahead else None


def ordered(items: list[Competition], now: datetime) -> list[tuple[datetime, Competition]]:
    """Open work sorted by nearest effective deadline; entries without a date are left out."""
    rows = []
    for c in items:
        if c.stage not in WORK_STAGES:
            continue
        due = effective_deadline(c, now)
        if due is not None:
            rows.append((due, c))
    return sorted(rows, key=lambda r: (r[0], r[1].id))


def lane(c: Competition) -> str:
    """Which queue owns the next step: the owner, the GPUs or an agent."""
    if c.gate == "owner":
        return "owner"
    if c.gate in ("organiser", "platform"):
        return "waiting"
    if c.compute == "gpu" and c.gpu_target_hours > 0:
        return "gpu"
    return "agent"


@dataclass(frozen=True)
class Pin:
    """A block fixed by the owner; it takes `gpus` cards between `start` and `end`."""

    id: str
    start: datetime
    end: datetime
    gpus: int


@dataclass
class Allocation:
    id: str
    stop: datetime
    target: int
    delivered: int = 0
    first: datetime | None = None
    last: datetime | None = None

    @property
    def status(self) -> str:
        if self.delivered >= self.target:
            return "FULL"
        return "PARTIAL" if self.delivered else "NONE"


def simulate(
    items: list[Competition],
    now: datetime,
    gpus: int = 2,
    pins: tuple[Pin, ...] = (),
    freeze_hours: int = FREEZE_HOURS,
) -> dict[str, Allocation]:
    """Give each hour's free GPUs to the nearest unfinished deadline.

    The target is in GPU-hours, so 48 means 24 wall-clock hours on two cards.
    Pinned hours count towards their own entry, and the time step is one hour.
    """
    allocations: dict[str, Allocation] = {}
    not_before: dict[str, datetime] = {}
    for c in items:
        if c.compute != "gpu" or c.gpu_target_hours <= 0 or c.stage not in WORK_STAGES:
            continue
        if c.submission is None or c.submission <= now:
            continue
        stop = c.submission - timedelta(hours=freeze_hours)
        allocations[c.id] = Allocation(c.id, stop, c.gpu_target_hours)
        if c.not_before:
            not_before[c.id] = c.not_before
    if not allocations:
        return {}
    horizon = max(a.stop for a in allocations.values())
    hour = timedelta(hours=1)
    t = now
    while t < horizon:
        free = gpus
        for pin in pins:
            if pin.start <= t < pin.end and free > 0:
                used = min(pin.gpus, free)
                free -= used
                if pin.id in allocations:
                    _credit(allocations[pin.id], used, t)
        ready = sorted(
            (
                a for a in allocations.values()
                if a.delivered < a.target and t < a.stop
                and not_before.get(a.id, t) <= t
            ),
            key=lambda a: a.stop,
        )
        for a in ready:
            if free <= 0:
                break
            used = min(free, a.target - a.delivered)
            free -= used
            _credit(a, used, t)
        t += hour
    return allocations


def _credit(a: Allocation, gpu_hours: int, t: datetime) -> None:
    a.delivered += gpu_hours
    a.first = a.first or t
    a.last = t
