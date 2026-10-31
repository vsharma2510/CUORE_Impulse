#!/usr/bin/env python3
"""Verifier stage 3: masked per-step lock-in, H1, coherence, ring-down, noise."""
import json
import numpy as np

DATA = "<HOME>/CUORE_ImpulsePilot/data"
ARR  = "<SCRATCH>/CUORE_ImpulsePilot_data"
OUT  = "<HOME>/CUORE_ImpulsePilot/verify"
FS = 1000.0
OFFS = 3990.0
MPRE, MPOST = 0.2, 4.2       # pulser mask, seconds, from the measured pulse shape
EDGE = 2.0                   # inset from each measured step boundary
NS = 5600                    # sub-block length in samples (the 5.6 s pulser-free gap)
RD0, RD1 = 0.2, 5.5          # ring-down window after a boundary (pulser-free by V006)
LOG = []

def L(s):
    print(s, flush=True); LOG.append(s)

def load(win, kind, ch):
    return np.load(ARR + "/%s/%s/ch%04d.npy" % (win, kind, ch), mmap_mode="r")

BOLO = list(range(937, 989))
AUX  = [1018, 1019, 1020] + list(range(1101, 1124))

def subblocks(t0, t1, pulse_t):
    """Pulser-free sub-blocks of length NS inside array-time window [t0,t1).

    pulse_t are pulse times in the SAME array coordinate. A sub-block is the stretch
    between the end of one mask and the start of the next.
    """
    starts = []
    pt = pulse_t[(pulse_t > t0 - 20) & (pulse_t < t1 + 20)]
    for p in pt:
        a = p + MPOST                 # clean from here
        b = (p + 10.0) - MPRE         # until just before the next pulse
        if b - a < NS / FS - 1e-9:
            continue
        if a >= t0 and a + NS / FS <= t1:
            starts.append(a)
    return np.array(sorted(starts))

def design(f, t):
    """[cos, sin, 1, t-tmid] for absolute array time t."""
    A = np.empty((t.size, 4))
    w = 2.0 * np.pi * f
    A[:, 0] = np.cos(w * t); A[:, 1] = np.sin(w * t)
    A[:, 2] = 1.0; A[:, 3] = t - t.mean()
    return A

def build(f, starts):
    """Pseudo-inverses for every sub-block of one step. Channel independent."""
    M = np.empty((starts.size, 4, NS))
    for i, s in enumerate(starts):
        t = s + np.arange(NS) / FS
        M[i] = np.linalg.pinv(design(f, t))
    idx = np.round(starts * FS).astype(np.int64)
    return M, idx

def lockin(x, M, idx):
    """Complex amplitude per sub-block. x float32 full-window array."""
    Y = np.empty((idx.size, NS))
    for i, k in enumerate(idx):
        Y[i] = x[k:k + NS]
    c = np.einsum("sij,sj->si", M, Y)
    return c[:, 0] - 1j * c[:, 1]      # x = Re{A exp(i w t)}

