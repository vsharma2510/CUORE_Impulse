#!/usr/bin/env python3
"""R6b: is the measured boundary self-consistent, and who is right about the 6 s offset?

E029 recorded the analyst's finding that data/steps.csv t_start was LATE by 6.34 s, and both nodes
shifted their boundaries earlier by about that much. r6 now measures the boundary directly from the
force channel and gets the opposite: steps.csv is right and both nodes are ~6 s EARLY. One of the two
is wrong, so test the measurement internally -- true boundaries are exactly 250 s apart -- and show
the force envelope around one boundary so the answer is visible rather than asserted.
"""
import numpy as np

FS, OFF, W = 1000.0, 3990.0, 0.5
A = np.load("analysis/responses.npz", allow_pickle=True)
f = A["f_drive_hz"]
ta = A["t_start_run_s"]
rows = [l.split(",") for l in open("data/steps.csv").read().splitlines() if l and l[0] != "#"]
h = rows[0]; ts = np.array([float(r[h.index("t_start_s_run")]) for r in rows[1:]])
x = np.load("data/arrays/excitation/aux/ch1111.npy", mmap_mode="r")


def env(fd, i0, i1):
    seg = np.asarray(x[i0:i1], dtype=np.float64); seg -= seg.mean()
    tt = np.arange(i0, i1) / FS + OFF
    z = seg * np.exp(-2j * np.pi * fd * (tt - tt[0]))
    nw = int(W * FS)
    c = np.cumsum(np.r_[0, z])
    return tt[nw // 2: nw // 2 + len(c) - nw - 1], np.abs(c[nw:-1] - c[:-nw - 1]) / nw


meas = []
for k in range(1, len(f)):
    i0, i1 = int((ts[k] - 20 - OFF) * FS), int((ts[k] + 20 - OFF) * FS)
    if i0 < 0 or i1 > len(x):
        meas.append(np.nan); continue
    tc, e_old = env(f[k - 1], i0, i1)
    _, e_new = env(f[k], i0, i1)
    d = e_new - e_old
    s = np.where(np.diff(np.sign(d)) > 0)[0]
    meas.append(tc[s[np.argmin(np.abs(tc[s] - ts[k]))]] if len(s) else np.nan)
meas = np.array(meas)
good = np.isfinite(meas)
dd = np.diff(meas[good])
print(f"measured boundary spacing: median {np.median(dd):.4f} s, "
      f"fraction within 0.1 s of 250 s = {np.mean(np.abs(dd-250)<0.1):.2f}")
r = meas - ts[1:]
print(f"measured minus steps.csv: median {np.median(r[good]):+.4f} s, "
      f"fraction within 0.2 s = {np.mean(np.abs(r[good])<0.2):.2f}, "
      f"n outliers>1 s = {int(np.sum(np.abs(r[good])>1))}")
print(f"measured minus analyst  : median {np.median((meas-ta[1:])[good]):+.4f} s")

k = 20
i0, i1 = int((ts[k] - 12 - OFF) * FS), int((ts[k] + 12 - OFF) * FS)
tc, e_old = env(f[k - 1], i0, i1); _, e_new = env(f[k], i0, i1)
print(f"\nforce-channel lock-in envelope across the boundary at steps.csv t={ts[k]:.1f} s "
      f"({f[k-1]:.2f} -> {f[k]:.2f} Hz)")
print(f"  analyst puts this boundary at {ta[k]:.2f} s, i.e. {ta[k]-ts[k]:+.2f} s")
print(f"  {'t-ts [s]':>9s} {'|lock-in @ old f| ':>19s} {'|lock-in @ new f|':>18s}")
for off in (-8, -6.3, -4, -2, -1, -0.3, 0, +0.3, +1, +2, +4):
    j = int(np.argmin(np.abs(tc - (ts[k] + off))))
    print(f"  {off:+9.2f} {e_old[j]:19.2f} {e_new[j]:18.2f}")
