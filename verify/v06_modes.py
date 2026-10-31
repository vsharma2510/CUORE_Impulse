#!/usr/bin/env python3
"""Verifier stage 4 (final): modes from |H| with RFP fit + SPEC half-power zeta rule."""
import json
import numpy as np
OUT = "<HOME>/CUORE_ImpulsePilot/verify"
LOG = []
def L(s):
    print(s, flush=True); LOG.append(s)

d = np.load(OUT + "/responses.npz")
ch = d["channels"]; kind = d["channel_kind"]
f = d["f_drive_hz"]; H = d["H"]; coh = d["coherence2"]; nsub = d["n_subblocks"]
bolo = np.where(kind == "bolo")[0]
mag = np.abs(H)[bolo]
med = np.median(mag, axis=0)
mcoh = np.median(coh[bolo], axis=0)
JUMPS = [(29, 30), (49, 50)]            # force discontinuities 5.4->5.5 and 7.4->7.5

def rfp1(fv, Hv, fc):
    """One-mode rational-fraction polynomial, H = (a0+a1 s+a2 s^2)/(s^2+b1 s+b0), s=i f/fc."""
    s = 1j * fv / fc
    A = np.column_stack([np.ones_like(s), s, s * s, -Hv, -Hv * s])
    rhs = Hv * s * s
    M = np.vstack([A.real, A.imag]); y = np.concatenate([rhs.real, rhs.imag])
    c, *_ = np.linalg.lstsq(M, y, rcond=None)
    b0, b1 = c[3], c[4]
    if b0 <= 0:
        return None
    wn = np.sqrt(b0); z = b1 / (2 * wn)
    pred = (c[0] + c[1] * s + c[2] * s * s) / (s * s + b1 * s + b0)
    rr = float(np.sqrt(np.mean(np.abs(Hv - pred) ** 2)) / np.sqrt(np.mean(np.abs(Hv) ** 2)))
    return float(fc * wn), float(z), rr

def hp_span(m, k0):
    """Half-power span in grid points, walking outward from k0 while m DECREASES and
    stays at/above peak/sqrt(2). Stopping at a valley rather than running down a
    neighbouring mode's skirt; if a valley is hit first that side is 'not crossed'."""
    thr = m[k0] / np.sqrt(2.0)
    lo, lo_cross = k0, False
    while lo - 1 >= 0 and m[lo - 1] < m[lo]:
        if m[lo - 1] < thr:
            lo_cross = True; break
        lo -= 1
    hi, hi_cross = k0, False
    while hi + 1 < m.size and m[hi + 1] < m[hi]:
        if m[hi + 1] < thr:
            hi_cross = True; break
        hi += 1
    # linear interpolation of the crossing in f, where it was actually crossed
    flo = f[lo]; fhi = f[hi]
    if lo_cross:
        flo = f[lo] - (m[lo] - thr) / (m[lo] - m[lo - 1]) * (f[lo] - f[lo - 1])
    if hi_cross:
        fhi = f[hi] + (m[hi] - thr) / (m[hi] - m[hi + 1]) * (f[hi + 1] - f[hi])
    return hi - lo + 1, lo, hi, float(fhi - flo), bool(lo_cross and hi_cross)

L("[V018] modes come from |H| = |lockin(bolo)/lockin(ch1111)| on the SAME step, not from the "
  "raw bolometer amplitude: the raw amplitude peaks at 3.4 Hz on 46/52 bolometers but the "
  "drive force also peaks at 3.4 Hz (1521.6 vs 363.0 mV at 2.5 Hz), so a raw peak there is "
  "partly the shaker/stinger response.")
# mode detection on the median |H|
PROM = 1.25
cands = []
for k in range(1, 70):
    if med[k] > med[k - 1] and med[k] > med[k + 1]:
        p = med[k] / (0.5 * (med[k - 1] + med[k + 1]))
        if p >= PROM and mcoh[k] >= 0.5:
            cands.append((k, p))
L("[V018] mode detection on the median |H| over 52 bolometers: local maxima with prominence "
  ">= %.2f against the mean of the two neighbours AND median coherence >= 0.50 at the peak. "
  "%d candidates: %s" % (PROM, len(cands),
  ", ".join("%.1f Hz (prom %.2f, coh %.3f)" % (f[k], p, mcoh[k]) for k, p in cands)))

