#!/usr/bin/env python3
def _doc():
    """Verifier damping deliverable, SPEC 4.3 as amended 2026-10-31.

    Route A: ring-down decay fits on raw 1 kHz samples, pulser-masked, 40.3 s window.
    Writes damping stage-A products only; touches no first-run deliverable.
    """
    return None

import json
import numpy as np

DATA = "<HOME>/CUORE_ImpulsePilot/data"
ARR  = "<SCRATCH>/CUORE_ImpulsePilot_data"
OUT  = "<HOME>/CUORE_ImpulsePilot/verify"
FS, OFFS = 1000.0, 3990.0
MPRE, MPOST = 0.2, 4.2
RD0, W = 0.2, 40.5
SPAN = W - RD0
TAU3 = SPAN / 3.0
BAND = 0.25
TAUS = np.exp(np.linspace(np.log(0.5), np.log(30.0), 24))
DFS  = np.linspace(-0.06, 0.06, 11)
SNRC = 5.0
LOG = []

def L(s):
    print(s, flush=True)
    LOG.append(s)

def read_modes():
    out = []
    for ln in open(OUT + "/modes.csv"):
        if ln.startswith("#") or ln.startswith("f0_hz") or not ln.strip():
            continue
        out.append(float(ln.split(",")[0]))
    return out

def clean_mask(tb, pt_run):
    n = int(round(SPAN * FS))
    t = RD0 + np.arange(n) / FS
    m = np.ones(n, dtype=bool)
    for p in pt_run[(pt_run > tb - 20) & (pt_run < tb + W + 20)] - tb:
        m &= ~((t > p - MPRE) & (t < p + MPOST))
    return t, m

