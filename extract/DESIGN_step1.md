# Step 1 extraction design — run RUNA, 2.5-9.5 Hz slice

Orchestrator, 2026-10-31 03:50 UTC. **Stop point 1: this design awaits Vivek's approval.**
Nothing has been extracted. No Slurm job has been submitted. Approval of this design is not
approval of the job — that is stop point 2, with the script and cost shown.

Supersedes the brief's Step 1 (which named tower 19 at 1 kHz for "a window holding at least 200
impulses"). The data are stepped-sine sweeps, not impulses; see AGENT_GRAPH_LOG.md, error E004.

## 1. What is extracted

| | |
| --- | --- |
| Excitation run | **RUNA**, shaker on MSP-X, 100 mV pp |
| Time window | **t = [3990, 21760] s** from run start (17,770 s = 4.93 h) |
| Drive frequencies | **71 steps, 2.52-9.52 Hz**, nominal 0.1 Hz increments, 250 s dwell each |
| Drive reference | **ch 1111 = shaker force**; ch 1112 = shaker accelerometer |
| Bolometers | **all 52 of tower 19, ch 937-988** |
| Aux / witness | **26 channels** (1018-1020, 1101-1123) — already on disk for the whole run |
| Sample rate | 1 kHz, as written by the DAQ; no decimation at this stage |

The window was **measured, not assumed**. The step map comes from ch 1111 of the already-extracted
witness data: 25 s blocks, Hann-windowed FFT (0.04 Hz bins), peak frequency and AC RMS per block,
boundaries where the peak moves by more than 0.05 Hz, then a cut at force RMS >= 10 mV to drop
shaker-off segments. That yields 161 shaker-on steps, strictly monotonic 1.00 -> 20.00 Hz, median
dwell 250 s. The 2.52-9.52 Hz subset spans t = [4000, 21750] s; 10 s of margin is added each side.

An arithmetic prediction of the same window (`f = 1.0 + 0.1k` at `t = 250 + 250k`) gave
[4000, 21500] — **wrong by 250 s**, because the sweep contains a **225 s shaker dropout at
t = 1275-1500 s** (force RMS 5.5 mV between the 1.32 Hz and 1.52 Hz steps) which shifts every later
step. The measured map is the authority. The dropout is outside the chosen band.

Force RMS across the 71 steps in band: **361-1520 mV, median 691** — a strong, well-measured drive.

## 2. Why this band

- It brackets both resonance regions the collaboration already hunted with fine short sweeps:
  **3.35-3.55 Hz** (runs 306468/469/470, 306486, 306492, 306503) and **8.0-9.0 Hz** (306477, 306485).
  Those runs are independent evidence of what a correct analysis should find, which the critic can
  use without seeing either agent's output.
- At 0.1 Hz spacing and 250 s dwell, damping ratios are recoverable by half-power bandwidth. The
  already-extracted run 306428 has 1 Hz spacing, which cannot resolve damping at all.
- It keeps the extraction at 3.44 GiB instead of 9.45 GiB for the full 1-20 Hz sweep, which is what
  makes the deadline survivable.
- **Pulse-tube harmonics fall inside it**: multiples of 1.4 Hz give 2.8, 4.2, 5.6, 7.0, 8.4 Hz. This
  is a feature, not a problem — the critic's PT check has something to bite on. Independent support
  already exists: in the three shaker-off segments of RUNA the dominant peaks are at **4.20 Hz and
  5.56 Hz**, i.e. 3x and 4x 1.4 Hz, measured. The two expected structural modes sit between PT lines.

## 3. Quiet (noise) reference

Primary, **in-run**, so the cryostat state and channel map are identical:

| segment | duration | ch1111 force RMS |
| --- | --- | --- |
| t = [0, 250] s | 250 s | 3.9 mV |
| t = [1275, 1500] s | 225 s | 5.5 mV |
| t = [48025, 48800] s | 775 s | 3.8 mV |
| **total** | **1250 s = 20.8 min** | |

That is short of the brief's 30 minutes. Two ways to close the gap, for Vivek to pick:

- **(a) retrieve run RUNB** — "short pedastal / No Impulse", same sb540 configuration as RUNA.
  The proper same-config quiet reference, and the honest choice. Costs one more retrieval.
- **(b) use run 306431** — 8066 s (2 h 14 min) shaker off, stinger detached, and its tower-19
  bolometers are **already staged**. Free, but it is sb522, about ten days earlier, with a different
  aux channel map. Fine for a bolometer noise floor, weaker as an aux reference.

Recommendation: extract the three in-run segments regardless (they are inside the run we are already
reading), use 306431 as the cross-check, and add RUNB only if its retrieval is cheap.

## 4. Route to the bolometers

The witness channels need no work: they are already on disk as `.bin` for the whole run and will be
sliced in software with `extract/read_vcts.py`. Only the 52 bolometers must be produced.

**Route A (recommended) — build the current `vibes` writer.**
`~/WriteContinuousDataToBinary.cpp` cannot compile against the `$VIBES` checkout: that checkout is
at master of 2025-08-02 and lacks `src/VibesUtil.hh`, which the writer includes. Verified by bare
clones of both remotes:

- `<INTERNAL_GITLAB_REMOTE>`, branch **`main`**, HEAD `6ca017a` (2026-10-21) — the
  canonical copy since the move to INFN GitLab. Contains `src/VibesUtil.hh` **and**
  `src/WriteContinuousDataToBinary.cpp`, and that writer is **byte-identical** to the copy in
  Vivek's home directory.
- `<INTERNAL_MIRROR_REMOTE>`, branch `master`, HEAD `a8e65c8` (2026-05-07) — older
  mirror; same two files, `VibesUtil.hh` byte-identical to GitLab's.

