# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Register schema: public fields, private overlay fields and validation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path

STAGES = (
    "DISCOVERED",      # seen in a source, rules not read
    "VERIFYING",       # rules, eligibility or access being checked
    "ELIGIBLE",        # rules read, eligible, work not started
    "PREPARING",       # work in progress without a GPU block
    "TRAINING",        # GPU block in progress
    "AUDIT",           # independent audit before delivery
    "READY",           # package complete, delivery action outstanding
    "SUBMITTED",       # delivery confirmed, window still open
    "RESULT_PENDING",  # window closed, result not published
    "CLOSED",          # finished with a final outcome
    "INELIGIBLE",      # excluded by rules, platform or organiser
    "ON_HOLD",         # parked on purpose, reason recorded
)
ACTIVE_STAGES = STAGES[:8]
WORK_STAGES = ("DISCOVERED", "VERIFYING", "ELIGIBLE", "PREPARING", "TRAINING", "AUDIT", "READY")
COMPUTE = ("gpu", "cpu", "none")
CODE_SHARING = ("open", "platform_only", "unknown")
VISIBILITY = ("public", "private", "none")
GATES = ("none", "owner", "organiser", "platform", "auditor")

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PRIVATE_URL_RE = re.compile(r"mail\.google\.com|^[A-Za-z]:[\\/]|/home/|/mnt/")


def parse_utc(value: str | None) -> datetime | None:
    """Parse an ISO-8601 instant and require an explicit UTC offset."""
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp without timezone: {value}")
    return parsed.astimezone(timezone.utc)


@dataclass
class Competition:
    """One competition. The fields above the marker are safe to publish."""

    id: str
    name: str
    platform: str
    url: str
    region: str
    compute: str
    stage: str
    submission_utc: str | None = None
    registration_utc: str | None = None
    not_before_utc: str | None = None
    deadline_note: str = ""
    code_sharing: str = "unknown"
    repo: str | None = None
    repo_visibility: str = "none"
    gpu_target_hours: int = 0
    # Private overlay, never written to the public register.
    gate: str = "none"
    next_action: str = ""
    blocker: str = ""
    rank: str = ""
    aliases: list[str] = field(default_factory=list)

    @property
    def submission(self) -> datetime | None:
        return parse_utc(self.submission_utc)

    @property
    def registration(self) -> datetime | None:
        return parse_utc(self.registration_utc)

    @property
    def not_before(self) -> datetime | None:
        return parse_utc(self.not_before_utc)

    @property
    def active(self) -> bool:
        return self.stage in ACTIVE_STAGES


PUBLIC_FIELDS = (
    "id", "name", "platform", "url", "region", "compute", "stage",
    "submission_utc", "registration_utc", "not_before_utc", "deadline_note",
    "code_sharing", "repo", "repo_visibility", "gpu_target_hours",
)
PRIVATE_FIELDS = ("gate", "next_action", "blocker", "rank", "aliases")


def validate(items: list[Competition]) -> list[str]:
    """Return every schema error; an empty list means the register is valid."""
    errors: list[str] = []
    seen: set[str] = set()
    for c in items:
        where = c.id or "<missing id>"
        if not ID_RE.match(c.id):
            errors.append(f"{where}: bad id")
        if c.id in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(c.id)
        if c.stage not in STAGES:
            errors.append(f"{where}: unknown stage {c.stage}")
        if c.compute not in COMPUTE:
            errors.append(f"{where}: unknown compute {c.compute}")
        if c.code_sharing not in CODE_SHARING:
            errors.append(f"{where}: unknown code_sharing {c.code_sharing}")
        if c.repo_visibility not in VISIBILITY:
            errors.append(f"{where}: unknown repo_visibility {c.repo_visibility}")
        if c.gate not in GATES:
            errors.append(f"{where}: unknown gate {c.gate}")
        if not c.url.startswith("https://"):
            errors.append(f"{where}: url must be https")
        if PRIVATE_URL_RE.search(c.url):
            errors.append(f"{where}: url points at private material")
        if c.gpu_target_hours < 0:
            errors.append(f"{where}: negative gpu_target_hours")
        if c.repo and c.repo_visibility == "none":
            errors.append(f"{where}: repo set without visibility")
        for label in ("submission_utc", "registration_utc", "not_before_utc"):
            try:
                parse_utc(getattr(c, label))
            except ValueError as exc:
                errors.append(f"{where}: {label}: {exc}")
        if c.active and not (c.submission_utc or c.registration_utc or c.deadline_note):
            errors.append(f"{where}: active entry without any deadline")
    return errors


def load_register(path: str | Path, overlay: str | Path | None = None) -> list[Competition]:
    """Load the public register and merge an optional private overlay by id."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))["competitions"]
    extra: dict[str, dict] = {}
    if overlay and Path(overlay).exists():
        extra = json.loads(Path(overlay).read_text(encoding="utf-8"))
    names = {f.name for f in fields(Competition)}
    items = []
    for row in rows:
        merged = {**row, **extra.get(row["id"], {})}
        unknown = set(merged) - names
        if unknown:
            raise ValueError(f"{row['id']}: unknown fields {sorted(unknown)}")
        items.append(Competition(**merged))
    return items


def public_rows(items: list[Competition]) -> list[dict]:
    """Project the register onto publishable fields, hiding private repository names."""
    rows = []
    for c in sorted(items, key=lambda x: x.id):
        row = {k: getattr(c, k) for k in PUBLIC_FIELDS}
        if c.repo_visibility != "public":
            row["repo"] = None
        rows.append(row)
    return rows
