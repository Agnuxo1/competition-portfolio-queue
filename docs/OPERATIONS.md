# Operations

## The queue, stage by stage

Every competition moves through the same stages. A stage changes only when there is evidence for it.

`DISCOVERED → VERIFYING → ELIGIBLE → PREPARING → TRAINING → AUDIT → READY → SUBMITTED → RESULT_PENDING → CLOSED`

`INELIGIBLE` and `ON_HOLD` are exits, and each needs a recorded reason.

| Stage | Exit condition |
|---|---|
| VERIFYING | Official rules read: eligibility, access, dates with time zone, rules on prior code and sharing |
| PREPARING | Baseline reproduced and a dedicated repository exists |
| TRAINING | Block finished, results compared with the control, best candidate kept |
| AUDIT | Independent audit passed |
| READY | Package complete; the delivery action belongs to the owner when it needs an account, a signature or a declaration |
| SUBMITTED | Platform receipt stored |

## Priority rule

1. Registrations and entry requirements that are about to lapse.
2. The nearest deadline with a useful training block available.
3. Packages ready to deliver.
4. Critical fixes, then improvements with high impact.

The target for a trainable entry is 24 hours on two GPUs (48 GPU-hours), when the deadline and rules allow it. Training stops two hours before the deadline so the result can be frozen and delivered. Entries that need no training are not given GPU hours.

## Authority

| Component | Authority |
|---|---|
| GPU queue and feeder on the server | Sole dispatch authority for GPU work |
| This engine | Reads, audits and proposes |
| Owner | Accounts, signatures, payments, legal declarations and final submissions |
| Independent auditor | Passes or blocks a package before delivery |

The tick runs in observe mode: it never assigns a lane. Moving it to an apply mode is a separate decision, and it stays closed while a campaign with an explicit priority order is running.

## Repository policy

Each finished project gets one dedicated repository. Visibility follows the competition rules:

- **Public as soon as the rules allow.** This is the default.
- **Private until the window closes** where rules limit sharing. Kaggle's standard rules, for example, ask that publicly shared competition code be posted on the competition's own forum or notebooks. Rules vary by competition, so each case is read individually.
- The tick reports `public_repo_while_sharing_restricted` so that those cases get checked against their rules.

Whatever can be public is published on both GitHub and Kaggle: code as a notebook, own data and artefacts as a dataset, weights as a model, each linking back to the repository. Work for an open competition waits for the close, unless the owner decides to share it there.

## Data policy

The public register holds only facts that are public anyway. Next actions, blockers, rankings and private repository names stay in the local overlay. Validation rejects mailbox links and local paths, and a test checks the published file.

## Updating

```bash
python -m competition_queue validate
python scripts/build_docs.py
python scripts/build_manifest.py
python -m pytest -q
```
