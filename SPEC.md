# SPEC.md — measurement task, CUORE tower-19 shaker response

**This identical text is given to the analysis agent and to the independent verifier.** It defines
**what** to produce, not **how**. Where it does constrain method, that is because a specific
contaminant in this data makes the constraint necessary, and the reason is stated.

Draft 1, orchestrator, 2026-10-31. Awaiting Vivek's approval (stop point 3).

---

## 1. The question

From a stepped-sine shaker run, measure the vibration response of the 52 tower-19 bolometers between
2.5 and 9.5 Hz, identify the dominant structural modes, and quantify how well each bolometer sees
them. Two agents do this independently by different methods and the results are reconciled.

**This is a feasibility pilot, not the final analysis.** Scope every claim to the run and channels
actually used. Mark estimates as estimates. Do not train neural networks.

## 2. The data

Everything is already extracted and checked. **Do not re-extract, and do not read CUORE data
directly** — if you believe you need to, stop and say so.

```
data/meta.json                     every number below, machine-readable, plus all provenance
data/steps.csv                     the 71 frequency steps: index, f_measured, t0, t1, force RMS
data/pulser_times.npy              4882 pulser times in RUN coordinates (see 4.1)
data/arrays/<window>/bolo/ch09NN.npy    float32 mV, median removed (offset in meta.json)
data/arrays/<window>/aux/ch1NNN.npy     float32 mV, median removed
```

Windows (`<window>` above), all at **1 kHz**:

| window | run | t (run coords) | samples | what it is |
| --- | --- | --- | --- | --- |
| `excitation` | RUNA | 3990–21760 s | 17,770,000 | shaker on, 71 steps, **2.50–9.50 Hz** |
| `quiet1` | RUNA | 0–250 s | 250,000 | shaker off, in-run |
| `quiet2` | RUNA | 1275–1500 s | 225,000 | shaker off, in-run (a dropout mid-sweep) |
| `quiet3` | RUNA | 48025–48800 s | 775,000 | shaker off, in-run |
| `quietrun` | RUNB | 0–2456 s | 2,456,000 | dedicated pedestal run, 40.9 min, same sb540 config |

Channels: **bolometers 937–988** (all 52 of tower 19). **Aux**: 1018–1020 and 1101–1123 for run
RUNA; 1101–1123 for RUNB. The device map is in `meta.json` under `channel_map_sb540`.

**The drive reference is channel 1111 (shaker force).** Channel 1112 is the shaker accelerometer.

### 2.1 Three things about the data you must not get wrong

1. **The arrays start at t = 3990 s, not 0.** Pulser times and `steps.csv` are in *run* coordinates.
   Subtract 3990 s before indexing the `excitation` arrays. Write a test for this.
2. **There are no UTC timestamps.** The run-start time does not exist in any accessible record. All
   times are seconds from run start. Do not invent a UTC time.
3. **The mV scale is exact at the ADC, and undetermined only before it.** The factor is
   `8.0108642578125e-02 mV/count`, which is **exactly `21000 / 2**18`** (verified bit-for-bit) — the
   least-significant bit of a ±10.5 V, 18-bit digitiser. That is a property of the DAQ board, so it
   is the *same for every channel through it*, bolometer and aux alike. **The arrays are therefore in
   millivolts at the ADC input, exactly, and this is not an assumption.**

   What is *not* determined is the per-channel **front-end amplifier gain** needed to refer a signal
   back to the bolometer itself, and the thermistor calibration needed to go further to temperature
   or energy. Those live in the CUORE DB (`QDetChannel`) and are retrievable, but they are **not
   needed for anything in this spec**: mode frequencies, damping ratios, coherences and
   signal-to-noise ratios are all scale-free, and a transfer function referenced to channel 1111 is
   a ratio of two ADC-input voltages. So:

   - Report `channel_gain.csv` amplitudes in **mV at the ADC input** and say so in the header.
   - Do **not** claim volts at the bolometer, temperature or energy.
   - If you want absolute bolometer units, stop and say so rather than assuming a gain.

## 3. Deliverables

Write all of these into your own directory (`analysis/` or `verify/`). Numbers go to
`../AGENT_GRAPH_LOG.md` under your heading as you obtain them, not at the end.

