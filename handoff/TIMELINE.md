# Timeline — what happened, when, and where the evidence is

One row per phase. **Times are measured**, not taken from the log headings: recording spans come from
each cast's header timestamp and its mtime, phase boundaries from the mtime of the artefact that
phase produced, and two gates from frames rendered out of the casts with `tools/cast_render.py`.
This matters because E022 established that the log's own headings between roughly 02:40 and 04:18
are overstated by up to 122 minutes. The log's *ordering* is reliable; its early *clock times* are
not, and it says so in an appended correction at line 1029.

Figure: `results/fig_timeline.pdf`. Total span **02:07 → 14:18 UTC, 730 minutes**, of which
**64 minutes are live recording**. Phases 9 and 10 were added after the stop-point-4 gate, when
Vivek asked whether the record conveyed a coherent workflow and then authorised further work.

| # | UTC | phase | what happened | evidence |
| --- | --- | --- | --- | --- |
| 0 | 02:07–02:08 | scaffold | project layout, three agent definitions verbatim from the brief, recorder dry run | log 30–125; `recordings/rec_00_test.cast`; `.claude/agents/*.md` |
| 1 | 02:08–03:01 | reconnaissance | what is actually on disk; **the brief's central premise refuted** — the data are stepped-sine sweeps, not impulses, so no threshold detection is possible (E004); drive amplitude checked; two live credentials found off camera (E008) | log 157–331; `results/errors.csv` E002–E011 |
| — | ~02:30 | **gate 1 / 1b** | run choice, method reset, channel scope, damping route — four decisions | log 126–156, 323–368 |
| 2 | 03:01–03:13 | extraction design | VCTS reader, DIANA environment shim, 283-channel driver, Slurm script written | `extract/DESIGN_step1.md`, `extract/vibes_env.sh`, `extract/extract_step1.sh` |
| — | ~03:07 | **gate 2** | Route A approved; **login node chosen over Slurm**, so the job script was never submitted | log 438–462, 563–606 |
| 3 | 03:13–03:51 | extract and convert | 283 channel-extractions; the advertised DB endpoint found dead (E012); triggers regenerated, which surfaced the **0.1 Hz heater pulser phase-locked to every step boundary** (E019); 21 sanity checks; conversion to float32 `.npy` | `logs/extract_driver.log`, `logs/triggers_RUNA.log`, `logs/sanity_step1.log`, `logs/to_npy.log`, `data/meta.json` |
| — | ~04:04 | **gate 3** | headline channel and damping route settled; home quota nearly full, caught before writing (E020) | log 795–862 |
| 4 | 03:51–04:17 | spec and isolation | `SPEC.md` written and copied to `verify/`; verifier isolation built **by construction**; sentinel planted and the boundary tested three ways | log 901–993; `SPEC.md`; `analysis/SENTINEL.txt` (04:16:17) |
| 5 | **04:17–04:58** | **the graph runs** | analyst and verifier in parallel. Verifier attempt 1 blocked by a missing allow list and **refused to fabricate** (E024); re-dispatched. A shared input was mutated mid-run (E027). Analyst delivered 12 modes, verifier 11. | **`rec_01_graph.cast` 0:00–41:00, 25.5 min live**; `logs/verifier_session.log`, `logs/verifier_session2.log`, `verify/VERIFIER_LOG.md` (30.8 kB), both `method_note.md`; log 994–1367 |
| — | 04:43:47 | **gate: model cost** | Vivek raises usage; critic moved to Sonnet; prompt change logged with old text, new text and reason | **`rec_01_graph.cast` at 26:40**; log 1268–1308 |
| 6 | 05:28–05:33 | critic | 7 checks on Sonnet with every threshold pre-supplied. 1 FAIL, 1 INCONCLUSIVE, 4 PASS, 1 N/A. Orchestrator's sealed audit matched it on every precomputed quantity. | **`rec_02_critic.cast` 0:00–6:00, 6.8 min live**; `critic/THRESHOLDS.md`, `critic/REPORT.md`; log 1417–1511 |
| — | 05:33–11:20 | *usage pause* | 5 h 47 m of dead time; `rec_02` stayed open across it, which is why its nominal length is 224 minutes | the gap is visible in `fig_timeline.pdf` |
| 7 | **11:20–12:32** | **reconcile** | each of the critic's eight ranked disagreements got a measurement, not a tabulation. Four moved. Two of the orchestrator's own attempts were void and were caught by checks written into their replacements (E039, E040). | **`rec_03_reconcile.cast`, 13.9 min live**; `reconcile/r1`…`r6c`; `results/comparison.csv` |
| — | 12:29–12:30 | **gate 4** | Vivek adjudicates the mode list — 11 headline, 7.46 Hz demoted — and cuts Step 6 | **`rec_03_reconcile.cast` at 68:45–69:29**; log 1581+ |
| 8 | 12:32–12:43 | deliver | process report, summary, reconciled modes, both figures, demo notes; `results/` swept of credentials and internal identifiers | `results/*` |
| — | 12:43–13:10 | **evidence audit** | Vivek asks whether the logs and recordings convey a coherent workflow. Measured recording coverage, which found **E044** — my own demo notes misdescribed my own recording and would have cut its best material. `TIMELINE.md` and `fig_timeline.pdf` written from measured spans only | this file; log 1660+ |
| 9 | **13:10–13:35** | **damping re-run** | **E032 closed.** SPEC §4.3 amended and approved: an upper limit is reportable only after an attempt that failed. Diffing both spec copies before editing exposed **E045** — `verify/SPEC.md` had been stale since 04:24 — which in turn retracted **E037** and under-credit **E047**. Verifier re-dispatched: **7 of 11 modes measured**, 4 honest non-detections, 5 cross-checking within 1.8 σ. It widened its window to 40.3 s, fitted across the pulser gaps, rejected its own acceptance cut mid-run, and built a null control nobody specified | **`rec_04_damping.cast`, 3.5 min live of 24.9**; `verify/damping.csv`, `verify/d0*.py`; log 1752+ |
| 10 | **14:04–14:18** | **causality re-run** | SPEC **§4.5 added**; both copies checksummed before dispatch, the E045 rule applied for the first time. Analyst re-dispatched with pre-boundary storage required. Result **inconclusive per cell (E051)** — median pre/null 0.98, the pre-boundary signal *is* the noise floor. It also measured the boundaries itself, refused my figure, and was right: **E050**, 0.24 s of my published number was a moving average | **`rec_05_causality.cast`, 13.5 min live of 13.5**; `analysis/causality.csv`, `causality_note.md`, `ringdown_precausal.npz`, `test_causality.py`; log 1815+ |