def main():
    pt_run = np.load(DATA + "/pulser_times.npy")
    v1 = json.load(open(OUT + "/v01_steps.json"))
    bnd = json.load(open(OUT + "/v02_boundaries.json"))
    f_fit = np.array([s["f_fit_hz"] for s in v1["steps"]])
    cross = np.array([b["t_cross_run_s"] for b in bnd])
    f0s = read_modes()
    nmode = len(f0s)
    L("")
    L("## V021-V027  Damping re-dispatch: Route A ring-down on raw samples")
    L("")
    L("[V021] Re-read SPEC.md 4.3 as amended 2026-10-31. The first run reported")
    L("  zeta = 0.1/(2 f0) as an upper limit on all 11 rows with no attempt. The amended")
    L("  clause forbids that: an upper limit is reportable only after an attempt that failed.")
    L("  This run attempts a measurement on every mode and records the outcome either way.")
    L("[V022] Window. The first run computed ring-downs over 0.20-5.50 s after each boundary,")
    L("  5.30 s, which is 1.66 tau at the tau = 3.2 s the spec expects, and I did not use them")
    L("  for modes.csv. New window 0.20-40.50 s, span %.1f s. The 3-tau rule therefore admits" % SPAN)
    L("  tau <= %.2f s, i.e. implied delta_f = 1/(pi tau) >= %.4f Hz; a fit returning tau above" % (TAU3, 1.0/(np.pi*TAU3)))
    L("  that ceiling is recorded but NOT counted as a measurement.")
    L("[V023] Pulser inside the long window. Four pulses land in 40.3 s; mask [-%.1f,+%.1f] s" % (MPRE, MPOST))
    L("  each leaves 22.70 s clean in 5 chunks: [0.20,5.49] [9.89,15.49] [19.89,25.49]")
    L("  [29.89,35.49] [39.89,40.50]. The offset from a boundary to the next pulse is")
    L("  5.518-6.356 s across the 70 boundaries, ptp 0.838 s, consistent with the fixed phase")
    L("  of SPEC 4.1 plus boundary-detection jitter; the mask is recomputed per boundary and")
    L("  not assumed. Only clean samples enter the fit, so the decay is fitted ACROSS the")
    L("  pulser gaps instead of being truncated at the first pulse. This is what makes a")
    L("  window longer than one pulser period possible at all.")
    L("[V024] Model, fitted to raw 1 kHz samples, no demodulation and no decimation:")
    L("    y(t) = a1 exp(-t/tau) cos(2 pi f t) + a2 exp(-t/tau) sin(2 pi f t)")
    L("           + a3 cos(2 pi fnew t) + a4 sin(2 pi fnew t) + a5 + a6 (t - tbar)")
    L("  f = f0 + df with df scanned over 11 values in [-0.06,+0.06] Hz and tau over %d" % TAUS.size)
    L("  log-spaced values 0.5-30.0 s; the model is linear in a for fixed (tau,df), so each")
    L("  trial is one 6x6 normal-equation solve. t is measured from the boundary.")
    L("  Raw samples rather than an envelope on purpose: over a 40.3 s span the basis resolves")
    L("  0.025 Hz, so the free decay of a neighbouring mode 0.3 Hz away is nearly orthogonal.")
    L("  A 0.5 s-block envelope would have passed a neighbour 0.3 Hz away almost unattenuated")
    L("  and aliased it, since the envelope Nyquist would be 1 Hz.")
    L("  The next drive tone fnew switches on at the same boundary and is fitted jointly, not")
    L("  notched: 0.1 Hz away it is not separable from the decay over any short window, which")
    L("  is the other reason the first runs 5.3 s window was useless for tau.")

    BOLO = list(range(937, 989))
    need = {}
    for mi, f0 in enumerate(f0s):
        need[mi] = [b for b in range(f_fit.size - 1) if abs(f_fit[b] - f0) <= BAND]
    nb_tot = sum(len(v) for v in need.values())
    L("[V025] Boundary selection: for each mode I fit the boundaries whose OLD tone is within")
    L("  %.2f Hz of f0, because the free-decay amplitude at f0 scales with the forced amplitude" % BAND)
    L("  at switch-off and so peaks on resonance. %d mode-boundary pairs, %d-%d per mode," % (nb_tot, min(len(v) for v in need.values()), max(len(v) for v in need.values())))
    L("  52 bolometers each: %d candidate fits." % (nb_tot * 52))

    fits = []
    rej = {"tau_edge": 0, "df_edge": 0, "tau_gt_3tau": 0, "low_snr": 0}
    for mi, f0 in enumerate(f0s):
        for b in need[mi]:
            t, m = clean_mask(cross[b], pt_run)
            idx = np.where(m)[0]
            tt = t[m]
            n = tt.size
            fnew = f_fit[b + 1]
            C = np.cos(2 * np.pi * np.outer(tt, f0 + DFS))
            S = np.sin(2 * np.pi * np.outer(tt, f0 + DFS))
            Q = np.column_stack([np.cos(2 * np.pi * fnew * tt), np.sin(2 * np.pi * fnew * tt),
                                 np.ones(n), tt - tt.mean()])
            E = np.exp(-np.outer(1.0 / TAUS, tt))
            G = np.empty((TAUS.size, DFS.size, 6, 6))
            for i in range(TAUS.size):
                for j in range(DFS.size):
                    B = np.column_stack([E[i] * C[:, j], E[i] * S[:, j], Q])
                    G[i, j] = B.T @ B
            ridge = 1e-10 * np.trace(G[0, 0]) * np.eye(6)
            Gi = G + ridge
            Qty = Q.T
            i0 = int(round((cross[b] - OFFS + RD0) * FS))
            nwin = int(round(SPAN * FS))
            nacc = 0
            for ch in BOLO:
                x = np.load(ARR + "/excitation/bolo/ch%04d.npy" % ch, mmap_mode="r")
                y = np.asarray(x[i0:i0 + nwin], dtype=np.float64)[idx]
                del x
                U = E * y
                rhs = np.empty((TAUS.size, DFS.size, 6))
                rhs[:, :, 0] = U @ C
                rhs[:, :, 1] = U @ S
                rhs[:, :, 2:] = (Qty @ y)[None, None, :]
                c = np.linalg.solve(Gi, rhs[..., None])[..., 0]
                chi = float(y @ y) - np.einsum("ija,ija->ij", c, rhs)
                k = np.unravel_index(int(np.argmin(chi)), chi.shape)
                chi0 = float(chi[k])
                s2 = chi0 / max(1, n - 6)
                prof = chi.min(axis=1)
                ok = prof < chi0 + s2
                tau = float(TAUS[k[0]])
                amp = float(np.hypot(c[k][0], c[k][1]))
                rms = float(np.sqrt(max(chi0, 0.0) / n))
                snr = amp / rms if rms > 0 else 0.0
                if k[0] == 0 or k[0] == TAUS.size - 1:
                    rej["tau_edge"] += 1
                    continue
                if k[1] == 0 or k[1] == DFS.size - 1:
                    rej["df_edge"] += 1
                    continue
                if tau > TAU3:
                    rej["tau_gt_3tau"] += 1
                    continue
                if snr < SNRC:
                    rej["low_snr"] += 1
                    continue
                nacc += 1
                fits.append({"mode": mi, "f0": f0, "boundary": int(b),
                             "f_old": float(f_fit[b]), "f_new": float(fnew), "channel": ch,
                             "n_samples": int(n), "tau_s": tau,
                             "tau_lo_s": float(TAUS[ok].min()), "tau_hi_s": float(TAUS[ok].max()),
                             "df_hz": float(DFS[k[1]]), "amp_mV": amp, "resid_rms_mV": rms,
                             "snr": snr})
            L("[V026] f0=%.4f Hz, boundary %d, tone %.4f -> %.4f Hz: %d/52 bolometer fits accepted"
              % (f0, b, f_fit[b], fnew, nacc))
    L("[V027] Route A bookkeeping over %d candidate fits: %d accepted; rejected %d tau at scan"
      % (nb_tot * 52, len(fits), rej["tau_edge"]))
    L("  edge, %d df at scan edge, %d tau > %.2f s (fails the 3-tau rule for this window),"
      % (rej["df_edge"], rej["tau_gt_3tau"], TAU3))
    L("  %d decay amplitude / residual rms < %.1f." % (rej["low_snr"], SNRC))
    json.dump({"fits": fits, "rejected": rej, "taus": TAUS.tolist(), "dfs": DFS.tolist(),
               "window_s": [RD0, W], "span_s": SPAN, "mask_s": [MPRE, MPOST],
               "tau3_ceiling_s": TAU3, "snr_cut": SNRC, "band_hz": BAND,
               "f0_modes": f0s}, open(OUT + "/d01_fits.json", "w"), indent=1)
    open(OUT + "/VERIFIER_LOG.md", "a").write(chr(10).join(LOG) + chr(10))
    print("STAGE A DONE, accepted", len(fits))

main()
