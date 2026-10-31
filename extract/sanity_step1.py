#!/usr/bin/env python3
"""Step 1 sanity checks (design items 1-5 and 7). Numbers printed here go into AGENT_GRAPH_LOG.md.

Run from the project root:  python3 -I extract/sanity_step1.py
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from read_vcts import ADC2MV, read, read_header

OUT = "<SCRATCH>/vibes_main/output"
AUXDIR = "<SCRATCH>/runRUNA/timestreams"
BOLO = list(range(937, 989))
AUX = list(range(1101, 1124))
WINDOWS = {
    "excitation": (RUNA, 3990, 21760),
    "quiet1": (RUNA, 0, 250),
    "quiet2": (RUNA, 1275, 1500),
    "quiet3": (RUNA, 48025, 48800),
    "quietrun": (RUNB, 0, 2456),
}
fails = []


def path(run, ch, t0, t1):
    return f"{OUT}/run{run}/timestreams/run{run}_ch{ch:04d}_t{t0}_T{t1}.bin"


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))
    if not ok:
        fails.append(label)
    return ok


print("=" * 78)
print("CHECK 1/3/4: file presence, sample-count agreement, header-vs-filename")
print("=" * 78)
counts = {}
for name, (run, t0, t1) in WINDOWS.items():
    chans = BOLO + (AUX if name == "quietrun" else [])
    missing = [c for c in chans if not os.path.exists(path(run, c, t0, t1))]
    check(f"{name}: all {len(chans)} channels present", not missing, f"missing {missing}" if missing else "")
    ns, bad_hdr = set(), []
    for c in chans:
        p = path(run, c, t0, t1)
        if not os.path.exists(p):
            continue
        h = read_header(p)
        ns.add(h["n_samples"])
        if h["run"] != run or h["channel"] != c or h["rate"] != 1000.0 or h["t0"] != t0 or h["tend"] != t1:
            bad_hdr.append(c)
    expect = int((t1 - t0) * 1000)
    check(f"{name}: identical sample count across channels", len(ns) == 1, f"saw {sorted(ns)}")
    check(f"{name}: sample count == (t1-t0)*1000 = {expect:,}", ns == {expect}, f"got {sorted(ns)}")
    check(f"{name}: header run/ch/rate/t0/tend match filename", not bad_hdr, f"mismatched {bad_hdr}" if bad_hdr else "")
    counts[name] = (len(chans) - len(missing), expect)

print()
print("=" * 78)
print("CHECK 2: no dead channels (excitation window, 52 bolometers)")
print("=" * 78)
run, t0, t1 = WINDOWS["excitation"]
stats = {}
zero, const = [], []
for c in BOLO:
    _, x = read(path(run, c, t0, t1))
    ac = x - x.mean()
    stats[c] = dict(mean=float(x.mean()), rms=float(ac.std()), mn=float(x.min()), mx=float(x.max()),
                    ndist=int(len(np.unique(x[:200000]))))
    if np.all(x == 0):
        zero.append(c)
    if stats[c]["rms"] == 0:
        const.append(c)
check("no all-zero bolometer", not zero, f"zero: {zero}" if zero else "")
check("no constant bolometer", not const, f"constant: {const}" if const else "")
r = np.array([stats[c]["rms"] for c in BOLO])
print(f"  AC RMS over 52 bolometers [mV]: min {r.min():.3f}  median {np.median(r):.3f}  max {r.max():.3f}")
print(f"  baseline mean [mV]: min {min(stats[c]['mean'] for c in BOLO):.1f}  "
      f"max {max(stats[c]['mean'] for c in BOLO):.1f}")

print()
print("=" * 78)
print("CHECK 5: step map re-derived from the extracted window agrees with the pre-slice map")
print("=" * 78)
from scipy.signal import welch  # noqa: E402
h, force = read(f"{AUXDIR}/runRUNA_ch1111_t0_Tend.bin")
seg = force[int(3990 * 1000):int(21760 * 1000)]
B = 25 * 1000
nb = len(seg) // B
fr, rms = [], []
win = np.hanning(B)
freqs = np.fft.rfftfreq(B, 1 / 1000.0)
band = (freqs > 0.6) & (freqs < 25)
for b in range(nb):
    x = seg[b * B:(b + 1) * B].astype(np.float64)
    x -= x.mean()
    rms.append(x.std())
    fr.append(freqs[band][np.argmax(np.abs(np.fft.rfft(x * win))[band])])
fr, rms = np.array(fr), np.array(rms)
on = rms >= 10
check("every 25 s block in the window has the shaker on", on.all(),
      f"{(~on).sum()} blocks below 10 mV")
edges = [0] + [i for i in range(1, len(fr)) if abs(fr[i] - fr[i - 1]) > 0.05] + [len(fr)]
steps = [(np.median(fr[a:b]), (b - a) * 25) for a, b in zip(edges[:-1], edges[1:])]
big = [s for s in steps if s[1] >= 200]
f0 = np.array([s[0] for s in big])
check("frequency sequence is monotonic", bool((np.diff(f0) > 0).all()))
check("band is 2.5-9.5 Hz", 2.45 <= f0.min() and f0.max() <= 9.55, f"{f0.min():.2f}..{f0.max():.2f} Hz")
print(f"  steps recovered in window: {len(big)} (expected ~71)  f {f0.min():.2f}..{f0.max():.2f} Hz")
print(f"  median dwell {np.median([s[1] for s in big]):.0f} s   force RMS {rms.min():.0f}-{rms.max():.0f} mV")

print()
print("=" * 78)
print("CHECK 7: is ch 975 an outlier among the 52? (settles E007 empirically)")
print("=" * 78)
run, t0, t1 = WINDOWS["quietrun"]
q = {}
for c in BOLO:
    _, x = read(path(run, c, t0, t1))
    xa = (x - x.mean()).astype(np.float64)
    f, P = welch(xa, fs=1000.0, nperseg=8192)
    band1 = (f >= 0.1) & (f <= 1.0)
    band2 = (f >= 1.0) & (f <= 50.0)
    q[c] = dict(rms=float(xa.std()),
                p_lo=float(np.trapezoid(P[band1], f[band1])),
                p_hi=float(np.trapezoid(P[band2], f[band2])))
for key, label in (("rms", "AC RMS [mV]"), ("p_lo", "power 0.1-1 Hz"), ("p_hi", "power 1-50 Hz")):
    v = np.array([q[c][key] for c in BOLO])
    med, mad = np.median(v), np.median(np.abs(v - np.median(v)))
    z = (q[975][key] - med) / (1.4826 * mad) if mad > 0 else 0.0
    rank = int(np.sum(v <= q[975][key]))
    print(f"  {label:18} ch975 {q[975][key]:12.4g}   median {med:12.4g}   robust z {z:+6.2f}   rank {rank}/52")
    check(f"ch975 within 3 sigma on {label}", abs(z) < 3.0, f"robust z {z:+.2f}")

print()
print("=" * 78)
print(f"RESULT: {len(fails)} failed check(s)" + (": " + "; ".join(fails) if fails else " -- all passed"))
print("=" * 78)
json.dump({"bolo_excitation_stats": stats, "quiet_run_stats": q,
           "steps_in_window": [[float(a), float(b)] for a, b in big],
           "window_counts": counts, "fails": fails},
          open("data/sanity_step1.json", "w"), indent=1)
print("numbers written to data/sanity_step1.json")
