# Task: agent-graph pilot on CUORE shaker impulse data

Brief for Claude Code on a cluster with CUORE data and libraries (NERSC Perlmutter or Pitt CRC).
Owner: Vivek Sharma. Written 2026-10-30. **Hard deadline: results by 2026-10-31 midday ET** (fellowship
application due that day). Budget: about 5 hours of work. Cut scope rather than run late.

## Purpose

The fellowship proposal (page 3) claims that the analysis will be run as a *graph of agents*: an
analysis agent, an independent verifier that never sees the analysis, and a physics critic, with Vivek
approving gated steps. This pilot tests that claim on one real shaker run.

**The process is the primary deliverable; the physics result is secondary.** The fellowship asks
above all how frontier AI is used in a scientific workflow: what worked, what failed, and how results
were verified. So every step must be instrumented so that, afterwards, it can be shown concretely how
the graph was set up, what each agent did, what it got wrong, which node or human caught it, and what
it cost in time. A clean physics result with an unrecorded process is worth less here than a modest
result with a complete, honest record. Outputs, in order of priority:

1. a process report: how the graph was built and run, every error and disagreement, who caught it,
   and what changed as a result (see "Process instrumentation" and Step 4);
2. a recorded session that shows the graph working and serves as the application's demo;
3. one figure and a few numbers from the physics.

The science question for the pilot: **from raw shaker data, can the impulse response of the tower 19
bolometers be measured, and can its dominant modes be identified and independently verified?**
This is a feasibility pilot, not the final analysis. Do not train neural networks (except in the
optional Step 6).

## Process instrumentation (applies to every step)

Record in `AGENT_GRAPH_LOG.md`, as the work happens, not reconstructed afterwards:

- **Graph events:** for each node run, the start and end time, the prompt or task text it was given
  (exactly), the files it read and wrote, and its final claims with numbers.
- **Human gates:** each point where Vivek was asked to approve, what was asked, his decision, and how
  long the work waited.
- **Human interventions:** every time Vivek corrected, redirected or overrode an agent, and why.
- **Errors and disagreements:** one row each in `results/errors.csv` with the columns
  `id, time, step, node_that_erred, description, category, caught_by, how_caught, resolution, cost_min`.
  `caught_by` is analyst, verifier, critic, orchestrator, Vivek, a test, or not caught. Categories:
  code bug, wrong method or convention, fabricated or unsupported claim (a number, citation or file
  that does not exist or does not support the claim), data handling (units, sampling, alignment,
  leakage), physics error, and tooling or environment.
- **Prompt changes:** whenever an agent definition or SPEC.md is revised mid-run, the old text, the
  new text and the reason.
- **Cost:** wall-clock time per node and in total; token or API usage if available; GPU-hours.
- **Separation of the verifier:** how independence was enforced (separate session and permission rule,
  or instruction only), and any breach.

Errors are not to be minimized or tidied away. An error caught by the verifier or the critic is
evidence that the graph works; an error that only Vivek caught, or that nobody caught until later,
is the most valuable finding of all and must be reported prominently.

## Working rules

1. **Ask Vivek before every Slurm job**, showing the script, resources and expected cost.
2. **Describe each design before building it** and wait for approval.
3. **CUORE data are read-only.** Write only inside the project directory. Never commit data.
4. **Log everything** in `AGENT_GRAPH_LOG.md`: timestamp, node, inputs, outputs, numbers, and every
   disagreement with its resolution. Never delete entries; append corrections.
5. **The verifier must not see the analysis.** It works in its own directory, from the spec below and
   the extracted data only. If it reads analysis files by mistake, log it and redo that check.
6. **Scope claims.** Report what was measured, on which run and channels. Mark estimates as estimates.
7. When something is unknown (run number, channel map, reader library), **stop and ask Vivek.**

## Questions for Vivek before starting (step 0 stop point)

- Shaker run number(s), date, and the time window of the impulses.
- Is there a shaker drive or trigger channel, or must impulse times be found from the accelerometers?
- Which library reads the raw data? Candidates already on the cluster: the reader used by WitnessDenoise
  and CUORE_SHRED, and `RootReader/read_root_output_config.yaml` (used for
  `<SCRATCH>/EarthquakeData`). Which CUORE environment/module must be loaded?