### `impulses.csv`
Despite the name, kept for continuity with the brief: **one row per detected frequency step**, not
per impulse. This run contains no impulses (see 4.1). Columns:
`step_index, t_start_s, t_end_s, f_drive_hz, force_rms_mV, n_samples_used, method`.
You are expected to recover the steps yourself from channel 1111 rather than copying `steps.csv`;
disagreement with `steps.csv` is a finding, not an error.

### `responses.npz`
Per channel (all **78** bolometer-plus-aux channels: 52 + 26), the response at each drive frequency:
complex transfer function, its standard error, and the coherence against channel 1111. Also, for
each frequency step, the ring-down segment you used for damping (see 4.3), with its standard error.
**That segment must begin BEFORE the step boundary, not at it** — see 4.5, which is a requirement on
what you store, not only on what you report. State the window, taper and averaging convention in the
method note.

### `modes.csv`
Dominant structural modes in **2.50–9.50 Hz**. Columns:
`f0_hz, f0_err_hz, zeta, zeta_err, zeta_is_upper_limit, n_channels_showing, channels, method, pt_harmonic_flag`.

- `f0_err_hz` is at best **±0.05 Hz** (half the 0.1 Hz step spacing). Do not quote better.
- `zeta_is_upper_limit` is a required boolean. See 4.3 — for narrow modes an upper limit is the
  correct answer and a point value would be fabricated.
- `pt_harmonic_flag` is true if `f0` falls within `f0_err` of a multiple of **1.39443 Hz** — the
  measured pulse-tube fundamental, *not* the 1.4 Hz the brief states (see `meta.json`; the difference
  reaches 33 mHz by the 6th harmonic).

### `channel_gain.csv`
Per bolometer: `channel, peak_response, peak_f_hz, inband_noise_rms_mV, snr, median_coherence`.
Noise from the quiet windows, in the same band and with the same estimator as the response.

### `method_note.md`
At most 400 words: what you did, every deviation from the suggestions below with its reason, and
every assumption. Be explicit about what you could not determine.

## 4. Constraints that come from the data, not from preference

### 4.1 There is a deterministic 0.1 Hz pulser and it will fool you

Every bolometer carries a heater pulser at **exactly 10.0000 s spacing**, 4882 pulses, synchronous
across channels, first at t = 5.002 s. **1777 of them are inside the excitation window.** Times are
in `data/pulser_times.npy`, run coordinates.

Two consequences:

- Its spectrum is a comb on every multiple of 0.1 Hz, and **every drive frequency here is such a
  multiple** — measured, not assumed: the grid is `f_k = 2.5 + 0.1k` Hz with a maximum deviation of
  **0.17 mHz** over all 71 steps, so `f mod 0.1 < 0.0002 Hz`. There is no frequency separation to
  exploit; masking in time is the only route. A transfer function referenced to channel 1111 is not *biased* by noise on the
  bolometer output, so the estimate survives — but variance is inflated and coherence depressed.
  **Report coherence per frequency; do not assume it.**
- Frequency steps are 250 s and **250 / 10 = 25 exactly**, so the pulser arrives at an *identical
  phase relative to every step boundary*. Any coherent average aligned on step boundaries
  accumulates the pulser **coherently**: it produces a clean, repeatable transient that looks like a
  structural response and looks *more* convincing the more steps you average.

**You must mask or otherwise defeat the pulser before any step-aligned averaging, and state how.**
An unmasked step-aligned average is a wrong answer, not a rough one.

### 4.2 The run is stepped sine, not impulses

The brief this pilot came from assumed ≥200 impulses with threshold detection, coherent averaging and
the eigensystem realization algorithm on impulse responses. **That premise is wrong for this data**:
RUNA is a stepped-sine sweep, 0.1 Hz steps, 250 s dwell. Threshold impulse detection has nothing to
find. The transfer-function and ring-down framing below replaces it.

### 4.3 Damping: when a number is possible and when only a limit is

The half-power width of a mode is `Δf = 2 ζ f0`. At 0.1 Hz spacing, at f0 = 3.45 Hz: ζ = 1% gives
Δf = 0.069 Hz, i.e. **0.7 of one step** — the peak falls between samples. ζ = 2% gives 1.4 points,
ζ = 5% gives 3.5. The collaboration re-swept 3.35–3.55 Hz at 0.025 Hz steps, implying a feature
≲0.2 Hz wide, so **ζ near 1.5–3% and 1–2 points across the peak** is the expected case.

Therefore:

**AMENDED 2026-10-31, approved by Vivek. See log E032: the previous wording offered the upper limit
as a branch and never required an attempt, so one node quoted `0.1/(2 f0)` on every row and the
pilot got no damping cross-check at all. That was a specification failure, not a node failure.**

**An upper limit is a result you may only report after an attempt that failed.** Reporting
`0.1/(2 f0)` without attempting a measurement is not compliance with this section; it is a
restatement of the frequency grid, and it carries no information about the detector. For every mode
you report, you must attempt at least one measurement and record what happened.

- **Route A — ring-down, resolution-independent, and the preferred one.** After each step the
  previous tone stops and an excited mode decays as `exp(-ζ·2πf0·t)`, time constant
  `τ = 1/(ζ·2πf0)` — about 3.2 s at 3.45 Hz for ζ = 1.45%, against a 250 s dwell. Fit the decay.
  Your fitting window must span **at least 3τ for the smallest ζ you intend to resolve**, and you
  must state the window and that ratio: a window shorter than ~1τ cannot constrain τ, and a fit that
  returns a number from such a window is not a measurement. Aggregate across channels before quoting
  a per-mode ζ, and say how you aggregated and how many fits entered each value.
- **Route B — half-power bandwidth**, where the peak spans ≥3 of the 0.1 Hz points.
- **Route C — the pole of your own rational-fraction fit.** If section 5 assigns you frequency-domain
  rational-fraction fitting, that fit already contains a damping term per pole. Report it. Do not fit
  the modes and then discard the damping the fit produced.

**The limit is void where it contradicts itself.** The upper limit `ζ ≲ 0.1/(2 f0)` rests on the
premise that the peak is unresolved, i.e. `Δf = 2 ζ f0 ≲ 0.1 Hz`. If any route returns a ζ whose
implied `Δf` **exceeds** the 0.1 Hz grid spacing, that premise is false for that mode, the limit does
not apply, and you must report the measurement rather than the limit — or report neither and say why.

**Required columns** for the damping deliverable, in addition to those in section 3: `zeta_method`
(one of `ringdown`, `bandwidth`, `rfp_pole`, `none`), `zeta_attempted` (boolean, must be `true` on
every row), `zeta_attempt_outcome` (one short clause: what you fitted, over what window, and if it
failed, the symptom), `n_fits_used`, and `implied_delta_f_hz` (`2 ζ f0`, so the self-consistency
check above is visible to the reader).

If every route fails for a mode, that is an acceptable and useful result. Report `zeta_method =
none`, **leave `zeta` empty rather than filling it with the grid formula**, and say in
`zeta_attempt_outcome` what you tried. A clearly reported gap is worth more than a filled-in number;
this is rule 6 of section 6, and it governs here.

**Scope, and it applies whether you succeed or fail.** This is one run of many that exist, one shaker
axis, one tower. Nothing you report here is definitive, and a damping result — or a documented
inability to measure one — is **partial and preliminary** either way. Write it in that register: no
conclusion in this deliverable should be phrased as settled, and the limits of what one run can
support should be stated alongside any number you quote.

### 4.5 Causality: store the samples the test needs

**AMENDED 2026-10-31, approved by Vivek. See log E035: the spec asked for a causality test and never
required anyone to store samples from before the boundary. Neither node did, so the test was
uncomputable and the critic correctly refused to score it as a pass. That was a specification
failure, not a node failure.**

Every ring-down array you store must begin at least **5 s before** its step boundary and carry an
explicit time axis with `t = 0` at the boundary, so that `t < 0` samples exist and are identifiable.
A deliverable whose earliest sample is at `t = 0` cannot be tested and does not satisfy section 3.

**What the test actually is, because the naive version is meaningless here.** The detector is *not*
quiet before a boundary: the previous tone is driving it at full amplitude. "Is there signal before
t = 0" is therefore always yes and tests nothing. The causal statement that has content is about the
**incoming** tone:

> No coherent response at the NEW drive frequency `f_new` may exist before `f_new` is switched on.

So measure, per boundary and per channel, the amplitude at `f_new` in a window ending at the
boundary, and compare it against the same quantity measured after. Report the pre/post amplitude
ratio. **Fail if it exceeds 0.2.**

Three things make this a real test rather than a formality, and you must address each:

