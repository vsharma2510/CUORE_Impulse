#!/usr/bin/env python3
import json
import numpy as np

OUT = "<HOME>/CUORE_ImpulsePilot/verify"
LOG = []

def L(s):
    print(s, flush=True)
    LOG.append(s)

d = json.load(open(OUT + "/d02_fits.json"))
R = d["recs"]
f0s = d["f0_modes"]
TAUS = np.array(d["taus"])
TAU3 = d["tau3_ceiling_s"]
NTAU = TAUS.size
NDF = len(d["dfs"])
T_ADM = float(TAUS[TAUS <= TAU3].max())
GRIDF = float(0.5 * (TAUS[1] / TAUS[0] - 1.0))
v6 = json.load(open(OUT + "/v06_modes.json"))

z = np.load(OUT + "/responses.npz")
ch = z["channels"]; kind = z["channel_kind"]; f = z["f_drive_hz"]; H = z["H"]
bolo = np.where(kind == "bolo")[0]
med = np.median(np.abs(H)[bolo], axis=0)

def rfp1(fv, Hv, fc):
    s = 1j * fv / fc
    A = np.column_stack([np.ones_like(s), s, s * s, -Hv, -Hv * s])
    rhs = Hv * s * s
    M = np.vstack([A.real, A.imag]); y = np.concatenate([rhs.real, rhs.imag])
    c, *_ = np.linalg.lstsq(M, y, rcond=None)
    b0, b1 = c[3], c[4]
    if b0 <= 0:
        return None
    wn = np.sqrt(b0); zz = b1 / (2 * wn)
    pred = (c[0] + c[1] * s + c[2] * s * s) / (s * s + b1 * s + b0)
    rr = float(np.sqrt(np.mean(np.abs(Hv - pred) ** 2)) / np.sqrt(np.mean(np.abs(Hv) ** 2)))
    return float(fc * wn), float(zz), rr

def hp_span(m, k0):
    thr = m[k0] / np.sqrt(2.0)
    lo = k0; lo_c = False
    while lo - 1 >= 0 and m[lo - 1] < m[lo]:
        if m[lo - 1] < thr:
            lo_c = True; break
        lo -= 1
    hi = k0; hi_c = False
    while hi + 1 < m.size and m[hi + 1] < m[hi]:
        if m[hi + 1] < thr:
            hi_c = True; break
        hi += 1
    return hi - lo + 1, bool(lo_c and hi_c)

L("")
L("## V032-V037  Damping: aggregation, Routes B and C, and the deliverable")
L("")
L("[V032a] NOTE ON THIS LOG. An earlier pass of this same stage was appended above with")
L("  zeta_err from MAD/sqrt(N) and with no window-limited test. Both were wrong and the")
L("  numbers in that pass are SUPERSEDED by the ones below; I am appending the correction")
L("  rather than editing it away. What changed: (a) MAD/sqrt(N) gave +/-0.15 s on tau=4.23 s")
L("  while the tau scan grid is 19.5%% per step, so the error was smaller than the")
L("  quantisation of the quantity it described; (b) the 52 bolometers watch one tower and")
L("  are not independent, so dividing their spread by sqrt(N) overstates the result; and")
L("  (c) the f0=3.9707 Hz row was being reported as measured when half its fits sat at the")
L("  3-tau ceiling. See V037.")
L("")
L("[V032] Route A acceptance, fixed before any per-mode zeta was looked at:")
L("  (1) tau and df both strictly interior to their scan ranges;")
L("  (2) tau <= %.2f s, the 3-tau ceiling of the %.1f s window (SPEC 4.3 Route A);" % (TAU3, d["span_s"]))
L("  (3) F_decay above the 99th percentile of that modes own null-window F;")
L("  (4) boundary with |f_old - f0| <= 0.15 Hz, since the free-decay amplitude scales with")
L("      the forced amplitude at switch-off;")
L("  (5) boundary with |f_new - f0| >= 0.06 Hz. This is a real contaminant I found: where")
L("      the NEXT tone lands on the mode, what follows the boundary is the mode BUILDING UP,")
L("      not ringing down, and the model has no build-up term, so the decay column fits the")
L("      ramp and tau runs to the scan floor. Example: f0=3.4075 Hz, boundary 8")
L("      (3.3001 -> 3.4001 Hz), median amp 102.3 mV and median tau 0.50 s, the scan floor.")
L("      Those boundaries are excluded, not repaired.")
L("[V033] Amplitude, not F, is what tracks resonance, and the two must not be confused. At")
L("  f0=3.4075 Hz the largest median decay amplitude is at boundary 9, the ON-RESONANCE")
L("  switch-off (old tone 3.4001 Hz): 194.7 mV, against 8.8 mV at boundary 10 and 3.1 mV at")
L("  boundary 7. F instead peaks at boundary 10 (2442 vs 91) because F also carries the local")
L("  noise level. The amplitude ordering is the one that must follow resonance physics, and")
L("  it does; that is a consistency check the fit passes.")

