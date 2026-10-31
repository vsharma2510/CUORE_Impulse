#!/usr/bin/env python3
"""R5: how long is the heater pulse? Settles the analyst's 1.1 s mask against the verifier's 4.4 s.

Neither node measured the pulse on quiet data with the drive absent: the analyst guessed 1.1 s and saw
no pulse shape in its quiet stacks; the verifier measured a shape but inside the excitation window,
where the drive tone is present. This stacks the quiet windows, where there is no drive at all, so the
only coherent feature is the pulse itself.

Quiet windows (run coordinates): quiet1 0-250 s, quiet2 1275-1500 s, quiet3 48025-48800 s.
"""
import json
import numpy as np

FS = 1000.0
PRE, POST = 2.0, 12.0                 # stack window around each pulse, seconds
meta = json.load(open("data/meta.json"))
tp = np.load("data/pulser_times.npy")
BOLO = [f"ch{c:04d}" for c in range(937, 989)]

for label in ("quiet1", "quiet2", "quiet3"):
    w = meta["windows"][label]
    a, b = w["t0_s"], w["t1_s"]
    sel = tp[(tp > a + PRE) & (tp < b - POST)]
    n = int((PRE + POST) * FS)
    acc = np.zeros(n); nch = 0
    for name in BOLO:
        x = np.load(f"data/arrays/{label}/bolo/{name}.npy", mmap_mode="r")
        st = np.zeros(n); m = 0
        for t in sel:
            i = int(round((t - a - PRE) * FS))
            if i < 0 or i + n > len(x):
                continue
            s = np.asarray(x[i:i + n], dtype=np.float64)
            s -= np.median(s[:int(PRE * FS)])            # baseline from the pre-pulse samples
            st += s; m += 1
        if m:
            acc += st / m; nch += 1
    stack = acc / nch
    t = np.arange(n) / FS - PRE
    pre = stack[t < -0.2]
    sig = 1.4826 * np.median(np.abs(pre - np.median(pre)))
    pk = int(np.argmax(np.abs(stack)))
    amp = stack[pk]
    print(f"\n=== {label}: {len(sel)} pulses x {nch} bolometers")
    print(f"    pre-pulse noise of the stack {sig:.5f} mV; peak {amp:+.4f} mV at t = {t[pk]:+.3f} s"
          f"  ({abs(amp)/sig:.0f} sigma)")
    # last time the stack is still above a few sigma, searching backwards from the end
    thr = [3, 5, 10]
    for k in thr:
        above = np.where(np.abs(stack) > k * sig)[0]
        if len(above) == 0:
            print(f"    never exceeds {k} sigma")
            continue
        j = above[above >= pk]
        # the contiguous run that contains the peak
        last = pk
        while last + 1 < n and abs(stack[last + 1]) > k * sig:
            last += 1
        first = pk
        while first - 1 >= 0 and abs(stack[first - 1]) > k * sig:
            first -= 1
        print(f"    above {k:2d} sigma from t = {t[first]:+.3f} to {t[last]:+.3f} s"
              f"   (width {t[last]-t[first]:.3f} s)")
    for lo, hi in ((-2, -0.1), (0, 0.5), (0.5, 1.0), (1.0, 1.1), (1.1, 2.0),
                   (2.0, 4.2), (4.2, 6.0), (6.0, 10.0)):
        m = (t >= lo) & (t < hi)
        print(f"      {lo:+5.1f} to {hi:+5.1f} s   mean {stack[m].mean():+8.5f}"
              f"   rms {stack[m].std():8.5f} mV   = {stack[m].std()/sig:6.1f} x pre-pulse noise")
    np.save(f"reconcile/r5_stack_{label}.npy", np.vstack([t, stack]))
