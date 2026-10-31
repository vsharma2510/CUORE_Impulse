#!/usr/bin/env python3
"""R1: do the 6 unmatched modes exist in the OTHER node's own |H|?

The critic established that the median-|H| maxima of both nodes include 6.2, 7.9 and 8.5 Hz, so the
disagreement is method, not data. This goes one level finer: for every unmatched mode, count how many
of the 52 bolometers show a 3-point local maximum of |H| at that frequency in EACH node's own data,
and require the peak to stand above its own standard error. That distinguishes "ERA missed a real
mode" (peak present in the analyst's own H on many channels) from "the |H| picker over-called"
(peak absent or within errors).
"""
import numpy as np

A = np.load("analysis/responses.npz", allow_pickle=True)
V = np.load("verify/responses.npz", allow_pickle=True)

fa, fv = A["f_drive_hz"], V["f_drive_hz"]
assert np.allclose(fa, fv, atol=2e-3), "frequency grids differ"
f = fa
ka = A["kind"] == "bolo"
kv = V["channel_kind"] == "bolo"
cha, chv = A["channel"][ka], V["channels"][kv]
assert list(cha) == list(chv), "channel order differs"

Ha, Hv = np.abs(A["H"][ka]), np.abs(V["H"][kv])
Sa, Sv = A["H_se_abs"][ka], V["H_se"][kv]
# verifier |H| is on a different absolute scale per the critic; peak finding is scale-free.

UNMATCHED = {6.2184: "V", 7.9209: "V", 8.5297: "V", 2.527: "A", 5.494: "A", 8.285: "A"}


def peak_count(H, S, f0, nsig=1.0):
    """channels with a 3-point local max at the grid point nearest f0, exceeding both neighbours
    by more than nsig combined standard errors."""
    i = int(np.argmin(np.abs(f - f0)))
    if i == 0 or i == len(f) - 1:
        return None, f[i]
    c, l, r = H[:, i], H[:, i - 1], H[:, i + 1]
    sc, sl, sr = S[:, i], S[:, i - 1], S[:, i + 1]
    ok = (c - l > nsig * np.hypot(sc, sl)) & (c - r > nsig * np.hypot(sc, sr))
    return int(ok.sum()), f[i]


print(f"{'mode':>8s} {'by':>3s} {'grid':>7s}  {'A peak/52':>9s} {'V peak/52':>9s}   verdict")
rows = []
for f0 in sorted(UNMATCHED):
    who = UNMATCHED[f0]
    na, g = peak_count(Ha, Sa, f0)
    nv, _ = peak_count(Hv, Sv, f0)
    other = na if who == "V" else nv
    if other is None:
        verdict = "AT THE BAND EDGE: no local maximum is definable at 2.50 Hz"
    elif other >= 11:
        verdict = "present in the other node's own |H|"
    else:
        verdict = "weak/absent in the other node's own |H|"
    sa = "edge" if na is None else f"{na:d}"
    sv = "edge" if nv is None else f"{nv:d}"
    print(f"{f0:8.4f} {who:>3s} {g:7.3f}  {sa:>9s} {sv:>9s}   {verdict}")
    rows.append((f0, who, g, na, nv))

print("\nreference: the same count for the 9 modes both nodes agree on")
for f0 in (3.021, 3.420, 3.962, 4.886, 5.349, 7.464, 8.099, 8.172, 8.794):
    na, g = peak_count(Ha, Sa, f0)
    nv, _ = peak_count(Hv, Sv, f0)
    print(f"{f0:8.4f} {'AV':>3s} {g:7.3f}  {na:9d} {nv:9d}")  # all nine are interior points

med_a, med_v = np.median(Ha, 0), np.median(Hv, 0)
print("\nmedian |H| around each unmatched mode (A then V, normalised to the mode's own value)")
for f0 in sorted(UNMATCHED):
    i = int(np.argmin(np.abs(f - f0)))
    s = slice(max(0, i - 2), i + 3)
    print(f"  {f0:7.4f}  f={np.round(f[s],2)}")
    print(f"           A={np.round(med_a[s]/med_a[i],3)}  V={np.round(med_v[s]/med_v[i],3)}")
