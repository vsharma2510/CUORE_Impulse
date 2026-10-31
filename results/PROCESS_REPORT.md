# Running a physics analysis as a graph of agents

**CUORE shaker impulse pilot, run RUNA, tower 19.** Written 2026-10-31. The primary deliverable of
this pilot is the process, not the physics. What follows is how the graph was built and run, what it
got wrong, who caught each error, and what changed as a result.

Companion files: `results/errors.csv` (53 rows, the full ledger), `results/comparison.csv` (44 rows,
analyst against verifier with the test that settled each disagreement),
`results/modes_reconciled.csv`, `results/fig_pilot.pdf`, `results/SUMMARY.md`,
`results/TIMELINE.md` with `results/fig_timeline.pdf` (measured phase-by-phase record and its
evidence pointers, including where the record is thin), `AGENT_GRAPH_LOG.md`
(1929 lines, append-only), `results/DEMO_NOTES.md`.

---

## 1. The graph

| Node | Model | Works in | Can read | Cost |
| --- | --- | --- | --- | --- |
| orchestrator | Opus 5 | repo root, `extract/`, `reconcile/`, `results/` | everything | the session itself |
| analyst | Opus 5 | `analysis/` | `data/`, `SPEC.md` | 118,782 tokens, 40 tool calls, 18.1 min |
| verifier | Opus 5 | `verify/` | `data/`, `verify/SPEC.md` — **not** `analysis/` | 2 attempts, 1 wasted |
| critic | **Sonnet** | `critic/` | `analysis/`, `verify/`, `data/` | 55,818 tokens, 10 tool calls, 3.4 min |
| Vivek | human | gates | everything | 6 gates, 4 errors caught |

Two nodes were **re-dispatched** after the critic exposed defects in my spec, each for a single
deliverable and each forbidden to overwrite its first-run output:

| re-run | why | produced | cost |
| --- | --- | --- | --- |
| verifier, damping | E032 — §4.3 let a node quote `0.1/(2f₀)` without attempting a measurement | `verify/damping.csv`, 7 of 11 modes measured | 25 min |
| analyst, causality | E035 — §4.5 did not exist; nobody stored pre-boundary samples | `analysis/causality.csv`, 70 × 78 cells | 40,414 tokens, 14 tool calls, 11 min |

Five design choices did the work.

**Isolation by construction, not by instruction.** The verifier runs as a headless `claude -p` rooted
in `verify/`, with `--add-dir` for `data/` only. `analysis/` is in no allowed directory, so reading it
is not a rule the node is asked to follow — it is a path that does not resolve. Verified with a
planted sentinel: `SENTINEL-7Q4X` was placed in `analysis/`, a throwaway session in `verify/` was told
to read it three times, all three were blocked, and `grep -ril SENTINEL-7Q4X verify/` returns nothing
after both verifier runs. The verifier's own log affirms the negative twice, unprompted.

**Divergent methods, specified in advance.** `SPEC.md` §5 assigned each node a different route to the
same five deliverables: the analyst does threshold step recovery, H1 = S_fb/S_ff, time-domain
ring-down and ERA; the verifier does matched-filter recovery, per-step lock-in least squares and a
frequency-domain rational-fraction fit. Agreement between them then means something. Both were given
the identical spec file, byte for byte.

**The critic sees both and is told every threshold up front.** `critic/THRESHOLDS.md` supplies every
number the critic would otherwise have to derive, and requires it to print the number it computed
beside each verdict so the orchestrator can re-check the arithmetic independently.

**Human gates at five points**, with the rule that no Slurm job is submitted and no design is built
without Vivek seeing it first.

**An append-only log.** `AGENT_GRAPH_LOG.md` is never edited; corrections are appended. That rule is
what makes the error ledger trustworthy, because a ledger you can quietly revise is not evidence.

---

## 2. What the graph caught that a single agent would not have

Of 53 logged errors, **21 were caught by a node other than the one that made them** — analyst 6,
verifier 5, critic 5, Vivek 4. The orchestrator caught 31, mostly its own. Panel (a) of
`fig_pilot.pdf` is this distribution.

The six that justify the whole structure:

**E023 — the verifier caught a number I had carried forward without checking.** `data/meta.json`
claimed the drive force varied "~25% across frequency". That figure belonged to run 306428 and I had
copied it into the RUNA metadata. The real span is 365 → 1521 mV, a factor **4.16**, with step
discontinuities. Every downstream node had been handed a wrong characterisation of the drive.

