# Changes since v1

**v2 — 2026-10-31.** If you already started drafting from v1, read this file; one change is a
retraction that affects what you can claim, and another means a v1 copy taken from git was
incomplete.

---

## 1. A physics conclusion is WITHDRAWN (E053) — this is the one that matters

**v1 said:** the step in |H| at 5.45 Hz was a **pure instrumental gain change** in the reference
channel ch1111, and the step at 7.45 Hz was a gain change **plus** a real shaker drive-point
resonance. The argument was a discriminator: a range change scales a channel's off-tone noise by
the same factor as its tone, a physical change scales only the tone.

**v2 says: the cause is undetermined.** Vivek asked whether the gain change was really instrumental.
Testing the premise broke it twice:

- The "off-tone" band ran 0.5–100 Hz with only the 2nd and 3rd harmonics removed, so **every
  harmonic from the 4th up stayed in it**. Those scale with the drive, so off-tone tracked the tone
  *by construction* — the agreement that was read as evidence.
- **The off-tone is not a stable reference.** ch1111's jumps beyond 5 σ at **20 of 70** boundaries,
  repeatedly up then straight back down, because the shaker is a broadband source and the rig's
  mechanical noise follows it.

Redone with a drive-free 30–45 Hz band notched at all 60 harmonics, the tone-to-noise ratio change
is ×1.14 at 5.45 and ×0.86 at 7.45 — and **the 7.45 result reverses sign** against v1.

**What replaces it**, needing no discriminator at all:

| boundary | ch1111 tone | ch1112 tone | monitors disagree by |
| --- | --- | --- | --- |
| 5.4 → 5.5 Hz | ×1.73 | ×1.10 | **×1.58** |
| 7.4 → 7.5 Hz | ×0.66 | ×3.11 | **×4.7** |

Two independent monitors of the same drive disagree by factors of 1.6 and 4.7, so |H| referenced to
ch1111 is **reference-dependent** across those boundaries and any mode adjacent to them is
unreliable. Instrument versus physics is **not established by this pilot**.

**The mode decisions are unchanged**, because they never rested on the withdrawn argument: 5.494 Hz
is withdrawn because **0 of 52 channels** show a local |H| maximum there, and 7.46 Hz is demoted on
the monitor disagreement plus its 4-of-52 peak support.

**If you drafted from v1**, change any sentence containing "gain change", "instrumental", or
"drive-point resonance" about these two boundaries. The safe phrasing is *"the two drive monitors
disagree by a factor of 1.6 (5.45 Hz) and 4.7 (7.45 Hz), so the transfer function there is
reference-dependent and modes adjacent to those boundaries are not reliable."*

**And this is now the most useful process result in the package.** The claim had a plausible
mechanism, a clean number and a confident write-up. It passed the critic, passed reconciliation,
and shipped in v1. **No node caught it**, because the graph has no node whose job is to audit a
mechanism the orchestrator proposes *after* the critic has run. If the proposal says the graph
catches errors, this is the honest counterweight: **it catches the ones it is pointed at.**

Files touched: `PROCESS_REPORT.md` §3.2 (rewritten) and §2 (new case), `comparison.csv` (two rows
marked RETRACTED in place), `CLAIMS.md` (do-not-claim entry rewritten, new "undetermined" row, new
lead anecdote), `errors.csv` (row E053).

---

## 2. Figure panel (b) redesigned

v1's right-hand panel carried mode *provenance* in its legend — "mode, accepted", "of which
verifier only", "tentative", "withdrawn". Four entries, and the second was undecodable without the
report. Which node found a mode is a **process** fact; it belongs in panel (a) and in
`modes_reconciled.csv`, not in the physics panel.

v2 panel (b) shows the physics and nothing else: median |H| over the 52 bolometers, the 16–84%
spread across channels, the 11 accepted modes as a marker row, the two reference-unreliable bands,
and the strongest feature called out (3.40 Hz, strongest on 42 of 52). Three legend entries, all
self-explanatory.

Panel (a) is unchanged in design and now shows 53 errors.

---

## 3. Ledger: 52 → 53 rows

One new entry, **E053** above. Attribution counts move to: orchestrator 32, analyst 6, verifier 5,
critic 5, **Vivek 5**. "Caught by someone other than the node that erred" goes from 20 to 21 of 53.
Orchestrator-origin errors: 31 of 53.

---

## 4. A v1 copy taken from git was missing its recordings

The repository's ignore rule was `recordings/` with no leading slash, which git matches at **any**
depth — so it also caught `handoff/recordings/`. The v1 package **as committed** therefore had its
seven recording files silently absent, while the v1 *tarball* (built with `tar`, which ignores git)
was complete.

Fixed by anchoring the pattern. If you took v1 from the repository rather than from the archive,
you were missing the five cut recordings; they are present in v2.

---

## 5. Unchanged

- Every physics number other than the two boundary rows.
- The eleven headline modes, the two tentative and the two withdrawn.
- Damping: 7 of 11 measured, 5 cross-checking within 1.8 σ, 4 non-detections.
- Causality: inconclusive per cell.
- The redaction: `errors.csv` and `DEMO_NOTES.md` still describe the two credential exposures
  without naming the files they sit in. All rows intact.
- `SUMMARY.md`, `TIMELINE.md`, `fig_timeline.pdf`, `modes_reconciled.csv`, the recordings.

## Not in this package, deliberately

A live API token was found in the environment during the pilot and is being rotated separately. It
is recorded in the ledger by description only, no value, and the handling is a security matter for
Vivek rather than grant content. Nothing in this package depends on it.
