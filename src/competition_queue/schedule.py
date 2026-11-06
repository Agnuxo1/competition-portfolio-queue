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
EPSILON = 1e-9


def registration_lapsed(c: Competition, now: datetime) -> bool:
    """True when the entry needed a registration whose date has already gone."""
    return bool(c.registration and not c.registered and c.registration <= now)


def effective_deadline(c: Competition, now: datetime) -> datetime | None:
    """Earliest date still ahead that can end the entry; a lapsed registration ends it."""
    if registration_lapsed(c, now):
        return None
    dates = []
    if c.registration and not c.registered:
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
    if c.compute == "gpu" and (c.gpu_target_hours > 0 or c.stage == "TRAINING"):
        return "gpu"
    return "agent"


@dataclass(frozen=True)
class Pin:
    """A block fixed by the owner; it takes `gpus` cards between `start` and `end`."""

    id: str
    start: datetime
    end: datetime
    gpus: int

    def __post_init__(self) -> None:
        if self.gpus <= 0 or self.end <= self.start:
            raise ValueError(f"invalid pin {self.id}: needs positive GPUs and end after start")


@dataclass
class Allocation:
    id: str
    stop: datetime
    target: float
    delivered: float = 0.0  # GPU-hours counted towards the target, never above it
    extra: float = 0.0      # pinned GPU-hours beyond the target
    first: datetime | None = None
    last: datetime | None = None

    @property
    def status(self) -> str:
        if self.delivered >= self.target - EPSILON:
            return "FULL"
        return "PARTIAL" if self.delivered > EPSILON else "NONE"


def simulate(
    items: list[Competition],
    now: datetime,
    gpus: int = 2,
    pins: tuple[Pin, ...] = (),
    freeze_hours: int = FREEZE_HOURS,
) -> dict[str, Allocation]:
    """Give the free GPUs of each exact time segment to the nearest unfinished deadline.

    Segments break at every stop, pin edge and start date, so no credit crosses a
    limit. The target is in GPU-hours: 48 means 24 wall-clock hours on two cards.
    """
    allocations: dict[str, Allocation] = {}
    not_before: dict[str, datetime] = {}
    for c in items:
        if c.compute != "gpu" or c.gpu_target_hours <= 0 or c.stage not in WORK_STAGES:
            continue
        if c.submission is None:
            continue
        stop = c.submission - timedelta(hours=freeze_hours)
        if c.registration and not c.registered:
            stop = min(stop, c.registration)  # work past a missed registration is lost
        if stop <= now:
            continue
        allocations[c.id] = Allocation(c.id, stop, c.gpu_target_hours)
        if c.not_before:
            not_before[c.id] = c.not_before
    if not allocations:
        return {}
    horizon = max(a.stop for a in allocations.values())
    edges = {now, horizon}
    edges.update(a.stop for a in allocations.values())
    edges.update(not_before.values())
    for pin in pins:
        edges.update((pin.start, pin.end))
    points = sorted(e for e in edges if now <= e <= horizon)
    for start, end in zip(points, points[1:]):
        _fill_segment(allocations, not_before, pins, start, end, gpus)
    return allocations


def _fill_segment(allocations, not_before, pins, start, end, gpus) -> None:
    """Credit one segment; every limit is a segment edge, so each holds throughout it."""
    hours = (end - start).total_seconds() / 3600
    free = gpus
    for pin in pins:
        if not (pin.start <= start and end <= pin.end) or free <= 0:
            continue
        used = min(pin.gpus, free)
        free -= used
        a = allocations.get(pin.id)
        if a is not None and start < a.stop and not_before.get(a.id, start) <= start:
            _credit(a, used * hours, start, end)
    if free <= 0:
        return
    capacity = free * hours
    spent = 0.0
    ready = sorted(
        (
            a for a in allocations.values()
            if a.target - a.delivered > EPSILON and start < a.stop
            and not_before.get(a.id, start) <= start
        ),
        key=lambda a: a.stop,
    )
    for a in ready:
        if capacity - spent <= EPSILON:
            break
        used = min(capacity - spent, a.target - a.delivered)
        begin = start + timedelta(hours=spent / free)
        spent += used
        _credit(a, used, begin, start + timedelta(hours=spent / free))


def _credit(a: Allocation, gpu_hours: float, start: datetime, end: datetime) -> None:
    towards = min(gpu_hours, a.target - a.delivered)
    a.delivered += towards
    a.extra += gpu_hours - towards
    a.first = a.first or start
    a.last = end