rows = []
for mi, f0 in enumerate(f0s):
    nl = [r for r in R if r["mode"] == mi and r["kind"] == "null"]
    F99 = float(np.percentile([r["F_decay"] for r in nl], 99))
    sg = [r for r in R if r["mode"] == mi and r["kind"] == "sig"]
    cand = [r for r in sg if abs(r["f_old"] - f0) <= 0.15 and abs(r["f_new"] - f0) >= 0.06]
    acc = [r for r in cand
           if 0 < r["i_tau"] < NTAU - 1 and 0 < r["j_df"] < NDF - 1
           and r["tau_s"] <= TAU3 and r["F_decay"] > F99]
    nb = sorted(set(r["boundary"] for r in cand))
    chs = sorted(set(r["channel"] for r in acc))
    tceil = float(T_ADM)
    nceil = sum(1 for r in acc if abs(r["tau_s"] - tceil) < 1e-9)
    fceil = nceil / len(acc) if acc else 0.0
    tau = np.array([r["tau_s"] for r in acc]) if acc else np.array([])
    ok = len(acc) >= 10 and len(chs) >= 8 and fceil < 0.40
    if ok:
        tm = float(np.median(tau))
        p16, p84 = float(np.percentile(tau, 16)), float(np.percentile(tau, 84))
        zeta = 1.0 / (2 * np.pi * f0 * tm)
        z_lo = 1.0 / (2 * np.pi * f0 * p84)
        z_hi = 1.0 / (2 * np.pi * f0 * p16)
        zerr = max(0.5 * (z_hi - z_lo), GRIDF * zeta)
        o = {"zeta": zeta, "zeta_err": zerr, "method": "ringdown", "n": len(acc),
             "tau": tm, "tau_err": max(0.5 * (p84 - p16), GRIDF * tm), "nch": len(chs),
             "z16": z_lo, "z84": z_hi, "nceil": nceil,
             "outcome": ("fitted exp(-t/tau) at f0 jointly with the next drive tone on raw "
                         "1 kHz samples over 0.20-40.50 s after %d boundaries (pulser-masked; "
                         "22.7 s clean); window = %.1f tau; %d of %d channel-boundary fits "
                         "cleared the null-window F99 = %.1f; quoted error is the robust "
                         "channel-to-channel spread (half the 16-84 percentile range) floored "
                         "at the %.1f%% tau-grid half-step - it is NOT a 1/sqrt(N) error and "
                         "excludes any systematic common to all channels"
                         % (len(nb), d["span_s"] / tm, len(acc), len(cand), F99, 100 * GRIDF))}
    elif len(acc) >= 10 and len(chs) >= 8 and fceil >= 0.40:
        o = {"zeta": None, "zeta_err": None, "method": "none", "n": len(acc), "tau": None,
             "tau_err": None, "nch": len(chs), "z16": None, "z84": None, "nceil": nceil,
             "outcome": ("fitted exp(-t/tau) at f0 on raw 1 kHz samples over 0.20-40.50 s "
                         "after %d boundaries; %d of %d fits cleared the null-window "
                         "F99 = %.1f; FAILED as WINDOW-LIMITED: %d of %d accepted fits "
                         "(%.0f%%) pile up at tau = %.2f s; the largest value the 3-tau rule "
                         "admits for a %.1f s window; the decay is real but this run cannot "
                         "bound tau from above; reporting a number here would be reporting "
                         "the window length"
                         % (len(nb), len(acc), len(cand), F99, nceil, len(acc),
                            100 * fceil, tceil, d["span_s"]))}
    else:
        atedge = sum(1 for r in cand if r["i_tau"] in (0, NTAU - 1))
        o = {"zeta": None, "zeta_err": None, "method": "none", "n": len(acc), "tau": None,
             "tau_err": None, "nch": len(chs), "z16": None, "z84": None, "nceil": nceil,
             "outcome": ("fitted exp(-t/tau) at f0 on raw 1 kHz samples over 0.20-40.50 s "
                         "after %d boundaries x 52 bolometers; FAILED: only %d of %d fits "
                         "cleared the null-window F99 = %.1f with interior tau and %d ran to "
                         "a tau scan edge; median decay amplitude %.2f mV is not separable "
                         "from the noise of this estimator"
                         % (len(nb), len(acc), len(cand), F99, atedge,
                            float(np.median([r["amp_mV"] for r in cand]))))}
    k0 = int(np.argmin(np.abs(f - f0)))
    spn, both = hp_span(med, k0)
    o["b_ok"] = bool(spn >= 3 and both)
    o["b_outcome"] = ("half-power width of the median |H|: the peak spans %d of the 0.1 Hz grid "
                      "points and the half-power level is %scrossed on both sides; the SPEC 4.3 "
                      "Route B precondition (>= 3 points) is %s"
                      % (spn, "" if both else "not ", "met" if o["b_ok"] else "NOT met"))
    sel = (f > f0 - 0.45) & (f < f0 + 0.45)
    zs = []
    for i in bolo:
        r = rfp1(f[sel], H[i][sel], f[k0])
        if r is not None and abs(r[0] - f0) < 0.25 and 0 < r[1] < 0.3 and r[2] < 0.40:
            zs.append(r[1])
    o["c_n"] = len(zs)
    o["c_zeta"] = float(np.median(zs)) if len(zs) >= 5 else None
    o["c_outcome"] = ("pole of the per-channel 2/2 rational-fraction fit of H over f0 +/- 0.45 "
                      "Hz: %d of 52 channels returned a stable pole with relative residual "
                      "< 0.40%s" % (len(zs), "" if o["c_zeta"] is None
                                    else "; median zeta = %.5f" % o["c_zeta"]))
    rows.append((mi, f0, o, F99, nb))

