# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Markdown views of the register and of the GPU capacity simulation."""
from __future__ import annotations

from datetime import datetime, timedelta

from .model import WORK_STAGES, Competition
from .schedule import Allocation, effective_deadline, lane, ordered

STAGE_ES = {
    "DISCOVERED": "Detectado", "VERIFYING": "Verificando", "ELIGIBLE": "Elegible",
    "PREPARING": "Preparando", "TRAINING": "Entrenando", "AUDIT": "Auditoría",
    "READY": "Listo para enviar", "SUBMITTED": "Enviado", "RESULT_PENDING": "Pendiente de fallo",
    "CLOSED": "Cerrado", "INELIGIBLE": "No elegible", "ON_HOLD": "En reserva",
}
LANE_ES = {"owner": "Fran", "gpu": "GPU", "agent": "Agentes", "waiting": "Esperando a terceros"}


def utc(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "-"


def madrid(dt: datetime | None) -> str:
    """Render November to March dates in CET, the zone of every deadline listed here."""
    return (dt + timedelta(hours=1)).strftime("%d/%m %H:%M") if dt else "-"


def cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")


def public_list(items: list[Competition], now: datetime) -> str:
    """Public English list: open work by deadline, then delivered and closed entries."""
    lines = [
        "# Competition portfolio",
        "",
        f"Generated {now:%Y-%m-%d %H:%M} UTC from `data/competitions.json`. Dates are UTC.",
        "Rankings are left out on purpose: each platform's leaderboard is the source of truth.",
        "",
        "## Open work, nearest deadline first",
        "",
        "| # | Competition | Platform | Next deadline (UTC) | Stage | Repository |",
        "|---:|---|---|---|---|---|",
    ]
    rows = [(d, c) for d, c in ordered(items, now) if c.stage != "DISCOVERED"]
    for i, (due, c) in enumerate(rows, 1):
        lines.append(
            f"| {i} | [{cell(c.name)}]({c.url}) | {cell(c.platform)} | {utc(due)} | {c.stage} | {repo_cell(c)} |"
        )
    groups = (
        ("Delivered, awaiting a result", ("SUBMITTED", "RESULT_PENDING")),
        ("Candidates under review", ("DISCOVERED",)),
        ("Parked on purpose", ("ON_HOLD",)),
        ("Finished", ("CLOSED",)),
        ("Not eligible", ("INELIGIBLE",)),
    )
    for title, stages in groups:
        chosen = sorted((c for c in items if c.stage in stages), key=lambda c: c.name.lower())
        if not chosen:
            continue
        lines += ["", f"## {title}", "", "| Competition | Platform | Stage | Repository |", "|---|---|---|---|"]
        for c in chosen:
            lines.append(f"| [{cell(c.name)}]({c.url}) | {cell(c.platform)} | {c.stage} | {repo_cell(c)} |")
    return "\n".join(lines) + "\n"


def repo_cell(c: Competition) -> str:
    if c.repo_visibility == "public" and c.repo:
        return f"[{c.repo}](https://github.com/Agnuxo1/{c.repo})"
    return "private until release" if c.repo_visibility == "private" else "-"


def private_list(items: list[Competition], now: datetime) -> str:
    """Spanish working list with the private overlay, split by who acts next."""
    lines = [
        "# Listado de trabajo de concursos",
        "",
        f"Generado {now:%d/%m/%Y %H:%M} UTC. Horas en Madrid (CET). Documento privado.",
        "",
    ]
    rows = ordered(items, now)
    for key in ("owner", "gpu", "agent", "waiting"):
        chosen = [(d, c) for d, c in rows if lane(c) == key]
        if not chosen:
            continue
        lines += [
            f"## {LANE_ES[key]} ({len(chosen)})",
            "",
            "| Cierre | Quedan | Concurso | Etapa | Siguiente paso |",
            "|---|---:|---|---|---|",
        ]
        for due, c in chosen:
            left = (due - now).total_seconds() / 86400
            step = cell(c.next_action or c.blocker or "-")
            lines.append(f"| {madrid(due)} | {left:.1f} d | [{cell(c.name)}]({c.url}) | {STAGE_ES[c.stage]} | {step} |")
        lines.append("")
    dated = {c.id for _, c in rows}
    undated = [c for c in items if c.stage in WORK_STAGES and c.id not in dated]
    if undated:
        lines += ["## Sin fecha exacta", "", "| Concurso | Etapa | Plazo publicado | Siguiente paso |", "|---|---|---|---|"]
        for c in sorted(undated, key=lambda c: c.name.lower()):
            lines.append(f"| [{cell(c.name)}]({c.url}) | {STAGE_ES[c.stage]} | {cell(c.deadline_note or '-')} | {cell(c.next_action or '-')} |")
        lines.append("")
    waiting = [c for c in items if c.stage in ("SUBMITTED", "RESULT_PENDING")]
    if waiting:
        lines += ["## Entregados", "", "| Concurso | Etapa | Puesto o nota | Pendiente |", "|---|---|---|---|"]
        for c in sorted(waiting, key=lambda c: c.name.lower()):
            lines.append(f"| {cell(c.name)} | {STAGE_ES[c.stage]} | {cell(c.rank or '-')} | {cell(c.next_action or '-')} |")
        lines.append("")
    closed = [c for c in items if c.stage in ("INELIGIBLE", "ON_HOLD", "CLOSED")]
    if closed:
        lines += ["## Cerrados, no elegibles y en reserva", "", "| Concurso | Etapa | Motivo |", "|---|---|---|"]
        for c in sorted(closed, key=lambda c: (c.stage, c.name.lower())):
            lines.append(f"| {cell(c.name)} | {STAGE_ES[c.stage]} | {cell(c.blocker or c.rank or '-')} |")
        lines.append("")
    return "\n".join(lines)


def schedule_table(results: dict[str, Allocation]) -> str:
    """GPU delivery table for one scenario, nearest stop first."""
    lines = [
        "| Competition | Stop (UTC) | Target GPU-h | Delivered GPU-h | Pinned beyond target | Result |",
        "|---|---|---:|---:|---:|---|",
    ]
    for a in sorted(results.values(), key=lambda a: a.stop):
        lines.append(f"| {a.id} | {utc(a.stop)} | {a.target:g} | {a.delivered:.1f} | {a.extra:.1f} | {a.status} |")
    return "\n".join(lines) + "\n"


def next_deadline(c: Competition, now: datetime) -> str:
    return utc(effective_deadline(c, now))