- Channel map for the 19 aux channels (1101-1119): which are the accelerometers, which the seismometer
  axes, which microphones.
- Do the impulse amplitudes vary within the run? (Needed for the linearity / quadratic-path check.)

## Project layout

```
CUORE_ImpulsePilot/
  AGENT_GRAPH_LOG.md        # the shared log (append-only)
  SPEC.md                   # the task spec given to analyst and verifier (identical text)
  extract/                  # extraction code (orchestrator)
  data/                     # extracted arrays (not committed)
  analysis/                 # analyst agent works only here
  verify/                   # verifier agent works only here
  critic/                   # critic agent writes its report here
  results/                  # reconciled outputs, figure, summary
  .claude/agents/           # agent definitions (below)
  tools/rec.sh, tools/pane_rec.py   # self-recording (Step 5)
  recordings/               # segment recordings (not committed until checked)
```

## Step 1. Extract one run (orchestrator; design approval, then ask before any job)

- Extract tower 19 (channels 937-988, 52 bolometers) and all 19 aux channels at 1 kHz for a window
  holding at least 200 impulses (or the whole run if shorter). Include the trigger channel if it exists.
- Also extract the same channels for 30 minutes of quiet data from the same run, or the nearest
  run, before the shaker starts. This is the noise reference.
- Save as float32 `.npy` per channel plus `data/meta.json` (run, UTC start, sample rate, channel list,
  units, any bad intervals). Estimate size first: 71 channels x 1 kHz x 4 B is about 1 GB per hour.
- Sanity checks to log: channel count, no all-zero channels, sample-count agreement across channels,
  a plot of 10 s of one accelerometer and one bolometer around an impulse.

## Step 2. Write SPEC.md (orchestrator; show Vivek before running agents)

The same spec goes to the analyst and to the verifier. It defines **what** to produce, not **how**:

- `impulses.csv`: sample index and amplitude of every detected impulse.
- `responses.npz`: impulse-averaged response of each of the 71 channels, from 2 s before to 20 s after
  the impulse, with the standard error of the mean.
- `modes.csv`: the dominant structural modes seen in the bolometers, 0.1-50 Hz: frequency (Hz), damping
  ratio, which channels show it, uncertainty.
- `channel_gain.csv`: for each bolometer, the peak-to-peak averaged response and its signal-to-noise
  ratio against the quiet reference.
- A one-paragraph method note and any assumptions.

## Step 3. Run the graph

Run order: analyst and verifier in parallel (both started from SPEC.md), then critic, then reconcile.

**Analyst** (`analysis/`), suggested methods, free to change with a logged reason:
impulse detection by threshold on the band-passed accelerometer; coherent averaging; H1 frequency
response function estimates with an accelerometer as reference; modes by the eigensystem realization
algorithm (Juang & Pappa 1985) with a stabilization diagram.

**Verifier** (`verify/`), must use *different* methods and must not read `analysis/`:
impulse detection by matched filter / cross-correlation with a template impulse; averaging aligned on
its own detections; modes by a frequency-domain method (peak picking with half-power bandwidth, or a
least-squares rational-fraction fit). Ideally run it as a separate headless session started inside
`verify/`, with a permission rule denying reads of `../analysis/**` (check the exact rule syntax with
the Claude Code permissions docs first). If that is not practical, use the subagent below and log
that the separation was by instruction only.

**Physics critic** (`critic/`), reads both outputs and checks, each pass/fail with numbers:
- causality: no averaged response before the impulse;
- damping positive and plausible for each mode;
- modes that coincide with pulse-tube harmonics (multiples of 1.4 Hz, within resolution) flagged as
  possible PT lines rather than structural modes;
- the same mode seen consistently across bolometers, and across the two methods (frequency within
  combined uncertainty);
- if amplitudes vary: linear scaling of the accelerometer-to-wiring response, and whether the slow
  bolometer response grows faster than linearly (a first hint of the quadratic thermal path);
- averaged response well above the quiet-data noise floor.

**Reconcile** (orchestrator): build `results/comparison.csv` (analyst vs verifier, per quantity), and
for every disagreement record in the log what was tried to resolve it and who turned out right
(analyst, verifier, both partly, or unresolved). Ask Vivek to adjudicate anything unresolved.