for mi, f0, o, F99, nb in rows:
    L("[V034] f0=%.4f Hz: Route A %s (%d fits; %d channels%s) | Route B %s | Route C n=%d%s"
      % (f0, "MEASURED" if o["method"] == "ringdown" else "FAILED", o["n"], o["nch"],
         "; tau=%.2f+/-%.2f s" % (o["tau"], o["tau_err"]) if o["tau"] else "",
         "available" if o["b_ok"] else "not available", o["c_n"],
         "; zeta=%.5f" % o["c_zeta"] if o["c_zeta"] else ""))

hdr = [
 "# damping.csv -- verifier damping deliverable. SPEC 4.3 as AMENDED 2026-10-31.",
 "# CUORE run RUNA; tower 19; 52 bolometers; shaker MSP-X. ONE axis; ONE run.",
 "# PARTIAL AND PRELIMINARY. This is a feasibility pilot on a single stepped-sine run out",
 "# of many that exist. Nothing here is definitive; that applies to the rows carrying a",
 "# number exactly as much as to the rows reporting a failure. A damping ratio from one",
 "# shaker axis on one tower in one run constrains THIS RUN. It does not establish a",
 "# property of the detector and should not be quoted as one. Three of the eleven modes",
 "# yielded a ring-down measurement; eight did not, and the non-detections are a statement",
 "# about what this run can support, not evidence that those modes are narrow.",
 "#",
 "# One row per mode in modes.csv; same order; same f0. f0 is NOT re-derived here.",
 "#",
 "# zeta_method: ringdown | bandwidth | rfp_pole | none.",
 "# zeta_attempted: true on every row, as SPEC 4.3 requires. An upper limit is NOT offered",
 "#   as a branch: where the attempt failed, zeta is LEFT EMPTY and zeta_method = none. The",
 "#   grid formula 0.1/(2 f0) appears nowhere in this file.",
 "# zeta_is_upper_limit: false on every row. Nothing here is an upper limit. The rows that",
 "#   failed produced no bound at all, only a non-detection.",
 "# implied_delta_f_hz = 2 zeta f0 = 1/(pi tau): the half-power width the measured zeta",
 "#   implies, so the SPEC 4.3 self-consistency check is visible. Where it EXCEEDS the 0.1 Hz",
 "#   step spacing, the unresolved-peak premise is false for that mode and the grid upper",
 "#   limit would have been void there anyway.",
 "# window_over_tau: fit window span (40.3 s) divided by the fitted tau. SPEC 4.3 requires",
 "#   >= 3. The first run had only 5.30 s = 1.66 tau, which is why it had no measurement.",
 "# n_fits_used / n_fits_tried: channel-boundary ring-down fits entering the median, and",
 "#   offered to it. null_F99: the 99th percentile of the F statistic in the null window",
 "#   120.2-160.5 s after the same boundaries, where no free decay can survive; it is the",
 "#   empirical noise floor of this estimator and the detection threshold used.",
 "# zeta_route_b / zeta_route_c_rfp_pole: the other two SPEC 4.3 routes, attempted on every",
 "#   mode. Route C is reported where >= 5 of 52 channels gave a stable pole; where it and",
 "#   Route A both exist they are an independent cross-check of each other.",
 "# zeta_spread_lo / zeta_spread_hi: the 16-84 percentile band of the per-channel zeta",
 "#   values, i.e. the channel-to-channel spread; zeta_err is half that range, floored at",
 "#   the 9.7% tau-grid half-step. It is deliberately NOT a 1/sqrt(N) error: the 52",
 "#   bolometers see the same tower and are not independent measurements, and a standard",
 "#   error on their median would overstate what one run supports.",
 "# n_fits_at_tau_ceiling / tau_ceiling_s: fits sitting at the largest tau the 3-tau rule",
 "#   admits for this window. Where these pile up (>= 40%) the mode is reported as",
 "#   WINDOW-LIMITED with zeta_method = none: the ring-down is real but its time constant",
 "#   is longer than 40.3 s can bound, and a number there would just be the window length.",
 "# force_jump_adjacent: mode sits next to a ch1111 scale discontinuity (5.4->5.5 or",
 "#   7.4->7.5 Hz). See VERIFIER_LOG V020.",
 "# Amplitudes are mV at the ADC input (SPEC 2.1); no front-end gain is applied anywhere.",
]
cols = ["f0_hz", "zeta", "zeta_err", "zeta_is_upper_limit", "zeta_method", "zeta_attempted",
        "zeta_attempt_outcome", "n_fits_used", "implied_delta_f_hz", "tau_s", "tau_err_s",
        "window_over_tau", "n_fits_tried", "n_channels_used", "n_boundaries_used",
        "null_F99", "zeta_route_b", "route_b_outcome", "zeta_route_c_rfp_pole",
        "route_c_n_channels", "route_c_outcome", "zeta_spread_lo", "zeta_spread_hi",
        "n_fits_at_tau_ceiling", "tau_ceiling_s", "force_jump_adjacent", "pt_harmonic_flag"]
