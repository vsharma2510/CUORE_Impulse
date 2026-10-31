# Demo notes — recorded session

Three segments, recorded with `tools/rec.sh` (tmux `pipe-pane` into asciinema v2) at a 120×33 pane.
Replay with `asciinema play recordings/<name>.cast`, or `asciinema play -s 4 -i 2` to speed up and
cap idle gaps. `python3 -I tools/cast_render.py <cast> --grep STR` replays through a VT100 screen
model and reports what actually **rendered**, which is the only reliable way to check a TUI recording
(see "Why a screen model" below).

## The segments

| file | pane | nominal | live content | shows |
| --- | --- | --- | --- | --- |
| `rec_01_graph.cast` | 120×33 | 41 min | ~26 min | the whole parallel phase: dispatch, isolation verified, the ledger growing, a human gate on model cost |
| `rec_02_critic.cast` | 120×33 | 224 min | ~6 min | the critic flagging a failure and the audit of it |
| `rec_03_reconcile.cast` | 120×33 | 72 min | ~14 min | a disagreement being resolved, and Vivek at a gate |
| `rec_04_damping.cast` | 120×33 | 25 min | ~3.5 min | the loop closing: a spec defect the critic exposed, amended and re-run |
| `rec_05_causality.cast` | 120×33 | 14 min | ~13 min | a node refusing the orchestrator's number, and turning out to be right |

`rec_00_test.cast` is the one-minute recorder dry run from Step 0; it is not part of the demo.

## The cut files

`recordings/cut/` holds the five segments already cut to the ranges below, produced by
`tools/cast_cut.py`. **49.2 minutes total, down from 376.** Play any of them with

    asciinema play recordings/cut/rec_04_damping.cast

Idle gaps inside a kept range are capped at 3 s, so no further `-i` is needed; `-s 2` speeds
playback if you want it shorter still.

| file | original | cut | what it is for |
| --- | --- | --- | --- |
| `rec_01_graph.cast` | 41.3 min | **15.4** | the graph dispatched and running, isolation confirmed, a gate |
| `rec_02_critic.cast` | 223.7 min | **5.5** | the critic flagging a failure, and the audit of it |
| `rec_03_reconcile.cast` | 72.4 min | **13.6** | a disagreement resolved, then Vivek at a gate |
| `rec_04_damping.cast` | 24.9 min | **1.2** | the loop closing: spec defect found, amended, re-run |
| `rec_05_causality.cast` | 13.5 min | **13.5** | an inconclusive result reported as inconclusive |

**Why a cut needs more than dropping events.** A cast is an output *stream*, not a sequence of
frames: what is on screen at 68:40 is the accumulated result of every byte written since 0:00. A
file that simply starts at 68:40 opens on a garbled screen, and Claude Code's TUI makes it worse by
redrawing with cursor moves rather than reprinting. So `cast_cut.py` replays every event from the
beginning through the VT100 model in `cast_render.py`, and opens each kept range after the first
with one synthetic paint event — erase, home, the reconstructed screen, cursor restored. The
reconstructed opening frame is monochrome, because the model ignores SGR; colour returns within a
second or two when the live events resume.

**Verified after cutting.** Every marker listed below was re-checked in the cut file and still
renders, and a splice frame was inspected in each. Both the rendered text and the raw bytes of all
five cut files were swept for `CUORE_DB_PWD`, bearer-token and JWT fragments and internal
hostnames: clean.

## Cut list

Timestamps are from `cast_render.py`, so each one is a frame where the text was verified on screen.

**Segment 1 — `rec_01_graph` (keep almost all of it; 25.5 of its 41 minutes are live).**

| at | what |
| --- | --- |
| 0:00 | dispatch command: both nodes named, with their directories and the spec each gets |
| 0:22 | `=== VERIFIER START ===` — the headless verifier launches, rooted in `verify/` |
| 0:41 | `impulse-analyst` begins; the two nodes now run in parallel |
| 0:59 | `=== GRAPH DISPATCHED ===` with the wall-clock stamp |
| 5:21 | verifier exits, `verify/` listed, and the **sentinel breach check returns nothing** |
| 6:40 | the analyst editing its own pipeline (`common.py`, `s01_steps.py`) — the node visibly working, not a spinner |
| 11:40 | the isolation result in full: the verifier volunteered that it read `verify/SPEC.md` because "the project-root copy is outside my allowed directories" — **the boundary confirmed from the inside** |
| 11:40 | the running ledger on screen at 26 entries, with `caught_by` already showing verifier 3 and Vivek 3 |
| 14:18 | node progress line: `impulse-analyst Rerunning s02_channels.py · 14m 18s · 103.4k tokens` — live cost accounting |
| 21:40 | E025/E028/E029 named as **one** root cause rather than three slips; ledger at 30 |
| 26:40 | **a human gate on screen**: Vivek raises usage, the critic is moved to Sonnet, and the prompt change is logged with old text, new text and reason |
| 35:00 | the verifier's own progress table, `v01` through `v04`, while it runs blind |

Trim only the two static stretches where the screen does not change: roughly **12:30–21:00** and
**36:00–41:00**. Everything else is live.

**Correction (logged as E044).** An earlier version of these notes said this segment held "~6 min"
of content and told the editor to cut everything after 6:00. That was written from where I had
placed the `===` markers rather than from what the cast actually rendered, and it would have
discarded the best material in the segment — the isolation confirmation, the live ledger and the
only human gate before stop point 4. Measured properly: 6,178 events, 25.5 minutes with no gap
longer than a minute. The lesson is the same one as E031: **check the screen, not your own notes
about the screen.**

This segment is where the isolation claim is demonstrated rather than asserted: the sentinel grep is
on screen, and so is the verifier explaining the boundary in its own words.