**E025 — the verifier caught me publishing bin centres as measurements.** `data/steps.csv` carried
25 s FFT bin centres quantised to 0.04 Hz as if they were measured drive frequencies. Rewritten at
~4 mHz: the grid is exactly `f_k = 2.5 + 0.1k` Hz, maximum deviation 0.17 mHz. The same root cause
produced E028 and E029, which the **analyst** caught: the brief's "multiples of 1.4 Hz" is wrong, and
the measured pulse-tube fundamental is **1.39443 Hz** (residuals ≤0.2 mHz against −11 to −33 mHz for
1.4 Hz). My earlier "confirmation" of 1.4 Hz from a 25 s FFT was the same error confirming itself.

**E036 — the critic refuted a premise I had written into its own instructions.** I told it that
forming H as a strict same-step ratio to ch1111 would make a gain change cancel. It tested the claim
instead of accepting it and showed the ratio cannot cancel a change that is **in** ch1111, which is
exactly the case at 5.45 Hz. A node given a false premise by its supervisor rejected it.

**E024 — the verifier refused to fabricate.** Its first sandbox had a `deny` list but no `allow`
list, so every Write and every `python3` was refused. It produced nothing, exited 0, and **named the
exact permissions it needed** rather than inventing results. A silent zero-exit failure is the
dangerous case; it was caught because the node reported the refusal.

**E053 — the human caught what the graph did not.** My instrumental explanation of the 5.45 Hz step
survived the critic, reconciliation and a shipped package, and collapsed when Vivek asked whether
the premise was true. The graph has no node whose job is to audit a *mechanism* the orchestrator
proposes after the critic has run. That is a gap in the design, not a slip in execution.

**E047 — the verifier beat the critic to the same finding, with a better test.** I logged E036 as
the critic's catch. The verifier had it first, at V020 of its own log, and tested it harder: against
**three** independent witness channels rather than one, concluding the ratio "does not cancel, and
in fact directly imports, a change in the CALIBRATION of ch1111 itself." It then carried that into
`modes.csv` as the discontinuity flag the analyst lacked. I under-credited it because I read the
critic's report closely and the verifier's log loosely.

**E050 — the analyst refused my number and was right.** Re-dispatched for causality, it measured the
step boundaries itself instead of adopting the figure I handed it, got a 0.37 s disagreement, and
**reported it as unresolved rather than picking one**. Chasing that down showed my estimator was
unbiased on an ideal step and the real transition is sharp, leaving only one explanation: 0.24 s of
my number was a 1 s moving average. The boundary ranking I had published inverts.

The ledger's shape is itself a finding: **29 of 51 errors were mine**, the orchestrator's, and 10
more were environmental. The agent nodes erred 8 times between them. The graph's value here was not
that the nodes were more reliable than the supervisor — it is that there was someone to check the
supervisor, and on six occasions they did — though E053 shows a human still caught something all three missed.

---

## 3. The disagreements, and how each was settled

Reconciliation did not tabulate the critic's eight ranked disagreements; it tried to measure its way
out of each one. Two of them turned out to be defects in my spec rather than disputes between nodes,
and those were fixed by amending the spec and re-running a node — §3.5 and §3.6. Scripts in
`reconcile/`, outcomes in `results/comparison.csv`.

### 3.1 Unmatched modes — resolved, verifier right

9 of the analyst's 12 modes matched 8 of the verifier's 11 at the 0.0707 Hz tolerance. The critic
observed that both nodes' median-|H| maxima contain the verifier-only frequencies, so the
disagreement was method, not data. `reconcile/r1_modes.py` went finer: for each unmatched mode, count
the channels showing a 3-point local maximum of |H| that clears its own standard errors, **in each
node's own data**.

| unmatched mode | found by | peak in analyst's own H | in verifier's | outcome |
| --- | --- | --- | --- | --- |
| 6.2184 Hz | verifier | **44 / 52** | 40 / 52 | accepted — the analyst's ERA missed it |
| 7.9209 Hz | verifier | **32 / 52** | 30 / 52 | accepted |
| 8.5297 Hz | verifier | **25 / 52** | 25 / 52 | accepted |
| 8.285 Hz | analyst | 10 / 52 | 7 / 52 | demoted to tentative |
| 5.494 Hz | analyst | **0 / 52** | 0 / 52 | **withdrawn** |
| 2.527 Hz | analyst | band edge, undefinable | — | **withdrawn** |

