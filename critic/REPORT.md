# critic/REPORT.md — physics critic verdicts

**Provenance.** Content is the critic node's own report, produced by the `physics-critic` agent
(`model: sonnet`, 55,818 tokens, 10 tool calls, 203 s). The node **could not write this file itself**
— it reported "my environment forbids writing report .md files" — so the orchestrator transcribed its
hand-back verbatim into this file. Logged as E034. The verdicts, numbers and wording are the
critic's; the orchestrator added only this header and the audit note below.

**Orchestrator audit.** Every quantity the orchestrator independently precomputed *before* reading
this report matches: all 23 pulse-tube distances, the 9/12 and 8/11 cross-method match counts, both
damping ranges, the per-mode channel counts, and the SNR statistics (A median 109.35 / min 7.745 /
max 798.7; V median 76.14 / min 5.048 / max 504.2). No arithmetic discrepancy was found.

---

## Pass / fail table

| # | Check | Verdict | Number |
| --- | --- | --- | --- |
| 1 | Causality | **INCONCLUSIVE** | pre/post fraction not computable — 0 pre-boundary samples stored by either node |
| 2 | Damping `0 < zeta < 0.5` | PASS | A 0.0020–0.0146; V 0.00569–0.0166. Cross-method damping comparison **vacuous** |
| 3 | PT harmonics (1.39443 Hz) | PASS | smallest distances: A 0.0816 (8.285 Hz), 0.0837 (5.494 Hz); V 0.1631 (8.5297 Hz); limit 0.05 |
| 4 | Cross-channel | PASS, one weak mode | A 2.527 Hz on **1 channel** (962); all others ≥ 11 |
| 5 | Cross-method | **FAIL (partial)** | 9/12 A modes match, 8/11 V modes match; tolerance 0.0707 Hz |
| 6 | SNR above quiet noise | PASS | A 52/52 > 1, median 109.35, min 7.745; V 52/52, median 76.14, min 5.048 |
| 7 | Amplitude scaling / quadratic path | **NOT APPLICABLE** | no amplitude variation at fixed frequency |

## Check 1 — causality: INCONCLUSIVE, not a pass

- The analyst's ring-down array is `(78, 71, 1000)`, t = 0 to 39.96 s at 0.04 s spacing, **starting
  at the step boundary**. Count of `t < 0` samples is **0**, so the pre/post fraction cannot be
  computed against the 0.2 threshold.
- The verifier's ring-down window is 0.2 to 5.5 s after its boundary — also no pre-boundary samples.
- **Proxy only:** analyst bolometer-median ring-down RMS is 11.4 mV at 0–1 s, 10.4 at 1–2 s, 7.5 at
  3–5 s, 1.7 at 20–40 s: highest at t = 0, decaying monotonically, no rise. Consistent with
  causality but **does not test it**, because an onset before t = 0 is invisible.
- Pulser mask in the analyst's ring-downs: NaN from 5.88–6.48 s to 7.0–7.56 s; the pulse arrives
  5.96–6.54 s after its boundary; 11.0% of samples NaN.
- ERA segments (0–5.4 s and 7.7–13.1 s) end before the first masked sample and start after the last.
- One unmasked bin near the mask edge had RMS 23 at t = 7.04 s, but it comes only from steps 9–11
  (3.4–3.6 Hz), which sit on the resonance, so attributed to the resonance rather than a pulser leak.
- Node boundaries differ: A − V median **−0.548 s**, range −0.872 to +0.394 s. A is ~6.0–6.5 s
  earlier than `steps.csv`, V ~5.85 s earlier. Close to each other, not identical.

## Check 2 — damping

- Analyst zeta 0.0020 (7.464 Hz) to 0.0146 (3.021 Hz).
- Verifier zeta is **11/11 upper limits**, each `0.1/(2 f0)` to rounding, 0.00569–0.0166. It carries
  no measurement, so the cross-method damping comparison is **vacuous** and is not scored as
  agreement.
- The analyst's 3.42 Hz value (0.009) is itself an upper limit, below SPEC's expected 1.5–3%.
- Two matched analyst values exceed the verifier's limits:
  - **5.349 Hz: A 0.0131 ± 0.0006 vs V limit 0.00942 — +39%, about 6 sigma. A real tension.** Either
    the ERA damping is biased high, or the mode is not a single pole.
  - 4.886 Hz: A 0.0108 vs V limit 0.0102 — +6%, within 1 sigma.
- The analyst's 7.464 Hz zeta of 0.2% is at its own stated resolution limit.
- The verifier's ring-down tau is finite for 69% of channel-steps but with median relative standard
  error **4950%**, i.e. unconstrained.

## Check 3 — pulse-tube harmonics (fundamental 1.39443 Hz)

Distance is `min_k |f0 − k·1.39443|` in Hz.

