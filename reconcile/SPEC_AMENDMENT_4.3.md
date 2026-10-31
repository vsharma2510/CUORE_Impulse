# Proposed amendment to SPEC.md §4.3 — damping

**Status: PROPOSAL, not applied.** Awaiting Vivek. If approved, `SPEC.md` and `verify/SPEC.md` are
both updated, the change is logged with old text, new text and reason as the brief requires, and the
verifier is re-dispatched for this deliverable only.

## Why

E032. The clause below offers the upper limit as a *branch* and never requires a node to attempt a
measurement first. The verifier took that branch on **all 11 rows** — every `zeta` equals
`0.1/(2 f0)` to within 5e-6 — so the pilot has **no damping cross-check at all**. That is a
specification failure, not a node failure: the node did exactly what it was told.

It is also not that the data lack the information. The verifier's own `responses.npz` already holds
`ringdown_tau_s` for all 3,640 channel-steps, of which **486 across 47 steps have a relative standard
error under 50%**. It computed them and then published the formula instead.

## Old text (SPEC.md §4.3, the two bullets)

> - **ζ from half-power bandwidth only where the peak spans ≥3 of the 0.1 Hz points.** Otherwise report
>   an **upper limit**: an unresolved peak implies `Δf ≲ 0.1 Hz`, hence `ζ ≲ 0.1 / (2 f0)` — about
>   **ζ < 1.4% at 3.45 Hz**. Set `zeta_is_upper_limit`.
> - **ζ from ring-down is resolution-independent and is the preferred route.** After each step the
>   previous tone stops and an excited mode decays as `exp(-ζ·2πf0·t)`, time constant
>   `τ = 1/(ζ·2πf0)` — about 3.2 s at 3.45 Hz for ζ = 1.45%, against a 250 s dwell. Fit the envelope.
>   This is the measurement the 250 s dwell buys, and it is why 4.1 matters so much.

## New text

> **An upper limit is a result you may only report after an attempt that failed.** Reporting
> `0.1/(2 f0)` without attempting a measurement is not compliance with this section; it is a
> restatement of the frequency grid, and it carries no information about the detector. For every mode
> you report, you must attempt at least one measurement and record what happened.
>
> **Route A — ring-down, resolution-independent, and the preferred one.** After each step the previous
> tone stops and an excited mode decays as `exp(-ζ·2πf0·t)`, time constant `τ = 1/(ζ·2πf0)` — about
> 3.2 s at 3.45 Hz for ζ = 1.45%, against a 250 s dwell. Fit the decay.
> - Your fitting window must span **at least 3τ for the smallest ζ you intend to resolve**, and you
>   must state the window and that ratio. A window shorter than ~1τ cannot constrain τ, and a fit that
>   returns a number from such a window is not a measurement.
> - Aggregate across channels before quoting a per-mode ζ. Single channel-step fits on this data are
>   not individually usable; say how you aggregated and how many fits entered each mode's value.
>
> **Route B — half-power bandwidth**, where the peak spans ≥3 of the 0.1 Hz points.
>
> **Route C — the pole of your own rational-fraction fit.** If §5 assigns you frequency-domain
> rational-fraction fitting, that fit already contains a damping term per pole. Report it. Do not fit
> the modes and then discard the damping the fit produced.
>
> **The limit is void where it contradicts itself.** The upper limit `ζ ≲ 0.1/(2 f0)` rests on the
> premise that the peak is unresolved, i.e. `Δf = 2 ζ f0 ≲ 0.1 Hz`. If any route returns a ζ whose
> implied `Δf` **exceeds** the 0.1 Hz grid spacing, that premise is false for that mode, the limit
> does not apply, and you must report the measurement rather than the limit — or report neither and
> say why.
>
> **Required columns**, in addition to those in §3: `zeta_method` (one of `ringdown`, `bandwidth`,
> `rfp_pole`, `none`), `zeta_attempted` (boolean, must be `true` for every row),
> `zeta_attempt_outcome` (one short clause: what you fitted, over what window, and if it failed, the
> symptom), `n_fits_used` (how many channel-step fits entered the value), and
> `implied_delta_f_hz` (`2 ζ f0`, so the self-consistency check above is visible to the reader).
>
> If every route fails for a mode, that is an acceptable and useful result. Report
> `zeta_method = none`, leave `zeta` empty rather than filling it with the grid formula, and say in
> `zeta_attempt_outcome` what you tried. **A clearly reported gap is worth more than a filled-in
> number** — this is rule 6 of §6, and it governs here.

## What does NOT change

- **§5 method assignment stands.** The verifier does not use ERA and does not use threshold
  detection. Route C is its own rational-fraction fit, which is already its assigned method; Route A
  is a decay fit, which is not the analyst's envelope-fitting-plus-ERA pipeline. The two directories
  still do not converge on the same method.
- **§6 rule 1 stands.** `analysis/` and `critic/` remain outside the verifier's allowed directories.
  Nothing in this amendment names, quotes or implies any value the analyst obtained. The
  self-consistency test is stated as a general rule about the grid, which it is.
- **Nothing is overwritten.** The verifier writes `verify/damping.csv` and appends to
  `verify/VERIFIER_LOG.md`. Its existing `modes.csv`, `responses.npz` and `method_note.md` stay
  exactly as they are, so the original claim remains auditable and the E032 record is not erased.

## Scope and cost of the re-run

One deliverable, not the whole node. The verifier re-reads `data/` and its own `responses.npz`,
which already contains the ring-down baseband it needs, so no re-extraction. Estimate **20–30
minutes**, login node, **no Slurm**. Recorded as `rec_04_damping`.

## What the pilot gets

The first real cross-method damping comparison: the analyst's ERA ζ values against the verifier's,
measured by a different route. It also puts one specific tension to the test — a mode where the
analyst's ζ implies a half-power width wider than the drive grid, which under the new clause voids
the limit the verifier previously quoted there.

## Honest risk

The verifier may come back and report that it cannot measure damping on this data — its ring-down
window is 0.2–5.5 s, which is barely one time constant for the ζ values in play, and it would have to
widen it. **That is a legitimate outcome and the amendment is written to accept it**, because the
point is to replace an uninformative formula with either a measurement or a documented failure. It
is not written to produce a number.