rows = []
for k0, prom in cands:
    sp, lo, hi, df, both = hp_span(med, k0)
    # per-channel RFP fits in a +/-0.4 Hz band
    sel = (f > f[k0] - 0.45) & (f < f[k0] + 0.45)
    f0s, zs, rrs = [], [], []
    for i in bolo:
        r = rfp1(f[sel], H[i][sel], f[k0])
        if r is None:
            continue
        if abs(r[0] - f[k0]) < 0.25 and 0 < r[1] < 0.3 and r[2] < 0.40:
            f0s.append(r[0]); zs.append(r[1]); rrs.append(r[2])
    if len(f0s) >= 5:
        f0 = float(np.median(f0s)); f0src = "rfp_median_n%d" % len(f0s)
        f0_err = float(max(0.05, np.std(f0s)))
    else:
        # parabolic interpolation on log|H|, 3 points
        y = np.log(med[k0 - 1:k0 + 2])
        dk = 0.5 * (y[0] - y[2]) / (y[0] - 2 * y[1] + y[2])
        f0 = float(f[k0] + dk * 0.1); f0src = "log_parabolic(rfp_ill_conditioned_n%d)" % len(f0s)
        f0_err = 0.05
    # channels showing it: local max in |H| within +/-0.1 Hz and coherence >= 0.3 there
    show = []
    for i in bolo:
        m = mag[list(bolo).index(i)] if False else np.abs(H[i])
        w = range(max(1, k0 - 1), min(70, k0 + 2))
        if any(m[k] > m[k - 1] and m[k] > m[k + 1] and coh[i, k] >= 0.3 for k in w):
            show.append(int(ch[i]))
    if sp >= 3 and both:
        zeta = df / (2.0 * f0); zerr = 0.1 / (2.0 * f0); upper = False
        meth = "halfpower_width_median_absH_span%dpts_df%.3fHz" % (sp, df)
    else:
        zeta = 0.1 / (2.0 * f0); zerr = float("nan"); upper = True
        meth = "upper_limit_peak_unresolved_span%dpts" % sp
    meth += "|f0_" + f0src
    jf = any(k0 in jj for jj in JUMPS)
    if jf:
        meth += "|ADJACENT_TO_CH1111_SCALE_DISCONTINUITY"
    ptf = bool(min(abs(f0 - 1.4 * j) for j in range(1, 8)) <= f0_err)
    rows.append({"f0_hz": f0, "f0_err_hz": f0_err, "zeta": zeta, "zeta_err": zerr,
                 "zeta_is_upper_limit": upper, "n_channels_showing": len(show),
                 "channels": show, "method": meth, "pt_harmonic_flag": ptf,
                 "span_points": sp, "prominence": float(prom),
                 "median_coherence_at_peak": float(mcoh[k0]),
                 "zeta_rfp_median": float(np.median(zs)) if len(zs) >= 5 else float("nan"),
                 "n_rfp_ok": len(zs), "force_jump_adjacent": jf})

hdr = ["# modes.csv -- dominant structural modes, 2.50-9.50 Hz, 52 tower-19 bolometers,",
       "# run RUNA, shaker at MSP-X, one axis, one run. Feasibility pilot: these are",
       "# estimates scoped to this run and these channels.",
       "# Modes are local maxima of the median |H| over the 52 bolometers, where",
       "# H = lockin(bolometer)/lockin(ch1111) on the SAME step, so the shaker/stinger",
       "# response (force peaks at 3.4 Hz) divides out. Detection: prominence >= 1.25 against",
       "# the mean of the two neighbouring grid points AND median coherence >= 0.50 at the peak.",
       "# f0: median over channels of a one-mode rational-fraction-polynomial fit (numerator",
       "#   order 2, denominator order 2) in a +/-0.45 Hz band, keeping only fits with",
       "#   relative residual < 0.40; where too few fits qualify, a 3-point parabolic",
       "#   interpolation on log|H| is used instead and the method column says so.",
       "# f0_err: the larger of 0.05 Hz (half the 0.1 Hz step spacing; the SPEC floor, never",
       "#   quoted better) and the across-channel scatter of the RFP f0.",
       "# zeta: from the half-power width ONLY where the peak spans >= 3 of the 0.1 Hz points",
       "#   AND the half-power level is actually crossed on both sides. Otherwise zeta is an",
       "#   UPPER LIMIT, 0.1/(2 f0), and zeta_is_upper_limit is true; zeta_err is then blank.",
       "# pt_harmonic_flag: f0 within f0_err of a multiple of 1.4 Hz (pulse-tube line).",
       "# ADJACENT_TO_CH1111_SCALE_DISCONTINUITY in the method column: this mode sits next to",
       "#   one of the two ch1111 scale jumps (5.4->5.5, 7.4->7.5 Hz). Its prominence may be",
       "#   partly instrumental. See VERIFIER_LOG.md V020.",
       "f0_hz,f0_err_hz,zeta,zeta_err,zeta_is_upper_limit,n_channels_showing,channels,method,pt_harmonic_flag"]
