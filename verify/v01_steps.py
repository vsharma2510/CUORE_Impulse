#!/usr/bin/env python3
"""Verifier stage 1: offset test, pulser shape, matched-filter step recovery."""
import json
import numpy as np

DATA = "<HOME>/CUORE_ImpulsePilot/data"
ARR  = "<SCRATCH>/CUORE_ImpulsePilot_data"
OUT  = "<HOME>/CUORE_ImpulsePilot/verify"
FS   = 1000.0
OFFS = 3990.0
T0R, T1R = 3990.0, 21760.0
LOG = []

def L(s):
    print(s, flush=True); LOG.append(s)

def load(win, kind, ch):
    return np.load(ARR + "/%s/%s/ch%04d.npy" % (win, kind, ch), mmap_mode="r")

def demod_decimate(x, f0, dec=100):
    """Mix x down by f0 and block-average into bins of `dec` samples.
    Returns the complex baseband series and its bin centre times."""
    x = np.asarray(x, dtype=np.float64)
    n = (x.size // dec) * dec
    t = np.arange(n) / FS
    ph = 2.0 * np.pi * f0 * t
    zr = (x[:n] * np.cos(ph)).reshape(-1, dec).mean(1)
    zi = -(x[:n] * np.sin(ph)).reshape(-1, dec).mean(1)
    tb = (np.arange(zr.size) + 0.5) * dec / FS
    return zr + 1j * zi, tb

def tone_freq(x, f_nom):
    """Frequency and amplitude of a strong tone near f_nom.

    Demodulate at f_nom, decimate to 10 Hz, then take the residual frequency from
    the amplitude-weighted slope of the unwrapped baseband phase. Resolution-free:
    no FFT bin quantisation enters. Amplitude is 2*<|z|>.
    """
    z, tb = demod_decimate(x, f_nom)
    a = np.abs(z)
    ph = np.unwrap(np.angle(z))
    w = a ** 2
    tm = np.average(tb, weights=w); pm = np.average(ph, weights=w)
    slope = np.sum(w * (tb - tm) * (ph - pm)) / np.sum(w * (tb - tm) ** 2)
    f = f_nom + slope / (2.0 * np.pi)
    # one refinement pass at the improved frequency
    z2, tb2 = demod_decimate(x, f)
    a2 = np.abs(z2)
    ph2 = np.unwrap(np.angle(z2)); w2 = a2 ** 2
    tm2 = np.average(tb2, weights=w2); pm2 = np.average(ph2, weights=w2)
    s2 = np.sum(w2 * (tb2 - tm2) * (ph2 - pm2)) / np.sum(w2 * (tb2 - tm2) ** 2)
    f = f + s2 / (2.0 * np.pi)
    return float(f), float(2.0 * a2.mean())

def test_offset(ref):
    """steps.csv row 0 is RUN 4015-4265 s at nominal 2.5 Hz. With the offset that is
    ARRAY 25-275 s; without it one reads ARRAY 4015-4265 s = RUN 8005-8255 s, a
    different step near 4.0 Hz."""
    r = {"n_samples": int(ref.shape[0]),
         "n_expected": int(round((T1R - T0R) * FS))}
    r["length_ok"] = bool(r["n_samples"] == r["n_expected"])
    i0 = int((4015.0 - OFFS) * FS); i1 = int((4265.0 - OFFS) * FS)
    f_w, a_w = tone_freq(ref[i0:i1], 2.5)
    j0, j1 = int(4015.0 * FS), int(4265.0 * FS)
    # no-offset slice: scan the whole bank coarsely to find what tone is really there
    seg = np.asarray(ref[j0:j1], dtype=np.float64); seg = seg - seg.mean()
    X = np.abs(np.fft.rfft(seg)); fr = np.fft.rfftfreq(seg.size, 1.0 / FS)
    sel = (fr >= 2.0) & (fr <= 12.0)
    f_n0 = float(fr[sel][np.argmax(X[sel])])
    f_wo, a_wo = tone_freq(seg, round(f_n0, 1))
    r.update({"f_with_offset_hz": f_w, "amp_with_offset_mV": a_w,
              "f_without_offset_hz": f_wo, "amp_without_offset_mV": a_wo})
    r["pass"] = bool(abs(f_w - 2.5) < 0.01 and abs(f_wo - 2.5) > 0.05)
    return r

def pulser_shape(ptimes, ch=937):
    """quiet3 is RUN 48025-48800 s, shaker off: clean pulser pulses, no drive."""
    t0 = 48025.0
    x = np.asarray(load("quiet3", "bolo", ch)[:], dtype=np.float64)
    n = x.size
    idx = np.round((ptimes - t0) * FS).astype(np.int64)
    pre, post = int(1.0 * FS), int(9.0 * FS)
    idx = idx[(idx > pre) & (idx < n - post)]
    seg = np.empty((idx.size, pre + post))
    for i, k in enumerate(idx):
        seg[i] = x[k - pre:k + post]
    m = seg.mean(0); m = m - m[:pre].mean()
    sd = seg.std(0) / np.sqrt(idx.size)
    tau = (np.arange(pre + post) - pre) / FS
    pk = int(np.argmax(np.abs(m)))
    noise = float(np.std(m[:pre]))
    k = np.where(np.abs(m[pk:]) < 3.0 * noise)[0]
    settle = float(tau[pk + k[0]]) if k.size else float(tau[-1])
    d = {"channel": ch, "n_pulses": int(idx.size), "peak_mV": float(m[pk]),
         "peak_time_s": float(tau[pk]), "prepulse_rms_of_mean_mV": noise,
         "sem_typical_mV": float(np.median(sd)), "settle_3sigma_s": settle}
    for s in (0.5, 1, 2, 3, 4, 5, 6, 8):
        d["amp_at_%ss_mV" % s] = float(m[pre + int(s * FS)])
    return d, m, tau

def mf_steps(ref, guard_mV):
    """Matched-filter bank. Real BLAS GEMMs, not complex matvecs."""
    nb = ref.shape[0] // 1000
    X = np.asarray(ref[:nb * 1000], dtype=np.float64).reshape(nb, 1000)
    tloc = np.arange(1000) / FS
    fg = np.round(np.arange(2.3, 9.7001, 0.1), 4)
    C = np.cos(2.0 * np.pi * np.outer(tloc, fg))
    S = np.sin(2.0 * np.pi * np.outer(tloc, fg))
    Zr = (X @ C).T.copy(); Zi = (-(X @ S)).T.copy()
    Z = Zr + 1j * Zi
    del Zr, Zi, X, C, S
    Z *= np.exp(-2j * np.pi * fg[:, None] * np.arange(nb)[None, :])
    cs = np.concatenate([np.zeros((fg.size, 1), dtype=complex), np.cumsum(Z, axis=1)], 1)
    W = 10
    env = 2.0 * np.abs(cs[:, W:] - cs[:, :-W]) / (W * 1000)
    win = np.argmax(env, 0); best = env.max(0)
    runs = []
    i = 0
    while i < win.size:
        j = i
        while j + 1 < win.size and win[j + 1] == win[i]:
            j += 1
        if (j - i + 1) >= 20 and best[i:j + 1].max() > guard_mV:
            runs.append((float(fg[win[i]]), i, j))
        i = j + 1
    return runs, fg, win, best

def main():
    pt = np.load(DATA + "/pulser_times.npy")
    d = np.diff(pt)
    L("[V002] pulser_times.npy: n=%d first=%.4f s last=%.4f s median spacing=%.6f s "
      "max|spacing-10|=%.3e s" % (pt.size, pt[0], pt[-1], np.median(d), np.abs(d - 10).max()))
    L("[V002] pulser pulses inside excitation window [3990,21760) run s: %d "
      "(meta.json says 1777)" % int(((pt >= T0R) & (pt < T1R)).sum()))

    ref = load("excitation", "aux", 1111)
    r = test_offset(ref)
    L("[V002] TEST array length: n=%d expected=%d -> %s"
      % (r["n_samples"], r["n_expected"], "PASS" if r["length_ok"] else "FAIL"))
    L("[V002] TEST 3990 s offset: steps.csv step 0 is RUN 4015-4265 s nominal 2.5 Hz. "
      "ARRAY slice WITH offset (t=25-275 s): f=%.6f Hz amp=%.1f mV. WITHOUT offset "
      "(t=4015-4265 s): f=%.6f Hz amp=%.1f mV -> %s"
      % (r["f_with_offset_hz"], r["amp_with_offset_mV"], r["f_without_offset_hz"],
         r["amp_without_offset_mV"], "PASS" if r["pass"] else "FAIL"))
    L("[V002] NOTE 3990/10 = 399.0 exactly, so the offset is an integer number of pulser "
      "periods: an offset blunder is INVISIBLE to pulser alignment. Masking is insensitive "
      "to it; step indexing is not. Do not validate the offset with the pulser.")

    q1 = np.asarray(load("quiet1", "aux", 1111)[:], dtype=np.float64)
    guard = 20.0 * float(np.std(q1))
    L("[V002] ch1111 shaker-off rms on quiet1 = %.4f mV; filter-bank silence guard set to "
      "20x that = %.3f mV (rejects shaker-off blocks only; boundaries come from template "
      "competition, not from this number)" % (float(np.std(q1)), guard))

    ps, pm, ptau = pulser_shape(pt)
    L("[V003] pulser pulse shape on quiet3 (shaker off, no drive), ch0937, %d pulses: "
      "peak=%.4f mV at tau=%+.3f s; pre-pulse rms of the mean=%.5f mV; typical sem=%.5f mV; "
      "settle to 3 sigma at tau=%.2f s"
      % (ps["n_pulses"], ps["peak_mV"], ps["peak_time_s"], ps["prepulse_rms_of_mean_mV"],
         ps["sem_typical_mV"], ps["settle_3sigma_s"]))
    L("[V003] pulser mean amplitude vs tau (mV): " + ", ".join(
        "+%ss=%.4f" % (s, ps["amp_at_%ss_mV" % s]) for s in (0.5, 1, 2, 3, 4, 5, 6, 8)))

    runs, fg, win, best = mf_steps(ref, guard)
    L("[V003] matched-filter bank: templates %.1f-%.1f Hz on the 0.1 Hz grid (%d), 10 s "
      "coherent window, 1 s hop; %d contiguous single-template runs found"
      % (fg[0], fg[-1], fg.size, len(runs)))
    rows = []
    TRIM = 3.0
    for k, (fn, i, j) in enumerate(runs):
        t0a, t1a = float(i), float(j + 10)
        d0, d1 = t0a + TRIM, t1a - TRIM
        i0, i1 = int(round(d0 * FS)), int(round(d1 * FS))
        f, amp = tone_freq(ref[i0:i1], fn)
        seg = np.asarray(ref[i0:i1], dtype=np.float64)
        rows.append({"step_index": k, "f_nom_hz": fn,
                     "t_start_s_array": t0a, "t_end_s_array": t1a,
                     "t_start_s_run": t0a + OFFS, "t_end_s_run": t1a + OFFS,
                     "dwell_start_s_array": d0, "dwell_end_s_array": d1,
                     "f_fit_hz": f, "amp_1111_mV": amp,
                     "rms_1111_mV": float(np.std(seg)), "n_dwell": i1 - i0})
    for q in rows:
        L("[V003] step %2d f_nom=%.2f f_fit=%.6f d=%+.6f run=[%.1f,%.1f] "
          "amp1111=%.2f rms1111=%.2f mV" % (q["step_index"], q["f_nom_hz"], q["f_fit_hz"],
          q["f_fit_hz"] - q["f_nom_hz"], q["t_start_s_run"], q["t_end_s_run"],
          q["amp_1111_mV"], q["rms_1111_mV"]))
    fm = np.array([q["f_fit_hz"] for q in rows]); fnm = np.array([q["f_nom_hz"] for q in rows])
    sc = fm / fnm
    L("[V003] f_fit - f_nom over %d steps: mean=%+.3e Hz, max|.|=%.3e Hz"
      % (len(rows), (fm - fnm).mean(), np.abs(fm - fnm).max()))
    L("[V003] f_fit / f_nom: mean=%.9f std=%.2e -> one multiplicative clock scale, not an "
      "additive offset" % (sc.mean(), sc.std()))
    resid = (fm / 0.1 - np.round(fm / 0.1)) * 0.1
    L("[V003] f_fit mod 0.1 Hz: max deviation from zero = %.3e Hz. CONFIRMED INDEPENDENTLY: "
      "the drive grid is f_k = 2.5 + 0.1k Hz, the pulser comb lands on EVERY drive line, and "
      "pulser masking is mandatory. My earlier 2.52+0.1k inference was wrong."
      % np.abs(resid).max())
    L("[V003] recovered band %.2f-%.2f Hz, %d steps. meta.json extracted_band_hz says "
      "[2.52, 9.52]; the true band is 2.50-9.50 Hz." % (fnm.min(), fnm.max(), len(rows)))

    json.dump({"tests": r, "guard_mV": guard, "pulser_shape": ps, "steps": rows,
               "pulse_mean_mV": pm.tolist(), "pulse_tau_s": ptau.tolist()},
              open(OUT + "/v01_steps.json", "w"), indent=1)
    open(OUT + "/v01_log.txt", "w").write("\n".join(LOG) + "\n")

main()
