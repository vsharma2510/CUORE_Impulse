#!/usr/bin/env python3
"""Verifier stage 4: modes by frequency-domain rational-fraction-polynomial fit of H."""
import json
import numpy as np

OUT = "<HOME>/CUORE_ImpulsePilot/verify"
LOG = []
def L(s):
    print(s, flush=True); LOG.append(s)

d = np.load(OUT + "/responses.npz", allow_pickle=False)
ch = d["channels"]; kind = d["channel_kind"]
f = d["f_drive_hz"]; H = d["H"]; coh = d["coherence2"]; nsub = d["n_subblocks"]
bolo = np.where(kind == "bolo")[0]
nb = bolo.size
mag = np.abs(H)

def rfp(fv, Hv, fc):
    """One-mode rational-fraction-polynomial fit, H = N(s)/D(s), s = i f/fc.

    Numerator order 2, denominator order 2. Linear least squares in
    (a0,a1,a2,b0,b1) from  N(s) - H*(b0 + b1 s) = H*s^2.
    """
    s = 1j * fv / fc
    A = np.column_stack([np.ones_like(s), s, s * s, -Hv, -Hv * s])
    rhs = Hv * s * s
    M = np.vstack([A.real, A.imag]); y = np.concatenate([rhs.real, rhs.imag])
    c, *_ = np.linalg.lstsq(M, y, rcond=None)
    b0, b1 = c[3], c[4]
    if b0 <= 0:
        return None
    wn = np.sqrt(b0)
    zeta = b1 / (2.0 * wn)
    f0 = fc * wn
    pred = (c[0] + c[1] * s + c[2] * s * s) / (s * s + b1 * s + b0)
    resid = float(np.sqrt(np.mean(np.abs(Hv - pred) ** 2)) / np.sqrt(np.mean(np.abs(Hv) ** 2)))
    return float(f0), float(zeta), resid

def halfpower_span(m, k0):
    """Number of consecutive 0.1 Hz grid points at or above peak/sqrt(2)."""
    thr = m[k0] / np.sqrt(2.0)
    lo = k0
    while lo - 1 >= 0 and m[lo - 1] >= thr:
        lo -= 1
    hi = k0
    while hi + 1 < m.size and m[hi + 1] >= thr:
        hi += 1
    return hi - lo + 1, lo, hi

# ------------------------------------------------- per-channel peaks in |H|
L("[V013] modes are taken from |H| (the ratio to ch1111), NOT from the raw bolometer "
  "amplitude. The raw amplitude peaks at 3.4 Hz on 46/52 bolometers, but the DRIVE force "
  "also peaks at 3.4 Hz (1521 mV vs 363 mV at 2.5 Hz), so a raw-amplitude peak there is "
  "partly the shaker, not the tower. Dividing by ch1111 on the same step removes it.")
peaks = {}
for i in bolo:
    m = mag[i]
    loc = [k for k in range(1, 70) if m[k] > m[k - 1] and m[k] > m[k + 1]
           and m[k] > 1.5 * np.median(m)]
    peaks[int(ch[i])] = [(int(k), float(f[k]), float(m[k])) for k in loc]
allpk = np.array([f[k] for v in peaks.values() for k, _, _ in v])
L("[V013] local maxima of |H| over the 52 bolometers: %d peaks total, %.1f per channel"
  % (allpk.size, allpk.size / nb))
u, c = np.unique(np.round(allpk, 1), return_counts=True)
o = np.argsort(-c)
L("[V013] peak frequency histogram of |H| (channels showing a local max at each grid "
  "point), most common first: " + ", ".join("%.1f Hz x%d" % (u[i], c[i]) for i in o[:12]))

# --------------------------------------------------------------- clustering
cand = [(u[i], c[i]) for i in np.argsort(-c) if c[i] >= 6]
cand.sort()
merged = []
for fq, n in cand:
    if merged and fq - merged[-1][-1][0] <= 0.1:
        merged[-1].append((fq, n))
    else:
        merged.append([(fq, n)])