Both remotes answer over SSH from Perlmutter with no credential prompt.

Plan: clone GitLab `main` into a **new** directory (not over `$VIBES`, which holds an uncommitted
modification to `src/GetAllTriggersByRun.cpp` and an `output/` tree), point `VIBES` at it for the
extraction only, `source $CUORE_INSTALL/setup.sh`, `make`, then

```
WriteContinuousDataToBinary -r RUNA -c 937...988 -t 3990 -T 21760
```

which writes `$VIBES/output/runRUNA/timestreams/runRUNA_ch09NN_t3990_T21760.bin`.
**This route needs the CUORE DB**: the writer resolves RDCF paths through
`QRunDataHandle` and `QBookkeepingContinuousHandle`. Untested from Perlmutter — a reachability check
is the first thing to run, and it is a read-only DB query, not a job.

**Route B (fallback) — read the staged QRDCF directly with a ROOT macro.**
No DB, no build. Proven on run 306428: the partials hold one `TTree` named `qtree` with 206
branches `Channel0781.` … `Channel0988.` plus `Channel1506.`, each carrying `fSize` (Int_t) and
`fData[fSize]` (Int_t), about 10,000 samples (10 s) per entry. Reading 52 of 206 branches touches
roughly a quarter of the file bytes.
**This route needs run RUNA's C-group partials staged to pscratch**, as `run306428_ch975_C6` and
`run306431_ch975_C6` already are. They are not staged today. It also bypasses DIANA's run time base,
so entry contiguity must be checked explicitly rather than trusted.

Route A is preferred because it reuses the same code path that produced every existing `.bin`, which
keeps the witness and bolometer streams on one convention. Route B is the insurance policy.

## 5. Outputs

Written under the project, never into the CUORE areas:

```
data/bolo/ch0937.npy … ch0988.npy      float32, (17_770_000,)   52 files, 3.44 GiB
data/aux/ch1018.npy  … ch1123.npy      float32, (17_770_000,)   26 files, 1.72 GiB
data/quiet/<segment>/ch*.npy           float32, the three in-run segments
data/meta.json                         see below
data/steps.csv                         step index, f_measured [Hz], t0, t1, force RMS  (71 rows)
results/fig_sanity.png                 10 s of one accelerometer and one bolometer at a step edge
```

`data/meta.json`: run, slice `[3990, 21760]`, sample rate, the full channel list with the sb540
device names, units, the ADC->mV factor and where it came from, the measured step map, the known bad
intervals, the PT harmonic frequencies, the reader's provenance (git SHA of the vibes clone), and
every assumption below. `data/` is gitignored; nothing from it is committed.

Total about **5.2 GiB**, against the brief's 1 GB/hour estimate for 71 channels — consistent
(78 channels x 4.93 h).

## 6. Sanity checks, all logged

1. 52 bolometer files and 26 aux files present; no channel missing.
2. No all-zero and no constant channel; report per-channel mean, AC RMS, min, max, distinct-value count.
3. Sample count identical across all 78 channels and equal to `(21760 - 3990) x 1000`.
4. Header run, channel and rate agree with each filename (as already verified for all 57 existing files).
5. The step map recovered from the extracted ch 1111 reproduces `data/steps.csv` from the pre-slice map.
6. A plot of 10 s spanning one frequency-step boundary, one accelerometer and one bolometer.
7. **ch 975 adjudication (Vivek chose "let the data decide")**: compare ch 975's noise spectrum and
   band-limited RMS in the quiet segments against the other 51 tower-19 channels, and flag it only if
   it is an outlier. This settles error E007 empirically rather than by assertion.

## 7. Assumptions, stated as assumptions

- **ADC -> mV = 8.0108642578125e-02 mV/count**, taken from `$VIBES/src/WriteTimestreamsFromDAQ.cpp`.
  Confirmed for aux channels only by provenance, **not verified for bolometer channels**. If the
  bolometer gain differs, the `channel_gain.csv` numbers scale but the mode frequencies and damping
  ratios do not. Needs Vivek, or a calibration source.
- The nominal 0.1 Hz step spacing is taken from the spreadsheet; the extraction relies only on the
  measured map, so a nominal error cannot propagate.
- No UTC start time exists for this run (the `RunStartTime` sheet is empty for it), so all times are
  **seconds from run start**. The brief's `data/meta.json` asks for a UTC start; it will record
  "unavailable" with the reason rather than a guess.
- The sb540 channel map from the `Diagnostic Devs` sheet is assumed to apply to RUNA. The map
  changes between service breaks, and RUNA is the first run of sb540 in the sheet, so this is worth
  one confirmation from Vivek.

## 8. What this design gives up

- **No linearity or quadratic-thermal-path check.** The drive is constant at each frequency (verified
  on 306428: 0.1-0.2% over 13 repeats), so amplitude is never varied at fixed frequency within a run.
  That check needs run **306473**, which steps 100/200/400/800 mV pp within one run, or the pair
  306439 (50 mV) / 306440 (100 mV). None has bolometer data. The critic's amplitude-scaling test is
  therefore marked **not applicable** rather than passed or failed.
- **No coverage outside 2.52-9.52 Hz.** Modes below 2.5 Hz or above 9.5 Hz will not be seen. The
  brief asks for 0.1-50 Hz; the honest statement is that this pilot measures 2.5-9.5 Hz.
- **One shaker axis.** RUNA is MSP-X only. Runs 306475 (MSP-Z), 306483 (MSP-Y), 306490 and 306501
  (Y-beam) would give the other axes and all have witness data already extracted, but each needs its
  own bolometer retrieval.