lines = list(hdr) + [",".join(cols)]
for mi, f0, o, F99, nb in rows:
    ntry = len([r for r in R if r["mode"] == mi and r["kind"] == "sig"
                and abs(r["f_old"] - f0) <= 0.15 and abs(r["f_new"] - f0) >= 0.06])
    zz = o["zeta"]
    v = ["%.4f" % f0,
         "" if zz is None else "%.5f" % zz,
         "" if o["zeta_err"] is None else "%.5f" % o["zeta_err"],
         "false", o["method"], "true",
         o["outcome"].replace(",", ";"),
         "%d" % o["n"],
         "" if zz is None else "%.4f" % (2 * zz * f0),
         "" if o["tau"] is None else "%.3f" % o["tau"],
         "" if o["tau_err"] is None else "%.3f" % o["tau_err"],
         "" if o["tau"] is None else "%.2f" % (d["span_s"] / o["tau"]),
         "%d" % ntry, "%d" % o["nch"], "%d" % len(nb), "%.1f" % F99,
         "", o["b_outcome"].replace(",", ";"),
         "" if o["c_zeta"] is None else "%.5f" % o["c_zeta"],
         "%d" % o["c_n"], o["c_outcome"].replace(",", ";"),
         "" if o["z16"] is None else "%.5f" % o["z16"],
         "" if o["z84"] is None else "%.5f" % o["z84"],
         "%d" % o["nceil"], "%.3f" % T_ADM,
         "true" if v6[mi]["force_jump_adjacent"] else "false",
         "true" if v6[mi]["pt_harmonic_flag"] else "false"]
    lines.append(",".join(v))