**Optional, only if time remains:** run the same task as a single agent from SPEC.md, with no
verifier or critic, and record which of the errors found by the graph it also made.

## Step 4. Outputs to bring back for the proposal (copy these off the cluster)

1. **`results/PROCESS_REPORT.md` (the main output)**, about one page:
   - the graph as built: nodes, what each was given, the order, the human gates, and how the
     verifier's independence was enforced (a small text diagram is enough);
   - a table of every error and disagreement from `results/errors.csv`, grouped by category and by who
     caught it, with counts;
   - the three most instructive episodes, a few sentences each: what went wrong, how it surfaced,
     what was changed;
   - human interventions: how many, and what kind;
   - what did not work about the graph itself (handoffs that failed, roles that overlapped, checks
     that added nothing, places where a single agent would have been as good);
   - cost: wall-clock time per node and in total, waiting time at human gates, tokens or GPU-hours;
   - two or three lessons that would change how the full project is run.
2. `results/SUMMARY.md`, at most 150 words, the physics in plain numbers:
   run and window; impulses detected (analyst / verifier); how many of 52 bolometers show a response
   above noise; dominant modes found and how many agree between methods; critic checks passed/failed.
3. `results/fig_pilot.pdf`, one figure, about 6.5 x 2.4 inches, two panels:
   (a) the graph's error record: errors caught, by category, stacked by which node or human caught
   them; (b) mode frequencies from analyst vs verifier, with the PT harmonics marked. If space only
   allows one panel in the proposal, panel (a) takes priority.
4. `results/errors.csv`, `results/comparison.csv` and `AGENT_GRAPH_LOG.md`.
5. The segment recordings `recordings/rec_*.cast` and `DEMO_NOTES.md` (see Step 5).

Do not include raw data or CUORE-internal file paths in these outputs.

## Step 5. Recording the demo (in segments, at checkpoints)

The demo is recorded in short segments, one per phase of the graph, instead of one continuous
recording. Each segment is a separate terminal recording, started by Vivek at a checkpoint. Setup,
debugging and anything else between phases happens off camera. This keeps each file small, lowers
the chance of recording something sensitive, and makes the edit simpler.

**Why segments follow phases, not events.** The interesting moments (a critic flag, a disagreement)
cannot be predicted, so recording only once they appear would miss them. The phases are fixed in
advance, and a recording can only be stopped safely between phases: leaving Claude Code while agents
are running would stop them. So each phase is recorded in full, and long waits are removed in the
edit.

**Segments** (written to `recordings/`).

| File | Phase | Starts | Ends |
| --- | --- | --- | --- |
| `rec_01_graph.cast` | analyst and verifier dispatched from SPEC.md and run to completion | dispatch | both report done |
| `rec_02_critic.cast` | physics critic run | critic start | critic report written |
| `rec_03_reconcile.cast` | reconciliation of disagreements, human gates | reconcile start | results written |
| `rec_04_shred.cast` | optional Step 6 | split committed | SHRED_PILOT.md written |
| `rec_0Nb_<name>.cast` | ad hoc: an unexpected episode worth showing (see below) | Vivek decides | episode resolved |

**Checkpoint procedure: Claude Code starts and stops the recording itself.**
Claude Code cannot wrap its own screen in asciinema, but it can record the tmux pane it runs in,
using `tools/rec.sh` (provided with this brief, together with `tools/pane_rec.py`). The script uses
`tmux pipe-pane` to copy everything the pane displays into an asciinema-format file, starting with a
snapshot of what is already on screen.

Setup, once, before Step 3:
1. Start tmux and run Claude Code inside it: `tmux new -s pilot`, then `claude`. Size the window to
   about 120 x 34 characters and do not resize it during a segment.
2. Allow the script without a prompt each time, by adding `"Bash(./tools/rec.sh:*)"` to the
   `permissions.allow` list in `.claude/settings.local.json` (check the rule syntax in the Claude Code
   permissions docs).
