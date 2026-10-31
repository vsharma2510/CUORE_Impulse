# Method note (analyst; run RUNA excitation window only; feasibility estimates)

**Steps.** ch1111 zero-phase band-passed 2-11 Hz; spectral-peak jump >0.04 Hz in 8 s windows (threshold) gives 71 onsets; a two-tone residual scan refines each boundary (7 poorly constrained ones replaced by the fitted 249.9994 s grid). Run coordinates; 3990 s is subtracted before every array index (`common.run_to_idx`, tested, including on real data). Drive frequencies recovered: 2.5, 2.6 ... 9.5 Hz. My boundaries are 5.96-6.54 s EARLIER than `data/steps.csv` t_start (cause unknown; I used mine).

**Pulser (1777 in window, phase-locked to boundaries).** Samples [t_p-0.1, t_p+1.0] s around every pulse (about 11 percent) get zero weight in all DFTs/fits (same mask on reference and response) and NaN in stored ring-downs. Ring-downs are never stacked across steps; ERA segments end before the first masked sample. Synthetic test: unmasked step-aligned stack gives a >20-sigma fake response; masked, none. Quiet stacks (77 pulses) showed no pulse shape, so 1.1 s is a conservative guess.

**H1.** 1.5-11 Hz zero-phase band-pass; 20 s Hann windows, 50 percent overlap, starting 60 s after each boundary; DFT at the exact drive frequency; H = <F*B>/<|F|^2>; coherence per step; SE = |H| sqrt((1-g2)/(2 n g2)), n = non-overlapping-equivalent windows. Pulse-tube lines (fundamental 1.39443 Hz: 2.789, 4.183, 5.578, 6.972, 8.367 Hz, measured in quiet3) lie 0.011-0.033 Hz from drive steps; they are fitted jointly with the drive and subtracted.

**Ring-down/ERA.** Residual = response minus fitted drive and PT lines, 25 Hz, segments 0-5.4 s and 7.7-13.1 s after each step (142 experiments; 52 bolometers + 21 accelerometer/geophone aux, each scaled by tail rms). Multi-experiment ERA, orders 2-60, stabilisation (df<1 percent, dzeta<20 percent, MAC>0.9); clusters of >=8 stable poles at order >=8 are reported. f0_err floored at 0.05 Hz. zeta_err is scatter across model orders only, no systematic. Where relative scatter exceeded 50 percent (3.42 Hz) I give an upper limit (84th percentile). No half-power zeta reported: no mode spans >=3 points on the channel-median |H|.

**Noise/SNR.** Same estimator on quiet1-3 (PT lines removed). channel_gain amplitudes are mV at the ADC input; peak taken among steps with coherence >=0.5.

**Limits.** Segments are short (5.4 s): zeta below about 0.2 percent and modes closer than about 0.2 Hz (8.10/8.17; the 4.89 cluster) are poorly resolved. The 2.53 and 3.02 Hz modes are seen by only 1 and 11 channels. 78 channels processed (52+26), not 71. No linearity test possible.
