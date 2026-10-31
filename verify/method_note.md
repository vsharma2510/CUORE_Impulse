# Method note (verifier)

Run RUNA, 52 tower-19 bolometers + 26 aux, 2.50–9.50 Hz. **Amplitudes are mV at the ADC input**;
no front-end gain or thermistor calibration is applied or claimed.

**Steps.** Matched-filter bank of tone templates on the 0.1 Hz grid, 10 s window, 1 s hop,
winner-take-all: 71 steps. No threshold detection, no ERA. Boundaries refined to 1 s by the crossover
of adjacent-template 1 s lock-in amplitudes. Frequencies from the baseband phase slope:
f_k = 2.5 + 0.1k Hz to better than 2e-4 Hz.

**Deviation.** steps.csv boundaries (4015 + 250k) are late by 5.851 ± 0.172 s; the true grid
is 4009.15 + 250k. I use mine, inset 2 s. Its frequency and force columns agree.

**Lock-in.** Per step, masked least squares of [cos, sin, 1, t] over the 24 pulser-free 5.6 s
sub-blocks (mask [−0.2, +4.2] s per pulse, from the measured pulse shape); 53.7% of the window used.
H1 = Σ R*B / Σ|R|², R = ch1111 on the same step; standard error from the complex scatter of
per-sub-block B/R; raw coherence reported with its 1/n = 0.042 floor.

**Caveat on the ratio.** A ratio to ch1111 cancels drive-*level* variation but not a miscalibration
of ch1111 itself. At 5.4→5.5 Hz ch1111 jumps ×1.73 while the MSP-X accelerometer on the driven axis
changes ×0.88, so that jump is a reference-scale change and propagates straight into |H|. The 7.4 Hz
mode is flagged for it.

**Modes.** Local maxima of the median |H| (prominence ≥ 1.25 vs neighbour mean, coherence ≥ 0.50).
f0 from a one-mode rational-fraction-polynomial fit (orders 2/2) with relative residual < 0.40, else
3-point log-parabolic; f0_err floored at 0.05 Hz. ζ from half-power width only where a peak spans
≥ 3 grid points with both crossings present — never the case, so all 11 ζ are upper limits. Modes
come from |H|, not raw amplitude, because the force also peaks at 3.4 Hz.

**Assumption.** 10 s is an integer number of drive cycles, so all sub-blocks share one drive phase:
their scatter does not bound a pulser-phase-locked systematic, measured separately at ≲11% of noise.

**Could not determine.** (i) ζ point values: every peak is unresolved at 0.1 Hz. (ii) ζ from
ring-down: window 5.3 s, next tone 0.1 Hz away = 0.53 of a beat cycle, τ unconstrained (~5000%).
(iii) A pedestal at excitation gain: no shaker-off data inside the window. (iv) Absolute units.