3. **Dry run (one minute):** ask Claude Code to run `./tools/rec.sh start rec_00_test`, print a few
   lines, then `./tools/rec.sh stop`. Render `recordings/rec_00_test.cast` (for example with `agg` or
   `asciinema play`) and check that Claude Code's interface plays back cleanly. If it does not, use
   the manual fallback below.

During the run:
1. At each phase boundary the orchestrator prints `=== RECORDING CHECKPOINT: rec_0N_<name> ===`, runs
   `./tools/rec.sh start rec_0N_<name>`, prints the phase marker, and runs the phase. At the end of the
   phase it runs `./tools/rec.sh stop`. It runs `./tools/rec.sh status` if unsure whether a recording
   is open.
2. Before starting a segment, the orchestrator states in one line what is about to be recorded, so
   Vivek can say no (for example if sensitive output is expected). Starting a recording is not one of
   the gated steps; Vivek can stop one at any time by asking.
3. Off-camera work (setup, debugging) happens with no recording open. If the earlier screen content
   should not appear in the first frame, start with `REC_CLEAN=1 ./tools/rec.sh start ...`.
4. **Ad hoc segments.** If an episode worth showing is about to be investigated, the orchestrator may
   open a `rec_0Nb_<name>` segment, announcing it as above.
5. If something important happens off camera, it stays in the log. In the edit it is shown as a
   caption card quoting the log entry, not reconstructed.

Manual fallback (if the dry run fails): at each checkpoint the orchestrator stops and waits; Vivek
exits Claude Code (`/exit`) and resumes the conversation inside a new recording,
`asciinema rec --idle-time-limit 2 -c "claude --continue" rec_0N_<name>.cast`, then types `go`.

**On screen.**
- Inside each phase, print a one-line marker at the key moments so the video can be cut by searching
  the recording for text: `=== GRAPH: analyst + verifier dispatched ===`, `=== VERIFIER START ===`,
  `=== CRITIC ===`, `=== RECONCILE: <short description> ===`,
  `=== HUMAN GATE: <what is being approved> ===`, and `=== DONE ===`. Keep them short and exact.
- The recordings together should show: the analyst and verifier starting from the same spec; the
  verifier working without access to the analysis; the critic flagging something; a disagreement
  being resolved; and Vivek approving or overriding at a gate.
- Set `export PS1='$ '` in the shell before starting tmux, so the hostname does not appear.
- A screen recording (OBS) is optional; if used, start and stop it at the same checkpoints.

**Notes and checks.**
- Write `results/DEMO_NOTES.md`: for each segment, one line on what it shows and the marker lines
  inside it.
- Keep the Claude Code transcript as well (it is saved under `~/.claude/projects/`).
- Before sharing, check each segment for tokens, passwords, internal hostnames or unpublished numbers
  Vivek has not cleared. A segment that shows something sensitive is cut in the edit, not shared.

## Step 6 (optional). SHRED exploration, only if time remains

Start only after stop point 4 and only with Vivek's go-ahead. Time-box it to about 2 hours, and stop
by 2026-10-31 10:00 ET regardless of progress. Steps 1-5 must not be put at risk. Whatever state it
reaches is reported honestly: a negative or incomplete result is still useful for the proposal.

**Question.** Can the impulse response of the tower 19 bolometers be reconstructed from the 19 aux
channels alone (the sparse-sensor problem SHRED was built for), and does a state-space (S4D) encoder
give eigenvalues that match the modes found in Step 3?

**Design (describe to Vivek before building).**
- Data: the impulse windows from Step 1, downsampled to 200 Hz as in CUORE_SHRED. Input: the 19 aux
  channels. Target: the 52 tower 19 bolometers. Window: 2 s before to 20 s after each impulse.
- Split **by impulse**, about 70/15/15 train/validation/test, in contiguous blocks of time, with a gap
  of at least one window between blocks so that no samples are shared. Write the test-impulse indices
  to `results/shred_split.json` and commit it **before** any model is trained.
- Models, in this order (stop wherever time runs out):
  1. Linear baseline: multiple-input Wiener filter or ridge regression from aux to each bolometer.
  2. SHRED with an S4D encoder: the S4D layer from WitnessDenoise as the encoder, followed by the
     SHRED shallow decoder. Take the decoder from the CUORE_SHRED code, or from PySHRED (Ye et al.
     2025) if it installs cleanly in the environment, otherwise write a minimal one.
  Keep the models small (the CUORE_SHRED sizes, about 70-300k parameters) and use one seed each; say so.
