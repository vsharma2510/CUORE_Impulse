#!/usr/bin/env python3
"""Boundary crossover: 1 s resolution step transitions from ch1111."""
import json
import numpy as np
ARR = "<SCRATCH>/CUORE_ImpulsePilot_data"
OUT = "<HOME>/CUORE_ImpulsePilot/verify"
FS, OFFS = 1000.0, 3990.0
ref = np.load(ARR + "/excitation/aux/ch1111.npy", mmap_mode="r")
nb = ref.shape[0] // 1000
X = np.asarray(ref[:nb * 1000], dtype=np.float64).reshape(nb, 1000)
tl = np.arange(1000) / FS
fg = np.round(np.arange(2.5, 9.5001, 0.1), 4)
C = np.cos(2 * np.pi * np.outer(tl, fg)); S = np.sin(2 * np.pi * np.outer(tl, fg))
A = 2.0 * np.sqrt((X @ C) ** 2 + (X @ S) ** 2) / 1000.0   # (nb, nf) 1 s amplitudes
out = []
for k in range(fg.size - 1):
    # search near the nominal boundary 4015+250*(k+1) run -> array 25+250*(k+1)
    c = 25 + 250 * (k + 1)
    lo, hi = c - 30, c + 30
    m = np.arange(lo, hi)
    d = A[m, k] - A[m, k + 1]           # >0 while tone k is on
    s = np.where(d[:-1] > 0)[0]
    j = m[s[-1]] if s.size else c
    # linear interpolation of the zero crossing between blocks j and j+1
    d0, d1 = A[j, k] - A[j, k + 1], A[j + 1, k] - A[j + 1, k + 1]
    frac = d0 / (d0 - d1) if d0 != d1 else 0.5
    tb = j + 0.5 + frac
    out.append({"boundary_index": k + 1, "f_before": float(fg[k]), "f_after": float(fg[k + 1]),
                "t_cross_array_s": float(tb), "t_cross_run_s": float(tb + OFFS),
                "t_nominal_run_s": float(c + OFFS),
                "delta_s": float(tb + OFFS - (c + OFFS))})
d = np.array([o["delta_s"] for o in out])
print("[V004] boundary crossover vs steps.csv nominal 4015+250k:")
print("[V004]   n=%d  mean delta=%+.3f s  median=%+.3f s  std=%.3f s  min=%+.3f  max=%+.3f"
      % (d.size, d.mean(), np.median(d), d.std(), d.min(), d.max()))
for o in out[:4] + out[-2:]:
    print("[V004]   %.1f->%.1f Hz: cross at run %.2f s, nominal %.1f s, delta %+.2f s"
          % (o["f_before"], o["f_after"], o["t_cross_run_s"], o["t_nominal_run_s"], o["delta_s"]))
# first tone-on and last tone-off
a0 = A[:60, 0]
print("[V004] 1 s amplitude at 2.5 Hz, array t=0..59 s (mV): " +
      " ".join("%.0f" % v for v in a0[:40]))
aL = A[-40:, -1]
print("[V004] 1 s amplitude at 9.5 Hz, array t=%d..%d s (mV): " % (nb - 40, nb - 1) +
      " ".join("%.0f" % v for v in aL))
json.dump(out, open(OUT + "/v02_boundaries.json", "w"), indent=1)