**Segment 2 — `rec_02_critic` (keep 0:00–6:00).**

| at | what |
| --- | --- |
| 0:01 | `=== CRITIC ===` |
| 0:17–5:20 | 722 rendered frames of `physics-critic` working on Sonnet |
| 5:22 | `=== CRITIC: 1 FAIL, 1 INCONCLUSIVE, 4 PASS, 1 N/A ===` |
| 5:25 | the audit line: every precomputed quantity matched |

Nominal length is 224 minutes because the recorder stayed open across a usage-limit pause. **Cut
everything after 6:00** — the remaining 3½ hours are dead air.

**Segment 3 — `rec_03_reconcile` (keep 0:00–10:30 and 68:40–72:30).**

| at | what |
| --- | --- |
| 0:01 | `=== RECONCILE ===` |
| 9:38 | `=== RESOLVED: verifier right on 6.22/7.92/8.53 Hz — present in the ANALYST's own H on 44/32/25 of 52 channels` |
| 9:41 | `=== RESOLVED: 5.45 Hz is a ch1111 GAIN CHANGE — off-tone noise ×1.836 tracks the tone ×1.729` |
| 9:44 | `=== E043: both nodes agreed on 7.46 Hz and both were wrong — shared reference channel, shared artefact` |
| 10:12 | the gate question appears on screen, with the three mode-list options |
| **68:45–69:15** | **Vivek at the gate**: the Step 6 question, the options being navigated, and both selections landing |
| 69:29 | `=== GATE 4: Vivek approves 11 modes, 7.46 Hz demoted. Step 6 CUT.` |
| 72:21 | closing state: `comparison.csv` 33 rows, ledger 43, figure written |

**Cut 10:30–68:40** — that is the gate open and waiting for a human, about 58 minutes. If one shot of
waiting is wanted, keep ten seconds of it: the graph genuinely stops at a human gate, and that is a
property of the design rather than a delay to hide.

These two moments — a disagreement being resolved on evidence, and a human overriding/approving at a
gate — are the two the brief asked for and the first two segments did not contain.

**Segment 4 — `rec_04_damping` (keep 0:00–0:30 and 24:30–25:00; only 3.5 of 24.9 minutes are live).**

The tightest segment, and the one that shows the graph as a loop rather than a pipeline.

| at | what |
| --- | --- |
| 0:02 | `=== DAMPING RE-RUN: SPEC 4.3 amended, both copies md5 20c731df4bfcceaa1dd0d9e98dc2d88b ===` |
| 0:02–24:40 | the verifier re-dispatched headless against the amended spec, working blind. **A headless node prints nothing while it works**, so this stretch is an idle terminal — cut it, or hold two seconds of it to make the point that the orchestrator is not watching |
| 24:43 | `=== DAMPING MEASURED on 7 of 11 modes; 4 honest non-detections; zeta column EMPTY where it failed` |
| 24:46 | `=== E032 CLOSED: 5 matched modes now cross-check, all within 1.8 sigma. Verifier built its own null control.` |

**Correction (E052).** An earlier version of this entry claimed all 25 minutes were live. Measured, it is 3.5. That is the same error as E044, made two phases after logging E044 — I asserted a property of a recording from expectation instead of from the file. The markers and the dispatch are what matter here, not the duration.

This is the segment to lead with if only one can be shown. The critic found that a whole column of
the pilot carried no information; the cause was traced to a defect in the orchestrator's own spec,
not the node's work; Vivek approved an amendment; the node was re-run and came back with a
measurement on seven modes, four documented non-detections, and a null control nobody had asked for.

**Segment 5 — `rec_05_causality` (keep all of it).**

| at | what |
| --- | --- |
| 0:02 | `=== CAUSALITY: SPEC 4.5 added, both copies md5 7946295bbdd8f8a5ef2800c41a501434 ===` — the checksum rule from E045 being applied |
| 0:29–13:15 | `impulse-analyst` running the causality test on stored pre-boundary samples |
| 13:21 | `=== CAUSALITY: no acausality above the floor; pre/null ratio 0.98. Not a clean per-cell pass.` |
| 13:23 | `=== E050: my r6c boundary was over-smoothed by 0.24 s. Analyst was right; my earlier verdict reverses.` |

Pair this with segment 4. Four shows the graph closing a gap successfully; five shows it returning
an **inconclusive** result and reporting it as such, and then a node refusing the orchestrator's
number and turning out to be right. Together they are the honest version of the claim on page 3.

## Why a screen model

`tmux pipe-pane` records the pane's output **stream**, and the TUI redraws by repositioning the
cursor and overwriting. Stripping escape sequences from that stream produces garbled text, so a plain
`grep` on the raw cast reports a marker missing when it rendered perfectly (logged as E031, where my
first diagnosis of a missing marker was itself wrong). `tools/cast_render.py` replays the stream
through a minimal VT100 screen — CUP, CUU/CUD/CUF/CUB, ED, EL, IL/DL, scroll-on-overflow — and
reports the lines that were ever fully rendered.

The second lesson (E033): the TUI truncates an echoed command at the pane width, so a marker placed
after a long command never appears. **One marker per short command**, then verify.

## Before sharing

- Every segment was rendered and searched for `CUORE_DB_PWD`, bearer-token fragments and internal
  hostnames before being described here. **Do not** display `~/.bashrc` or the vibes `setup.sh` on
  camera: both contain live credentials (logged as E008 by description only). DIANA is sourced off
  camera for this reason.
- `grep -ril SENTINEL-7Q4X verify/` returning nothing is on screen in segment 1 — note that the
  literal sentinel string does appear in the cast, because the check itself prints it. That is the
  check, not a breach.
- Delete the `recordings/.*.screen` scratch files before handing the directory over; they are the
  pane snapshots the recorder starts from, not part of any segment.