- Metrics on the test impulses: residual power ratio (residual over original) in 0.1-1 Hz and 1-50 Hz,
  median over the 52 bolometers and for the three bolometers in the Step 4 figure.
- Interpretability check for model 2: convert the trained S4D eigenvalues to frequency and damping
  ratio (continuous-time poles: f = |Im(lambda)| / 2pi, zeta = -Re(lambda) / |lambda|), keep the
  lightly damped ones, and compare them with `results/comparison.csv` from Step 3.

**Graph roles.** The analyst agent builds and trains the models. Before any test number is reported,
the physics critic checks the split for leakage (shared samples, overlapping windows, test impulses
used for early stopping) and confirms the split file was committed before training. The verifier
recomputes the linear baseline's test metrics independently from the saved predictions.

**Compute.** Expect under 2 A100 GPU-hours in total. Ask Vivek before submitting the job.

**Outputs (add to the Step 4 hand-back).**
- `results/SHRED_PILOT.md`, at most 100 words: impulses in each split; test residual power ratios for
  each model in both bands; how many S4D eigenvalues fall within uncertainty of a Step 3 mode; what
  was not finished. Log errors from this step in `results/errors.csv` like any other, and add a
  short paragraph to PROCESS_REPORT.md on how the graph handled model training (in particular whether
  the critic's leakage check found anything).
- Optionally `results/fig_shred.pdf`: test-impulse reconstruction of one bolometer by both models,
  for the proposal only if page 3 has room.

**Caveats to state in SHRED_PILOT.md.** About 200 impulses from one run is far less than the data SHRED
is usually trained on, so these numbers are a feasibility check, not a benchmark. Impulse-window
reconstruction is not the same task as continuous noise prediction.

## Stop points (report to Vivek and wait)

1. After the step 0 questions are answered and the extraction design is ready.
2. Before the extraction job.
3. After SPEC.md is written.
4. After reconciliation, with PROCESS_REPORT.md, SUMMARY.md and the figure.
5. (Optional) Before starting Step 6, and before its training job.

## Agent definitions (create in `.claude/agents/`)

`.claude/agents/impulse-analyst.md`
```markdown
---
name: impulse-analyst
description: Analysis node. Produces the SPEC.md outputs from the extracted shaker data, working only in analysis/.
tools: Read, Write, Edit, Bash, Grep, Glob
---
You are the analysis agent in a verification graph. Read SPEC.md and data/meta.json. Work only in
analysis/. Produce exactly the files SPEC.md lists, with a method note. Write and run tests for impulse
detection and averaging. Log every number you report to ../AGENT_GRAPH_LOG.md under the heading
"analyst". Do not submit Slurm jobs; if one is needed, stop and say what it is.
```

`.claude/agents/independent-verifier.md`
```markdown
---
name: independent-verifier
description: Verification node. Reproduces the SPEC.md outputs with different methods, without reading analysis/.
tools: Read, Write, Edit, Bash, Grep, Glob
---
You are the independent verifier in a verification graph. Read SPEC.md and data/meta.json only. Never
open, list or search analysis/ or critic/. Work only in verify/. Use methods different from threshold
detection and the eigensystem realization algorithm: matched-filter impulse detection and a
frequency-domain modal fit. Produce the files SPEC.md lists and a method note. Log every number to
../AGENT_GRAPH_LOG.md under "verifier". If you accidentally see analysis output, say so in the log.
```

`.claude/agents/physics-critic.md`
```markdown
---
name: physics-critic
description: Critic node. Checks analyst and verifier outputs against physical constraints and against each other.
tools: Read, Write, Bash, Grep, Glob
---
You are the physics critic in a verification graph. Read analysis/ and verify/ outputs. Do not fix
them. Check causality, positive damping, pulse-tube harmonics (multiples of 1.4 Hz) mistaken for
modes, cross-channel and cross-method consistency, amplitude scaling, and signal above the quiet-data
noise floor. Write critic/REPORT.md with a pass/fail table and numbers, and log a summary to
../AGENT_GRAPH_LOG.md under "critic".
```
