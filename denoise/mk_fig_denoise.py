#!/usr/bin/env python3
"""results/fig_denoise_ch714.pdf -- S4D witness denoising on CUORE channel 714, ASD before/after.

Data: the diagnostics curves of run
  ch714_w19_demeanPsd0p1to50HzLogGuard50to70_withinRun_ds5_s4d
in ~/ML_denoising_ssm/DenoisingAux/WitnessDenoise, validation part, within-run block split.
Nothing is recomputed or refitted here; the curves are the model's own measured output.

Normalisation. The diagnostics file stores `target_psd` SUMMED over windows and `ratio` as a POWER
ratio, so the amplitude spectral density in the project's own convention (evaluate.py `_finalize`:
asd = sqrt(mean PSD)) is

    ASD_before = sqrt(target_psd / num_windows)
    ASD_after  = sqrt(target_psd * ratio / num_windows)

Checked against the run's own published asd_comparison.png: 106 against ~90 at 0.1 Hz, 7.18 against
~7 at 1 Hz, 5.58 against ~6 at 3.4 Hz. The residual difference is the window length (20 s here),
which changes how narrow lines are resolved. Units are the channel's own ADC-side units, which the
upstream project labels "ch. 714 units" -- NOT calibrated to energy, and not relabelled here.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotstyle as ps                                                            # noqa: E402

SRC = Path.home() / "ML_denoising_ssm/DenoisingAux/WitnessDenoise"
RUN = "ch714_w19_demeanPsd0p1to50HzLogGuard50to70_withinRun_ds5_s4d"
STEM = SRC / "runs/diagnostics/power_bands_ch0714" / f"ae_{RUN}_lp60x101"

z = np.load(f"{STEM}_curves.npz")
diag = json.load(open(f"{STEM}.json"))
met = json.load(open(SRC / "runs" / RUN / "eval/metrics.json"))
N = diag["num_windows"]
FLO, FHI = diag["loss"]["f_low"], diag["loss"]["f_high"]

f = z["20s__freqs"]
before = np.sqrt(z["20s__target_psd"] / N)
after = np.sqrt(z["20s__target_psd"] * z["20s__ratio"] / N)

band = (f >= FLO) & (f <= FHI)
out = f > 70.0
pw = diag["pooled"]["20s"]["power_weighted"]
print(f"in-band power ratio  {pw['0.1-50']:.4f}  -> ASD reduced {100*(1-np.sqrt(pw['0.1-50'])):.1f}%")
print(f"above the guard band {pw['100-500']:.6f}  -> untouched, as intended")
print(f"time-domain RMS      {met['rms_before']:.1f} -> {met['rms_after']:.1f} "
      f"({met['rms_reduction_pct']:.1f}% lower), {met['num_windows']} validation windows")

ps.use("paper")
C = ps.COLORS
fig, ax = ps.figure(figsize=(3.6, 2.7))

ax.axvspan(FLO, FHI, color=C["fill"], alpha=0.75, lw=0, zorder=0)
ax.loglog(f[1:], before[1:], color=C["grey"], lw=ps.ctx()["lw"], zorder=3, label="before")
ax.loglog(f[1:], after[1:], color=C["teal"], lw=ps.ctx()["lw"], zorder=4, label="after S4D")

ax.set_xlim(0.1, 500)
ax.set_ylim(2e-2, 3e2)
ps.style_axes(ax, "Channel 714 noise, S4D denoising",
              "f (Hz)", "ASD (ch. 714 units / √Hz)")
ps.legend(ax)
ax.text(0.035, 0.05,
        f"shaded: trained band {FLO:g}–{FHI:g} Hz\n"
        f"in band  ASD −{100*(1-np.sqrt(pw['0.1-50'])):.0f}%,  RMS −{met['rms_reduction_pct']:.0f}%\n"
        f"above 70 Hz  unchanged to 1 part in 10⁶",
        transform=ax.transAxes, ha="left", va="bottom", family=ps.MONO_FONTS,
        size=ps.ctx()["note"] - 0.5, color=C["ink"], zorder=6, linespacing=1.45)
ps.finalize(fig, ax)
print(ps.save(fig, "results/fig_denoise_ch714"))