| analyst f0 | dist | k | | verifier f0 | dist | k |
| --- | --- | --- | --- | --- | --- | --- |
| 2.527 | 0.2619 | 2 | | 3.0127 | 0.2238 | 2 |
| 3.021 | 0.2321 | 2 | | 3.4075 | 0.6186 | 2 |
| 3.420 | 0.6311 | 2 | | 3.9707 | 0.2126 | 3 |
| 3.962 | 0.2213 | 3 | | 4.8990 | 0.6787 | 4 |
| 4.886 | 0.6917 | 4 | | 5.3060 | 0.2717 | 4 |
| 5.349 | 0.2287 | 4 | | 6.2184 | 0.6407 | 4 |
| 5.494 | **0.0837** | 4 | | 7.4269 | 0.4547 | 5 |
| 7.464 | 0.4919 | 5 | | 7.9209 | 0.4457 | 6 |
| 8.099 | 0.2676 | 6 | | 8.1274 | 0.2392 | 6 |
| 8.172 | 0.1946 | 6 | | 8.5297 | 0.1631 | 6 |
| 8.285 | **0.0816** | 6 | | 8.7834 | 0.4168 | 6 |
| 8.794 | 0.4274 | 6 | | | | |

- No mode is within `f0_err` of a harmonic, so none is flagged. Both nodes' `pt_harmonic_flag`
  columns are all false, agreeing with this calculation.
- The analyst's **5.494 and 8.285 Hz** are within about 1.6 sigma of 5.578 and 8.367 Hz — not
  flagged, but the ones to watch. The analyst fitted and subtracted the PT lines before ERA.
- **The verifier's `modes.csv` header text says its flag uses multiples of 1.4 Hz, contrary to SPEC.**
  No flag changes, because distances to 1.4 Hz multiples also all exceed 0.05.

## Check 4 — channels (of 52)

- **Analyst:** 2.527→1, 3.021→11, 3.420→52, 3.962→49, 4.886→52, 5.349→34, 5.494→18, 7.464→32,
  8.099→44, 8.172→45, 8.285→39, 8.794→45.
- **Verifier:** 3.0127→34, 3.4075→52, 3.9707→48, 4.899→52, 5.306→35, 6.2184→46, 7.4269→49,
  7.9209→36, 8.1274→47, 8.5297→46, 8.7834→48.
- The analyst's 2.527 Hz mode is on a single channel (962), has 9 stable poles, and sits at the band
  edge (2.5 Hz): read as an **ERA single-channel artefact**.
- The analyst sees 3.021 Hz on 11 channels; the verifier sees the same mode on 34.

## Check 5 — cross-method: FAIL (partial)

Tolerance `sqrt(0.05² + 0.05²) = 0.0707 Hz`, or 0.0828 where the analyst error is 0.066.

| A mode | nearest V | separation | agrees |
| --- | --- | --- | --- |
| 2.527 | 3.0127 | +0.486 | **NO** |
| 3.021 | 3.0127 | −0.008 | yes |
| 3.420 | 3.4075 | −0.0125 | yes |
| 3.962 | 3.9707 | +0.009 | yes |
| 4.886 | 4.8990 | +0.013 | yes |
| 5.349 | 5.3060 | −0.043 | yes |
| 5.494 | 5.3060 | −0.188 | **NO** |
| 7.464 | 7.4269 | −0.037 | yes |
| 8.099 | 8.1274 | +0.028 | yes |
| 8.172 | 8.1274 | −0.045 | yes |
| 8.285 | 8.1274 | −0.158 | **NO** |
| 8.794 | 8.7834 | −0.011 | yes |

- **9/12** analyst modes agree. A's 8.099 and 8.172 both map to V's 8.1274, so only **8/11** verifier
  modes are matched.
- Unmatched analyst: **2.527, 5.494, 8.285**. Unmatched verifier: **6.2184** (nearest A 0.724 away),
  **7.9209** (0.178), **8.5297** (0.245).
- **Both nodes' median-|H| local maxima include 6.2, 7.9, 8.5** (prominence 2.03, 1.72, 1.31 for A)
  and 2.6 (1.52 for A). **So the data show these peaks: the disagreement is in the mode-detection
  method (ERA vs peaks of |H|), not in the underlying response.**
- The verifier's 2.6 Hz local maximum has prominence 1.46, above its own 1.25 threshold, yet is **not
  in its own mode list**. Its 9.2 and 9.4 Hz maxima were not scored.
- Raw transfer-function agreement is strong: log median |H| correlation **0.998**; per-channel |H|
  ratio A/V median **1.0003**, range 0.965–1.030; per-channel log|H| correlation median 0.978,
  minimum 0.872. **Partly shared by construction, since both nodes reference ch1111.**
