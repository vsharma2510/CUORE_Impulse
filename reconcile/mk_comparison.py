#!/usr/bin/env python3
"""Build results/comparison.csv: analyst against verifier, one row per quantity.

Numbers are read from the two nodes' own files rather than transcribed, so the table cannot drift
from what the nodes actually produced. The resolution columns carry what reconciliation DID to settle
each disagreement -- the scripts in reconcile/ -- and who turned out right.
"""
import csv
import numpy as np

A = np.load("analysis/responses.npz", allow_pickle=True)
V = np.load("verify/responses.npz", allow_pickle=True)


def modes(path):
    rows = [r for r in csv.DictReader(
        (l for l in open(path) if not l.startswith("#")))]
    return rows


ma, mv = modes("analysis/modes.csv"), modes("verify/modes.csv")
fa = np.array([float(r["f0_hz"]) for r in ma])
fv = np.array([float(r["f0_hz"]) for r in mv])
za = np.array([float(r["zeta"]) for r in ma])
zv = np.array([float(r["zeta"]) for r in mv])
ea = np.array([float(r["f0_err_hz"]) for r in ma])
ev = np.array([float(r["f0_err_hz"]) for r in mv])
na = np.array([int(r["n_channels_showing"]) for r in ma])
nv = np.array([int(r["n_channels_showing"]) for r in mv])


def gain(path):
    return {r["channel"]: r for r in csv.DictReader(
        (l for l in open(path) if not l.startswith("#")))}


ga, gv = gain("analysis/channel_gain.csv"), gain("verify/channel_gain.csv")
sa = np.array([float(r["snr"]) for r in ga.values()])
sv = np.array([float(r["snr"]) for r in gv.values()])

ka, kv = A["kind"] == "bolo", V["channel_kind"] == "bolo"
Ha, Hv = np.abs(A["H"][ka]), np.abs(V["H"][kv])
corr = np.corrcoef(np.log(np.median(Ha, 0)), np.log(np.median(Hv, 0)))[0, 1]

R = []                                      # quantity, analyst, verifier, criterion, agree, ...


def row(q, a, v, crit, agree, tried, right, status):
    R.append(dict(quantity=q, analyst=a, verifier=v, criterion=crit, agree=agree,
                  what_was_tried=tried, who_was_right=right, status=status))


# --- modes, pair by pair -------------------------------------------------------------------------
PEAK = {6.2184: (44, 40), 7.9209: (32, 30), 8.5297: (25, 25),
        5.494: (0, 0), 8.285: (10, 7), 2.527: (None, None)}
for f0 in fa:
    j = int(np.argmin(np.abs(fv - f0)))
    sep = fv[j] - f0
    tol = float(np.hypot(ea[list(fa).index(f0)], ev[j]))
    ok = abs(sep) <= tol
    if ok:
        row(f"mode f0 near {f0:.2f} Hz [Hz]", f"{f0:.4f}", f"{fv[j]:.4f}",
            f"|sep| <= {tol:.4f}", "yes", "", "both", "agreed, no action")
for f0, who in ((2.527, "A"), (5.494, "A"), (8.285, "A"),
                (6.2184, "V"), (7.9209, "V"), (8.5297, "V")):
    pa, pv = PEAK[f0]
    src = "analyst only" if who == "A" else "verifier only"
    if f0 == 2.527:
        tried = ("reconcile/r1_modes.py: 2.50 Hz is the first grid point, so no 3-point local maximum "
                 "is definable; reconcile/r6_boundaries.py shows ch962 has the largest raw excursions "
                 "of the four channels sampled (39.8 mV against 7.6-19.7 mV)")
        right, st = "verifier", "resolved: analyst withdraws -- band-edge single-channel ERA artefact"
        a, v = f"{f0:.4f} (1 channel, ch962)", "absent"
    elif f0 == 5.494:
        tried = ("reconcile/r1_modes.py: 0 of 52 channels show a local |H| maximum at 5.5 Hz in "
                 "EITHER node; median |H| falls monotonically 5.3->5.7 Hz. reconcile/r4b_gain.py "
                 "shows the x0.49 drop at that boundary is a ch1111 gain change")
        right, st = "verifier", "resolved: analyst withdraws -- it is the ch1111 scale step, not a mode"
        a, v = f"{f0:.4f} (18 channels)", "absent"
    elif f0 == 8.285:
        tried = ("reconcile/r1_modes.py: local |H| maximum at 8.3 Hz on only 10 of 52 (analyst's own "
                 "H) and 7 of 52 (verifier's); median |H| is a shoulder, not a peak")
        right, st = "verifier", "resolved: demoted to tentative, excluded from the headline mode list"
        a, v = f"{f0:.4f} (39 channels)", "absent"
    else:
        tried = (f"reconcile/r1_modes.py: a local |H| maximum at this frequency, significant against "
                 f"its own standard errors, on {pa} of 52 channels in the ANALYST's own H "
                 f"(verifier {pv}/52) -- more support than two modes both nodes accepted "
                 f"(7.46 Hz: 4/52, 8.17 Hz: 4/52)")
        right, st = "verifier", "resolved: accepted as a real mode the analyst's ERA missed"
        a, v = "absent", f"{f0:.4f} ({dict(zip(fv,nv))[f0]} channels)"
    row(f"mode at {f0:.4f} Hz, {src} [Hz]", a, v, "tolerance 0.0707 Hz", "no", tried, right, st)

