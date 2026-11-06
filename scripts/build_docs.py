# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Regenerate docs/COMPETITIONS.md, docs/GPU_SCENARIOS.md and the hero figure."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

from competition_queue.model import load_register, parse_utc  # noqa: E402
from competition_queue.render import public_list, schedule_table  # noqa: E402
from competition_queue.schedule import Pin, simulate  # noqa: E402

NOW = parse_utc("2026-11-06T08:00:00Z")
TRAFFIC = Pin("traffic-flow-bench", NOW, parse_utc("2026-11-07T04:55:00Z"), 2)
UMUD_START = parse_utc("2026-11-07T04:55:00Z")
UMUD_END = parse_utc("2026-11-14T21:00:00Z")
UMUD_SPLIT = parse_utc("2026-11-10T04:55:00Z")
SCENARIOS = {
    "A. One entry holds both GPUs until its stop": (
        TRAFFIC, Pin("umud", UMUD_START, UMUD_END, 2),
    ),
    "B. Both GPUs for 72 h, then one GPU rotates by deadline": (
        TRAFFIC, Pin("umud", UMUD_START, UMUD_SPLIT, 2), Pin("umud", UMUD_SPLIT, UMUD_END, 1),
    ),
}
THIRD = "C. Scenario B with a third GPU available"
SHOWN = ("solar-filament-2026", "ai-emulation", "k12-misconception", "eeg-emg-foundation", "soil-grain-size")
INK, MUTED, A_COL, B_COL, BG = "#14213d", "#6b7280", "#d1495b", "#00798c", "#fbfaf7"


def frame(title: str, results: dict, colour: str, shown_upto: int) -> Image.Image:
    fig, ax = plt.subplots(figsize=(8.4, 4.2), dpi=100, facecolor=BG)
    ax.set_facecolor(BG)
    names = list(SHOWN)[::-1]
    for y, name in enumerate(names):
        a = results[name]
        ax.barh(y, a.target, color="#e5e3dc", height=0.58)
        visible = a.delivered if SHOWN.index(name) < shown_upto else 0
        ax.barh(y, visible, color=colour, height=0.58)
        if SHOWN.index(name) < shown_upto:
            ax.text(a.target + 1, y, f"{a.delivered:.0f}/{a.target:g}", va="center", color=INK, fontsize=11)
    ax.set_yticks(range(len(names)), names, color=INK, fontsize=11)
    ax.set_xlim(0, 58)
    ax.set_xlabel("GPU-hours delivered before each freeze point (simulated)", color=MUTED, fontsize=10)
    ax.set_title(title, loc="left", color=INK, fontsize=13, fontweight="bold", pad=12)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c6bd")
    ax.tick_params(axis="x", colors=MUTED)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    fig.canvas.draw()
    image = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB")
    plt.close(fig)
    return image.quantize(colors=64, dither=Image.Dither.NONE)


def main() -> None:
    items = load_register(ROOT / "data" / "competitions.json")
    (ROOT / "docs" / "COMPETITIONS.md").write_text(public_list(items, NOW), encoding="utf-8", newline="\n")

    parts = [
        "# GPU capacity scenarios",
        "",
        f"Simulated from `data/competitions.json` at {NOW:%Y-%m-%d %H:%M} UTC on two GPUs unless stated,",
        "with the last two hours before each deadline reserved for freezing and delivery.",
        "A target of 48 GPU-hours means 24 wall-clock hours on two cards.",
        "These are capacity estimates, not measured training runs and not a forecast of any result.",
        "Delivered hours count only the time ahead of the simulation start.",
        "",
    ]
    frames: list[Image.Image] = []
    durations: list[int] = []
    colours = (A_COL, B_COL)
    for (title, pins), colour in zip(SCENARIOS.items(), colours):
        results = simulate(items, NOW, pins=pins)
        parts += [f"## {title}", "", schedule_table(results)]
        for shown in range(1, len(SHOWN) + 1):
            frames.append(frame(title, results, colour, shown))
            durations.append(450 if shown < len(SHOWN) else 2600)
    pins = list(SCENARIOS.values())[1]
    parts += [f"## {THIRD}", "", schedule_table(simulate(items, NOW, gpus=3, pins=pins))]
    (ROOT / "docs" / "GPU_SCENARIOS.md").write_text("\n".join(parts), encoding="utf-8", newline="\n")
    frames[0].save(
        ROOT / "assets" / "hero-workflow.gif", save_all=True, append_images=frames[1:],
        duration=durations, loop=0, optimize=True,
    )


if __name__ == "__main__":
    main()