- Collaboration cross-check: **3.35–3.55 Hz corroborated** (A 3.420, V 3.4075 both inside);
  **8.0–9.0 Hz corroborated** (A 8.099/8.172/8.285/8.794, V 8.1274/8.5297/8.7834). Modes at 3.0,
  3.97, 4.9, 5.3, 6.2, 7.4 Hz have no collaboration corroboration — which does not make them wrong.

## Check 6 — SNR

- Analyst 52/52 > 1, median 109.35, min 7.745 (ch981), max 798.7. Verifier 52/52 > 1, median 76.14,
  min 5.048 (ch981), max 504.2. Per-channel log-SNR correlation 0.988. Peak frequencies agree on
  47/52; 3.4 Hz is the peak for 42 (A) and 46 (V).
- **This is a weak test**, since SNR is taken at each channel's maximum step. Stricter: over all
  channel-steps with SNR > 1, A 87.4% and V 51.4%. No verifier channel exceeds 1 on every step;
  4 analyst channels do.
- Noise estimates differ: median A/V noise ratio **0.517** (A uses 20 s Hann tone-RMS over quiet1–3;
  V uses 5.6 s lock-in sub-blocks on quiet3 — different bandwidths, not directly comparable).
- `peak_response` is **not comparable** between files: A is the ratio |H| (mV/mV), V is mV RMS.
  Median coherence 0.731 (A) vs 0.527 (V), from different estimators.

## Check 7 — amplitude scaling / quadratic thermal path: NOT APPLICABLE

Each drive frequency occurs once in run RUNA, so amplitude is never varied at fixed frequency. The
test needs run 306473 (100/200/400/800 mV pp) or the pair 306439/306440, none of which has bolometer
data extracted.

**Strict-ratio sub-check — and the premise fails.**

- Both nodes form H as a strict same-step ratio to ch1111 (the verifier's |H| equals |amp/ref| to
  0.05% median; the analyst uses a single ch1111 force tone per step).
- **The ratio does NOT cancel the 5.4→5.5 Hz jump, because the jump is in ch1111 itself.**
  Force 427.2 → 741.4 mV (×1.735), accelerometer ch1112 only ×1.096 (A) / ×1.095 (V), bolometer
  median response 0.264 → 0.224 mV (×0.85), median |H| ×0.496 (A) / ×0.451 (V). Since
  0.85/1.735 = 0.49, **essentially the whole |H| drop is reference scale: a spurious step in |H| in
  both nodes.**
- At 7.4→7.5 Hz the character differs: force ×0.672, median |H| ×0.627 (A) / ×0.667 (V), bolometer
  response ×0.474, ch1112 ×3.18. The |H| drop is **larger** than the force drop would produce, so
  there is a **real response change** here — this boundary is not clearly instrumental.
- The analyst's 5.494 Hz and the verifier's 7.4269 Hz sit adjacent to these jumps. **Only the
  verifier flags it** (`ADJACENT_TO_CH1111_SCALE_DISCONTINUITY` on 7.4269 Hz); the analyst does not.

## Pulser mask declared by each node

- **Analyst:** `[t_p − 0.1, t_p + 1.0]` s, ~11% of samples. The 1.1 s width was a guess; its quiet
  stacks showed no pulse shape.
- **Verifier:** `[−0.2, +4.2]` s from a **measured** pulse shape; 44% masked, 53.7% of samples used.
- The 4× difference is **unresolved**. Analyst ring-down samples 1.0–1.4 s after a pulse have RMS
  4.1–4.2 against 2.6–2.9 at 2–4 s: only mildly raised, and confounded with ordinary ring-down decay,
  so it neither confirms nor excludes a longer tail.

## Disagreements for reconciliation, ranked

1. **Unmatched modes**: 6.2184, 7.9209, 8.5297 Hz (V only) and 2.527, 5.494, 8.285 Hz (A only). The
   first three have peaks in *both* nodes' |H| (prominence ≥ 1.31 in A). Decide whether ERA misses
   real modes or the |H| picker over-calls.
2. **The analyst's 2.527 Hz mode** on one channel at the band edge. Likely drop or demote.
3. **Zeta tension at 5.349 Hz**: A 0.0131 vs V limit 0.00942. And the verifier's damping is entirely
   upper limits, so there is no real damping cross-check anywhere.
4. **The 5.5 Hz ch1111 scale jump.** The analyst's 5.494 Hz mode sits right after it and is not
   tagged. The jump is in ch1111, so no ratio cancels it. Nobody has established instrument vs
   physical.
5. **Pulser mask width**, 1.1 s vs 4.4 s. Settle with a pulse-shape stack on quiet data.
6. **Step boundaries** differ by 0.55 s median (−0.87 to +0.39). Minor but systematic.
7. **The analyst's 3.021 Hz on 11 channels vs the verifier's 34.** `n_channels_showing` is not
   comparable across the methods.
8. Cosmetic: the verifier's `modes.csv` header says 1.4 Hz for the PT flag; SNR and `peak_response`
   definitions differ between the two `channel_gain.csv` files.
