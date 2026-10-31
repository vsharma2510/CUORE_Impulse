#!/usr/bin/env python3
"""Is the orchestrator's boundary estimator biased? The analyst says yes, by 0.37 s.

r6c_instfreq.py (orchestrator) puts the boundaries at steps.csv - 5.986 s, robust sigma 0.127.
The analyst, re-dispatched for causality, measured them independently with a two-segment sinusoid
changepoint scan and got steps.csv - 6.356 s, robust sigma 0.147. Its first-run threshold method had
given - 6.420 s. So the analyst's TWO independent methods agree to 0.064 s and both disagree with the
orchestrator's single method by about 0.4 s. That asymmetry suggests the orchestrator is the outlier.

Settled the only way it can be settled quickly: run the orchestrator's estimator on synthetic data
with a boundary at a KNOWN time, at the same frequencies, sample rate and SNR as the real thing.
"""
import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt

FS = 1000.0
rng = np.random.default_rng(0)
sos = butter(4, [2.0, 10.0], btype="band", fs=FS, output="sos")


def orchestrator_estimator(seg, t, f_old, f_new, t_guess):
    """Exactly the r6c method: unwrap the analytic phase, differentiate, 1 s moving average,
    take the crossing of the midpoint frequency."""
    ph = np.unwrap(np.angle(hilbert(sosfiltfilt(sos, seg))))
    fi = np.gradient(ph) * FS / (2 * np.pi)
    n = int(1.0 * FS)
    c = np.cumsum(np.r_[0, fi]); fi = (c[n:] - c[:-n]) / n
    tt = t[:len(fi)] + n / (2 * FS)
    mid = 0.5 * (f_old + f_new)
    s = np.where(np.diff(np.sign(fi - mid)))[0]
    if not len(s):
        return np.nan
    j = s[np.argmin(np.abs(tt[s] - t_guess))]
    return tt[j] + (mid - fi[j]) / (fi[j + 1] - fi[j]) / FS


print(f"{'f_old':>6s} {'f_new':>6s} {'SNR':>6s} {'bias [s]':>10s} {'scatter [s]':>12s}")
allb = []
for f_old, f_new in ((3.4, 3.5), (4.4, 4.5), (6.2, 6.3), (8.1, 8.2)):
    for snr in (50.0, 10.0):
        errs = []
        for trial in range(12):
            T0 = 40.0                                   # true boundary, seconds into the segment
            t = np.arange(int(80 * FS)) / FS
            ph = np.where(t < T0, 2 * np.pi * f_old * t,
                          2 * np.pi * f_old * T0 + 2 * np.pi * f_new * (t - T0))
            x = np.cos(ph + rng.uniform(0, 2 * np.pi))
            x += rng.normal(0, 1 / snr, x.size)
            est = orchestrator_estimator(x, t, f_old, f_new, T0)
            errs.append(est - T0)
        e = np.array(errs)
        allb.append(np.median(e))
        print(f"{f_old:6.1f} {f_new:6.1f} {snr:6.0f} {np.median(e):+10.3f} {e.std():12.3f}")

b = float(np.median(allb))
print(f"\nmedian bias of the orchestrator's estimator on synthetic data: {b:+.3f} s")
print(f"orchestrator measured boundaries at steps.csv - 5.986 s")
print(f"bias-corrected                     steps.csv - {5.986 + b:.3f} s")
print(f"analyst changepoint scan           steps.csv - 6.356 s  (its threshold method: - 6.420 s)")
print(f"\nresidual orchestrator-minus-analyst after correction: {6.356 - (5.986 + b):+.3f} s")
