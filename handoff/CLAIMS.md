# What this pilot supports, and what it does not

For the fellowship proposal. Every number below traces to a file in this package; the provenance
column names it. **Read the "Do not claim" section before drafting.** Three claims that look
attractive are not supportable, and two of them were in my own earlier drafts before the graph
caught them.

Blanket scope, applying to every physics line: **one run (RUNA), one shaker axis (MSP-X), one
tower (19), 52 bolometers, 71 drive frequencies, no repeat of any frequency.** This is a feasibility
pilot. A number here constrains *this run*; it does not establish a property of the detector.

---

## 1. Process claims — these are the strong ones

Page 3 of the proposal claims the analysis runs as a graph of agents. These support that claim.

| Claim | Number | Provenance |
| --- | --- | --- |
| The analysis ran as a graph of four agent nodes plus human gates | orchestrator, analyst, blind verifier, physics critic; 7 human gates | `PROCESS_REPORT.md` §1, `TIMELINE.md` |
| Every error was logged with attribution | **53 entries**, each naming phase, who erred, who caught it, how, and what changed | `errors.csv` |
| The graph caught errors a single agent would not have | **21 of 53 caught by someone other than the node that erred** — analyst 6, verifier 5, critic 5, human 5 | `errors.csv`, `fig_pilot.pdf` panel (a) |
| Most errors were the supervisor's | **31 of 53 were the orchestrator's own.** The nodes erred 8 times between them | `errors.csv` |
| Verifier independence was enforced by construction, not instruction | headless session rooted in `verify/`, `analysis/` in no allowed directory; planted sentinel never appeared, verified after every run | `PROCESS_REPORT.md` §1 |
| A weaker model held in an enumerated verification role | critic on Sonnet, **55,818 tokens vs the analyst's 118,782**; every quantity matched an independently precomputed audit | `PROCESS_REPORT.md` §4 |
| Specification defects are findable and fixable mid-pilot | 2 of the critic's 8 disagreements were defects in the spec, not disputes between nodes; amended and re-run for 25 and 11 minutes | `PROCESS_REPORT.md` §3.5, §3.6 |

**The most honest anecdote (E053).** I explained the 5.45 Hz discontinuity as an instrumental gain
change, with a plausible mechanism and a clean number. It passed the critic, passed reconciliation,
and shipped. When Vivek asked whether the premise was actually true, it took ten minutes to show the
argument rested on a noise floor that is not stable — it jumps beyond 5 σ at 20 of 70 boundaries.
The conclusion is withdrawn; what survives is the weaker, method-independent statement that two
drive monitors disagree by ×1.6 and ×4.7. **No node caught this, because none was asked to audit a
mechanism the orchestrator proposed after the critic had run.** If the proposal claims the graph
catches errors, this is the honest counterweight: it catches the ones it is pointed at.

**The single best anecdote (E043).** Two nodes with genuinely different methods independently found a
mode at 7.43–7.46 Hz and agreed to 0.037 Hz — and the mode was still demoted, because both
referenced the same miscalibrated channel. *Agreement between nodes bounds method error, not
instrumental error.* That is a result about multi-agent verification, not just about a shaker.

**The second best (E024).** The verifier's first run had no write permission. It produced nothing,
exited 0, and **named the exact permissions it needed rather than inventing results.** A silent
zero-exit failure is the dangerous case.

**Third (E050).** The analyst was handed a boundary measurement by the orchestrator, measured it
itself anyway, found a 0.37 s disagreement, and reported it unresolved rather than adopting either
value. The orchestrator turned out to be wrong — 0.24 s of its number was a smoothing artefact.

---

## 2. Physics claims that are supportable

| Claim | Number | Provenance |
| --- | --- | --- |
| All tower-19 bolometers respond to the shaker above the quiet-data noise floor | **52 of 52**, median SNR 109 (analyst) / 76 (verifier) | `comparison.csv` |
| The dominant response is near 3.4 Hz | strongest on **42 of 52** channels (analyst), 46 (verifier) | `comparison.csv` |
| Eleven modes identified in 2.50–9.50 Hz | 3.02, 3.42, 3.96, 4.89, 5.35, 6.22, 7.92, 8.10, 8.17, 8.53, 8.79 Hz | `modes_reconciled.csv` |
| Two independently hunted resonance regions corroborated | 3.35–3.55 Hz and 8.0–9.0 Hz, from runs neither node saw | `PROCESS_REPORT.md` §3.1 |
| No mode is a pulse-tube harmonic | measured fundamental **1.39443 Hz**, not the 1.4 Hz assumed; nearest mode 0.163 Hz away | `modes_reconciled.csv` |
| Two independent methods agree on the transfer function | log median \|H\| correlation **0.998**, partly shared by construction since both reference ch1111 | `comparison.csv` |
| Two drive monitors disagree across two boundaries | ch1111 vs ch1112 tone ratios differ by **×1.58** at 5.45 Hz and **×4.7** at 7.45 Hz, so \|H\| there is reference-dependent | `comparison.csv`, `PROCESS_REPORT.md` §3.2 |
| Damping measured on seven modes, cross-checked on five | all five within **1.8 σ** between ERA and ring-down | `PROCESS_REPORT.md` §3.5 |