1. **Use a measured boundary, not an assumed one.** A response that appears to precede the boundary
   by less than your boundary uncertainty is a timing error, not acausality. State the boundary
   times you used and their uncertainty, and say whether any apparent pre-response is larger than
   that uncertainty.
2. **Spectral leakage mimics acausality.** A finite window at `f_old` leaks into `f_new` only
   0.1 Hz away. Quantify that leakage for your own window and subtract or bound it; an unquantified
   leakage term makes a pre/post ratio uninterpretable.
3. **Give the statistic a null.** Repeat the identical measurement at a frequency that is never
   driven at that boundary, or in a window far from any boundary, so the reader knows the floor of
   your estimator rather than assuming it is zero.

A documented failure is an acceptable result here exactly as in 4.3: if leakage or boundary
uncertainty dominates, say so and report the bound you can support. **Partial and preliminary** — one
run, one axis, one tower — governs this section too.

### 4.4 What this data cannot answer

State these as not-applicable rather than passing or failing them:

- **No amplitude variation at fixed frequency.** Each frequency occurs exactly once in this run, so
  **no linearity test and no quadratic-thermal-path test is possible from it.**
- **The drive force is *not* smooth across frequency, and part of it may be instrumental.** Force RMS
  spans 365–1521 mV, a factor **4.16**, and contains two **step discontinuities**: **+71% between 5.4
  and 5.5 Hz** and **−32% between 7.4 and 7.5 Hz**. A one-step 71% jump cannot be smooth shaker and
  stinger response; a reference-channel range or amplifier gain change is at least as likely. Form
  every transfer function as a strict ratio to ch1111 **on the same step**, where such a change
  cancels. Any magnitude not formed that way will show these jumps as spurious response changes.
  Report both boundaries to the critic.
- **Nothing outside 2.52–9.52 Hz.** Do not extrapolate to the brief's 0.1–50 Hz.
- **One shaker axis** (MSP-X) and **one run**.

## 5. Suggested methods — change them with a logged reason

Your two directories must not converge on the same method; that is the point of the graph.

- **Analyst** (`analysis/`): recover steps by thresholding the band-passed channel 1111; H1 transfer
  function estimates `S_fb / S_ff` with 1111 as reference, averaged over sub-windows within each
  dwell; damping from **time-domain ring-down**; modes via the eigensystem realization algorithm on
  the ring-downs, with a stabilization diagram.
- **Verifier** (`verify/`): recover steps by matched filter or cross-correlation against a tone
  template; response by **per-step lock-in / synchronous detection** at the known drive frequency;
  modes by **frequency-domain least-squares rational-fraction fitting** of the measured transfer
  function. Do not use ERA and do not use threshold detection.

Both: write and run tests for step recovery, for the 3990 s offset, and for pulser masking.

## 6. Rules

1. **Read only your own directory, plus `data/`, `SPEC.md` and `data/meta.json`.** The verifier must
   never open, list or search `analysis/` or `critic/`. If you see the other agent's output by
   accident, say so in the log immediately; that check will be redone.
2. **CUORE data are read-only** and you should not need to touch them at all.
3. **No Slurm jobs.** If you think one is needed, stop and say what it is.
4. **Log every number you report** to `../AGENT_GRAPH_LOG.md` under your heading, as you get it.
5. **Report all 52 bolometers.** Do not pre-select a favourite channel: the example channel for the
   figure is chosen *after* reconciliation, by the highest median in-band coherence, a criterion
   fixed in advance precisely so nobody cherry-picks.
6. If something is unknown or looks wrong, **stop and say so** rather than guessing. A clearly
   reported gap is worth more here than a filled-in number.

## 7. Context you may use, and should

These are independent of both analyses and exist to be checked against, not copied:

- **Pulse-tube lines at multiples of 1.39443 Hz** (measured, not the brief's 1.4 Hz): **2.789,
  4.183, 5.578, 6.972, 8.367 Hz**, all inside the band. Measured on quiet3 at 1.29 mHz resolution;
  residuals to a 1.39443 Hz fundamental are under 0.2 mHz, against 11-33 mHz for 1.4 Hz.
- **The collaboration already hunted two resonances** with fine short sweeps: **3.35–3.55 Hz** (runs
  306468/469/470, 306486, 306492, 306503) and **8.0–9.0 Hz** (306477, 306485). Finding peaks near
  these is corroboration; finding none there is a result worth stating plainly.
