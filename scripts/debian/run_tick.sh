#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
# Read-only audit tick. It copies the queue file, then reads the copy.
set -euo pipefail
BASE="${PORTFOLIO_BASE:-/mnt/datos/competition-portfolio}"
QUEUE="${PORTFOLIO_QUEUE:-/home/ai/servidor-ia/cola.json}"
mkdir -p "$BASE/state"
cp "$QUEUE" "$BASE/state/queue-snapshot.json"
cd "$BASE/repo"
PYTHONPATH=src python3 -m competition_queue \
  --register data/competitions.json \
  --overlay "$BASE/overlay_private.json" \
  tick --queue "$BASE/state/queue-snapshot.json" --out "$BASE/state/tick-latest.json" > /dev/null
PYTHONPATH=src python3 -m competition_queue \
  --register data/competitions.json \
  --overlay "$BASE/overlay_private.json" \
  render --private --out "$BASE/state/LISTADO_CONCURSOS.md"