## Where the record is strong

- **The log is continuous.** 1,618 lines, ~50 headed entries, no phase missing, append-only with
  every correction appended rather than applied in place.
- **Every error is attributable.** 51 rows, each naming the phase, who erred, who caught it, how it
  was caught, and what changed. **20 were caught by someone other than the node that erred**, and
  three of those are retractions of my own earlier attributions (E046, E047, E050).
- **Every disagreement names the test that settled it.** `comparison.csv` carries a `what_was_tried`
  column pointing at a specific script, and a `who_was_right` column that includes
  "neither — orchestrator's spec was at fault" twice.
- **Three nodes wrote their own accounts**, independent of the orchestrator's: `VERIFIER_LOG.md`
  (30.8 kB), two `method_note.md`, and a session log in which the verifier explains a blocker in its
  own words rather than inventing a result.

## Where it is thin, stated plainly

- **129 minutes have no video**, from the end of the dry run to the graph dispatch. That window holds
  **24 of the 51 ledger rows** and three of the seven gates, including the refutation of the brief's
  central premise. A reader of the log sees all of it; a viewer of the recordings sees none of it.
  Phases 9 and 10 are fully recorded, so the gap is now confined to the pilot's first two hours.
- **The log and the recordings cannot be aligned on the clock before 04:18**, only ordinally, because
  of E022. Two hard anchors are given in the correction entry.
- **`rec_04_damping` is only 3.5 live minutes of 24.9**, because a headless node prints nothing
  while it works. Its three markers and the dispatch are what matter; the rest is a waiting terminal.
  I first wrote "all 25 minutes live" into the demo notes without measuring it — the same mistake as
  E044, two phases after logging E044.
- **`rec_02_critic` is 97% dead air** — 6.8 live minutes inside a 224-minute file, because the
  recorder stayed open across the usage pause.
- **The nodes run headless or as subagents**, so what the camera shows during their work is progress
  frames and token counts, not the node's reasoning. The reasoning is in their own logs, which is a
  better record but not a visual one.