For scale, two modes the analyst reported and both nodes accepted reach only 4/52 on the same
measure. The verifier-only modes have more per-channel support than modes nobody disputed (**E042**).

The analyst wins one: its 8.099 and 8.172 Hz are 0.073 Hz apart, **below the 0.1 Hz drive grid**, so
median-|H| peak-picking cannot separate them by construction while ERA can. Both are kept.

### 3.2 The reference-channel steps — the conclusion I published was wrong

The drive force has two step discontinuities, +71% at 5.4→5.5 Hz and −32% at 7.4→7.5 Hz. The
verifier (V020) and then the critic (E036) established that a ratio to ch1111 cannot remove them,
because the change is in ch1111 itself. The open question was whether the cause was instrumental.

**What I published, and why it is withdrawn (E053).** I claimed a discriminator: an amplifier or
ADC range change scales a channel's *off-tone noise* by the same factor as its tone, a physical
change scales only the tone. On that basis I reported 5.45 Hz as a pure gain change (ch1111 tone
×1.729, off-tone ×1.836, ratio 0.94) and 7.45 Hz as a gain change plus a real drive-point
resonance (ratio ×0.37).

Vivek asked whether the gain change was really instrumental. Testing the premise rather than
restating it broke it twice over:

- My "off-tone" band was 0.5–100 Hz with only the 2nd and 3rd harmonics removed, so **every harmonic
  from the 4th up stayed in it**. Those scale with the drive, so off-tone tracked the tone *by
  construction* — the very agreement I read as evidence.
- More seriously, **the off-tone is not a stable reference at all.** ch1111's jumps beyond 5 σ at
  **20 of 70 boundaries**, frequently up and straight back down, because the shaker is a broadband
  source and the rig's mechanical noise responds to it. A floor that moves by factors of 2–3 on its
  own cannot certify that a ×1.7 coincidence means anything.

Redone with a drive-free 30–45 Hz band notched at all 60 harmonics, the tone-to-noise ratio change
is **×1.14 at 5.45** and **×0.86 at 7.45** — neither the clean ×1.0 of a pure rescale nor a clean
tone-only signature, and the 7.45 result **reverses sign** against what I published.

**What is actually defensible** is narrower, and needs no discriminator at all — just two numbers
per boundary:

| boundary | ch1111 tone | ch1112 tone | monitors disagree by |
| --- | --- | --- | --- |
| 5.4 → 5.5 Hz | ×1.73 | ×1.10 | **×1.58** |
| 7.4 → 7.5 Hz | ×0.66 | ×3.11 | **×4.7** |

Two independent monitors of the same drive disagree by factors of 1.6 and 4.7. Therefore |H|
referenced to ch1111 is **reference-dependent at that level across those boundaries, and any mode
adjacent to them is unreliable.** Whether the cause is an instrument range change or a physical
drive-point effect is **not established by this pilot.**

The downstream decisions survive on independent evidence: 5.494 Hz is withdrawn because **0 of 52
channels** show a local |H| maximum there (§3.1), and 7.46 Hz is demoted on the monitor
disagreement plus its 4-of-52 peak support, the weakest of any agreed mode.

**The process point is sharper than the physics one.** A plausible mechanism, a clean number and a
confident write-up are not evidence. This passed the critic, passed reconciliation, and shipped in
a handoff package, and it fell over in ten minutes once a human asked whether the premise was true.
The nodes did not catch it, because none of them was asked to.

### 3.3 Pulser mask width — resolved as a null, with a control

The analyst masked 1.1 s around each heater pulse and the verifier 4.4 s, costing it 44% of its
samples. My first attempt to settle it reported a 6–13 σ feature and was **baseline drift**
(**E040**): a 14 s window folded in the next pulse and the "peak" sat at +11.9 s, nowhere near t = 0.

`reconcile/r5b_pulser.py` added what should have been there first — the same stack at a deliberately
wrong phase, pulse times + 5 s. On-pulse and control are indistinguishable in every band in all three
quiet windows, and single-channel peak excursions match the control to within 5%. **No heater pulse
is detectable on tower-19 bolometers in quiet data below about 0.3 mV**, which is the size of the
shaker response itself. Neither mask is justified by a measurement. The verifier's "measured shape"
was measured in-band, where a pulse-aligned stack accumulates the drive tone — precisely the trap the
analyst had demonstrated synthetically (>20 σ fake response).