L("[V014] clusters of >=6 channels, merged across adjacent grid points: " +
  ", ".join("[%s]" % "+".join("%.1f" % q for q, _ in g) for g in merged))

rows = []
for g in merged:
    fqs = np.array([q for q, _ in g]); wts = np.array([float(n) for _, n in g])
    fcen = float(np.average(fqs, weights=wts))
    k0g = int(np.argmin(np.abs(f - fcen)))
    # which channels show it: a local max in |H| within +/-0.15 Hz of the cluster
    show, f0s, z_rfp, zr_ok, spans = [], [], [], [], []
    for i in bolo:
        m = mag[i]
        loc = [k for k, _, _ in peaks[int(ch[i])] if abs(f[k] - fcen) <= 0.15]
        if not loc:
            continue
        k0 = max(loc, key=lambda k: m[k])
        show.append(int(ch[i]))
        sp, lo, hi = halfpower_span(m, k0)
        spans.append(sp)
        sel = (f > fcen - 0.6) & (f < fcen + 0.6)
        r = rfp(f[sel], H[i][sel], fcen)
        if r is not None and abs(r[0] - fcen) < 0.4 and 0 < r[1] < 0.5:
            f0s.append(r[0]); z_rfp.append(r[1]); zr_ok.append(r[2])
    if len(show) < 6:
        continue
    spans = np.array(spans)
    med_span = int(np.median(spans))
    f0 = float(np.median(f0s)) if f0s else float(f[k0g])
    f0_err = float(max(0.05, np.std(f0s) if len(f0s) > 2 else 0.05))
    if med_span >= 3:
        # half-power width from the median |H| of the showing channels
        mm = np.median(mag[[i for i in bolo if int(ch[i]) in show]], axis=0)
        kk = int(np.argmin(np.abs(f - f0)))
        kk = int(np.argmax(mm[max(0, kk - 2):kk + 3])) + max(0, kk - 2)
        sp, lo, hi = halfpower_span(mm, kk)
        df = float(f[hi] - f[lo])
        zeta = df / (2.0 * f0); zeta_err = 0.1 / (2.0 * f0); upper = False
        meth = "halfpower_width_on_median_absH(span=%d points)" % sp
    else:
        zeta = 0.1 / (2.0 * f0); zeta_err = float("nan"); upper = True
        meth = "upper_limit_unresolved(median span=%d point)" % med_span
    ptf = bool(min(abs(f0 - 1.4 * k) for k in range(1, 8)) <= f0_err)
    rows.append({"f0_hz": f0, "f0_err_hz": f0_err, "zeta": zeta, "zeta_err": zeta_err,
                 "zeta_is_upper_limit": upper, "n_channels_showing": len(show),
                 "channels": show, "method": meth, "pt_harmonic_flag": ptf,
                 "median_span_points": med_span,
                 "zeta_rfp_median": float(np.median(z_rfp)) if z_rfp else float("nan"),
                 "zeta_rfp_iqr": float(np.subtract(*np.percentile(z_rfp, [75, 25]))) if len(z_rfp) > 3 else float("nan"),
                 "rfp_resid_median": float(np.median(zr_ok)) if zr_ok else float("nan"),
                 "n_rfp_ok": len(z_rfp)})
rows.sort(key=lambda r: -r["n_channels_showing"])

hdr = ["# modes.csv -- dominant structural modes in 2.50-9.50 Hz from the 52 tower-19",
       "# bolometers. Modes are local maxima of |H| = |lock-in(bolo)/lock-in(ch1111)| on the",
       "# same step, so the shaker/stinger response (force peaks at 3.4 Hz) is divided out.",
       "# f0 from a one-mode rational-fraction-polynomial fit (num order 2, den order 2) in a",
       "# +/-0.6 Hz band, median over the showing channels. f0_err is the larger of 0.05 Hz",
       "# (half the step spacing, the SPEC floor) and the across-channel scatter.",
       "# zeta from the half-power width ONLY where the peak spans >=3 of the 0.1 Hz points;",
       "# otherwise zeta is an UPPER LIMIT 0.1/(2 f0) and zeta_is_upper_limit is true.",
       "# pt_harmonic_flag: f0 within f0_err of a multiple of 1.4 Hz (pulse-tube line).",
       "f0_hz,f0_err_hz,zeta,zeta_err,zeta_is_upper_limit,n_channels_showing,channels,method,pt_harmonic_flag"]