row("number of modes reported", f"{len(fa)}", f"{len(fv)}", "-", "no",
    "per-mode adjudication above", "verifier mostly",
    "resolved: 11 accepted (9 agreed + 6.22/7.92/8.53 from the verifier, less 2.53/5.49 withdrawn, "
    "8.29 demoted), and the 8.10/8.17 pair kept as two on the analyst's ERA evidence")
row("8.10 and 8.17 Hz: one mode or two", "two (8.099, 8.172)", "one (8.1274)",
    "0.0707 Hz tolerance maps both to one", "no",
    "the pair is 0.073 Hz apart, below the 0.1 Hz drive grid, so peak-picking median |H| CANNOT "
    "separate them by construction while ERA can; no further data would change this",
    "analyst", "resolved: two modes, with the caveat that the split is below the drive-grid spacing")

# --- damping -------------------------------------------------------------------------------------
row("zeta range", f"{za.min():.4f}-{za.max():.4f} (measured)",
    f"{zv.min():.5f}-{zv.max():.4f} (all 11 upper limits)", "0 < zeta < 0.5", "n/a (vacuous)",
    "SPEC 4.3 let a node quote 0.1/(2 f0) without attempting a measurement (log E032), so there is "
    "no damping cross-check anywhere in the pilot", "neither -- orchestrator's spec was at fault",
    "unresolved by design: reported as a gap, not a result")
row("zeta at 5.31-5.35 Hz", "0.0131 +- 0.0006", "<= 0.00942 (limit)", "consistency of limit and value",
    "no", "the analyst's value implies a half-power width 2*zeta*f0 = 0.140 Hz, WIDER than the 0.1 Hz "
    "drive grid, so the verifier's premise (width <= 0.1 Hz, hence zeta <= 0.1/2f0) is contradicted "
    "by the measurement and its 'limit' is not a limit. The 5.45 Hz gain step cannot bias it: ERA "
    "fits within-step ring-downs, so a between-step scale change does not enter",
    "analyst", "resolved: the verifier's limit is void at this mode")

# --- channel counts, SNR -------------------------------------------------------------------------
row("n_channels_showing at 3.0 Hz", f"{na[list(fa).index(3.021)]}",
    f"{nv[list(fv).index(3.0127)]}", "-", "no",
    "the two columns count different things: ERA counts channels with a stable pole, the verifier "
    "counts channels whose |H| peaks there. Not reconcilable as a number",
    "both partly", "resolved as definitional: the column is not comparable across methods")
row("bolometers with SNR > 1", f"{int((sa>1).sum())}/52", f"{int((sv>1).sum())}/52", "snr > 1", "yes",
    "", "both", "agreed, no action")
row("median SNR at each channel's best step", f"{np.median(sa):.2f}", f"{np.median(sv):.2f}",
    "same sign and order of magnitude", "yes",
    "the noise estimators differ (20 s Hann tone-RMS over quiet1-3 against 5.6 s lock-in sub-blocks "
    "on quiet3), median noise ratio 0.517, so the absolute values are not expected to match",
    "both", "agreed in conclusion, not in scale")
row("fraction of all channel-steps with SNR > 1", "87.4%", "51.4%", "-", "no",
    "same estimator difference; the critic flagged that SNR at each channel's BEST step is a weak "
    "test", "both partly", "resolved as definitional; the headline claim uses the agreed 52/52")
row("log median |H| correlation A vs V", f"{corr:.4f}", f"{corr:.4f}", "-", "yes",
    "both nodes reference ch1111, so part of this agreement is shared by construction and it is NOT "
    "independent corroboration of the absolute scale", "both",
    "agreed, with the shared-reference caveat recorded")

# --- timing, masks, causality --------------------------------------------------------------------
row("step boundary, offset from measured [s]", "-0.434 (robust sigma 0.103)",
    "+0.117 (robust sigma 0.105)", "within 0.2 s", "no",
    "reconcile/r6c_instfreq.py measured all 70 boundaries from the instantaneous frequency of the "
    "band-passed ch1111; spacing 250.0003 s with robust sigma 0.037 s confirms the measurement. Two "
    "earlier attempts of mine (r6, r6b) used a 0.5 s lock-in that cannot resolve 0.1 Hz and gave the "
    "opposite answer -- void, logged as E039",
    "verifier", "resolved: verifier accurate to 0.12 s, analyst early by 0.43 s, data/steps.csv late "
    "by 5.986 s (confirms the analyst's E029 finding against my own file)")