### 3.4 Step boundaries — resolved twice, and the second time against me

Two void attempts first (**E039**): a 0.5 s lock-in cannot separate 4.4 from 4.5 Hz, so the envelope
"crossing" was noise and it returned **the opposite of the truth**. Caught by a consistency check
written into the replacement — true boundaries are exactly 250 s apart. `reconcile/r6c_instfreq.py`
then located all 70 from the instantaneous frequency of the band-passed force channel and I
published: `data/steps.csv` late by 5.986 s, verifier +0.117 s, analyst −0.434 s.

**That verdict has since been retracted (E050).** Re-dispatched for causality, the analyst measured
the boundaries independently with a two-segment changepoint scan, got steps.csv − 6.356 s against my
− 5.986 s, and reported the 0.37 s gap as unresolved rather than adopting either figure. Two tests
settled it: `r6d_bias.py` showed my estimator is **unbiased on an ideal step** (+0.000 s, scatter
0.006–0.022 s), ruling out a coding error; `r6e_width.py` showed the real transition is **sharp at
0.048 s**, ruling out a ramp, which would have explained only 0.020 s. Re-measuring with a 0.15 s
average instead of 1.0 s gives steps.csv − 6.227 s. **0.24 s of my published number was the moving
average.**

Corrected, the ranking inverts:

| | distance from the corrected boundary |
| --- | --- |
| analyst | **0.06–0.19 s** — closest |
| verifier | 0.36–0.49 s |

`data/steps.csv` is still late, by 6.2–6.4 s rather than 5.99 s, so the analyst's original E029
finding stands and is if anything understated. The retraction is marked in `comparison.csv` and the
superseded script annotated rather than deleted.

### 3.5 Damping — the spec was amended and the gap closed

`SPEC.md` §4.3 let a node quote the upper limit `0.1/(2f₀)` without first attempting a measurement
(**E032**). The verifier quoted it on all 11 rows, so the pilot initially had **no damping
cross-check anywhere**. That was a specification failure, not a node failure.

Vivek approved an amendment and the verifier was re-dispatched for that one deliverable. The clause
now reads: **"An upper limit is a result you may only report after an attempt that failed."**
`zeta_attempted` must be true on every row; three routes are named, including the pole of the node's
own rational-fraction fit, which it had been computing and discarding; the fit window must span ≥3τ;
and the limit is **void where it contradicts itself**, i.e. where a measured ζ implies a half-power
width wider than the 0.1 Hz drive grid. Failure is explicitly permitted: `zeta_method = none` with
`zeta` **left empty**, never the grid formula.

The re-run measured damping on **7 of 11 modes** and reported **4 honest non-detections**. The grid
formula appears nowhere in `verify/damping.csv`. Five modes now have a genuine cross-method
comparison, **all agreeing within 1.8 σ**:

| mode | analyst (ERA) | verifier (ring-down) | tension |
| --- | --- | --- | --- |
| 3.42 Hz | 0.0090 *(was its own upper limit)* | 0.01103 ± 0.00165 | +1.2 σ |
| 4.89 Hz | 0.0108 | 0.01309 ± 0.00280 | +0.8 σ |
| 7.43 Hz | 0.0020 | 0.00355 ± 0.00088 | +1.8 σ |
| 8.13 Hz | 0.0034 | 0.00324 ± 0.00081 | −0.2 σ |
| 8.79 Hz | 0.0038 | 0.00358 ± 0.00123 | −0.2 σ |

At **three** modes the measured width exceeds the 0.1 Hz grid, so the limit the first pass had quoted
there was void exactly as the amendment predicted.

**The node did more than it was asked.** It mid-run rejected its own first acceptance cut — *"My
stage-A cut was ill-posed and I am replacing it, not keeping it"* — because it had been dividing a
narrowband amplitude by a broadband residual. It replaced it with an F-statistic, and then built a
**null control nobody specified**: every fit repeated in a window 120.2 s after the boundary, where
any decay with τ < 13 s is gone by nine e-foldings, giving the measured noise floor of its own
estimator on this detector. A mode counts as measured only if it stands clear of its own null. It
also fitted *across* the pulser gaps rather than truncating at the first pulse, which is what made a
window longer than one pulser period possible at all.

