# Competition status — 8 November 2026

## Verification update - 8 November, 18:48 UTC

The earlier leaderboard table below remains a dated snapshot. These checks add technical evidence and do not establish a new competition score or ranking.

- **Traffic Flow Bench:** a CPU-only run recomposed V1 from the three saved per-task prediction files and the public submission key. All **6,980,503 rows** and all six columns matched the frozen V1 baseline, with **zero mismatches** and byte identity after CRLF/LF normalization. The normalized SHA-256 is `c3cb3594d011309a8d53ae71fff9c58ec32ff9896c71e06aa2daf1c9615ba89f`. The computation took **45.30 seconds**, under effective limits of 8 GiB RAM, zero swap and a CPU quota of 200%; twelve final checks passed and the process is closed. This verifies assembly of saved predictions. Retraining, the exact historical model runtime and end-to-end model reproduction remain unverified. Recovered historical logs declare 300,000 state-training samples, whereas the published run_a.sh specifies 400,000; that discrepancy remains to be reconciled. The code/PDF package has not yet been sent. The [official evaluation and timeline](https://www.kaggle.com/competitions/2026-ieee-big-data-traffic-flow-bench/overview/evaluation) require it by 10 November, 23:59 AoE (**11 November, 12:59 Madrid**) for award eligibility; the review pool comprises the top ten eligible teams, rather than simply the first ten positions overall.
- **Builder:** a bounded local test completed three reviews in distinct reviewer threads, separate from the draft author's thread, and the deterministic verdict **revise, internal score 6.47/10** on an existing synthetic 20-case draft. This demonstrates the review/verdict stage; successful new researcher generation, scientific benefit and official competition acceptance are not established. The model and preview processes are closed. The public video and official entry remain pending.
- **GPU observation at 18:48 UTC:** GPU0 and GPU1 utilization was 97% and 99%, respectively, while managed Solar and QVC jobs were active. This is a sample, not evidence of uninterrupted operation.

---


Leaderboard snapshot verified through authenticated platform pages and submission APIs between 11:38 and 12:00 UTC. Receipt and publication updates below have their own later timestamps. Ranks can change while a competition remains open. Madrid times below use CET (UTC+01:00).

| Competition | Stage | Verified position and best score | Deadline, Madrid |
|---|---|---|---|
| [Traffic Flow Bench](https://www.kaggle.com/competitions/2026-ieee-big-data-traffic-flow-bench/leaderboard) | Prediction competition completed | **642**, final private leaderboard; **0.74291** | Predictions closed **7 Nov, 07:55** |
| [UMUD](https://www.kaggle.com/competitions/umud-challenge-muscle-architecture-in-ultrasound-data/leaderboard) | Active | **44**, public; **0.22941** | **15 Nov, 00:00** |
| [Filament Segmentation](https://www.kaggle.com/competitions/filament-segmentation-2026/leaderboard) | Active | **327**, public; **0.39** | **15 Nov, 07:00** |
| [AI Emulation](https://www.kaggle.com/competitions/ieee-bigdata-cup-2026-ai-emulation-challenge/leaderboard) | Active | **41**, public; **0.062** | **16 Nov, 06:00** |
| [K-12 Misconception Detection](https://www.kaggle.com/competitions/misconception-detection-in-k-12-student-math-workings/leaderboard) | Active | **92**, public; **0.67683** | **17 Nov, 01:00** |
| [Neural Interfaces — Track 3 Sleep Onset](https://www.codabench.org/competitions/17983/) | Sealed final opening postponed; no active phase | Warm-up: **157/188**, **55.82 s W-bMAE**. No sealed-final submission or final rank | Published final deadline remains **21 Nov, 23:59**; opening date unconfirmed |

Scores use different metrics and cannot be compared across competitions. A warm-up position is not a final position. The Traffic row uses the final private leaderboard; other Kaggle positions above are public.

## Verified work in this recovery cycle

- AI Emulation C21, submission **58125450**, completed with **0.154**. It did not beat C20 (**58108828**, **0.062**), so C20 was retained and no manual final-selection change was made. The negative result is preserved. All five daily submission slots were used on 8 November.
- K-12's documentation now uses the organiser's **1,000 public / 2,498 private** split and withdraws unsupported paired public uncertainty calculations. The model and final pair are unchanged. [Reviewed correction](https://github.com/Agnuxo1/k12-misconception-tribunal/pull/1); [primary dataset description](https://huggingface.co/datasets/colearnlab/misconception-detection#splits-and-statistics). The solution repository remains private during the competition.
- The public ARC-AGI-3 notebook [arc3-chimera-v3](https://www.kaggle.com/code/franciscoangulo/arc3-chimera-v3), version **364389551** (internal experiment label **S03**), is available. Its associated model submission **57858448** has public score **0.26**. Publishing a notebook is separate from submitting the Paper Track write-up.
- **Edge Medicine:** the official application form confirmed receipt on 8 November at **12:09 UTC**. This is an application receipt, not finalist selection.
- **ARC Paper Track:** write-up **124655** shows **Submitted!**, observed at **12:28 UTC**. [CHIMERA paper entry](https://www.kaggle.com/competitions/arc-prize-2026-paper-track/writeups/chimera-online-holographic-outcome-memory-for-arc). It has 1,413 words in the editor, the public S03 notebook attached and a cover image. Jury outcome is pending. The paper is to be released under CC BY 4.0 at competition close, attributed to the author's Kaggle display name.
- CHIMERA's original code and methods now have an additional [MIT-0 option](https://github.com/Agnuxo1/arc3-chimera-explorer/blob/main/ARC_LICENSE_GRANT.md), expressly authorized by the author. Existing code, images, credits and watermarks are preserved. [Attribution and financial support are requested voluntarily](https://github.com/Agnuxo1/arc3-chimera-explorer/blob/main/AUTHOR_CREDITS_AND_SUPPORT.md); they impose no additional licence conditions. Third-party licences remain applicable.

GPU experiments use the managed server queue. Job completion, successful validation and an official score are recorded separately. No claim of uninterrupted GPU occupancy or a top-three result follows from this snapshot. This report contains no individual records from competition datasets, model weights or private source code.
