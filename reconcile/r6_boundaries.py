#!/usr/bin/env python3
"""R6: where is the step boundary really, and is any heater pulse visible at all?

(a) Boundaries. The nodes' step boundaries differ by a median 0.55 s and both sit ~6 s before
    data/steps.csv. Measured here from ch1111 itself: demodulate the force channel at f_k and at
    f_k+1 and take the boundary as the crossing of the two envelopes. That is independent of both
    nodes and of steps.csv.
(b) Pulser visibility. r5b found no pulse in any quiet stack. Checked once more without stacking:
    the largest excursion of a single bolometer in a +-0.5 s window around pulse times, against the
    same statistic at wrong phase.
"""
import json
import numpy as np

FS = 1000.0
OFF = 3990.0
A = np.load("analysis/responses.npz", allow_pickle=True)
V = np.load("verify/responses.npz", allow_pickle=True)
f = A["f_drive_hz"]
ta, tv = A["t_start_run_s"], V["step_t0_run_s"]
steps = [l.split(",") for l in open("data/steps.csv").read().splitlines() if l and l[0] != "#"]
hdr = steps[0]
ts_csv = np.array([float(r[hdr.index("t_start_s_run")]) for r in steps[1:]])

x = np.load("data/arrays/excitation/aux/ch1111.npy", mmap_mode="r")
t = np.arange(len(x)) / FS + OFF

W = 0.5                                   # +-0.5 s sliding envelope half-width
meas = np.full(len(f), np.nan)
for k in range(1, len(f)):
    lo, hi = ts_csv[k] - 12.0, ts_csv[k] + 12.0
    i0, i1 = int((lo - OFF) * FS), int((hi - OFF) * FS)
    if i0 < 0 or i1 > len(x):
        continue
    seg = np.asarray(x[i0:i1], dtype=np.float64); seg -= seg.mean()
    tt = t[i0:i1]
    nw = int(W * FS)
    env = {}
    for fd in (f[k - 1], f[k]):
        z = seg * np.exp(-2j * np.pi * fd * (tt - tt[0]))
        c = np.cumsum(np.r_[0, z])
        env[fd] = np.abs(c[nw:] - c[:-nw]) / nw           # boxcar lock-in magnitude
    tc = tt[nw // 2: nw // 2 + len(env[f[k - 1]])]
    d = env[f[k]] - env[f[k - 1]]
    s = np.where(np.diff(np.sign(d)) > 0)[0]
    if len(s):
        j = s[np.argmin(np.abs(tc[s] - ts_csv[k]))]
        meas[k] = tc[j]

ok = np.isfinite(meas)
print(f"measured {ok.sum()} of {len(f)-1} interior boundaries from ch1111 directly\n")
for name, arr in (("analyst  t_start", ta), ("verifier t_start", tv), ("steps.csv t_start", ts_csv)):
    d = (arr - meas)[ok]
    print(f"  {name:20s} minus measured:  median {np.median(d):+7.3f} s   "
          f"IQR {np.percentile(d,25):+.3f} to {np.percentile(d,75):+.3f}   "
          f"max |dev| {np.max(np.abs(d)):.3f} s")
print(f"\n  analyst minus verifier: median {np.median((ta-tv)[ok]):+.3f} s")

print("\n--- pulser visibility, single channel, no stacking ---")
meta = json.load(open("data/meta.json"))
tp = np.load("data/pulser_times.npy")
w = meta["windows"]["quiet3"]; a, b = w["t0_s"], w["t1_s"]
sel = tp[(tp > a + 2) & (tp < b - 8)]
for ch in (937, 962, 975, 988):
    y = np.load(f"data/arrays/quiet3/bolo/ch{ch:04d}.npy", mmap_mode="r")
    for tag, off in (("on-pulse", 0.0), ("control", 5.0)):
        pk = []
        for tt in sel[:40]:
            i = int((tt - a + off) * FS)
            s = np.asarray(y[i - 500:i + 500], dtype=np.float64)
            pk.append(np.abs(s - np.median(s)).max())
        print(f"  ch{ch}  {tag}: median peak excursion in +-0.5 s = {np.median(pk):7.3f} mV")
