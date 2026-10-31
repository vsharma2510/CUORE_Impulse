#!/usr/bin/env python3
"""Re-check r4b. Its "off-tone" band was 0.5-100 Hz with only the drive and its 2nd and 3rd
harmonics removed, so every harmonic from the 4th up stayed IN the off-tone sum. Those scale with
the drive, which makes off-tone partly track the tone BY CONSTRUCTION -- the exact agreement r4b
read as evidence of a gain change.

Redone here with a genuinely drive-free estimator: a fixed 30-45 Hz band with +-0.3 Hz notches at
every harmonic of the drive, so nothing that scales with the drive can enter.
"""
import numpy as np
from numpy.fft import rfft, rfftfreq

FS, OFF = 1000.0, 3990.0
A = np.load("analysis/responses.npz", allow_pickle=True)
f, t0, t1 = A["f_drive_hz"], A["t_start_run_s"], A["t_end_run_s"]
out = {}
for ch in (1111, 1112):
    x = np.load(f"data/arrays/excitation/aux/ch{ch:04d}.npy", mmap_mode="r")
    tone = np.empty(len(f)); clean = np.empty(len(f))
    for k in range(len(f)):
        a, b = int((t0[k] - OFF) * FS), int((t1[k] - OFF) * FS)
        seg = np.asarray(x[a + 5000:b - 5000], dtype=np.float64)   # drop 5 s at each end
        seg = seg[:int(len(seg) // FS) * int(FS)]
        seg -= seg.mean()
        p = 2 * np.abs(rfft(seg) / len(seg)) ** 2
        fr = rfftfreq(len(seg), 1 / FS)
        harm = np.zeros_like(fr, dtype=bool)
        for h in range(1, 61):
            harm |= np.abs(fr - h * f[k]) < 0.30
        tone[k] = np.sqrt(p[np.abs(fr - f[k]) < 0.05].sum())
        band = (fr > 30.0) & (fr < 45.0) & ~harm                   # drive-free by construction
        clean[k] = np.sqrt(p[band].sum())
    out[ch] = (tone, clean)

print(f"{'':14s} {'tone x':>8s} {'clean-band x':>13s} {'ratio x':>8s}")
for fb in (5.4, 7.4):
    i = int(np.argmin(np.abs(f - fb)))
    print(f"\n=== {f[i]:.2f} -> {f[i+1]:.2f} Hz")
    for ch in (1111, 1112):
        t_, c_ = out[ch]
        rt, rc = t_[i + 1] / t_[i], c_[i + 1] / c_[i]
        print(f"  ch{ch:<10d} {rt:8.3f} {rc:13.3f} {rt/rc:8.3f}")
for ch in (1111, 1112):
    t_, c_ = out[ch]
    lc = np.log(c_[1:] / c_[:-1])
    s = 1.4826 * np.median(np.abs(lc - np.median(lc)))
    n5 = int((np.abs(lc) > 5 * s).sum())
    i54, i74 = int(np.argmin(np.abs(f - 5.4))), int(np.argmin(np.abs(f - 7.4)))
    print(f"\nch{ch} drive-free 30-45 Hz band: robust sigma of log step ratio {s:.3f}; "
          f"boundaries beyond 5 sigma: {n5} of 70")
    print(f"   5.45 boundary {lc[i54]/s:+6.1f} sigma    7.45 boundary {lc[i74]/s:+6.1f} sigma")
