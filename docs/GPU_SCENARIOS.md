# GPU capacity scenarios

Simulated from `data/competitions.json` at 2026-11-06 08:00 UTC on two GPUs, one-hour steps,
with the last two hours before each deadline reserved for freezing and delivery.
A target of 48 GPU-hours means 24 wall-clock hours on both cards.
These are capacity estimates, not measured training runs and not a forecast of any result.
Delivered hours count only the time ahead of the simulation start.

## A. One entry holds both GPUs until its stop

| Competition | Stop (UTC) | Target GPU-h | Delivered GPU-h | Pinned beyond target | Result |
|---|---|---:|---:|---:|---|
| umud | 2026-11-14 21:00 | 48 | 48.0 | 320.2 | FULL |
| solar-filament-2026 | 2026-11-15 04:00 | 48 | 14.0 | 0.0 | PARTIAL |
| ai-emulation | 2026-11-16 03:00 | 48 | 46.0 | 0.0 | PARTIAL |
| k12-misconception | 2026-11-16 22:00 | 48 | 38.0 | 0.0 | PARTIAL |
| eeg-emg-foundation | 2026-11-21 20:59 | 48 | 48.0 | 0.0 | FULL |
| soil-grain-size | 2026-11-30 09:00 | 48 | 48.0 | 0.0 | FULL |
| gemma4-dev-agent | 2026-12-02 21:59 | 48 | 48.0 | 0.0 | FULL |
| light-my-cells-2 | 2026-12-13 21:59 | 48 | 48.0 | 0.0 | FULL |
| enveda-casmi-2026 | 2026-12-14 21:59 | 48 | 48.0 | 0.0 | FULL |
| climx-2026 | 2026-12-15 08:59 | 48 | 48.0 | 0.0 | FULL |
| name-that-llm | 2027-01-14 21:59 | 48 | 48.0 | 0.0 | FULL |

## B. Both GPUs for 72 h, then one GPU rotates by deadline

| Competition | Stop (UTC) | Target GPU-h | Delivered GPU-h | Pinned beyond target | Result |
|---|---|---:|---:|---:|---|
| umud | 2026-11-14 21:00 | 48 | 48.0 | 208.1 | FULL |
| solar-filament-2026 | 2026-11-15 04:00 | 48 | 48.0 | 0.0 | FULL |
| ai-emulation | 2026-11-16 03:00 | 48 | 48.0 | 0.0 | FULL |
| k12-misconception | 2026-11-16 22:00 | 48 | 48.0 | 0.0 | FULL |
| eeg-emg-foundation | 2026-11-21 20:59 | 48 | 48.0 | 0.0 | FULL |
| soil-grain-size | 2026-11-30 09:00 | 48 | 48.0 | 0.0 | FULL |
| gemma4-dev-agent | 2026-12-02 21:59 | 48 | 48.0 | 0.0 | FULL |
| light-my-cells-2 | 2026-12-13 21:59 | 48 | 48.0 | 0.0 | FULL |
| enveda-casmi-2026 | 2026-12-14 21:59 | 48 | 48.0 | 0.0 | FULL |
| climx-2026 | 2026-12-15 08:59 | 48 | 48.0 | 0.0 | FULL |
| name-that-llm | 2027-01-14 21:59 | 48 | 48.0 | 0.0 | FULL |