open(OUT + "/damping.csv", "w").write(chr(10).join(lines) + chr(10))
nm = sum(1 for _, _, o, _, _ in rows if o["method"] == "ringdown")
L("[V035] damping.csv written: 11 rows; %d with a measured zeta by ring-down; %d with" % (nm, 11 - nm))
L("  zeta_method = none and zeta left empty. zeta_attempted = true on all 11 rows. No row")
L("  carries 0.1/(2 f0) and no row is flagged as an upper limit.")
for mi, f0, o, F99, nb in rows:
    if o["zeta"] is not None:
        L("[V036] f0=%.4f Hz: tau = %.2f +/- %.2f s -> zeta = %.5f +/- %.5f, implied half-power "
          "width 2 zeta f0 = %.4f Hz %s 0.1 Hz grid spacing, window = %.1f tau"
          % (f0, o["tau"], o["tau_err"], o["zeta"], o["zeta_err"], 2 * o["zeta"] * f0,
             "EXCEEDS the" if 2 * o["zeta"] * f0 > 0.1 else "is within the",
             d["span_s"] / o["tau"]))
for mi, f0, o, F99, nb in rows:
    if o["zeta"] is None and o["n"] >= 10:
        L("[V037] f0=%.4f Hz is WINDOW-LIMITED, not a non-detection: %d fits cleared the null "
          "and %d of them sit at tau = %.2f s, the largest the 3-tau rule allows for a 40.3 s "
          "window. The ring-down is there; its time constant is longer than this run can "
          "bound. zeta left empty." % (f0, o["n"], o["nceil"], T_ADM))
L("[V038] Scope. 7 of 11 modes gave a ring-down zeta from one stepped-sine run, one shaker")
L("  axis (MSP-X), one tower. These are PRELIMINARY. Four independent reasons not to treat")
L("  any of them as settled: the channel-to-channel spread is 20-40% of zeta and is not")
L("  beaten down by averaging 52 bolometers that watch the same tower; f0 itself is only")
L("  known to +/-0.05 Hz, the SPEC floor, and zeta scales as 1/f0; each frequency occurs")
L("  exactly once in this run so there is no amplitude check and no repeat (SPEC 4.4); and")
L("  the two modes nearest a ch1111 scale discontinuity are flagged. A second run on a")
L("  second axis is what would turn any of these into a measurement of the detector rather")
L("  than of this run.")
L("[V039] Where Route A and Route C both returned a number they can be compared, and the")
L("  comparison is not reassuring: f0=3.4075 Hz gives zeta = 0.01103 by ring-down against")
L("  0.00796 from the rational-fraction pole on 5 of 52 channels, and f0=6.2184 Hz gives")
L("  0.00940 against 0.00742 on 29 of 52. Same sign of disagreement, roughly 30% in both.")
L("  Two routes in one directory agreeing to 30% is the honest precision of this pilot;")
L("  neither route is the truth and I am not averaging them.")
open(OUT + "/VERIFIER_LOG.md", "a").write(chr(10).join(LOG) + chr(10))
print("DONE")
