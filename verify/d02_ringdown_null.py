#!/usr/bin/env python3
def _doc():
    """Stage B: same ring-down fit, with a formal detection statistic and a null.

    For every (mode, boundary, bolometer) the identical 6-parameter model is fitted
    (i) in the post-boundary window, where a free decay at f0 should exist, and
    (ii) in a null window 120 s later in the same dwell, where it must not.
    Nothing is cut here; every fit is recorded and the decision is made in stage C.
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
NULL0 = 120.2
SPAN = W - RD0
TAU3 = SPAN / 3.0
BAND = 0.25
TAUS = np.exp(np.linspace(np.log(0.5), np.log(30.0), 24))
DFS  = np.linspace(-0.06, 0.06, 11)
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

def clean(tb, t0, pt_run):
    n = int(round(SPAN * FS))
    t = t0 + np.arange(n) / FS
    m = np.ones(n, dtype=bool)
    for p in pt_run[(pt_run > tb + t0 - 20) & (pt_run < tb + t0 + SPAN + 20)] - tb:
        m &= ~((t > p - MPRE) & (t < p + MPOST))
    return t, m

def design(tt, f0, fnew):
    n = tt.size
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
    Gi = G + 1e-11 * np.trace(G[0, 0]) * np.eye(6)
    Ginv = np.linalg.inv(Gi)
    GQ = Q.T @ Q
    return C, S, Q, E, Gi, Ginv, GQ

def one(y, C, S, Q, E, Gi, Ginv, GQ):
    n = y.size
    rhs = np.empty((TAUS.size, DFS.size, 6))
    U = E * y
    rhs[:, :, 0] = U @ C
    rhs[:, :, 1] = U @ S
    rhs[:, :, 2:] = (Q.T @ y)[None, None, :]
    c = np.linalg.solve(Gi, rhs[..., None])[..., 0]
    yty = float(y @ y)
    chi = yty - np.einsum("ija,ija->ij", c, rhs)
    k = np.unravel_index(int(np.argmin(chi)), chi.shape)
    chi0 = float(chi[k])
    s2 = chi0 / max(1, n - 6)
    prof = chi.min(axis=1)
    ok = prof < chi0 + s2
    amp = float(np.hypot(c[k][0], c[k][1]))
    gv = Ginv[k]
    sa = float(np.sqrt(s2 * 0.5 * (gv[0, 0] + gv[1, 1])))
    cq = np.linalg.solve(GQ, Q.T @ y)
    chiq = yty - float((Q.T @ y) @ cq)
    F = ((chiq - chi0) / 2.0) / s2
    return {"tau_s": float(TAUS[k[0]]), "tau_lo_s": float(TAUS[ok].min()),
            "tau_hi_s": float(TAUS[ok].max()), "i_tau": int(k[0]), "j_df": int(k[1]),
            "df_hz": float(DFS[k[1]]), "amp_mV": amp, "amp_sig_mV": sa,
            "amp_snr": amp / sa if sa > 0 else 0.0, "F_decay": float(F),
            "resid_rms_mV": float(np.sqrt(max(chi0, 0.0) / n)), "n": int(n)}

def main():
    pt_run = np.load(DATA + "/pulser_times.npy")
    v1 = json.load(open(OUT + "/v01_steps.json"))
    bnd = json.load(open(OUT + "/v02_boundaries.json"))
    f_fit = np.array([s["f_fit_hz"] for s in v1["steps"]])
    cross = np.array([b["t_cross_run_s"] for b in bnd])
    f0s = read_modes()
    BOLO = list(range(937, 989))
    L("")
    L("## V028-V031  Damping: detection statistic and null control")
    L("")
    L("[V028] My stage-A cut was ill-posed and I am replacing it, not keeping it. I had cut on")
    L("  decay amplitude over the BROADBAND residual rms, but the raw 1 kHz residual is")
    L("  dominated by out-of-band bolometer noise and has nothing to do with the error on a")
    L("  narrowband amplitude. Replaced by two proper statistics: amp / sigma_amp from the")
    L("  least-squares covariance s2 * inv(BtB), and an F statistic for the 2 decay columns,")
    L("  F = ((chi2_without_decay - chi2_with) / 2) / s2, which tests whether a decaying")
    L("  component at f0 is present at all.")
    L("[V029] Because bolometer noise is not white, a formal sigma underestimates the true")
    L("  error. So every fit is repeated as a NULL: the identical 6-parameter model, same")
    L("  channel, same f0, same pulser geometry, in a window starting %.1f s after the" % NULL0)
    L("  boundary instead of %.1f s. By then any free decay with tau < 13 s is gone by more" % RD0)
    L("  than 9 e-foldings, so whatever amplitude and F the null returns is the noise floor of")
    L("  this estimator on this detector. A mode is only called measured if its boundary fits")
    L("  stand clear of its own null distribution.")
    need = {}
    for mi, f0 in enumerate(f0s):
        need[mi] = [b for b in range(f_fit.size - 1) if abs(f_fit[b] - f0) <= BAND]
    recs = []
    nwin = int(round(SPAN * FS))
    for mi, f0 in enumerate(f0s):
        for b in need[mi]:
            fnew = f_fit[b + 1]
            packs = {}
            for tag, t0 in (("sig", RD0), ("null", NULL0)):
                t, m = clean(cross[b], t0, pt_run)
                idx = np.where(m)[0]
                packs[tag] = (idx, design(t[m], f0, fnew),
                              int(round((cross[b] - OFFS + t0) * FS)))
            for ch in BOLO:
                x = np.load(ARR + "/excitation/bolo/ch%04d.npy" % ch, mmap_mode="r")
                for tag in ("sig", "null"):
                    idx, dz, i0 = packs[tag]
                    y = np.asarray(x[i0:i0 + nwin], dtype=np.float64)[idx]
                    r = one(y, *dz)
                    r.update({"mode": mi, "f0": f0, "boundary": int(b),
                              "f_old": float(f_fit[b]), "f_new": float(fnew),
                              "channel": ch, "kind": tag})
                    recs.append(r)
                del x
            sg = [r for r in recs if r["mode"] == mi and r["boundary"] == b and r["kind"] == "sig"]
            nl = [r for r in recs if r["mode"] == mi and r["boundary"] == b and r["kind"] == "null"]
            L("[V030] f0=%.4f b=%d tone %.4f->%.4f : median F sig=%.1f null=%.1f ; median amp_snr "
              "sig=%.1f null=%.1f ; median tau sig=%.2f s"
              % (f0, b, f_fit[b], fnew, np.median([r["F_decay"] for r in sg]),
                 np.median([r["F_decay"] for r in nl]),
                 np.median([r["amp_snr"] for r in sg]), np.median([r["amp_snr"] for r in nl]),
                 np.median([r["tau_s"] for r in sg])))
    json.dump({"recs": recs, "taus": TAUS.tolist(), "dfs": DFS.tolist(),
               "window_s": [RD0, RD0 + SPAN], "null_window_s": [NULL0, NULL0 + SPAN],
               "span_s": SPAN, "mask_s": [MPRE, MPOST], "tau3_ceiling_s": TAU3,
               "band_hz": BAND, "f0_modes": f0s},
              open(OUT + "/d02_fits.json", "w"), indent=0)
    open(OUT + "/VERIFIER_LOG.md", "a").write(chr(10).join(LOG) + chr(10))
    print("STAGE B DONE", len(recs))

main()