One tension survives and is now cleaner. At 5.31–5.35 Hz the analyst reports ζ = 0.0131 ± 0.0006 and
the verifier reports a **non-detection** — 0 of 104 fits cleared its null. The analyst's value stands
uncontested rather than contradicted, which is a better state than a formula pretending to disagree
with it.

Two faults in the delivered file, both found by counting: its header says "three of the eleven modes
yielded a ring-down measurement" when its own table says seven (**E048**, it conflated the Route C
count), and two conflicting sets of per-mode verdicts were appended without marking which supersedes
(**E049** — `damping.csv` carries the second, with the wider error bars).

### 3.6 Causality — spec amended, test run, and the honest answer is inconclusive

`SPEC.md` asked for a pre/post boundary test but never required either node to **store** samples
before the boundary (**E035**). Neither did. §4.5 was added, approved by Vivek, requiring ring-downs
to begin ≥5 s before the boundary, and the analyst was re-dispatched.

**Writing the clause showed the obvious test is vacuous.** The detector is not quiet before a
boundary — the previous tone drives it at full amplitude — so "is there signal before t = 0" is
always yes. The statement with content concerns the *incoming* tone: no coherent response at `f_new`
may exist before `f_new` is switched on. The clause also named three adversaries the node had to
handle rather than quote a ratio: measured boundaries, spectral leakage, and a null.

**Result: inconclusive per cell, and reported that way (E051).** Median pre/post 0.049 against a
null of 0.052 — **median pre/null = 0.98**, so the pre-boundary signal *is* the estimator's noise
floor, and ~11% of cells exceed the 0.2 threshold even in the nulls. No acausality was detected
above that floor. What the run supports: on strong channels (n = 660) the median is **0.010** with
0.9% above 0.2, and **68 of 70 boundaries** pass by median over trusted channels. The two exceptions
sit 0.017 Hz from the 4.18329 Hz pulse-tube line and have failing nulls, so the node attributed them
to that line rather than claiming a violation.

Its leakage handling is the part worth showing: a 20 s window chosen so `Δf·W = 2` makes the old
tone exactly orthogonal to the new, then the explicit caveat that this is "small by construction,
not a measurement of the real detector". Without that joint term the leakage would have been 0.12 —
comparable to the signal being looked for. It also wrote a **positive control**: an injected acausal
tone that the pipeline detects.

**And it caught me (E050).** It measured the boundaries itself instead of adopting my figure, got
steps.csv − 6.356 s against my − 5.986 s, and reported the 0.37 s gap as unresolved rather than
picking one. My estimator turned out to be unbiased on an ideal step (+0.000 s) and the transition
is sharp (0.048 s), so neither a coding error nor a ramp explained it: **0.24 s of my number was a
1 s moving average.** Corrected, the ranking I had published inverts — the **analyst** is closest at
0.06–0.19 s, the verifier furthest at 0.36–0.49 s.

### 3.7 and 3.8 Definitional and cosmetic

`n_channels_showing` counts stable ERA poles for one node and |H| peaks for the other, and
`peak_response` is a dimensionless ratio for one and mV RMS for the other. Neither is reconcilable as
a number; both are recorded as not comparable. The verifier's `modes.csv` header declares a 1.4 Hz
pulse-tube convention against spec (**E037**) with no change to any flag, and its own 2.6 Hz peak
exceeds its own prominence threshold yet is absent from its own list (**E038**) — both caught by the
critic reading the verifier's work, which is what the critic exists for.

---

## 4. Where a cheaper model sat safely

After Vivek flagged usage, the critic was moved to Sonnet with every threshold pre-supplied and a
requirement to print its number beside each verdict. Before reading its report I precomputed an
independent audit and sealed it. **Every quantity matched**: all 23 pulse-tube distances, both match
counts, both ζ ranges, the per-mode channel counts, and the SNR statistics to three decimals. It ran
at **55,818 tokens, about half the analyst's**, and produced more adjudication.

The honest caveat is that this says nothing about Sonnet on an open-ended task. It held *because* the
checks were enumerated, the thresholds supplied, and the arithmetic re-checked by a second party. The
transferable claim is narrow: **a verification node whose checks are fully enumerated in advance is a
place where a weaker model is safe, provided someone re-checks it.**