for r in rows:
    hdr.append("%.4f,%.4f,%.5f,%s,%s,%d,%s,%s,%s" % (
        r["f0_hz"], r["f0_err_hz"], r["zeta"],
        "" if r["zeta_err"] != r["zeta_err"] else "%.5f" % r["zeta_err"],
        str(r["zeta_is_upper_limit"]).lower(), r["n_channels_showing"],
        ";".join(str(c) for c in r["channels"]), r["method"],
        str(r["pt_harmonic_flag"]).lower()))
open(OUT + "/modes.csv", "w").write("\n".join(hdr) + "\n")
L("[V015] modes.csv written: %d modes" % len(rows))
for r in rows:
    L("[V015] mode f0=%.4f +/- %.4f Hz | zeta=%.5f%s | span=%d pts | %d/52 channels | "
      "pt_harmonic=%s | rfp zeta median=%.5f (iqr %.5f, n=%d, median rel resid %.3f)"
      % (r["f0_hz"], r["f0_err_hz"], r["zeta"],
         " (UPPER LIMIT)" if r["zeta_is_upper_limit"] else " +/- %.5f" % r["zeta_err"],
         r["median_span_points"], r["n_channels_showing"], r["pt_harmonic_flag"],
         r["zeta_rfp_median"], r["zeta_rfp_iqr"], r["n_rfp_ok"], r["rfp_resid_median"]))

L("[V016] corroboration against SPEC section 7, stated either way:")
got = [r["f0_hz"] for r in rows]
in335 = [q for q in got if 3.35 <= q <= 3.55]
in80 = [q for q in got if 8.0 <= q <= 9.0]
L("[V016]   collaboration hunt 3.35-3.55 Hz (runs 306468/469/470, 306486, 306492, 306503): "
  "I find %s" % ("modes at " + ", ".join("%.3f Hz" % q for q in in335) if in335
                 else "NO mode in that interval"))
L("[V016]   collaboration hunt 8.0-9.0 Hz (runs 306477, 306485): I find %s"
  % ("modes at " + ", ".join("%.3f Hz" % q for q in in80) if in80
     else "NO mode in that interval"))
pth = [r["f0_hz"] for r in rows if r["pt_harmonic_flag"]]
L("[V016]   pulse-tube 1.4 Hz harmonics (2.8/4.2/5.6/7.0/8.4 Hz): %d of %d modes are flagged "
  "as coincident within f0_err: %s" % (len(pth), len(rows),
  ", ".join("%.3f" % q for q in pth) if pth else "none"))

mc = np.median(coh[bolo], axis=1)
L("[V017] median in-band coherence per bolometer: median %.4f, range %.4f-%.4f; "
  "the uncorrelated floor is 1/n_sub = %.4f, so coherence is genuinely resolved on "
  "%d of 52 channels (median coh2 > 5x floor)"
  % (np.median(mc), mc.min(), mc.max(), float(np.median(1.0 / nsub)),
     int((mc > 5.0 / np.median(nsub)).sum())))
cf = np.median(coh[bolo], axis=0)
worst = np.argsort(cf)[:5]
L("[V017] coherence vs frequency (median over bolometers), 5 worst steps: " +
  ", ".join("%.1f Hz:%.3f" % (f[k], cf[k]) for k in worst))
best = np.argsort(-cf)[:5]
L("[V017] coherence vs frequency, 5 best steps: " +
  ", ".join("%.1f Hz:%.3f" % (f[k], cf[k]) for k in best))
json.dump(rows, open(OUT + "/v05_modes.json", "w"), indent=1)
open(OUT + "/v05_log.txt", "w").write("\n".join(LOG) + "\n")
