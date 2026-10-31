# CUORE agent-graph pilot — handoff package

**Version 2 — 2026-10-31.** If you have seen v1, read `CHANGES.md` first: one physics conclusion
is withdrawn, and a v1 copy taken from the repository was missing its recordings.

Self-contained. Copy this directory into the grant-proposal session; nothing here points outside
it, and it contains no CUORE data, no internal paths and no credentials.

**Start with `CLAIMS.md`.** It is the only file written specifically for the proposal: every
defensible claim with its number and provenance, the results that are inconclusive and must be
presented as such, and a list of things that look attractive but are not supportable.

## What this was

A feasibility pilot run as a graph of agents on CUORE shaker data — run RUNA, tower 19,
52 bolometers, 2.50–9.50 Hz. Four nodes (orchestrator, analyst, blind verifier, physics critic)
plus human gates. **The process is the deliverable; the physics is secondary**, and both are
reported here.

12 h 11 m wall clock, 02:07 → 14:18 UTC on 2026-10-31.

## Files

| file | what it is | read if |
| --- | --- | --- |
| **`CLAIMS.md`** | claims, numbers, provenance, and what not to say | **always, first** |
| **`CHANGES.md`** | what moved between v1 and v2, and what to edit if you drafted from v1 | **first, if you saw v1** |
| `SUMMARY.md` | 150 words of physics | you need a paragraph |
| `PROCESS_REPORT.md` | the primary deliverable: how the graph was built and run, every disagreement and how it was settled, where a cheaper model sat safely, what I would change | you are writing the methodology section |
| `TIMELINE.md` | phase by phase with measured times and evidence pointers; states where the record is thin | a reviewer asks "show me" |
| `DEMO_NOTES.md` | the five recordings, what is in each, and the cut list | you are preparing a demo |
| `errors.csv` | the full 52-row ledger | you want to quote the error record |
| `comparison.csv` | 44 rows, analyst vs verifier per quantity, with the test that settled each | you want to quote a disagreement |
| `modes_reconciled.csv` | 15 modes: 11 headline, 2 tentative, 2 withdrawn, each with the test behind its status | you are quoting physics |
| `fig_pilot.pdf` | (a) error record by who caught it; (b) the transfer function with adjudicated modes | the figure for the proposal |
| `fig_timeline.pdf` | the graph as a swimlane over measured clock time | the backup figure |

`recordings/` holds the five cut session segments, 49.2 minutes total, playable with
`asciinema play recordings/<name>.cast`. They are omitted from the text-only archive; see
**Recordings** below.

## Three things to get right

**The nodes are not symmetric.** The verifier is a separate OS process whose allowed directories
exclude `analysis/` — isolation by construction, verified with a planted sentinel. The analyst is an
in-process subagent with full project access. The independence requirement is one-directional, but
the asymmetry is real and the report says so. Do not describe them as two equivalent sandboxes.

**The error ledger is not a list of the nodes' mistakes.** 30 of 52 were the orchestrator's own.
That is the finding: the graph's value was that someone could check the supervisor.

**Two results are honestly inconclusive** — causality, and damping on 4 of 11 modes. They are
reported as non-results on purpose, and the specification was amended mid-pilot so that a node
*could* report "I tried and could not" instead of filling the column. Presenting them as passes
would undo the most defensible thing in the package.

## Recordings

Five cut segments in `recordings/`, 3.5 MB, produced from the raw casts by `cast_cut.py`
(reconstructing screen state at each splice, since a terminal recording cannot be cut by dropping
events). Both the rendered text and the raw bytes of all five were swept for credentials, token
fragments and internal hostnames: clean.

One caveat for anyone searching them: the literal string `SENTINEL-7Q4X` appears in
`rec_01_graph.cast`. That is the isolation check printing its own needle, and the same recording
shows the search returning nothing. It is the test, not a breach.

## One difference from the repository copy

`errors.csv` and `DEMO_NOTES.md` here are **lightly redacted**: row E008 and the demo hygiene notes
describe two credential exposures found in the environment, and in this shareable copy they no
longer name the specific files the credentials live in. The finding, its category, who caught it and
how are unchanged, and all 52 rows are intact. The unredacted text stays in the project log. No
credential value appears in either copy.

## Provenance

Full append-only log, all node outputs, and every analysis script live in the project repository at
commit `cfc173f` and later, branch `master`, not pushed to any remote. This package is a copy of the
`results/` deliverables plus `CLAIMS.md`; nothing here was edited after being copied.