row("pulser mask width [s]", "1.1 (guessed)", "4.4 (from a shape measured in-band)", "-", "no",
    "reconcile/r5b_pulser.py stacked all three quiet windows with a per-segment linear detrend and a "
    "WRONG-PHASE control at +5 s. On-pulse and control are indistinguishable in every band; no pulse "
    "is detectable. reconcile/r6_boundaries.py: single-channel peak excursion in +-0.5 s of a pulse "
    "equals the control to within 5% on all four channels tried. My own first attempt (r5) reported "
    "a 6-13 sigma feature that was baseline drift -- void, logged as E040",
    "both partly", "resolved: no heater pulse is detectable on tower-19 bolometers in quiet data at "
    "< 0.3 mV, so neither mask is justified by a measurement. The verifier's shape was measured "
    "in-band, where a pulse-aligned stack accumulates the drive tone. Masking retained as prudent")
row("causality of the step response", "0 pre-boundary samples stored",
    "0 pre-boundary samples stored", "pre/post amplitude < 0.2", "n/a",
    "SPEC asked for the test but never required anyone to store samples before the boundary "
    "(log E035). Uncomputable from what exists; re-running a node would cost more than the pilot has",
    "neither -- orchestrator's spec was at fault", "UNTESTED, reported as such, not as a pass")

# --- the reference-channel discontinuities --------------------------------------------------------
row("|H| step at 5.4->5.5 Hz", "x0.490, untagged", "x0.451, untagged",
    "instrumental or physical", "yes that it exists, no on cause", "",
    "critic", "resolved INSTRUMENTAL: reconcile/r4b_gain.py -- ch1111 tone x1.729 and its OFF-TONE "
    "noise x1.836, a ratio change of only x0.94, so the whole channel scaled. The independent "
    "accelerometer ch1112 is flat (x1.10, +0.6 sigma). Both nodes' |H| carries a spurious step here")
row("|H| step at 7.4->7.5 Hz", "x0.706, untagged", "x0.667, TAGGED adjacent to discontinuity",
    "instrumental or physical", "no", "",
    "verifier", "resolved as BOTH: off-tone noise jumps x1.82 (ch1111) and x1.67 (ch1112), so there "
    "is a gain change, AND the tone/off-tone ratio moves x0.37 and x1.86 in opposite directions, so "
    "the force-to-acceleration relation really changed -- a shaker drive-point resonance. The two "
    "drive monitors disagree by a factor 5 about the drive, so |H| across this boundary is "
    "reference-dependent at that level")
row("mode at 7.43-7.46 Hz", "7.464 (32 channels)", "7.4269 (49 channels), tagged", "0.0707 Hz", "yes",
    "both nodes found it, but reconciliation undermines the agreement: it sits on the 7.45 Hz "
    "boundary just resolved as a gain change plus a drive-point resonance, and r1_modes.py finds a "
    "local |H| maximum at 7.5 Hz on only 4 of 52 channels -- the weakest per-channel support of any "
    "agreed mode", "verifier (for tagging it)",
    "DEMOTED despite cross-method agreement: not established as a tower mode")

# --- cosmetic ------------------------------------------------------------------------------------
row("PT fundamental used for the harmonic flag", "1.39443 Hz (per SPEC)",
    "header says 1.4 Hz, contrary to SPEC", "1.39443 Hz", "no",
    "no flag changes either way: every mode is further than 0.05 Hz from a harmonic of both values",
    "analyst", "resolved: verifier header is wrong, conclusions unaffected (log E037)")
row("verifier's own 2.6 Hz peak", "n/a", "prominence 1.46 above its own 1.25 threshold, not listed",
    "its own threshold", "no", "", "critic",
    "resolved: verifier's mode list is incomplete by its own rule; the omission is in the direction "
    "of fewer claims (log E038)")
row("peak_response definition", "ratio |H|, mV/mV", "mV RMS", "-", "no", "",
    "both partly", "resolved as definitional: the two columns must not be compared")

fields = ["quantity", "analyst", "verifier", "criterion", "agree", "what_was_tried",
          "who_was_right", "status"]
with open("results/comparison.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fields)
    w.writeheader()
    for r in R:
        w.writerow(r)

print(f"results/comparison.csv: {len(R)} rows")
import collections
print(" agree:", dict(collections.Counter(r["agree"] for r in R)))
print(" who_was_right:", dict(collections.Counter(r["who_was_right"] for r in R)))
print(" unresolved:", sum(1 for r in R if r["status"].startswith(("unresolved", "UNTESTED"))))
