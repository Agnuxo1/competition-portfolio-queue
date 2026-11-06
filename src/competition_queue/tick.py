# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Read-only audit of the register against the GPU queue.

The tick never changes the queue. It reports what is stale, missing or next,
and writes proposals that a person or an authorised agent may apply.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from .model import ACTIVE_STAGES, WORK_STAGES, Competition, parse_utc
from .schedule import lane, ordered, registration_lapsed

MISMATCH_TOLERANCE = timedelta(hours=1)
QUEUE_GROUPS = ("en_cola", "activos", "pendiente_cierre")
FINAL_QUEUE_STATES = ("ENTREGADO", "CERRADO")


def queue_entries(queue: dict) -> dict[str, dict]:
    """Flatten a queue listing or a raw queue file into id -> entry.

    The raw file is the read-only path: `cola listar` itself reviews and saves.
    """
    if "proyectos" in queue:
        return {
            pid: entry for pid, entry in queue["proyectos"].items()
            if entry.get("estado") not in FINAL_QUEUE_STATES
        }
    entries: dict[str, dict] = {}
    for group in QUEUE_GROUPS:
        for entry in queue.get(group, []):
            if isinstance(entry, str):
                entries.setdefault(entry, {"id": entry})
            else:
                entries[entry["id"]] = {**entries.get(entry["id"], {}), **entry}
    return entries


def match_queue(items: list[Competition], entries: dict[str, dict]) -> dict[str, str]:
    """Map queue ids onto register ids through the id itself or declared aliases."""
    index = {c.id: c.id for c in items}
    for c in items:
        for alias in c.aliases:
            index[alias] = c.id
    return {qid: index[qid] for qid in entries if qid in index}


def audit(items: list[Competition], queue: dict, now: datetime) -> dict:
    """Compare both sources and return anomalies, lanes and proposals."""
    entries = queue_entries(queue)
    matched = match_queue(items, entries)
    by_id = {c.id: c for c in items}
    anomalies: dict[str, list[dict]] = defaultdict(list)
    proposals: list[str] = []

    for qid, entry in sorted(entries.items()):
        rid = matched.get(qid)
        if rid is None:
            anomalies["queue_entry_not_in_register"].append({"id": qid})
            continue
        c = by_id[rid]
        closed = parse_utc(entry.get("cierre_utc"))
        if c.stage in ("INELIGIBLE", "CLOSED") and entry.get("estado") in ("EN COLA", "AUDITORIA"):
            anomalies["finished_entry_still_queued"].append({"id": qid, "stage": c.stage})
            proposals.append(f"client.py cola cerrar {qid}  # register stage {c.stage}")
        if closed and closed < now and entry.get("estado") in ("EN COLA", "AUDITORIA") and c.stage not in ("INELIGIBLE", "CLOSED"):
            anomalies["queue_date_already_past"].append({"id": qid, "cierre_utc": entry["cierre_utc"], "stage": c.stage})
        dates = [d for d in (c.submission, c.registration) if d]
        if c.active and closed and not dates:
            anomalies["register_date_missing"].append({"id": qid, "queue": entry["cierre_utc"]})
        elif c.active and dates and "estado" in entry and not closed:
            anomalies["queue_date_missing"].append({"id": qid, "register": c.submission_utc or c.registration_utc})
        elif c.active and closed and all(abs(closed - d) > MISMATCH_TOLERANCE for d in dates):
            anomalies["deadline_mismatch"].append(
                {"id": qid, "queue": entry["cierre_utc"], "register": c.submission_utc or c.registration_utc}
            )

    in_queue = set(matched.values())
    for c in items:
        if c.stage in WORK_STAGES and registration_lapsed(c, now):
            anomalies["registration_lapsed"].append({"id": c.id, "registration_utc": c.registration_utc})
        if c.stage in ("VERIFYING", "ELIGIBLE", "PREPARING", "TRAINING", "AUDIT", "READY") and c.id not in in_queue:
            anomalies["active_entry_not_in_queue"].append({"id": c.id, "stage": c.stage})
        if c.code_sharing == "platform_only" and c.repo_visibility == "public" and c.stage in ACTIVE_STAGES:
            anomalies["public_repo_while_sharing_restricted"].append({"id": c.id, "repo": c.repo})
        if c.stage in ACTIVE_STAGES and c.repo_visibility == "none" and c.stage not in ("DISCOVERED", "VERIFYING"):
            anomalies["no_dedicated_repository"].append({"id": c.id, "stage": c.stage})

    lanes: dict[str, list[dict]] = defaultdict(list)
    for due, c in ordered(items, now):
        lanes[lane(c)].append(
            {
                "id": c.id,
                "due_utc": due.strftime("%Y-%m-%dT%H:%MZ"),
                "hours_left": round((due - now).total_seconds() / 3600, 1),
                "stage": c.stage,
                "next_action": c.next_action,
            }
        )
    return {
        "generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "observe",
        "counts": {
            "register": len(items),
            "queue": len(entries),
            "open_work": sum(len(v) for v in lanes.values()),
        },
        "anomalies": {k: anomalies[k] for k in sorted(anomalies)},
        "lanes": {k: lanes[k] for k in sorted(lanes)},
        "proposals": proposals,
    }
