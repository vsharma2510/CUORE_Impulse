#!/usr/bin/env python3
"""Build results/modes_reconciled.csv -- the adjudicated mode list, after the stop-point-4 gate.

Status is set by reconciliation and approved by Vivek at the gate: 11 headline, 2 tentative,
2 withdrawn. Frequencies and damping come from whichever node measured them; nothing is re-fitted
here, so every number traces to a node file.
"""
import csv
import numpy as np


def modes(p):
    return list(csv.DictReader(l for l in open(p) if not l.startswith("#")))


ma, mv = modes("analysis/modes.csv"), modes("verify/modes.csv")
A = {float(r["f0_hz"]): r for r in ma}
V = {float(r["f0_hz"]): r for r in mv}

PEAK = {3.021: (33, 30), 3.420: (47, 47), 3.962: (48, 46), 4.886: (40, 40), 5.349: (16, 14),
        6.2184: (44, 40), 7.464: (4, 3), 7.9209: (32, 30), 8.099: (37, 35), 8.172: (4, 4),
        8.285: (10, 7), 8.5297: (25, 25), 8.794: (45, 43), 2.527: (None, None), 5.494: (0, 0)}

# (f_analyst, f_verifier, status, found_by, note)
TAB = [
    (3.021,  3.0127, "headline",  "both",     "n_channels_showing differs by method (11 vs 34); not comparable"),
    (3.420,  3.4075, "headline",  "both",     "strongest mode: peak response for 42 (A) and 46 (V) of 52 channels; inside the collaboration's 3.35-3.55 Hz hunt"),
    (3.962,  3.9707, "headline",  "both",     ""),
    (4.886,  4.8990, "headline",  "both",     ""),
    (5.349,  5.3060, "headline",  "both",     "zeta 0.0131 +- 0.0006 implies a half-power width of 0.140 Hz, wider than the 0.1 Hz drive grid, so the verifier's upper limit is void here"),
    (None,   6.2184, "headline",  "verifier", "the analyst's ERA missed it: a significant local |H| maximum sits here on 44 of 52 channels in the ANALYST's own transfer functions (E042)"),
    (None,   7.9209, "headline",  "verifier", "as 6.2184 Hz: present on 32 of 52 channels in the analyst's own H (E042)"),
    (8.099,  8.1274, "headline",  "both",     "the 8.099/8.172 split is 0.073 Hz, below the 0.1 Hz drive grid, so median-|H| peak-picking cannot separate the pair by construction while ERA can"),
    (8.172,  8.1274, "headline",  "analyst",  "second pole of the pair above; inside the collaboration's 8.0-9.0 Hz hunt"),
    (None,   8.5297, "headline",  "verifier", "as 6.2184 Hz: present on 25 of 52 channels in the analyst's own H (E042)"),
    (8.794,  8.7834, "headline",  "both",     "inside the collaboration's 8.0-9.0 Hz hunt"),
    (7.464,  7.4269, "tentative", "both",     "DEMOTED despite cross-method agreement at 0.037 Hz: sits on the 7.45 Hz boundary, where ch1111 and ch1112 off-tone noise jump x1.82 and x1.67 (a gain change) AND their tone/off-tone ratios move x0.37 and x1.86 in opposite directions (a real drive-point resonance). The two drive monitors disagree by a factor 5 about the drive, and per-channel support is 4 of 52, the weakest of any agreed mode (E043)"),
    (8.285,  None,   "tentative", "analyst",  "a local |H| maximum on only 10 of 52 channels in the analyst's own H and 7 of 52 in the verifier's; median |H| is a shoulder, not a peak (E041)"),
    (5.494,  None,   "withdrawn", "analyst",  "no local |H| maximum on ANY of the 52 channels in either node's data; median |H| falls monotonically through it. It is the ch1111 gain step: off-tone noise x1.836 tracks the tone x1.729 while the independent accelerometer ch1112 is flat (E036, E041)"),
    (2.527,  None,   "withdrawn", "analyst",  "one channel only (ch962, the noisiest of the four sampled, 39.8 mV peak excursions against 7.6-19.7) and on the first grid point, 2.50 Hz, where no local maximum is definable (E041)"),
]

PT = 1.39443
rows = []
for fa, fv, status, by, note in TAB:
    a = A.get(fa) if fa else None
    v = V.get(fv) if fv else None
    f0 = float(a["f0_hz"]) if a else float(v["f0_hz"])
    pk = PEAK.get(fa if fa else fv, (None, None))
    k = int(round(f0 / PT))
    rows.append(dict(
        f0_hz=f"{f0:.4f}",
        f0_err_hz=f"{float((a or v)['f0_err_hz']):.3f}",
        status=status,
        found_by=by,
        f0_analyst_hz=f"{fa:.4f}" if fa else "",
        f0_verifier_hz=f"{fv:.4f}" if fv else "",
        separation_hz=f"{fv-fa:+.4f}" if (fa and fv) else "",
        zeta=a["zeta"] if a and a["zeta_is_upper_limit"] == "false" else "",
        zeta_err=a["zeta_err"] if a and a["zeta_is_upper_limit"] == "false" else "",
        zeta_upper_limit=(a["zeta"] if a and a["zeta_is_upper_limit"] == "true"
                          else (v["zeta"] if v else "")),
        n_channels_peak_analyst="" if pk[0] is None else pk[0],
        n_channels_peak_verifier="" if pk[1] is None else pk[1],
        dist_to_pt_harmonic_hz=f"{abs(f0 - k*PT):.4f}",
        pt_harmonic_flag="false",
        note=note))

flds = list(rows[0])
with open("results/modes_reconciled.csv", "w", newline="\n") as fh:
    w = csv.DictWriter(fh, flds); w.writeheader(); w.writerows(rows)

import collections
print("results/modes_reconciled.csv:", len(rows), "rows")
print(" ", dict(collections.Counter(r["status"] for r in rows)))
print(f"\n  {'f0':>8s} {'status':>10s} {'by':>9s}  {'A':>7s} {'V':>7s} {'sep':>8s} {'zeta':>8s} "
      f"{'A pk':>5s} {'V pk':>5s} {'dPT':>7s}")
for r in rows:
    print(f"  {r['f0_hz']:>8s} {r['status']:>10s} {r['found_by']:>9s}  {r['f0_analyst_hz']:>7s} "
          f"{r['f0_verifier_hz']:>7s} {r['separation_hz']:>8s} {r['zeta']:>8s} "
          f"{str(r['n_channels_peak_analyst']):>5s} {str(r['n_channels_peak_verifier']):>5s} "
          f"{r['dist_to_pt_harmonic_hz']:>7s}")
print(f"\n  smallest distance to a {PT} Hz harmonic among the 11 headline modes: "
      f"{min(float(r['dist_to_pt_harmonic_hz']) for r in rows if r['status']=='headline'):.4f} Hz "
      f"(flag limit 0.05) -> no headline mode is a pulse-tube line")
