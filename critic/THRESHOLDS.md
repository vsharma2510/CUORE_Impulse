# Thresholds for the physics critic — supplied by the orchestrator

Every number you need is here, so you do not have to derive any of it. **For every check, print the
number you computed next to the verdict.** The orchestrator will re-check your arithmetic
independently, so a verdict without its number is not usable.

## Inputs

- `analysis/` — analyst node: `impulses.csv`, `responses.npz`, `modes.csv`, `channel_gain.csv`,
  `method_note.md`. Methods: threshold step recovery, H1 = S_fb/S_ff referenced to ch1111,
  time-domain ring-down, eigensystem realization algorithm. **12 modes.**
- `verify/` — verifier node, same spec, different methods: matched-filter step recovery, per-step
  lock-in least squares, frequency-domain rational-fraction fit. **11 modes.**
- `data/meta.json`, `data/steps.csv`, `data/pulser_times.npy`, `data/sanity_step1.json`.

`channel_gain.csv` in **both** directories begins with a `#` comment line, so read with
`comment='#'`. Amplitudes are **mV at the ADC input**, not bolometer volts.

## The checks, with their thresholds

### 1. Causality
No averaged step-transient or ring-down response may begin **before** its step boundary. Inspect the
analyst's ring-down segments in `responses.npz`. Allowed pre-boundary leakage: anything consistent
with the **1.1 s pulser mask** and the taper the node declares in its method note. Report the largest
pre-boundary amplitude as a fraction of the peak post-boundary amplitude. **Fail if > 0.2.**

### 2. Damping positive and plausible
Every `zeta` in both `modes.csv` files must satisfy `0 < zeta < 0.5`. Report the min and max.
**Fail on any `zeta <= 0` or `>= 0.5`.**

Note before you judge: the verifier's `zeta` column is **entirely** the prescribed upper limit
`0.1/(2*f0)`, with `zeta_is_upper_limit = true` on all 11 rows. That is spec-compliant but carries no
measurement. State plainly that the cross-method damping comparison is therefore **vacuous** — do not
score it as agreement.

### 3. Pulse-tube harmonics mistaken for modes
**Use a fundamental of 1.39443 Hz, NOT the 1.4 Hz the original brief states.** The 1.4 Hz figure is
wrong; see `meta.json` and log E028. Measured harmonics inside the band:

| k | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- |
| f [Hz] | **2.78886** | **4.18329** | **5.57772** | **6.97215** | **8.36658** |

For every mode in both files, compute `min_k |f0 - k*1.39443|`. Flag as a possible PT line if that is
`<= f0_err` (f0_err is 0.05 Hz for the verifier on every row; use each file's own value).
Report the distance for every mode. Also check whether either node's `pt_harmonic_flag` column agrees
with your own calculation, and say so if it does not.

### 4. Cross-channel consistency
For each mode, how many of the 52 bolometers show it (`n_channels_showing`). **Flag any mode seen in
fewer than 5 channels as weakly supported.** The analyst's 2.527 Hz mode is reported on **1 channel**
— call that out explicitly.

### 5. Cross-method consistency
Match analyst modes to verifier modes. Two modes agree if
`|f0_analyst - f0_verifier| <= sqrt(err_a^2 + err_v^2)`. With both errors at the 0.05 Hz floor the
combined tolerance is **0.0707 Hz**. Report, as a table: every analyst mode, its nearest verifier
mode, the separation, and whether it agrees. Then report **how many of the 12 and 11 match**, and
list the unmatched ones on each side. Unmatched modes are the disagreements reconciliation will act
on, so be precise.

### 6. Response above the quiet-data noise floor
Use the `snr` column of each `channel_gain.csv`. **Fail a channel if `snr <= 1`.** Report how many of
the 52 bolometers exceed `snr > 1`, and the median SNR, for each node. The analyst's
`inband_noise_rms_mV` is the **median over the 71 drive frequencies** of the quiet-window noise
through its own 20 s Hann tone-RMS estimator, not a broadband RMS — do not compare it against a
broadband number.

### 7. Amplitude scaling and the quadratic thermal path
**NOT APPLICABLE for this run, and you must say so rather than pass or fail it.** Each drive
frequency occurs exactly once in run RUNA, so amplitude is never varied at fixed frequency. State
that the test would need run 306473 (which steps 100/200/400/800 mV pp within one run) or the pair
306439/306440, none of which has bolometer data extracted.

Related, and do check this: the drive force is **not** smooth across frequency. Force RMS spans
365.21 to 1521.01 mV, a factor **4.16**, with **step discontinuities of +71% between 5.4 and 5.5 Hz
and −32% between 7.4 and 7.5 Hz** (`data/steps.csv`). These are suspected reference-channel range or
amplifier changes. Verify that each node formed its transfer function as a **strict ratio to ch1111
on the same step**, so such a change cancels. If a node did not, its `|H|` will show these jumps as
spurious response changes — check its `responses.npz` around 5.45 and 7.45 Hz and report what you
find.

## Context you may check against, not copy

- The collaboration independently hunted two resonances with fine short sweeps: **3.35–3.55 Hz**
  (runs 306468/469/470, 306486, 306492, 306503) and **8.0–9.0 Hz** (306477, 306485). Modes found near
  these are corroborated by work neither node saw; modes found nowhere near them are not thereby
  wrong, but say so.
- Band is **2.50–9.50 Hz**, 71 drive steps on the grid `f_k = 2.5 + 0.1k` Hz (measured, max deviation
  0.17 mHz).
- The pulser is deterministic at 10.0000 s, 1777 pulses in the window, **phase-locked 2 ms after
  every frequency-step boundary**. The analyst masked `[t_p-0.1, t_p+1.0]` s and demonstrated with a
  synthetic test that an unmasked step-aligned stack yields a **>20 sigma fake response**. Confirm
  each node declares a mask and say what it is.

## Output

Write `critic/REPORT.md`: a pass/fail/not-applicable table with **one row per check**, each carrying
the number behind the verdict, then a short section per check with your working, then a list of the
disagreements for reconciliation ranked by how much they matter. Do **not** fix either node's
outputs. Append a summary to `../AGENT_GRAPH_LOG.md` under a heading "critic".
