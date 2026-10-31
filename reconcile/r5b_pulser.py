#!/usr/bin/env python3
"""R5b: pulse shape on quiet data, done properly.

r5_pulser.py gave a monotonic ramp with no feature at t = 0. That was bolometer baseline DRIFT, not a
pulse: the per-segment median baseline leaves a low-frequency wander that the pre-pulse sigma
underestimates, and a 14 s window also folds in the next pulse 10 s later. Fixed here by
  (a) a window shorter than the 10 s pulse period,
  (b) a per-segment LINEAR detrend fitted on pre-pulse and far-post samples,
  (c) a CONTROL stack at deliberately wrong phase (pulse times + 5 s), which is the null: any feature
      that appears in the control is drift or 0.1 Hz-comb structure, not the pulse.
"""
import json
import numpy as np

FS = 1000.0
PRE, POST = 2.0, 7.5
meta = json.load(open("data/meta.json"))
tp = np.load("data/pulser_times.npy")
BOLO = [f"ch{c:04d}" for c in range(937, 989)]
n = int((PRE + POST) * FS)
t = np.arange(n) / FS - PRE
FIT = ((t >= -2.0) & (t <= -0.3)) | ((t >= 6.0) & (t <= 7.5))
V = np.vander(t, 2)                                        # linear detrend basis


def stack(label, a, b, times):
    acc = np.zeros(n); nch = 0
    for name in BOLO:
        x = np.load(f"data/arrays/{label}/bolo/{name}.npy", mmap_mode="r")
        st = np.zeros(n); m = 0
        for tt in times:
            i = int(round((tt - a - PRE) * FS))
            if i < 0 or i + n > len(x):
                continue
            s = np.asarray(x[i:i + n], dtype=np.float64)
            c, *_ = np.linalg.lstsq(V[FIT], s[FIT], rcond=None)
            st += s - V @ c
            m += 1
        if m:
            acc += st / m; nch += 1
    return acc / nch, m, nch


for label in ("quiet1", "quiet2", "quiet3"):
    w = meta["windows"][label]
    a, b = w["t0_s"], w["t1_s"]
    sel = tp[(tp > a + PRE) & (tp < b - POST)]
    sig_s, m, nch = stack(label, a, b, sel)
    ctl = sel + 5.0
    ctl = ctl[(ctl > a + PRE) & (ctl < b - POST)]
    ctl_s, mc, _ = stack(label, a, b, ctl)
    rms_pre = sig_s[t < -0.3].std()
    print(f"\n=== {label}: {m} pulses x {nch} bolometers   (control {mc} at +5 s phase)")
    print(f"    {'band [s]':>14s} {'ON-PULSE mean':>14s} {'CONTROL mean':>13s}"
          f" {'ON rms':>9s} {'CTL rms':>9s}")
    for lo, hi in ((-2, -0.3), (0, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 1.1),
                   (1.1, 2.0), (2.0, 4.2), (4.2, 6.0)):
        mm = (t >= lo) & (t < hi)
        print(f"    {lo:+6.2f}{hi:+7.2f} {sig_s[mm].mean():+14.5f} {ctl_s[mm].mean():+13.5f}"
              f" {sig_s[mm].std():9.5f} {ctl_s[mm].std():9.5f}")
    pk = int(np.argmax(np.abs(sig_s[(t > -0.3) & (t < 6)]))) + int(1700)
    print(f"    largest |stack| in -0.3..6 s: {sig_s[pk]:+.4f} mV at t = {t[pk]:+.3f} s;"
          f" pre-pulse rms {rms_pre:.4f} mV; control rms {ctl_s[(t>-0.3)&(t<6)].std():.4f} mV")
    np.save(f"reconcile/r5b_{label}.npy", np.vstack([t, sig_s, ctl_s]))