for r in rows:
    hdr.append("%.4f,%.4f,%.5f,%s,%s,%d,%s,%s,%s" % (
        r["f0_hz"], r["f0_err_hz"], r["zeta"],
        "" if r["zeta_err"] != r["zeta_err"] else "%.5f" % r["zeta_err"],
        str(r["zeta_is_upper_limit"]).lower(), r["n_channels_showing"],
        ";".join(str(c) for c in r["channels"]), r["method"], str(r["pt_harmonic_flag"]).lower()))
open(OUT + "/modes.csv", "w").write("\n".join(hdr) + "\n")
L("[V019] modes.csv written: %d modes, 2.50-9.50 Hz" % len(rows))
for r in rows:
    L("[V019] f0=%.4f +/- %.4f Hz | zeta %s %.5f%s | span=%d pt | prom=%.2f | coh=%.3f | "
      "%d/52 channels | pt_harm=%s | rfp zeta med=%s (n=%d)%s"
      % (r["f0_hz"], r["f0_err_hz"], "<" if r["zeta_is_upper_limit"] else "=", r["zeta"],
         "" if r["zeta_is_upper_limit"] else " +/- %.5f" % r["zeta_err"], r["span_points"],
         r["prominence"], r["median_coherence_at_peak"], r["n_channels_showing"],
         r["pt_harmonic_flag"],
         "nan" if r["zeta_rfp_median"] != r["zeta_rfp_median"] else "%.5f" % r["zeta_rfp_median"],
         r["n_rfp_ok"], "  [FORCE-JUMP ADJACENT]" if r["force_jump_adjacent"] else ""))
nu = sum(1 for r in rows if r["zeta_is_upper_limit"])
L("[V019] %d of %d modes give only a zeta UPPER LIMIT because the peak spans < 3 of the "
  "0.1 Hz grid points. This is exactly the case SPEC 4.3 anticipated; a point value for "
  "those would be fabricated. The 0.1 Hz step spacing, not the statistics, is the limit."
  % (nu, len(rows)))
got = [r["f0_hz"] for r in rows]
i335 = [q for q in got if 3.35 <= q <= 3.55]; i80 = [q for q in got if 8.0 <= q <= 9.0]
L("[V019] SPEC 7 corroboration, stated either way: collaboration hunt 3.35-3.55 Hz -> I find %s; "
  "hunt 8.0-9.0 Hz -> I find %s"
  % ("f0 = " + ", ".join("%.3f Hz" % q for q in i335) if i335 else "NO mode there",
     "f0 = " + ", ".join("%.3f Hz" % q for q in i80) if i80 else "NO mode there"))
pth = [r["f0_hz"] for r in rows if r["pt_harmonic_flag"]]
L("[V019] pulse-tube 1.4 Hz harmonics (2.8/4.2/5.6/7.0/8.4 Hz): %d of %d modes flagged "
  "coincident within f0_err: %s" % (len(pth), len(rows),
  ", ".join("%.3f" % q for q in pth) if pth else "none"))
json.dump(rows, open(OUT + "/v06_modes.json", "w"), indent=1)
open(OUT + "/v06_log.txt", "w").write("\n".join(LOG) + "\n")
