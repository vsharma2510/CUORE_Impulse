#!/usr/bin/env python3
"""R4b: discriminate a DAQ range change from a physical drive-point impedance change.

At 5.45 Hz the force channel jumps x1.735 while the accelerometer is flat; at 7.45 Hz force falls
x0.672 while the accelerometer rises x3.18. Either could be a gain change OR a real change in the
shaker's drive-point impedance (at a drive-point resonance force falls and acceleration rises).

The discriminator: an amplifier or ADC range change is a pure multiplicative scale, so it scales the
channel's OFF-TONE noise by the same factor as the tone. A physical impedance change scales the tone
only. So compare, step by step, the tone RMS against the broadband RMS with the drive tone and its
first two harmonics notched out.
"""
import numpy as np
from numpy.fft import rfft, rfftfreq

FS = 1000.0
OFF = 3990.0                                  # arrays start at t = 3990 s of the run (meta.json)
A = np.load("analysis/responses.npz", allow_pickle=True)
f = A["f_drive_hz"]
t0, t1 = A["t_start_run_s"], A["t_end_run_s"]

out = {}
for ch in (1111, 1112):
    x = np.load(f"data/arrays/excitation/aux/ch{ch:04d}.npy", mmap_mode="r")
    tone = np.empty(len(f)); wide = np.empty(len(f))
    for k in range(len(f)):
        a = int((t0[k] - OFF) * FS); b = int((t1[k] - OFF) * FS)
        seg = np.asarray(x[a:b], dtype=np.float64)
        seg = seg[:int(len(seg) // FS) * int(FS)]          # whole seconds -> 1 Hz bin spacing
        seg -= seg.mean()
        X = rfft(seg) / len(seg)
        fr = rfftfreq(len(seg), 1 / FS)
        # tone RMS in a +-0.05 Hz band around the drive and its 2nd/3rd harmonics
        m = np.zeros_like(fr, dtype=bool)
        for h in (1, 2, 3):
            m |= np.abs(fr - h * f[k]) < 0.05
        p = 2 * np.abs(X) ** 2
        band = (fr > 0.5) & (fr < 100.0)
        tone[k] = np.sqrt(p[m & band].sum())
        wide[k] = np.sqrt(p[~m & band].sum())
    out[ch] = (tone, wide)
    print(f"ch{ch}: tone and off-tone RMS computed over {len(f)} steps")

for fb in (5.4, 7.4):
    i = int(np.argmin(np.abs(f - fb)))
    print(f"\n=== {f[i]:.2f} -> {f[i+1]:.2f} Hz")
    for ch in (1111, 1112):
        tone, wide = out[ch]
        print(f"  ch{ch}  tone     {tone[i]:9.3f} -> {tone[i+1]:9.3f}  x{tone[i+1]/tone[i]:.3f}")
        print(f"  ch{ch}  off-tone {wide[i]:9.3f} -> {wide[i+1]:9.3f}  x{wide[i+1]/wide[i]:.3f}")
    for ch in (1111, 1112):
        tone, wide = out[ch]
        r_t, r_w = tone[i + 1] / tone[i], wide[i + 1] / wide[i]
        rr = np.log(wide[1:] / wide[:-1])
        s = 1.4826 * np.median(np.abs(rr - np.median(rr)))
        verdict = ("GAIN CHANGE: off-tone tracks the tone" if abs(np.log(r_w / r_t)) < 0.25
                   else "NOT a gain change: off-tone does not track the tone")
        print(f"  ch{ch}  tone/off-tone ratio change x{r_t/r_w:.3f}"
              f"   off-tone jump {np.log(r_w)/s:+5.1f} sigma   -> {verdict}")

np.savez("reconcile/r4b_tone_offtone.npz", f=f, **{f"ch{c}_{n}": v
         for c, (t, w) in out.items() for n, v in (("tone", t), ("offtone", w))})