**Three modes were found only by the blind verifier** — 6.2184, 7.9209, 8.5297 Hz — and sit in the
*analyst's own* transfer functions on 44, 32 and 25 of 52 channels. The analyst's ERA missed them.
This is the cleanest demonstration in the pilot that the second node earned its cost.

---

## 3. Results that are inconclusive, and must be presented that way

| | Status |
| --- | --- |
| **Cause of the two \|H\| discontinuities** | **Undetermined.** The monitors demonstrably disagree; instrument versus physics was claimed and then withdrawn (E053). |
| **Causality** | **Inconclusive per cell.** Median pre/post 0.049 against a null of 0.052 — the pre-boundary signal *is* the estimator's noise floor. No acausality detected above that floor; 68 of 70 boundaries pass by median over trusted channels, and on strong channels the median is 0.010. Say "no acausality was detected above the measurement floor", never "causality was verified". |
| **Damping on 4 of 11 modes** | Non-detections, reported with the field left empty. Not upper limits — no bound at all. |
| **5.31–5.35 Hz damping** | Analyst 0.0131 ± 0.0006; verifier non-detection. Uncontested, not confirmed. |
| **Linearity and the quadratic thermal path** | **Not applicable to this run** — each frequency occurs exactly once, so amplitude is never varied at fixed frequency. Needs run 306473 or the 306439/306440 pair. |
| **Absolute mV scale on bolometer channels** | An assumption. The ADC constant is confirmed by provenance for aux channels only. |
| **7.46 and 8.29 Hz** | Tentative, excluded from the headline eleven. |

---

## 4. Do not claim

- **Do not say the data are impulse-response measurements.** They are stepped-sine sweeps. The
  original brief's central premise was wrong and this was found in the first two hours (E004). The
  impulse response is inferred from a swept transfer function, not measured directly.
- **Do not use 1.4 Hz as the pulse-tube fundamental.** It is **1.39443 Hz**, measured; the 1.4 Hz
  figure is off by up to 33 mHz by the sixth harmonic, which matters for harmonic rejection (E028).
- **Do not quote a mode at 5.494 Hz.** Zero of 52 channels show a local \|H\| maximum there, in
  either node's data (E041). Say it is a reference-channel artefact — **do not say it is a gain
  change**: that stronger claim was made, tested when questioned, and withdrawn (E053).
- **Do not quote damping as an upper limit of `0.1/(2f₀)`.** That number appeared in the first pass
  and carries no information; it is the frequency grid restated. It has been superseded (E032).
- **Do not describe causality as passed or verified.** See above.
- **Do not present the two nodes as symmetric sandboxes.** The verifier is a separate OS process with
  filesystem isolation; the analyst is an in-process subagent with full project access. The
  independence requirement is one-directional and the asymmetry is real.
- **Do not quote any figure from `data/steps.csv` timing without the correction** — it is late by
  6.2–6.4 s.

---

## 5. If you have room for only one figure

`fig_pilot.pdf`, panel (a): the 52-entry error record by category, stacked by which node caught each
one. It is the process claim in one image, and the grey bar — the orchestrator catching its own
mistakes — being the largest is the honest part of it.

`fig_timeline.pdf` is the backup: the graph as a swimlane over measured clock time, with the human
gates marked and the 129 minutes of unrecorded work shaded rather than hidden.

---

## 6. If you have room for only one recording

`recordings/rec_04_damping.cast`, 1.2 minutes. The critic finds that a whole column of the pilot
carries no information; the cause traces to a defect in the orchestrator's own specification rather
than the node's work; the human approves an amendment; the node is re-run and returns measurements
on seven modes, four documented non-detections, and a null control nobody asked for.

Pair it with `rec_05_causality.cast` (13.5 min) if you can, which is the same loop returning an
**inconclusive** result and saying so.
