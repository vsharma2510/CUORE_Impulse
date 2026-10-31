#!/usr/bin/env python3
"""R6c: locate the step boundaries from the INSTANTANEOUS FREQUENCY of the force channel.

r6/r6b used a 0.5 s boxcar lock-in, which cannot separate 4.4 from 4.5 Hz: its frequency resolution
is ~2 Hz, so both envelopes were equal and the "crossing" was noise. That test is void.

The right tool needs no frequency resolution at all: unwrap the analytic phase of the band-passed
force channel and differentiate. The drive is a single strong tone (tone 600 mV against 50 mV
off-tone), so the instantaneous frequency is accurate to a few mHz over 1 s, and the boundary is where
it crosses the midpoint between the two step frequencies.
"""
import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt

FS, OFF = 1000.0, 3990.0
A = np.load("analysis/responses.npz", allow_pickle=True)
V = np.load("verify/responses.npz", allow_pickle=True)
f, ta, tv = A["f_drive_hz"], A["t_start_run_s"], V["step_t0_run_s"]
rows = [l.split(",") for l in open("data/steps.csv").read().splitlines() if l and l[0] != "#"]
h = rows[0]; ts = np.array([float(r[h.index("t_start_s_run")]) for r in rows[1:]])
x = np.load("data/arrays/excitation/aux/ch1111.npy", mmap_mode="r")
sos = butter(4, [2.0, 10.0], btype="band", fs=FS, output="sos")

PAD, HALF = 5.0, 20.0
meas = np.full(len(f), np.nan)
for k in range(1, len(f)):
    i0 = int((ts[k] - HALF - PAD - OFF) * FS); i1 = int((ts[k] + HALF + PAD - OFF) * FS)
    if i0 < 0 or i1 > len(x):
        continue
    seg = np.asarray(x[i0:i1], dtype=np.float64); seg -= seg.mean()
    ph = np.unwrap(np.angle(hilbert(sosfiltfilt(sos, seg))))
    fi = np.gradient(ph) * FS / (2 * np.pi)
    n = int(1.0 * FS)                                       # 1 s moving average
    c = np.cumsum(np.r_[0, fi]); fi = (c[n:] - c[:-n]) / n
    tt = (np.arange(len(fi)) + i0) / FS + OFF + n / (2 * FS)
    m = (tt > ts[k] - HALF) & (tt < ts[k] + HALF)
    tt, fi = tt[m], fi[m]
    mid = 0.5 * (f[k - 1] + f[k])
    s = np.where(np.diff(np.sign(fi - mid)))[0]
    if len(s):
        j = s[np.argmin(np.abs(tt[s] - ts[k]))]
        meas[k] = tt[j] + (mid - fi[j]) / (fi[j + 1] - fi[j]) / FS

g = np.isfinite(meas)
dd = np.diff(meas[g])
print(f"{g.sum()} of {len(f)-1} boundaries located")
print(f"spacing of consecutive measured boundaries: median {np.median(dd):.4f} s, "
      f"robust sigma {1.4826*np.median(np.abs(dd-np.median(dd))):.4f} s, "
      f"fraction within 0.1 s of 250 s {np.mean(np.abs(dd-250)<0.1):.2f}")
for name, arr in (("data/steps.csv", ts), ("analyst", ta), ("verifier", tv)):
    d = (arr - meas)[g]
    print(f"  {name:15s} minus measured: median {np.median(d):+7.3f} s   "
          f"robust sigma {1.4826*np.median(np.abs(d-np.median(d))):.3f} s   "
          f"max |dev| {np.max(np.abs(d)):6.3f} s")

k = 20
i0 = int((ts[k] - 25 - OFF) * FS); i1 = int((ts[k] + 25 - OFF) * FS)
seg = np.asarray(x[i0:i1], dtype=np.float64); seg -= seg.mean()
ph = np.unwrap(np.angle(hilbert(sosfiltfilt(sos, seg))))
fi = np.gradient(ph) * FS / (2 * np.pi)
n = int(FS); c = np.cumsum(np.r_[0, fi]); fi = (c[n:] - c[:-n]) / n
tt = (np.arange(len(fi)) + i0) / FS + OFF + n / (2 * FS)
print(f"\ninstantaneous drive frequency across the boundary steps.csv says is at {ts[k]:.1f} s")
print(f"  analyst {ta[k]-ts[k]:+.2f} s, verifier {tv[k]-ts[k]:+.2f} s, measured {meas[k]-ts[k]:+.3f} s")
for off in (-10, -8, -6.3, -4, -2, -0.5, 0, +0.5, +2, +4, +8):
    j = int(np.argmin(np.abs(tt - (ts[k] + off))))
    print(f"   t {off:+6.1f} s   f_inst {fi[j]:7.4f} Hz")
