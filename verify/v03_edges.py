#!/usr/bin/env python3
"""Is array t=0-25 s really shaker-off, and is there a shaker-off tail?
A 1 s window cannot resolve 2.4 from 2.5 Hz; use 18 s windows."""
import numpy as np
ARR = "<SCRATCH>/CUORE_ImpulsePilot_data"
FS, OFFS = 1000.0, 3990.0
ref = np.load(ARR + "/excitation/aux/ch1111.npy", mmap_mode="r")
n = ref.shape[0]

def amps(i0, i1, flist):
    x = np.asarray(ref[i0:i1], dtype=np.float64); x = x - x.mean()
    t = np.arange(x.size) / FS
    o = []
    for f in flist:
        c = np.dot(x, np.cos(2 * np.pi * f * t)); s = np.dot(x, np.sin(2 * np.pi * f * t))
        o.append(2.0 * np.hypot(c, s) / x.size)
    return o

fl = [2.3, 2.4, 2.5, 2.6]
print("[V005] head of excitation window, amplitude (mV) at 2.3/2.4/2.5/2.6 Hz")
for lab, i0, i1 in [("array 0-18 s   (run 3990-4008)", 0, 18000),
                    ("array 21-39 s  (run 4011-4029)", 21000, 39000),
                    ("array 40-250 s (run 4030-4240)", 40000, 250000)]:
    a = amps(i0, i1, fl)
    print("[V005]   %-32s " % lab + "  ".join("%.1f@%.1fHz" % (v, f) for v, f in zip(a, fl)))
print("[V005] rms of ch1111 over array 0-18 s = %.2f mV (quiet1 shaker-off rms is 3.89 mV)"
      % float(np.std(np.asarray(ref[:18000], dtype=np.float64))))

fl2 = [9.4, 9.5, 9.6]
print("[V005] tail of excitation window, amplitude (mV) at 9.4/9.5/9.6 Hz")
for lab, i0, i1 in [("array 17500-17740 s", 17500000, 17740000),
                    ("array 17740-17770 s (last 30 s)", 17740000, 17770000)]:
    a = amps(i0, i1, fl2)
    print("[V005]   %-32s " % lab + "  ".join("%.1f@%.1fHz" % (v, f) for v, f in zip(a, fl2)))
print("[V005] rms of ch1111 over last 20 s (array 17750-17770 s) = %.2f mV"
      % float(np.std(np.asarray(ref[17750000:], dtype=np.float64))))