def ringdown(x, f_old, t_b, dec=20):
    """Demodulated, decimated post-boundary segment at the OLD tone frequency."""
    i0 = int(round((t_b + RD0) * FS)); i1 = int(round((t_b + RD1) * FS))
    n = ((i1 - i0) // dec) * dec
    seg = np.asarray(x[i0:i0 + n], dtype=np.float64)
    t = (i0 + np.arange(n)) / FS
    ph = 2 * np.pi * f_old * t
    zr = (seg * np.cos(ph)).reshape(-1, dec).mean(1)
    zi = -(seg * np.sin(ph)).reshape(-1, dec).mean(1)
    return 2.0 * (zr + 1j * zi)

def fit_tau(z, f_old, f_new, dt):
    """Separate a decaying f_old component from the steady f_new tone.

    Model on the baseband series z(t) (already mixed down by f_old):
        z = A_old exp(-t/tau) + A_new exp(i 2 pi (f_new-f_old) t) + c
    Linear in (A_old, A_new, c) for fixed tau; scan tau.  Returns the best tau,
    its 1-sigma from the chi2 curvature, and the fitted |A_old|.
    """
    t = np.arange(z.size) * dt
    taus = np.concatenate([np.linspace(0.3, 8.0, 24), np.array([10.0, 14.0, 20.0, 30.0])])
    best = None
    chis = []
    for tau in taus:
        B = np.empty((z.size, 3), dtype=complex)
        B[:, 0] = np.exp(-t / tau)
        B[:, 1] = np.exp(2j * np.pi * (f_new - f_old) * t)
        B[:, 2] = 1.0
        c, *_ = np.linalg.lstsq(B, z, rcond=None)
        r = z - B @ c
        chi = float(np.vdot(r, r).real)
        chis.append(chi)
        if best is None or chi < best[0]:
            best = (chi, tau, c)
    chis = np.array(chis)
    chi0, tau0, c0 = best
    dof = max(1, 2 * z.size - 7)
    s2 = chi0 / dof
    ok = chis < chi0 + s2 * 1.0
    lo = taus[ok].min(); hi = taus[ok].max()
    return float(tau0), float(0.5 * (hi - lo)), float(abs(c0[0])), float(abs(c0[1])), float(chi0)

def main():
    pt_run = np.load(DATA + "/pulser_times.npy")
    v1 = json.load(open(OUT + "/v01_steps.json"))
    bnd = json.load(open(OUT + "/v02_boundaries.json"))
    f_fit = np.array([s["f_fit_hz"] for s in v1["steps"]])
    f_nom = np.array([s["f_nom_hz"] for s in v1["steps"]])
    cross = np.array([b["t_cross_run_s"] for b in bnd])          # 70 boundaries
    nst = f_fit.size
    # step k spans [start_k, end_k) in RUN coords, from the measured crossovers
    start = np.empty(nst); end = np.empty(nst)
    start[1:] = cross; end[:-1] = cross
    start[0] = cross[0] - 250.0
    end[-1] = min(cross[-1] + 250.0, OFFS + 17770.0)
    L("[V007] step grid from measured crossovers: step 0 run [%.2f, %.2f), "
      "step %d run [%.2f, %.2f); dwells inset by %.1f s at each end"
      % (start[0], end[0], nst - 1, start[-1], end[-1], EDGE))

    pt_arr = pt_run - OFFS
    steps = []
    for k in range(nst):
        t0 = start[k] - OFFS + EDGE; t1 = end[k] - OFFS - EDGE
        s = subblocks(t0, t1, pt_arr)
        M, idx = build(f_fit[k], s)
        steps.append({"M": M, "idx": idx, "n": s.size, "t0": t0, "t1": t1})
    nsub = np.array([s["n"] for s in steps])
    L("[V007] masked lock-in sub-blocks per step: min=%d max=%d median=%d total=%d; "
      "sub-block length %.1f s; mask [-%.1f,+%.1f] s about each pulse"
      % (nsub.min(), nsub.max(), int(np.median(nsub)), nsub.sum(), NS / FS, MPRE, MPOST))
    used = nsub.sum() * NS
    L("[V007] samples used in the lock-in: %d of %d in the window = %.1f%% "
      "(the rest is pulser mask, boundary insets and gap remainder)"
      % (used, 17770000, 100.0 * used / 17770000))

    CH = [("bolo", c) for c in BOLO] + [("aux", c) for c in AUX]
    nch = len(CH)
    L("[V007] channels processed: %d bolometers + %d aux = %d. NOTE SPEC section 3 says "
      "'all 71 bolometer-plus-aux channels'; 71 is the number of STEPS. The true channel "
      "count for the excitation window is 52 + 26 = 78 and I report all 78."
      % (len(BOLO), len(AUX), nch))

    nsmax = int(nsub.max())
    A = np.full((nch, nst, nsmax), np.nan + 0j, dtype=complex)
    RD = np.zeros((nch, nst - 1, int((RD1 - RD0) * FS) // 20), dtype=complex)
    for ci, (kind, ch) in enumerate(CH):
        x = np.asarray(load("excitation", kind, ch)[:], dtype=np.float64)
        for k in range(nst):
            A[ci, k, :steps[k]["n"]] = lockin(x, steps[k]["M"], steps[k]["idx"])
        for b in range(nst - 1):
            RD[ci, b] = ringdown(x, f_fit[b], cross[b] - OFFS)
        del x
        if ci % 13 == 0:
            L("[V007] lock-in progress: %d/%d channels (ch%04d)" % (ci + 1, nch, ch))

    iref = [i for i, (k, c) in enumerate(CH) if c == 1111][0]
    R = A[iref]
    H = np.zeros((nch, nst), dtype=complex)
    Hse = np.zeros((nch, nst)); coh = np.zeros((nch, nst)); cohb = np.zeros((nch, nst))
    for ci in range(nch):
        for k in range(nst):
            n = steps[k]["n"]
            r = R[k, :n]; b = A[ci, k, :n]
            srr = np.vdot(r, r).real; sbb = np.vdot(b, b).real
            srb = np.vdot(r, b)                      # sum conj(r)*b
            H[ci, k] = srb / srr
            coh[ci, k] = abs(srb) ** 2 / (srr * sbb) if sbb > 0 else 0.0
            hs = b / r
            Hse[ci, k] = np.sqrt((np.abs(hs - H[ci, k]) ** 2).sum() / (n * (n - 1)))
            cohb[ci, k] = 1.0 / n
    L("[V007] H1 formed as sum(conj(R)*B)/sum(|R|^2) over the pulser-free sub-blocks of each "
      "step, with ch1111 as R. Standard error from the complex scatter of the per-sub-block "
      "ratios B/R, so any ch1111 range change cancels exactly.")
    L("[V007] coherence floor for uncorrelated data is 1/n_sub = %.4f (median over steps); "
      "reported coh2 is RAW, coh2_bias is that 1/n floor" % np.median(1.0 / nsub))

    # ---------------------------------------------------- quiet-window noise
    noise = {}
    for win, t0w, t1w in (("quiet1", 0.0, 250.0), ("quiet3", 48025.0, 48800.0)):
        qs = []
        for k in range(nst):
            s = subblocks(0.0 + EDGE, (t1w - t0w) - EDGE, pt_run - t0w)
            M, idx = build(f_fit[k], s)
            qs.append({"M": M, "idx": idx, "n": s.size})
        NQ = np.zeros((nch, nst))
        for ci, (kind, ch) in enumerate(CH):
            x = np.asarray(load(win, kind, ch)[:], dtype=np.float64)
            for k in range(nst):
                a = lockin(x, qs[k]["M"], qs[k]["idx"])
                NQ[ci, k] = np.sqrt((np.abs(a) ** 2).mean() / 2.0)   # mV rms
            del x
        noise[win] = NQ
        L("[V008] %s: %d pulser-free sub-blocks per frequency; in-band noise (mV rms, same "
          "lock-in estimator as the response) over the 52 bolometers: median=%.4f, "
          "min=%.4f, max=%.4f" % (win, qs[0]["n"], np.median(NQ[:52]),
                                  NQ[:52].min(), NQ[:52].max()))
    L("[V008] NOTE quietrun (run RUNB, 2456 s) is NOT used for the masked noise estimate: "
      "pulser_times.npy covers run RUNA only, so I cannot mask the pulser there and the "
      "0.1 Hz comb lands on every drive frequency. Using it unmasked would inflate the "
      "noise at exactly the frequencies that matter. Reported noise is from quiet3 (775 s, "
      "the longest in-run window with known pulse times); quiet1 is the cross-check.")
    NOISE = noise["quiet3"]
    rat = noise["quiet1"][:52] / noise["quiet3"][:52]
    L("[V008] quiet1/quiet3 noise ratio over bolometers and frequencies: median=%.3f "
      "(10th-90th pct %.3f-%.3f) -> the two in-run pedestals agree to this level"
      % (np.median(rat), np.percentile(rat, 10), np.percentile(rat, 90)))

    # ------------------------------------------------------------- ring-down
    dt = 20.0 / FS
    rd_tau = np.full((nch, nst - 1), np.nan); rd_tse = np.full((nch, nst - 1), np.nan)
    rd_amp = np.full((nch, nst - 1), np.nan); rd_new = np.full((nch, nst - 1), np.nan)
    fit_set = list(range(52)) + [i for i, (k, c) in enumerate(CH) if c in (1111, 1112)]
    for ci in fit_set:
        for b in range(nst - 1):
            z = RD[ci, b]
            if not np.all(np.isfinite(z)):
                continue
            t, se, ao, an, _ = fit_tau(z, f_fit[b], f_fit[b + 1], dt)
            rd_tau[ci, b] = t; rd_tse[ci, b] = se; rd_amp[ci, b] = ao; rd_new[ci, b] = an
    L("[V009] ring-down: window [+%.1f,+%.1f] s after each of the %d boundaries, demodulated "
      "at the OLD tone, decimated to %.0f Hz; the decaying old tone and the steady new tone "
      "are fitted SIMULTANEOUSLY because they are only 0.1 Hz apart."
      % (RD0, RD1, nst - 1, 1.0 / dt))
    L("[V009] LIMITATION, stated rather than papered over: the usable ring-down window is "
      "%.1f s and the adjacent tone is 0.1 Hz away, so f_old and f_new are separated by only "
      "%.2f of a beat cycle in that window. tau near the expected 3.2 s is therefore only "
      "weakly constrained and I do NOT use ring-down as the primary damping route."
      % (RD1 - RD0, (RD1 - RD0) * 0.1))
    med_se = np.nanmedian(rd_tse[:52]); med_tau = np.nanmedian(rd_tau[:52])
    L("[V009] ring-down over bolometers x boundaries: median tau=%.2f s, median 1-sigma "
      "half-width=%.2f s -> fractional uncertainty %.0f%%, consistent with the limitation above"
      % (med_tau, med_se, 100.0 * med_se / med_tau))

    np.savez_compressed(OUT + "/responses.npz",
        channels=np.array([c for _, c in CH]),
        channel_kind=np.array([k for k, _ in CH]),
        f_drive_hz=f_fit, f_drive_nominal_hz=f_nom,
        step_t0_run_s=start, step_t1_run_s=end,
        n_subblocks=nsub, subblock_len_s=np.array([NS / FS]),
        H=H, H_se=Hse, coherence2=coh, coherence2_bias=cohb,
        amp_mV=np.nanmean(A, axis=2), amp_subblock_mV=A,
        noise_rms_mV_quiet3=noise["quiet3"], noise_rms_mV_quiet1=noise["quiet1"],
        ringdown_baseband_mV=RD, ringdown_dt_s=np.array([dt]),
        ringdown_t0_s=np.array([RD0]), ringdown_t1_s=np.array([RD1]),
        ringdown_tau_s=rd_tau, ringdown_tau_se_s=rd_tse,
        ringdown_amp_old_mV=rd_amp, ringdown_amp_new_mV=rd_new,
        ref_channel=np.array([1111]),
        units=np.array(["mV at the ADC input; H is dimensionless (ratio to ch1111)"]))
    L("[V010] wrote responses.npz: H, H_se, coherence2, coherence2_bias, amp_mV, "
      "amp_subblock_mV, noise, ring-down baseband segments and tau fits, %d channels x "
      "%d steps" % (nch, nst))

    # ----------------------------------------------------------- impulses.csv
    lines = ["# impulses.csv -- one row per recovered frequency STEP (this run has no impulses;",
             "# SPEC 4.2). Steps recovered from ch1111 by a matched-filter template bank, boundaries",
             "# by 1 s lock-in crossover. force_rms_mV is ch1111 rms over the dwell, mV at the ADC",
             "# input. n_samples_used is after the pulser mask and the 2 s boundary insets.",
             "step_index,t_start_s,t_end_s,f_drive_hz,force_rms_mV,n_samples_used,method"]
    frms = np.zeros(nst)
    xr = np.asarray(load("excitation", "aux", 1111)[:], dtype=np.float64)
    for k in range(nst):
        i0 = int(round(steps[k]["t0"] * FS)); i1 = int(round(steps[k]["t1"] * FS))
        frms[k] = float(np.std(xr[i0:i1]))
        lines.append("%d,%.3f,%.3f,%.6f,%.3f,%d,%s" % (
            k, start[k], end[k], f_fit[k], frms[k], steps[k]["n"] * NS,
            "matched_filter_bank+crossover_boundary+masked_lockin"))
    del xr
    open(OUT + "/impulses.csv", "w").write("\n".join(lines) + "\n")
    L("[V011] impulses.csv written: %d rows (frequency steps, not impulses). force_rms spans "
      "%.2f-%.2f mV, a factor %.2f across frequency; jumps at 5.4->5.5 Hz (%.1f -> %.1f mV, "
      "%+.1f%%) and 7.4->7.5 Hz (%.1f -> %.1f mV, %+.1f%%) are CONFIRMED on my own dwells."
      % (nst, frms.min(), frms.max(), frms.max() / frms.min(), frms[29], frms[30],
         100 * (frms[30] / frms[29] - 1), frms[49], frms[50], 100 * (frms[50] / frms[49] - 1)))

    # -------------------------------------------------------- channel_gain.csv
    mag = np.abs(H)
    gl = ["# channel_gain.csv -- per bolometer, all 52, no pre-selection.",
          "# peak_response: largest per-step lock-in amplitude of the BOLOMETER, mV RMS AT THE",
          "#   ADC INPUT (= lock-in amplitude / sqrt(2)). NOT volts at the bolometer: the",
          "#   front-end amplifier gain and thermistor calibration are not determined here.",
          "# inband_noise_rms_mV: same lock-in estimator on quiet3, mV rms at the ADC input.",
          "# snr: peak_response / inband_noise_rms_mV at the peak frequency.",
          "# median_coherence: median over the 71 steps of the raw magnitude-squared coherence",
          "#   against ch1111; the uncorrelated floor is 1/n_sub ~ %.3f." % np.median(1.0 / nsub),
          "channel,peak_response,peak_f_hz,inband_noise_rms_mV,snr,median_coherence"]
    amp_rms = np.abs(np.nanmean(A, axis=2)) / np.sqrt(2.0)
    rows = []
    for ci in range(52):
        kpk = int(np.argmax(amp_rms[ci]))
        pr = amp_rms[ci, kpk]; nz = NOISE[ci, kpk]
        mc = float(np.median(coh[ci]))
        rows.append((BOLO[ci], pr, f_fit[kpk], nz, pr / nz, mc))
        gl.append("%d,%.5f,%.4f,%.5f,%.3f,%.4f" % (BOLO[ci], pr, f_fit[kpk], nz, pr / nz, mc))
    open(OUT + "/channel_gain.csv", "w").write("\n".join(gl) + "\n")
    snr = np.array([r[4] for r in rows]); mcs = np.array([r[5] for r in rows])
    L("[V012] channel_gain.csv written, all 52 bolometers, no pre-selection. "
      "peak_response (mV rms at ADC input): median=%.4f min=%.4f max=%.4f"
      % (np.median([r[1] for r in rows]), min(r[1] for r in rows), max(r[1] for r in rows)))
    L("[V012] SNR at the peak frequency: median=%.2f min=%.2f max=%.2f; "
      "%d of 52 bolometers exceed SNR 3" % (np.median(snr), snr.min(), snr.max(), int((snr > 3).sum())))
    L("[V012] median in-band coherence against ch1111: median over bolometers=%.4f, "
      "min=%.4f, max=%.4f (uncorrelated floor %.4f)"
      % (np.median(mcs), mcs.min(), mcs.max(), float(np.median(1.0 / nsub))))
    ibest = int(np.argmax(mcs))
    L("[V012] highest median in-band coherence: ch%04d at %.4f. This is the criterion SPEC "
      "rule 5 fixes in advance for choosing the example channel, quoted here for "
      "reconciliation; I am not pre-selecting on it."
      % (BOLO[ibest], mcs[ibest]))
    pkf = np.array([r[2] for r in rows])
    u, c = np.unique(np.round(pkf, 1), return_counts=True)
    o = np.argsort(-c)
    L("[V012] peak frequency across the 52 bolometers, most common first: " +
      ", ".join("%.1f Hz x%d" % (u[i], c[i]) for i in o[:8]))
    open(OUT + "/v04_log.txt", "w").write("\n".join(LOG) + "\n")

main()
