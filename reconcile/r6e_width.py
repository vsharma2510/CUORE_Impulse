#!/usr/bin/env python3
"""Why the orchestrator and the analyst differ by 0.37 s on the step boundaries.

r6d showed the orchestrator's instantaneous-frequency estimator is unbiased on an IDEAL step
(+0.000 s, scatter 0.006-0.022 s). So the 0.37 s is not an estimator defect. The remaining
explanation is that the real transition is not a step but a ramp of finite width, in which case the
two nodes are measuring two different and equally valid definitions:

  orchestrator  -> the MIDPOINT of the frequency transition (where f crosses (f_old+f_new)/2)
  analyst       -> the ONSET, since a two-segment changepoint fit places the break where the first
                   segment stops describing the data

For a ramp of width W those differ by W/2. If W is about 0.74 s the whole disagreement is explained.
Measured here with light smoothing so the ramp is not itself smeared.
"""
import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt

FS, OFF = 1000.0, 3990.0
sos = butter(4, [2.0, 10.0], btype="band", fs=FS, output="sos")
A = np.load("analysis/responses.npz", allow_pickle=True)
f = A["f_drive_hz"]
rows = [l.split(",") for l in open("data/steps.csv").read().splitlines() if l and l[0] != "#"]
h = rows[0]; ts = np.array([float(r[h.index("t_start_s_run")]) for r in rows[1:]])
x = np.load("data/arrays/excitation/aux/ch1111.npy", mmap_mode="r")

widths, mids, onsets = [], [], []
for k in range(1, len(f), 7):                       # every 7th boundary, 10 of them
    i0 = int((ts[k] - 20 - OFF) * FS); i1 = int((ts[k] + 20 - OFF) * FS)
    if i0 < 0 or i1 > len(x):
        continue
    seg = np.asarray(x[i0:i1], dtype=np.float64); seg -= seg.mean()
    ph = np.unwrap(np.angle(hilbert(sosfiltfilt(sos, seg))))
    fi = np.gradient(ph) * FS / (2 * np.pi)
    n = int(0.15 * FS)                              # light 0.15 s smoothing, not 1.0 s
    c = np.cumsum(np.r_[0, fi]); fi = (c[n:] - c[:-n]) / n
    tt = (np.arange(len(fi)) + i0) / FS + OFF + n / (2 * FS)
    lo, hi = f[k - 1], f[k]
    m = (tt > ts[k] - 15) & (tt < ts[k] + 10)
    tt, fi = tt[m], fi[m]

    def cross(frac):
        lev = lo + frac * (hi - lo)
        s = np.where(np.diff(np.sign(fi - lev)))[0]
        if not len(s):
            return np.nan
        j = s[np.argmin(np.abs(tt[s] - (ts[k] - 6.2)))]
        return tt[j]

    t10, t50, t90 = cross(0.10), cross(0.50), cross(0.90)
    if not np.isfinite([t10, t50, t90]).all():
        continue
    widths.append(t90 - t10); mids.append(t50 - ts[k]); onsets.append(t10 - ts[k])

w = np.array(widths); mi = np.array(mids); on = np.array(onsets)
print(f"{len(w)} boundaries sampled")
print(f"  10-90% transition width : median {np.median(w):.3f} s   IQR "
      f"{np.percentile(w,25):.3f}-{np.percentile(w,75):.3f}")
print(f"  midpoint  vs steps.csv  : median {np.median(mi):+.3f} s   <- orchestrator's definition")
print(f"  10% onset vs steps.csv  : median {np.median(on):+.3f} s   <- closer to a changepoint fit")
print(f"\n  orchestrator (r6c, 1 s smoothing) : steps.csv - 5.986 s")
print(f"  analyst (changepoint scan)        : steps.csv - 6.356 s")
print(f"  difference to explain             : 0.370 s")
print(f"  half the measured transition width: {np.median(w)/2:.3f} s")
print(f"  midpoint minus onset, measured    : {np.median(mi - on):.3f} s")