One thing it could not do: write its own report. It reported that its environment forbade writing
`.md` files, so the orchestrator transcribed its hand-back verbatim with a provenance header
(**E034**). A transcription is a weaker artefact than a file the node wrote itself, and it is labelled
as such.

---

## 5. What I would change

**The spec is the single highest-leverage artefact, and two of its flaws made results
uncomputable.** E032 and E035 are not analysis errors — they are specification errors, and no amount
of node quality recovers from them. A spec that asks for a test must also require the inputs that
test needs. Next time, each deliverable gets a stated precondition.

**Freeze shared inputs for the duration of a phase.** I rewrote `data/steps.csv` while the analyst
was running and forced it to retract a finding (**E027**). The rule now is that a shared input is
immutable while any node depends on it.

**Record wall-clock from `date`, never from memory.** Every log timestamp after ~02:40 UTC was
overstated by up to 122 minutes because I wrote plausible times instead of calling `date` (**E022**).
The correction is appended, not applied in place, so the error is visible.

**Build the falsification into the script, not the review.** Both of reconciliation's void results
(E039, E040) were caught by checks written into the *replacement* script — the 250 s spacing test,
the wrong-phase control. The void methods had looked entirely convincing, one of them at 13 σ.

**Checksum a shared document before every dispatch, not once.** `verify/SPEC.md` was written at
04:24 and the root copy edited at 04:59, after the verifier had already finished. It ran against a
stale spec and the divergence sat unnoticed for eight hours, through the critic and through
reconciliation (**E045**). It surfaced only because Vivek told me to apply an amendment to *both*
copies, which meant diffing them. One of the two ledger entries it invalidated had blamed the
verifier for obeying the document it held.

**A defect in the spec is fixable mid-pilot, and fixing it is cheaper than it looks.** Two of the
critic's eight disagreements were not disputes between nodes at all — they were places where my
spec made a result uncomputable. Amending the clause and re-running one node for one deliverable
cost 25 and 11 minutes respectively, and converted a column of arithmetic into seven measurements
and an untested claim into an honestly inconclusive one. I had initially written both up as
permanent gaps. They were not.

**Write the acceptance criterion so that failure is reportable.** Both amendments say, in the spec
itself, that a documented failure is a legitimate result — `zeta_method = none` with the field left
empty, never the grid formula. The verifier returned four non-detections and the analyst returned an
inconclusive causality verdict, and in both cases that is the *correct* output rather than a
shortfall. The old §4.3 had no way to express "I tried and could not", so a node with nothing to say
filled the column anyway.

**Agreement between nodes is not truth.** E043 is the one I would put first. Two nodes with genuinely
different methods agreed on a mode, and the agreement was worthless because both referenced the same
faulty channel. Independence of method is not independence of instrument.

---

## 6. Honest scope

One run, one shaker axis (MSP-X), one tower, 52 bolometers, 71 drive frequencies from 2.50 to
9.50 Hz, 100 mV pp drive. No amplitude variation at fixed frequency exists in this run, so linearity
and the quadratic thermal path were **not tested** and are reported as not applicable, not as passes.

**Damping** is now measured on 7 of 11 modes, with 5 cross-checking between two independent methods
inside 1.8 σ, and 4 honest non-detections. **Causality** was tested and is **inconclusive per
cell**: the pre-boundary signal equals the estimator's own noise floor, so the test neither shows
nor excludes a pre-response, though no acausality appears above that floor and 68 of 70 boundaries
pass by median over trusted channels. Neither result is definitive. This is one stepped-sine run out
of many that exist; a damping ratio from one axis on one tower constrains **this run** and does not
establish a property of the detector. The absolute mV scale rests on the
`adc2mV` constant from the writer's source, confirmed by provenance for the auxiliary channels but
**not independently verified for the bolometer channels** — `channel_gain.csv` absolute scale is an
assumption, and is labelled one in `data/meta.json`.

Step 6 (the SSM/SHRED denoising comparison) was cut at the stop-point-4 gate to protect the primary
deliverables, on the brief's instruction to cut scope rather than run late.

No raw data and no CUORE-internal paths appear in `results/`. Two credential exposures found in the
environment during the pilot (**E008**) are recorded in the log by description only; neither the token
nor the password is reproduced anywhere in this directory or in any recording, and the recordings were
checked before any sharing.
