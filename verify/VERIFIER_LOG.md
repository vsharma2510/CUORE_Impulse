# VERIFIER_LOG.md — independent verifier, run RUNA shaker response

Agent: independent verifier. Working dir `verify/`. Attempt 2 (attempt 1 was blocked by permissions).
Date 2026-10-30. Numbers are appended as they are obtained.

## V000 Environment and permissions

- Python 3.13.7, numpy 2.3.2, scipy 1.16.1, at
  `<CUORE_SCRATCH>/Conda/pyT/bin/python3`.
- PERMISSION NOTE: `verify/.claude/settings.local.json` is NOT being loaded by the harness (project
  settings are read from the repo-root `.claude/`, which is outside my working directories). The Read
  calls that succeed do so only because `verify/`, `data/` and the pscratch array root are session
  working directories, which grants Read implicitly. The Write and Edit TOOLS are therefore still
  denied. I am instead writing every file with python (`open(...).write(...)`), which is permitted and
  is what the instructions specified. No shell redirection is used anywhere.
- `SPEC.md` was read from `verify/SPEC.md` (the repo-root copy is outside my working dirs and is
  denied). It is Draft 1, orchestrator, 2026-10-31, awaiting approval at stop point 3.
- I have NOT seen any `analysis/` or `critic/` output. Those paths are explicitly denied in the
  settings and I have not listed, read or searched them. I will state it here immediately if that
  changes.

## V001 Inputs as read

- `data/meta.json`: run_excitation RUNA, run_quiet RUNB, fs 1000.0 Hz, adc_to_mV
  0.080108642578125 = 21000/2**18 exactly, slice_offset_s 3990, excitation window run
  3990-21760 s, 17,770,000 samples, 52 bolometers 937-988, aux 1018-1020 + 1101-1123,
  drive reference ch1111, drive accel ch1112.
- `data/steps.csv` (the REWRITTEN version, with `f_drive_hz_nominal` present): 71 steps,
  step 0 run t 4015-4265 s at 2.50005 Hz, step 70 run t 21515-21740 s at 9.50013 Hz,
  225,000 samples on the last step and 250,000 on all others.
- steps.csv force_rms_mV spans 363.05 mV (step 0, 2.5 Hz) to 1521.25 mV (step 9, 3.4 Hz),
  a factor 4.19 excursion across frequency. I confirm the two discontinuities the orchestrator
  accepted: 5.4->5.5 Hz is 431.00 -> 744.84 mV (+72.8%) and 7.4->7.5 Hz is 723.54 -> 490.20 mV
  (-32.2%). Treated as suspected reference-channel range / amplifier changes, NOT as drive changes.
  Every transfer function below is formed as a strict ratio to ch1111 on the SAME step so that any
  such gain change cancels.
- steps.csv `f_drive_hz_measured` minus `f_drive_hz_nominal` is +0.00005 Hz at 2.5 Hz rising
  monotonically to +0.00017 Hz at 9.5 Hz, i.e. a pure multiplicative clock scale of about
  1 + 1.9e-5, not an additive offset. This is consistent with the orchestrator's refutation of my
  earlier 2.52+0.1k inference: the grid is f_k = 2.5 + 0.1k Hz. I re-measure it independently in
  V003 below rather than taking it from steps.csv.

## V002-V003 Tests and step recovery (script `v01_steps.py`, log `v01_log.txt`)

[V002] pulser_times.npy: n=4882 first=5.0020 s last=48815.0020 s median spacing=10.000000 s max|spacing-10|=4.547e-13 s
[V002] pulser pulses inside excitation window [3990,21760) run s: 1777 (meta.json says 1777)
[V002] TEST array length: n=17770000 expected=17770000 -> PASS
[V002] TEST 3990 s offset: steps.csv step 0 is RUN 4015-4265 s nominal 2.5 Hz. ARRAY slice WITH offset (t=25-275 s): f=2.500323 Hz amp=603.0 mV. WITHOUT offset (t=4015-4265 s): f=4.099983 Hz amp=1486.7 mV -> PASS
[V002] NOTE 3990/10 = 399.0 exactly, so the offset is an integer number of pulser periods: an offset blunder is INVISIBLE to pulser alignment. Masking is insensitive to it; step indexing is not. Do not validate the offset with the pulser.
[V002] ch1111 shaker-off rms on quiet1 = 3.8937 mV; filter-bank silence guard set to 20x that = 77.874 mV (rejects shaker-off blocks only; boundaries come from template competition, not from this number)
[V003] pulser pulse shape on quiet3 (shaker off, no drive), ch0937, 76 pulses: peak=1.7915 mV at tau=+1.321 s; pre-pulse rms of the mean=0.22872 mV; typical sem=1.55619 mV; settle to 3 sigma at tau=1.37 s
[V003] pulser mean amplitude vs tau (mV): +0.5s=-0.1237, +1s=0.4360, +2s=0.7311, +3s=0.6668, +4s=0.1303, +5s=-0.1184, +6s=-0.2808, +8s=0.0175
[V003] matched-filter bank: templates 2.3-9.7 Hz on the 0.1 Hz grid (75), 10 s coherent window, 1 s hop; 71 contiguous single-template runs found
[V003] step  0 f_nom=2.50 f_fit=2.500060 d=+0.000060 run=[4004.0,4263.0] amp1111=600.23 rms1111=363.01 mV
[V003] step  1 f_nom=2.60 f_fit=2.600045 d=+0.000045 run=[4254.0,4513.0] amp1111=683.61 rms1111=445.33 mV
[V003] step  2 f_nom=2.70 f_fit=2.700048 d=+0.000048 run=[4504.0,4763.0] amp1111=831.75 rms1111=545.97 mV
[V003] step  3 f_nom=2.80 f_fit=2.800045 d=+0.000045 run=[4754.0,5013.0] amp1111=1014.09 rms1111=669.88 mV
[V003] step  4 f_nom=2.90 f_fit=2.900043 d=+0.000043 run=[5004.0,5263.0] amp1111=1231.30 rms1111=818.78 mV
[V003] step  5 f_nom=3.00 f_fit=3.000059 d=+0.000059 run=[5254.0,5514.0] amp1111=1485.21 rms1111=993.67 mV
[V003] step  6 f_nom=3.10 f_fit=3.100050 d=+0.000050 run=[5505.0,5763.0] amp1111=1755.17 rms1111=1180.49 mV
[V003] step  7 f_nom=3.20 f_fit=3.200052 d=+0.000052 run=[5754.0,6014.0] amp1111=1999.48 rms1111=1352.03 mV
[V003] step  8 f_nom=3.30 f_fit=3.300068 d=+0.000068 run=[6005.0,6264.0] amp1111=2171.42 rms1111=1475.88 mV
[V003] step  9 f_nom=3.40 f_fit=3.400071 d=+0.000071 run=[6255.0,6514.0] amp1111=2226.86 rms1111=1521.24 mV
[V003] step 10 f_nom=3.50 f_fit=3.500061 d=+0.000061 run=[6505.0,6763.0] amp1111=2178.89 rms1111=1495.65 mV
[V003] step 11 f_nom=3.60 f_fit=3.600052 d=+0.000052 run=[6754.0,7014.0] amp1111=2069.10 rms1111=1426.82 mV
[V003] step 12 f_nom=3.70 f_fit=3.700070 d=+0.000070 run=[7005.0,7264.0] amp1111=1935.10 rms1111=1340.38 mV
[V003] step 13 f_nom=3.80 f_fit=3.800070 d=+0.000070 run=[7255.0,7514.0] amp1111=1803.76 rms1111=1254.67 mV
[V003] step 14 f_nom=3.90 f_fit=3.900075 d=+0.000075 run=[7505.0,7764.0] amp1111=1684.62 rms1111=1176.19 mV
[V003] step 15 f_nom=4.00 f_fit=4.000080 d=+0.000080 run=[7755.0,8014.0] amp1111=1577.59 rms1111=1105.28 mV
[V003] step 16 f_nom=4.10 f_fit=4.100069 d=+0.000069 run=[8005.0,8263.0] amp1111=1484.94 rms1111=1043.39 mV
[V003] step 17 f_nom=4.20 f_fit=4.200058 d=+0.000058 run=[8254.0,8513.0] amp1111=1402.55 rms1111=988.22 mV
[V003] step 18 f_nom=4.30 f_fit=4.300059 d=+0.000059 run=[8504.0,8763.0] amp1111=1331.23 rms1111=940.15 mV
[V003] step 19 f_nom=4.40 f_fit=4.400069 d=+0.000069 run=[8754.0,9014.0] amp1111=1267.28 rms1111=896.68 mV
[V003] step 20 f_nom=4.50 f_fit=4.500085 d=+0.000085 run=[9005.0,9264.0] amp1111=1209.96 rms1111=857.55 mV
[V003] step 21 f_nom=4.60 f_fit=4.600085 d=+0.000085 run=[9255.0,9514.0] amp1111=1157.01 rms1111=821.18 mV
[V003] step 22 f_nom=4.70 f_fit=4.700085 d=+0.000085 run=[9505.0,9764.0] amp1111=1109.75 rms1111=788.27 mV
[V003] step 23 f_nom=4.80 f_fit=4.800079 d=+0.000079 run=[9755.0,10013.0] amp1111=1062.99 rms1111=755.72 mV
[V003] step 24 f_nom=4.90 f_fit=4.900076 d=+0.000076 run=[10004.0,10264.0] amp1111=1017.84 rms1111=723.95 mV
[V003] step 25 f_nom=5.00 f_fit=5.000092 d=+0.000092 run=[10255.0,10514.0] amp1111=969.41 rms1111=689.66 mV
[V003] step 26 f_nom=5.10 f_fit=5.100084 d=+0.000084 run=[10505.0,10763.0] amp1111=914.84 rms1111=650.90 mV
[V003] step 27 f_nom=5.20 f_fit=5.200075 d=+0.000075 run=[10754.0,11014.0] amp1111=840.42 rms1111=597.93 mV
[V003] step 28 f_nom=5.30 f_fit=5.300092 d=+0.000092 run=[11005.0,11263.0] amp1111=680.63 rms1111=484.40 mV
[V003] step 29 f_nom=5.40 f_fit=5.400134 d=+0.000134 run=[11254.0,11513.0] amp1111=604.23 rms1111=430.45 mV
[V003] step 30 f_nom=5.50 f_fit=5.500098 d=+0.000098 run=[11504.0,11764.0] amp1111=1044.15 rms1111=742.20 mV
[V003] step 31 f_nom=5.60 f_fit=5.600102 d=+0.000102 run=[11755.0,12014.0] amp1111=1197.61 rms1111=849.10 mV
[V003] step 32 f_nom=5.70 f_fit=5.700104 d=+0.000104 run=[12005.0,12264.0] amp1111=1222.75 rms1111=866.17 mV
[V003] step 33 f_nom=5.80 f_fit=5.800108 d=+0.000108 run=[12255.0,12514.0] amp1111=1202.78 rms1111=851.18 mV
[V003] step 34 f_nom=5.90 f_fit=5.900107 d=+0.000107 run=[12505.0,12764.0] amp1111=1166.07 rms1111=824.70 mV
[V003] step 35 f_nom=6.00 f_fit=6.000111 d=+0.000111 run=[12755.0,13014.0] amp1111=1128.24 rms1111=797.31 mV
[V003] step 36 f_nom=6.10 f_fit=6.100114 d=+0.000114 run=[13005.0,13264.0] amp1111=1094.30 rms1111=772.85 mV
[V003] step 37 f_nom=6.20 f_fit=6.200113 d=+0.000113 run=[13255.0,13514.0] amp1111=1067.06 rms1111=753.09 mV
[V003] step 38 f_nom=6.30 f_fit=6.300117 d=+0.000117 run=[13505.0,13764.0] amp1111=1042.96 rms1111=735.66 mV
[V003] step 39 f_nom=6.40 f_fit=6.400119 d=+0.000119 run=[13755.0,14014.0] amp1111=1024.65 rms1111=722.23 mV
[V003] step 40 f_nom=6.50 f_fit=6.500121 d=+0.000121 run=[14005.0,14264.0] amp1111=1008.16 rms1111=710.19 mV
[V003] step 41 f_nom=6.60 f_fit=6.600120 d=+0.000120 run=[14255.0,14514.0] amp1111=994.82 rms1111=700.40 mV
[V003] step 42 f_nom=6.70 f_fit=6.700122 d=+0.000122 run=[14505.0,14764.0] amp1111=983.10 rms1111=691.91 mV
[V003] step 43 f_nom=6.80 f_fit=6.800125 d=+0.000125 run=[14755.0,15014.0] amp1111=973.95 rms1111=685.27 mV
[V003] step 44 f_nom=6.90 f_fit=6.900123 d=+0.000123 run=[15005.0,15264.0] amp1111=966.81 rms1111=680.02 mV
[V003] step 45 f_nom=7.00 f_fit=7.000119 d=+0.000119 run=[15255.0,15514.0] amp1111=960.72 rms1111=675.67 mV
[V003] step 46 f_nom=7.10 f_fit=7.100116 d=+0.000116 run=[15505.0,15764.0] amp1111=959.26 rms1111=674.50 mV
[V003] step 47 f_nom=7.20 f_fit=7.200111 d=+0.000111 run=[15755.0,16014.0] amp1111=960.78 rms1111=675.70 mV
[V003] step 48 f_nom=7.30 f_fit=7.300124 d=+0.000124 run=[16005.0,16264.0] amp1111=974.70 rms1111=685.48 mV
[V003] step 49 f_nom=7.40 f_fit=7.400136 d=+0.000136 run=[16255.0,16515.0] amp1111=1027.03 rms1111=722.36 mV
[V003] step 50 f_nom=7.50 f_fit=7.500189 d=+0.000189 run=[16506.0,16764.0] amp1111=689.50 rms1111=493.03 mV
[V003] step 51 f_nom=7.60 f_fit=7.600135 d=+0.000135 run=[16755.0,17014.0] amp1111=823.83 rms1111=580.32 mV
[V003] step 52 f_nom=7.70 f_fit=7.700135 d=+0.000135 run=[17005.0,17264.0] amp1111=852.35 rms1111=600.31 mV
[V003] step 53 f_nom=7.80 f_fit=7.800136 d=+0.000136 run=[17255.0,17514.0] amp1111=857.44 rms1111=604.13 mV
[V003] step 54 f_nom=7.90 f_fit=7.900137 d=+0.000137 run=[17505.0,17764.0] amp1111=855.40 rms1111=603.15 mV
[V003] step 55 f_nom=8.00 f_fit=8.000125 d=+0.000125 run=[17755.0,18014.0] amp1111=853.31 rms1111=601.96 mV
[V003] step 56 f_nom=8.10 f_fit=8.100132 d=+0.000132 run=[18005.0,18264.0] amp1111=848.64 rms1111=599.02 mV
[V003] step 57 f_nom=8.20 f_fit=8.200137 d=+0.000137 run=[18255.0,18514.0] amp1111=844.76 rms1111=596.73 mV
[V003] step 58 f_nom=8.30 f_fit=8.300131 d=+0.000131 run=[18505.0,18764.0] amp1111=841.29 rms1111=594.59 mV
[V003] step 59 f_nom=8.40 f_fit=8.400124 d=+0.000124 run=[18755.0,19014.0] amp1111=837.51 rms1111=592.36 mV
[V003] step 60 f_nom=8.50 f_fit=8.500127 d=+0.000127 run=[19005.0,19264.0] amp1111=834.18 rms1111=590.36 mV
[V003] step 61 f_nom=8.60 f_fit=8.600132 d=+0.000132 run=[19255.0,19514.0] amp1111=829.98 rms1111=587.84 mV
[V003] step 62 f_nom=8.70 f_fit=8.700144 d=+0.000144 run=[19505.0,19764.0] amp1111=826.64 rms1111=585.77 mV
[V003] step 63 f_nom=8.80 f_fit=8.800143 d=+0.000143 run=[19755.0,20014.0] amp1111=823.22 rms1111=583.70 mV
[V003] step 64 f_nom=8.90 f_fit=8.900106 d=+0.000106 run=[20005.0,20265.0] amp1111=819.19 rms1111=581.30 mV
[V003] step 65 f_nom=9.00 f_fit=9.000149 d=+0.000149 run=[20256.0,20514.0] amp1111=816.86 rms1111=579.82 mV
[V003] step 66 f_nom=9.10 f_fit=9.100144 d=+0.000144 run=[20505.0,20764.0] amp1111=813.43 rms1111=577.77 mV
[V003] step 67 f_nom=9.20 f_fit=9.200148 d=+0.000148 run=[20755.0,21014.0] amp1111=810.35 rms1111=575.84 mV
[V003] step 68 f_nom=9.30 f_fit=9.300155 d=+0.000155 run=[21005.0,21264.0] amp1111=807.29 rms1111=573.91 mV
[V003] step 69 f_nom=9.40 f_fit=9.400159 d=+0.000159 run=[21255.0,21514.0] amp1111=803.47 rms1111=571.35 mV
[V003] step 70 f_nom=9.50 f_fit=9.500150 d=+0.000150 run=[21505.0,21760.0] amp1111=801.87 rms1111=570.34 mV
[V003] f_fit - f_nom over 71 steps: mean=+1.034e-04 Hz, max|.|=1.886e-04 Hz
[V003] f_fit / f_nom: mean=1.000017432 std=2.23e-06 -> one multiplicative clock scale, not an additive offset
[V003] f_fit mod 0.1 Hz: max deviation from zero = 1.886e-04 Hz. CONFIRMED INDEPENDENTLY: the drive grid is f_k = 2.5 + 0.1k Hz, the pulser comb lands on EVERY drive line, and pulser masking is mandatory. My earlier 2.52+0.1k inference was wrong.
[V003] recovered band 2.50-9.50 Hz, 71 steps. meta.json extracted_band_hz says [2.52, 9.52]; the true band is 2.50-9.50 Hz.


## V004 Step boundaries are NOT where steps.csv puts them (script `v02_bound.py`)

The 10 s matched-filter window smears a boundary by its own length, so I re-measured every
transition at 1 s resolution: per-1-s-block lock-in amplitude at f_k and at f_(k+1), boundary taken
at the crossover where the two are equal (for an abrupt switch this is unbiased to +/-0.5 s).

- 70 boundaries measured. Offset from the steps.csv grid 4015 + 250k: mean -5.851 s, median
  -5.810 s, std 0.172 s, min -6.354 s, max -5.516 s.
- The 250 s cadence is right (std 0.17 s over 70 boundaries) but its PHASE is wrong in steps.csv by
  -5.85 s. The true step grid is run t = 4009.15 + 250k s, not 4015 + 250k s.
- Consequence: a dwell taken from steps.csv straddles the real boundary by ~5.9 s at the END of
  every step, i.e. ~2.3% of each 250 s dwell is the NEXT tone. That is a small but real bias on any
  per-step estimate taken from the steps.csv windows, and it biases every step in the same
  direction. I use my own crossover boundaries, inset by 2 s, for all lock-in work below.
- Cross-check that my windows are right: ch1111 rms on my dwells reproduces the steps.csv
  force_rms_mV column to ~0.01-0.5% (e.g. step 0: 363.01 vs 363.05; step 29: 430.45 vs 431.00;
  step 30: 742.20 vs 744.84). So the FORCE column is sound; only the time column is shifted.

## V005 There is no shaker-off data inside the excitation window (script `v03_edges.py`)

This REFUTES item 4 of the orchestrator's list ("25 s of shaker-off data at array t=0-25 s and the
~20 s tail after the last step ... use them as extra in-band pedestal"). There is no such data.
A 1 s window cannot resolve 2.4 from 2.5 Hz, which is how the head of the window can look like a
low-amplitude 2.5 Hz step; with 18 s windows it resolves cleanly:

- array t 0-18 s (run 3990-4008): amplitude 413.1 mV at 2.4 Hz, 44.1 mV at 2.5 Hz. ch1111 rms over
  this stretch is 295.19 mV, against 3.89 mV when the shaker is genuinely off (quiet1).
  This is the TAIL OF THE 2.4 Hz STEP, fully driven. The 2.4->2.5 Hz transition is at run 4009.3 s,
  which is exactly the grid of V004.
- array t 21-39 s (run 4011-4029): 507.5 mV at 2.5 Hz, 54.0 mV at 2.4 Hz -> the 2.5 Hz step.
- array t 17740-17770 s (the last 30 s): 801.6 mV at 9.5 Hz, ch1111 rms over the last 20 s is
  572.50 mV. The 9.5 Hz step runs to run 21759.2 s and the array ends at 21760 s. There is no tail.
- So the excitation window is driven end to end. All pedestal/noise numbers below therefore come
  from quiet1, quiet3 and quietrun ONLY, and I cannot offer an in-band pedestal "at exactly the
  excitation gain settings". That gap is real and I am not filling it with a number.
- Incidental: the first 18 s of the window is a usable partial 2.4 Hz step, one grid point below the
  stated band. I do not use it; the band stays 2.50-9.50 Hz.

## V006 The pulser mask and the ring-down windows are commensurate - a lucky break

- Pulser: 4882 pulses, first at run 5.0020 s, spacing 10.000000 s with max|spacing-10| = 4.5e-13 s.
  1777 inside the excitation window, matching meta.json exactly.
- Pulse shape, measured on quiet3 where the shaker is off (ch0937, 76 pulses): peak +1.79 mV at
  tau = +1.32 s after the tabulated time, decaying through +0.73 mV at +2 s, +0.67 at +3 s,
  +0.13 at +4 s, -0.12 at +5 s. Pre-pulse rms of the mean waveform 0.229 mV. So the pulse is
  ~1.8 mV peak and is gone into the noise by about +4 s.
- Mask adopted: [-0.2, +4.2] s about every pulse, 44% of the excitation window masked. Surviving
  sub-blocks are the 5.6 s pulser-free gaps, array t in [9.202 + 10m, 14.802 + 10m].
- Step boundaries sit at run 4009.15 + 250k and pulses at 5.002 + 10k; 250 s is exactly 25 pulser
  periods, so the first pulse after ANY boundary falls at +5.68 s, identically for all 71
  boundaries. The window [+0.2, +5.5] s after every boundary is therefore inherently pulser-free,
  which is where the ring-down fits below live. No masking is needed there.

## V007-V012 Masked lock-in, H1, noise, ring-down (script `v04_lockin.py`)

[V007] step grid from measured crossovers: step 0 run [4009.32, 4259.32), step 70 run [21509.19, 21759.19); dwells inset by 2.0 s at each end
[V007] masked lock-in sub-blocks per step: min=24 max=24 median=24 total=1704; sub-block length 5.6 s; mask [-0.2,+4.2] s about each pulse
[V007] samples used in the lock-in: 9542400 of 17770000 in the window = 53.7% (the rest is pulser mask, boundary insets and gap remainder)
[V007] channels processed: 52 bolometers + 26 aux = 78. NOTE SPEC section 3 says 'all 71 bolometer-plus-aux channels'; 71 is the number of STEPS. The true channel count for the excitation window is 52 + 26 = 78 and I report all 78.
[V007] lock-in progress: 1/78 channels (ch0937)
[V007] lock-in progress: 14/78 channels (ch0950)
[V007] lock-in progress: 27/78 channels (ch0963)
[V007] lock-in progress: 40/78 channels (ch0976)
[V007] lock-in progress: 53/78 channels (ch1018)
[V007] lock-in progress: 66/78 channels (ch1111)
[V007] H1 formed as sum(conj(R)*B)/sum(|R|^2) over the pulser-free sub-blocks of each step, with ch1111 as R. Standard error from the complex scatter of the per-sub-block ratios B/R, so any ch1111 range change cancels exactly.
[V007] coherence floor for uncorrelated data is 1/n_sub = 0.0417 (median over steps); reported coh2 is RAW, coh2_bias is that 1/n floor
[V008] quiet1: 24 pulser-free sub-blocks per frequency; in-band noise (mV rms, same lock-in estimator as the response) over the 52 bolometers: median=0.1457, min=0.0670, max=7.2677
[V008] quiet3: 77 pulser-free sub-blocks per frequency; in-band noise (mV rms, same lock-in estimator as the response) over the 52 bolometers: median=0.1490, min=0.0753, max=7.2129
[V008] NOTE quietrun (run RUNB, 2456 s) is NOT used for the masked noise estimate: pulser_times.npy covers run RUNA only, so I cannot mask the pulser there and the 0.1 Hz comb lands on every drive frequency. Using it unmasked would inflate the noise at exactly the frequencies that matter. Reported noise is from quiet3 (775 s, the longest in-run window with known pulse times); quiet1 is the cross-check.
[V008] quiet1/quiet3 noise ratio over bolometers and frequencies: median=0.982 (10th-90th pct 0.814-1.154) -> the two in-run pedestals agree to this level
[V009] ring-down: window [+0.2,+5.5] s after each of the 70 boundaries, demodulated at the OLD tone, decimated to 50 Hz; the decaying old tone and the steady new tone are fitted SIMULTANEOUSLY because they are only 0.1 Hz apart.
[V009] LIMITATION, stated rather than papered over: the usable ring-down window is 5.3 s and the adjacent tone is 0.1 Hz away, so f_old and f_new are separated by only 0.53 of a beat cycle in that window. tau near the expected 3.2 s is therefore only weakly constrained and I do NOT use ring-down as the primary damping route.
[V009] ring-down over bolometers x boundaries: median tau=0.30 s, median 1-sigma half-width=14.85 s -> fractional uncertainty 4950%, consistent with the limitation above
[V010] wrote responses.npz: H, H_se, coherence2, coherence2_bias, amp_mV, amp_subblock_mV, noise, ring-down baseband segments and tau fits, 78 channels x 71 steps
[V011] impulses.csv written: 71 rows (frequency steps, not impulses). force_rms spans 362.97-1521.58 mV, a factor 4.19 across frequency; jumps at 5.4->5.5 Hz (429.9 -> 744.9 mV, +73.3%) and 7.4->7.5 Hz (723.4 -> 490.8 mV, -32.2%) are CONFIRMED on my own dwells.
[V012] channel_gain.csv written, all 52 bolometers, no pre-selection. peak_response (mV rms at ADC input): median=14.0178 min=0.6399 max=183.3194
[V012] SNR at the peak frequency: median=76.14 min=5.05 max=504.19; 52 of 52 bolometers exceed SNR 3
[V012] median in-band coherence against ch1111: median over bolometers=0.5275, min=0.0984, max=0.9730 (uncorrelated floor 0.0417)
[V012] highest median in-band coherence: ch0939 at 0.9730. This is the criterion SPEC rule 5 fixes in advance for choosing the example channel, quoted here for reconciliation; I am not pre-selecting on it.
[V012] peak frequency across the 52 bolometers, most common first: 3.4 Hz x46, 4.9 Hz x4, 3.5 Hz x1, 4.8 Hz x1


## V013-V017 First modal pass, SUPERSEDED (script `v05_modes.py`)

My first mode pass over-fragmented: clustering on the per-channel peak histogram with a
+/-0.15 Hz assignment window let neighbouring clusters claim the same peak, so it emitted 13 modes
including near-duplicates (4.9070 and 4.9033 Hz; five separate entries between 8.05 and 8.56 Hz) and
two entries with zeta = 0.00000 where the half-power walk returned hi == lo on the median curve.
Those numbers are wrong and are NOT in modes.csv. I record the failure rather than hide it; the
replacement is V018-V019 below, which detects on the single median |H| curve with non-maximum
suppression and guards the half-power walk against running down a neighbouring mode's skirt.
`v05_modes.py` and `v05_modes.json` are kept only as the superseded record.


## V018-V019 Modes, FINAL (script `v06_modes.py`, writes `modes.csv`)

[V018] modes come from |H| = |lockin(bolo)/lockin(ch1111)| on the SAME step, not from the raw bolometer amplitude: the raw amplitude peaks at 3.4 Hz on 46/52 bolometers but the drive force also peaks at 3.4 Hz (1521.6 vs 363.0 mV at 2.5 Hz), so a raw peak there is partly the shaker/stinger response.
[V018] mode detection on the median |H| over 52 bolometers: local maxima with prominence >= 1.25 against the mean of the two neighbours AND median coherence >= 0.50 at the peak. 11 candidates: 3.0 Hz (prom 2.15, coh 0.561), 3.4 Hz (prom 3.32, coh 0.999), 4.0 Hz (prom 1.97, coh 0.980), 4.9 Hz (prom 1.50, coh 0.997), 5.3 Hz (prom 1.26, coh 0.847), 6.2 Hz (prom 2.02, coh 0.902), 7.4 Hz (prom 2.15, coh 0.929), 7.9 Hz (prom 1.80, coh 0.811), 8.1 Hz (prom 2.21, coh 0.969), 8.5 Hz (prom 1.34, coh 0.951), 8.8 Hz (prom 2.58, coh 0.926)
[V019] modes.csv written: 11 modes, 2.50-9.50 Hz
[V019] f0=3.0127 +/- 0.0500 Hz | zeta < 0.01660 | span=1 pt | prom=2.15 | coh=0.561 | 34/52 channels | pt_harm=False | rfp zeta med=nan (n=0)
[V019] f0=3.4075 +/- 0.0500 Hz | zeta < 0.01467 | span=1 pt | prom=3.32 | coh=0.999 | 52/52 channels | pt_harm=False | rfp zeta med=0.00796 (n=5)
[V019] f0=3.9707 +/- 0.0500 Hz | zeta < 0.01259 | span=2 pt | prom=1.97 | coh=0.980 | 48/52 channels | pt_harm=False | rfp zeta med=nan (n=1)
[V019] f0=4.8990 +/- 0.0500 Hz | zeta < 0.01021 | span=1 pt | prom=1.50 | coh=0.997 | 52/52 channels | pt_harm=False | rfp zeta med=nan (n=4)
[V019] f0=5.3060 +/- 0.0500 Hz | zeta < 0.00942 | span=3 pt | prom=1.26 | coh=0.847 | 35/52 channels | pt_harm=False | rfp zeta med=nan (n=0)
[V019] f0=6.2184 +/- 0.0500 Hz | zeta < 0.00804 | span=1 pt | prom=2.02 | coh=0.902 | 46/52 channels | pt_harm=False | rfp zeta med=0.00742 (n=29)
[V019] f0=7.4269 +/- 0.0500 Hz | zeta < 0.00673 | span=1 pt | prom=2.15 | coh=0.929 | 49/52 channels | pt_harm=False | rfp zeta med=nan (n=0)  [FORCE-JUMP ADJACENT]
[V019] f0=7.9209 +/- 0.0500 Hz | zeta < 0.00631 | span=1 pt | prom=1.80 | coh=0.811 | 36/52 channels | pt_harm=False | rfp zeta med=nan (n=1)
[V019] f0=8.1274 +/- 0.0500 Hz | zeta < 0.00615 | span=1 pt | prom=2.21 | coh=0.969 | 47/52 channels | pt_harm=False | rfp zeta med=nan (n=3)
[V019] f0=8.5297 +/- 0.0500 Hz | zeta < 0.00586 | span=2 pt | prom=1.34 | coh=0.951 | 46/52 channels | pt_harm=False | rfp zeta med=nan (n=1)
[V019] f0=8.7834 +/- 0.0500 Hz | zeta < 0.00569 | span=1 pt | prom=2.58 | coh=0.926 | 48/52 channels | pt_harm=False | rfp zeta med=nan (n=4)
[V019] 11 of 11 modes give only a zeta UPPER LIMIT because the peak spans < 3 of the 0.1 Hz grid points. This is exactly the case SPEC 4.3 anticipated; a point value for those would be fabricated. The 0.1 Hz step spacing, not the statistics, is the limit.
[V019] SPEC 7 corroboration, stated either way: collaboration hunt 3.35-3.55 Hz -> I find f0 = 3.408 Hz; hunt 8.0-9.0 Hz -> I find f0 = 8.127 Hz, 8.530 Hz, 8.783 Hz
[V019] pulse-tube 1.4 Hz harmonics (2.8/4.2/5.6/7.0/8.4 Hz): 0 of 11 modes flagged coincident within f0_err: none


## V020 The force discontinuities are reference-SCALE changes, and the ratio does NOT cancel them

The orchestrator's instruction was to "form every transfer function as a strict ratio to ch1111 on
the same step so it cancels". That cancels a change in the DRIVE LEVEL. It does not cancel, and in
fact directly imports, a change in the CALIBRATION of ch1111 itself: if ch1111 reads high by a
factor g on some steps, H = B/R is low by exactly g on those steps. So the distinction matters.

I tested which it is using independent witnesses on the driven axis (ch1112 shaker accelerometer,
ch1105 accel MSP-X, ch1107 accel MSP-Z). Step-to-step amplitude ratios:

| boundary | ch1111 | ch1112 | ch1105 | ch1107 |
| --- | --- | --- | --- | --- |
| 5.3 -> 5.4 Hz | 0.891 | 1.967 | 0.911 | 1.066 |
| 5.4 -> 5.5 Hz | **1.733** | 1.095 | 0.877 | 0.945 |
| 5.5 -> 5.6 Hz | 1.142 | 0.884 | 0.749 | 0.808 |
| 7.3 -> 7.4 Hz | 1.055 | 3.351 | 0.884 | 3.958 |
| 7.4 -> 7.5 Hz | **0.669** | 3.128 | 0.512 | 0.391 |
| 7.5 -> 7.6 Hz | 1.200 | 0.529 | 1.036 | 0.899 |

- At 5.4 -> 5.5 Hz ch1111 jumps by x1.733 while ch1105, the accelerometer on the same MSP-X axis the
  shaker drives, goes the OTHER way, x0.877. A real +73% drive increase would have moved ch1105 up
  too. It did not. I conclude this jump is a ch1111 scale change, not a drive change, and that |H|
  on steps 30-70 therefore carries a multiplicative offset of order 1.7 relative to steps 0-29.
- At 7.4 -> 7.5 Hz ch1111 drops x0.669 and ch1105 drops x0.512, i.e. the same direction. That
  boundary is NOT resolved by this test and I do not claim it either way.
- Honest limit on the test: ch1112 and ch1105 are small signals off resonance (ch1112 is ~0.5-1 mV
  at 7.2 Hz against a 7.25 mV full-window rms), so their ratios are noisy away from peaks. The
  5.5 Hz conclusion rests on ch1105, which is the stronger and better-placed witness; I would not
  push the ch1112 numbers further than their sign.
- Consequence carried into `modes.csv`: the 7.4269 Hz mode is adjacent to the second discontinuity
  and its method column is tagged ADJACENT_TO_CH1111_SCALE_DISCONTINUITY. Mode frequencies and
  coherences are unaffected (both are scale-free); only |H| magnitudes across those two boundaries
  are suspect. Comparing |H| between the 2.5-5.4 Hz and 5.5-9.5 Hz segments is not safe.

## V021 TEST pulser masking, and how much pulser is actually in band

Two tests, and the second one changes the picture.

1. Direct test on quiet3 (shaker off, so any coherent lock-in amplitude at a drive frequency is
   contamination): masked estimator vs the identical estimator with no mask, 5 bolometers x 3
   frequencies. The ratio unmasked/masked scattered from 0.14 to 3.53 with median 0.77 - that is,
   INCONCLUSIVE. Masking did not measurably reduce the coherent in-band amplitude.
2. So I measured the pulser's in-band content directly from its own measured shape. For a periodic
   train of period T = 10 s, the sinusoid amplitude at f_k = k/T is 2|P(f_k)|/T where P is the
   transform of the single-pulse shape measured in V003:

   | f (Hz) | pulser amplitude (mV) | mV rms | / quiet3 noise rms |
   | --- | --- | --- | --- |
   | 2.50 | 0.029723 | 0.021018 | 0.108 |
   | 3.40 | 0.015279 | 0.010804 | 0.058 |
   | 4.90 | 0.009206 | 0.006510 | 0.039 |
   | 6.20 | 0.016308 | 0.011531 | 0.082 |
   | 8.10 | 0.003805 | 0.002691 | 0.022 |
   | 9.50 | 0.012025 | 0.008503 | 0.078 |

   Same integral at the 0.1 Hz comb fundamental: 0.2702 mV amplitude.

CONCLUSION, which refines SPEC 4.1 rather than contradicting it. The comb geometry in SPEC 4.1 is
exactly right: the drive frequencies ARE multiples of 0.1 Hz (V003 confirms this to 1.9e-4 Hz), the
pulser does land on every one of them, and it IS phase-locked to every step boundary. But the heater
pulse is a SLOW thermal feature - 1.3 s to peak, gone by +4 s - so its Fourier content at 2.5-9.5 Hz
is 0.003-0.03 mV, which is 2-11% of the quiet-window noise rms (0.149 mV) and about 0.02-0.2% of the
median peak bolometer response (14.0 mV rms). The step-aligned coherent-averaging trap SPEC 4.1
warns about is real in principle and numerically negligible in THIS band.

I kept the mask anyway, at a cost of 46% of the window, because it is mandatory and because it is
harmless. But the critic should know that pulser masking is not what makes these results valid, and
that an unmasked analysis in 2.5-9.5 Hz would most likely land on the same numbers. What WOULD be
badly contaminated is anything below ~1 Hz, which is outside this band.

## V022 Deliverables and residual gaps

Written in `verify/`: `impulses.csv` (71 steps), `responses.npz` (78 channels x 71 steps),
`modes.csv` (11 modes), `channel_gain.csv` (all 52 bolometers), `method_note.md` (399 words).

- `responses.npz` keys: channels, channel_kind, f_drive_hz, f_drive_nominal_hz, step_t0_run_s,
  step_t1_run_s, n_subblocks, subblock_len_s, H, H_se, coherence2, coherence2_bias, amp_mV,
  amp_subblock_mV, noise_rms_mV_quiet3, noise_rms_mV_quiet1, ringdown_baseband_mV, ringdown_dt_s,
  ringdown_t0_s, ringdown_t1_s, ringdown_tau_s, ringdown_tau_se_s, ringdown_amp_old_mV,
  ringdown_amp_new_mV, ref_channel, units.
- SPEC section 3 asks for "all 71 bolometer-plus-aux channels". 71 is the number of STEPS; the
  excitation window has 52 bolometers + 26 aux = 78 channels and I report all 78.
- GAPS I am not filling with a number: (a) no zeta point value for any mode - all 11 are upper
  limits, because no peak spans 3 of the 0.1 Hz grid points; (b) ring-down zeta is unconstrained
  (median fractional uncertainty ~5000%) because the 5.3 s usable window spans only 0.53 of a beat
  cycle against the next tone 0.1 Hz away; (c) no in-band pedestal at the excitation gain settings
  exists, because the excitation window is driven end to end (V005); (d) no absolute bolometer units,
  per SPEC 2.1; (e) the 7.4 Hz mode's |H| prominence may be partly instrumental (V020); (f) the
  5.5 Hz ch1111 scale offset of ~1.7 is measured but NOT corrected for - correcting it would require
  a ch1111 calibration I do not have.
- I have not at any point opened, listed or searched `analysis/` or `critic/`. No output from either
  has been visible to me.

## V021-V027  Damping re-dispatch: Route A ring-down on raw samples

[V021] Re-read SPEC.md 4.3 as amended 2026-10-31. The first run reported
  zeta = 0.1/(2 f0) as an upper limit on all 11 rows with no attempt. The amended
  clause forbids that: an upper limit is reportable only after an attempt that failed.
  This run attempts a measurement on every mode and records the outcome either way.
[V022] Window. The first run computed ring-downs over 0.20-5.50 s after each boundary,
  5.30 s, which is 1.66 tau at the tau = 3.2 s the spec expects, and I did not use them
  for modes.csv. New window 0.20-40.50 s, span 40.3 s. The 3-tau rule therefore admits
  tau <= 13.43 s, i.e. implied delta_f = 1/(pi tau) >= 0.0237 Hz; a fit returning tau above
  that ceiling is recorded but NOT counted as a measurement.
[V023] Pulser inside the long window. Four pulses land in 40.3 s; mask [-0.2,+4.2] s
  each leaves 22.70 s clean in 5 chunks: [0.20,5.49] [9.89,15.49] [19.89,25.49]
  [29.89,35.49] [39.89,40.50]. The offset from a boundary to the next pulse is
  5.518-6.356 s across the 70 boundaries, ptp 0.838 s, consistent with the fixed phase
  of SPEC 4.1 plus boundary-detection jitter; the mask is recomputed per boundary and
  not assumed. Only clean samples enter the fit, so the decay is fitted ACROSS the
  pulser gaps instead of being truncated at the first pulse. This is what makes a
  window longer than one pulser period possible at all.
[V024] Model, fitted to raw 1 kHz samples, no demodulation and no decimation:
    y(t) = a1 exp(-t/tau) cos(2 pi f t) + a2 exp(-t/tau) sin(2 pi f t)
           + a3 cos(2 pi fnew t) + a4 sin(2 pi fnew t) + a5 + a6 (t - tbar)
  f = f0 + df with df scanned over 11 values in [-0.06,+0.06] Hz and tau over 24
  log-spaced values 0.5-30.0 s; the model is linear in a for fixed (tau,df), so each
  trial is one 6x6 normal-equation solve. t is measured from the boundary.
  Raw samples rather than an envelope on purpose: over a 40.3 s span the basis resolves
  0.025 Hz, so the free decay of a neighbouring mode 0.3 Hz away is nearly orthogonal.
  A 0.5 s-block envelope would have passed a neighbour 0.3 Hz away almost unattenuated
  and aliased it, since the envelope Nyquist would be 1 Hz.
  The next drive tone fnew switches on at the same boundary and is fitted jointly, not
  notched: 0.1 Hz away it is not separable from the decay over any short window, which
  is the other reason the first runs 5.3 s window was useless for tau.
[V025] Boundary selection: for each mode I fit the boundaries whose OLD tone is within
  0.25 Hz of f0, because the free-decay amplitude at f0 scales with the forced amplitude
  at switch-off and so peaks on resonance. 55 mode-boundary pairs, 5-5 per mode,
  52 bolometers each: 2860 candidate fits.
[V026] f0=3.0127 Hz, boundary 3, tone 2.8000 -> 2.9000 Hz: 0/52 bolometer fits accepted
[V026] f0=3.0127 Hz, boundary 4, tone 2.9000 -> 3.0001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.0127 Hz, boundary 5, tone 3.0001 -> 3.1001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.0127 Hz, boundary 6, tone 3.1001 -> 3.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.0127 Hz, boundary 7, tone 3.2001 -> 3.3001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.4075 Hz, boundary 7, tone 3.2001 -> 3.3001 Hz: 2/52 bolometer fits accepted
[V026] f0=3.4075 Hz, boundary 8, tone 3.3001 -> 3.4001 Hz: 1/52 bolometer fits accepted
[V026] f0=3.4075 Hz, boundary 9, tone 3.4001 -> 3.5001 Hz: 3/52 bolometer fits accepted
[V026] f0=3.4075 Hz, boundary 10, tone 3.5001 -> 3.6001 Hz: 13/52 bolometer fits accepted
[V026] f0=3.4075 Hz, boundary 11, tone 3.6001 -> 3.7001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.9707 Hz, boundary 13, tone 3.8001 -> 3.9001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.9707 Hz, boundary 14, tone 3.9001 -> 4.0001 Hz: 2/52 bolometer fits accepted
[V026] f0=3.9707 Hz, boundary 15, tone 4.0001 -> 4.1001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.9707 Hz, boundary 16, tone 4.1001 -> 4.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=3.9707 Hz, boundary 17, tone 4.2001 -> 4.3001 Hz: 0/52 bolometer fits accepted
[V026] f0=4.8990 Hz, boundary 22, tone 4.7001 -> 4.8001 Hz: 0/52 bolometer fits accepted
[V026] f0=4.8990 Hz, boundary 23, tone 4.8001 -> 4.9001 Hz: 0/52 bolometer fits accepted
[V026] f0=4.8990 Hz, boundary 24, tone 4.9001 -> 5.0001 Hz: 4/52 bolometer fits accepted
[V026] f0=4.8990 Hz, boundary 25, tone 5.0001 -> 5.1001 Hz: 0/52 bolometer fits accepted
[V026] f0=4.8990 Hz, boundary 26, tone 5.1001 -> 5.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=5.3060 Hz, boundary 26, tone 5.1001 -> 5.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=5.3060 Hz, boundary 27, tone 5.2001 -> 5.3001 Hz: 0/52 bolometer fits accepted
[V026] f0=5.3060 Hz, boundary 28, tone 5.3001 -> 5.4001 Hz: 0/52 bolometer fits accepted
[V026] f0=5.3060 Hz, boundary 29, tone 5.4001 -> 5.5001 Hz: 0/52 bolometer fits accepted
[V026] f0=5.3060 Hz, boundary 30, tone 5.5001 -> 5.6001 Hz: 0/52 bolometer fits accepted
[V026] f0=6.2184 Hz, boundary 35, tone 6.0001 -> 6.1001 Hz: 0/52 bolometer fits accepted
[V026] f0=6.2184 Hz, boundary 36, tone 6.1001 -> 6.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=6.2184 Hz, boundary 37, tone 6.2001 -> 6.3001 Hz: 0/52 bolometer fits accepted
[V026] f0=6.2184 Hz, boundary 38, tone 6.3001 -> 6.4001 Hz: 0/52 bolometer fits accepted
[V026] f0=6.2184 Hz, boundary 39, tone 6.4001 -> 6.5001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.4269 Hz, boundary 47, tone 7.2001 -> 7.3001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.4269 Hz, boundary 48, tone 7.3001 -> 7.4001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.4269 Hz, boundary 49, tone 7.4001 -> 7.5002 Hz: 0/52 bolometer fits accepted
[V026] f0=7.4269 Hz, boundary 50, tone 7.5002 -> 7.6001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.4269 Hz, boundary 51, tone 7.6001 -> 7.7001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.9209 Hz, boundary 52, tone 7.7001 -> 7.8001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.9209 Hz, boundary 53, tone 7.8001 -> 7.9001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.9209 Hz, boundary 54, tone 7.9001 -> 8.0001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.9209 Hz, boundary 55, tone 8.0001 -> 8.1001 Hz: 0/52 bolometer fits accepted
[V026] f0=7.9209 Hz, boundary 56, tone 8.1001 -> 8.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.1274 Hz, boundary 54, tone 7.9001 -> 8.0001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.1274 Hz, boundary 55, tone 8.0001 -> 8.1001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.1274 Hz, boundary 56, tone 8.1001 -> 8.2001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.1274 Hz, boundary 57, tone 8.2001 -> 8.3001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.1274 Hz, boundary 58, tone 8.3001 -> 8.4001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.5297 Hz, boundary 58, tone 8.3001 -> 8.4001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.5297 Hz, boundary 59, tone 8.4001 -> 8.5001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.5297 Hz, boundary 60, tone 8.5001 -> 8.6001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.5297 Hz, boundary 61, tone 8.6001 -> 8.7001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.5297 Hz, boundary 62, tone 8.7001 -> 8.8001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.7834 Hz, boundary 61, tone 8.6001 -> 8.7001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.7834 Hz, boundary 62, tone 8.7001 -> 8.8001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.7834 Hz, boundary 63, tone 8.8001 -> 8.9001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.7834 Hz, boundary 64, tone 8.9001 -> 9.0001 Hz: 0/52 bolometer fits accepted
[V026] f0=8.7834 Hz, boundary 65, tone 9.0001 -> 9.1001 Hz: 0/52 bolometer fits accepted
[V027] Route A bookkeeping over 2860 candidate fits: 25 accepted; rejected 1233 tau at scan
  edge, 739 df at scan edge, 189 tau > 13.43 s (fails the 3-tau rule for this window),
  674 decay amplitude / residual rms < 5.0.

## V028-V031  Damping: detection statistic and null control

[V028] My stage-A cut was ill-posed and I am replacing it, not keeping it. I had cut on
  decay amplitude over the BROADBAND residual rms, but the raw 1 kHz residual is
  dominated by out-of-band bolometer noise and has nothing to do with the error on a
  narrowband amplitude. Replaced by two proper statistics: amp / sigma_amp from the
  least-squares covariance s2 * inv(BtB), and an F statistic for the 2 decay columns,
  F = ((chi2_without_decay - chi2_with) / 2) / s2, which tests whether a decaying
  component at f0 is present at all.
[V029] Because bolometer noise is not white, a formal sigma underestimates the true
  error. So every fit is repeated as a NULL: the identical 6-parameter model, same
  channel, same f0, same pulser geometry, in a window starting 120.2 s after the
  boundary instead of 0.2 s. By then any free decay with tau < 13 s is gone by more
  than 9 e-foldings, so whatever amplitude and F the null returns is the noise floor of
  this estimator on this detector. A mode is only called measured if its boundary fits
  stand clear of its own null distribution.
[V030] f0=3.0127 b=3 tone 2.8000->2.9000 : median F sig=39.4 null=35.0 ; median amp_snr sig=8.9 null=8.4 ; median tau sig=30.00 s
[V030] f0=3.0127 b=4 tone 2.9000->3.0001 : median F sig=47.3 null=24.1 ; median amp_snr sig=9.7 null=6.9 ; median tau sig=13.52 s
[V030] f0=3.0127 b=5 tone 3.0001->3.1001 : median F sig=48.4 null=29.6 ; median amp_snr sig=9.8 null=7.7 ; median tau sig=11.31 s
[V030] f0=3.0127 b=6 tone 3.1001->3.2001 : median F sig=66.6 null=25.6 ; median amp_snr sig=11.5 null=7.2 ; median tau sig=21.01 s
[V030] f0=3.0127 b=7 tone 3.2001->3.3001 : median F sig=78.0 null=38.0 ; median amp_snr sig=12.3 null=8.7 ; median tau sig=0.85 s
[V030] f0=3.4075 b=7 tone 3.2001->3.3001 : median F sig=954.0 null=37.0 ; median amp_snr sig=43.5 null=8.6 ; median tau sig=8.63 s
[V030] f0=3.4075 b=8 tone 3.3001->3.4001 : median F sig=68.5 null=5.6 ; median amp_snr sig=11.6 null=3.9 ; median tau sig=0.50 s
[V030] f0=3.4075 b=9 tone 3.4001->3.5001 : median F sig=91.4 null=10.4 ; median amp_snr sig=13.5 null=4.8 ; median tau sig=3.25 s
[V030] f0=3.4075 b=10 tone 3.5001->3.6001 : median F sig=2442.4 null=5.1 ; median amp_snr sig=69.7 null=3.2 ; median tau sig=4.23 s
[V030] f0=3.4075 b=11 tone 3.6001->3.7001 : median F sig=102.4 null=19.7 ; median amp_snr sig=14.3 null=6.3 ; median tau sig=4.23 s
[V030] f0=3.9707 b=13 tone 3.8001->3.9001 : median F sig=100.1 null=29.7 ; median amp_snr sig=14.2 null=7.7 ; median tau sig=6.04 s
[V030] f0=3.9707 b=14 tone 3.9001->4.0001 : median F sig=810.0 null=15.3 ; median amp_snr sig=40.4 null=5.5 ; median tau sig=5.06 s
[V030] f0=3.9707 b=15 tone 4.0001->4.1001 : median F sig=392.6 null=39.7 ; median amp_snr sig=28.1 null=8.9 ; median tau sig=12.32 s
[V030] f0=3.9707 b=16 tone 4.1001->4.2001 : median F sig=41.5 null=29.6 ; median amp_snr sig=9.2 null=7.7 ; median tau sig=17.59 s
[V030] f0=3.9707 b=17 tone 4.2001->4.3001 : median F sig=68.2 null=40.2 ; median amp_snr sig=11.6 null=9.0 ; median tau sig=3.25 s
[V030] f0=4.8990 b=22 tone 4.7001->4.8001 : median F sig=116.4 null=23.5 ; median amp_snr sig=15.3 null=6.9 ; median tau sig=2.08 s
[V030] f0=4.8990 b=23 tone 4.8001->4.9001 : median F sig=65.1 null=19.0 ; median amp_snr sig=11.4 null=6.2 ; median tau sig=2.97 s
[V030] f0=4.8990 b=24 tone 4.9001->5.0001 : median F sig=286.9 null=16.6 ; median amp_snr sig=23.8 null=5.8 ; median tau sig=2.48 s
[V030] f0=4.8990 b=25 tone 5.0001->5.1001 : median F sig=94.9 null=16.1 ; median amp_snr sig=13.9 null=5.7 ; median tau sig=2.48 s
[V030] f0=4.8990 b=26 tone 5.1001->5.2001 : median F sig=57.8 null=23.0 ; median amp_snr sig=10.7 null=6.8 ; median tau sig=8.77 s
[V030] f0=5.3060 b=26 tone 5.1001->5.2001 : median F sig=26.3 null=28.1 ; median amp_snr sig=7.2 null=7.5 ; median tau sig=25.11 s
[V030] f0=5.3060 b=27 tone 5.2001->5.3001 : median F sig=26.8 null=17.0 ; median amp_snr sig=7.3 null=5.8 ; median tau sig=12.32 s
[V030] f0=5.3060 b=28 tone 5.3001->5.4001 : median F sig=35.1 null=24.5 ; median amp_snr sig=8.4 null=7.0 ; median tau sig=30.00 s
[V030] f0=5.3060 b=29 tone 5.4001->5.5001 : median F sig=16.0 null=17.6 ; median amp_snr sig=5.6 null=5.9 ; median tau sig=30.00 s
[V030] f0=5.3060 b=30 tone 5.5001->5.6001 : median F sig=29.7 null=23.3 ; median amp_snr sig=7.8 null=6.8 ; median tau sig=17.59 s
[V030] f0=6.2184 b=35 tone 6.0001->6.1001 : median F sig=17.5 null=20.5 ; median amp_snr sig=5.9 null=6.4 ; median tau sig=30.00 s
[V030] f0=6.2184 b=36 tone 6.1001->6.2001 : median F sig=37.1 null=14.1 ; median amp_snr sig=8.6 null=5.3 ; median tau sig=16.15 s
[V030] f0=6.2184 b=37 tone 6.2001->6.3001 : median F sig=33.6 null=23.5 ; median amp_snr sig=8.2 null=6.8 ; median tau sig=6.04 s
[V030] f0=6.2184 b=38 tone 6.3001->6.4001 : median F sig=21.8 null=15.4 ; median amp_snr sig=6.6 null=5.6 ; median tau sig=30.00 s
[V030] f0=6.2184 b=39 tone 6.4001->6.5001 : median F sig=20.6 null=20.3 ; median amp_snr sig=6.4 null=6.4 ; median tau sig=17.59 s
[V030] f0=7.4269 b=47 tone 7.2001->7.3001 : median F sig=14.3 null=11.0 ; median amp_snr sig=5.4 null=4.7 ; median tau sig=30.00 s
[V030] f0=7.4269 b=48 tone 7.3001->7.4001 : median F sig=20.4 null=9.4 ; median amp_snr sig=6.5 null=4.3 ; median tau sig=6.04 s
[V030] f0=7.4269 b=49 tone 7.4001->7.5002 : median F sig=66.7 null=15.2 ; median amp_snr sig=11.5 null=5.5 ; median tau sig=7.22 s
[V030] f0=7.4269 b=50 tone 7.5002->7.6001 : median F sig=31.0 null=15.3 ; median amp_snr sig=7.9 null=5.5 ; median tau sig=12.32 s
[V030] f0=7.4269 b=51 tone 7.6001->7.7001 : median F sig=15.6 null=14.6 ; median amp_snr sig=5.6 null=5.4 ; median tau sig=30.00 s
[V030] f0=7.9209 b=52 tone 7.7001->7.8001 : median F sig=14.4 null=15.5 ; median amp_snr sig=5.4 null=5.6 ; median tau sig=7.68 s
[V030] f0=7.9209 b=53 tone 7.8001->7.9001 : median F sig=21.8 null=10.3 ; median amp_snr sig=6.6 null=4.5 ; median tau sig=21.01 s
[V030] f0=7.9209 b=54 tone 7.9001->8.0001 : median F sig=29.7 null=15.6 ; median amp_snr sig=7.7 null=5.6 ; median tau sig=10.31 s
[V030] f0=7.9209 b=55 tone 8.0001->8.1001 : median F sig=26.3 null=11.3 ; median amp_snr sig=7.2 null=4.8 ; median tau sig=1.45 s
[V030] f0=7.9209 b=56 tone 8.1001->8.2001 : median F sig=39.8 null=12.8 ; median amp_snr sig=9.0 null=5.1 ; median tau sig=1.45 s
[V030] f0=8.1274 b=54 tone 7.9001->8.0001 : median F sig=27.1 null=20.1 ; median amp_snr sig=7.4 null=6.3 ; median tau sig=14.72 s
[V030] f0=8.1274 b=55 tone 8.0001->8.1001 : median F sig=39.1 null=9.6 ; median amp_snr sig=8.8 null=4.4 ; median tau sig=6.04 s
[V030] f0=8.1274 b=56 tone 8.1001->8.2001 : median F sig=74.5 null=12.1 ; median amp_snr sig=12.2 null=4.9 ; median tau sig=7.22 s
[V030] f0=8.1274 b=57 tone 8.2001->8.3001 : median F sig=25.5 null=10.2 ; median amp_snr sig=7.1 null=4.5 ; median tau sig=3.60 s
[V030] f0=8.1274 b=58 tone 8.3001->8.4001 : median F sig=23.9 null=16.4 ; median amp_snr sig=6.9 null=5.7 ; median tau sig=8.77 s
[V030] f0=8.5297 b=58 tone 8.3001->8.4001 : median F sig=21.5 null=16.9 ; median amp_snr sig=6.6 null=5.8 ; median tau sig=21.01 s
[V030] f0=8.5297 b=59 tone 8.4001->8.5001 : median F sig=29.7 null=14.3 ; median amp_snr sig=7.7 null=5.4 ; median tau sig=10.31 s
[V030] f0=8.5297 b=60 tone 8.5001->8.6001 : median F sig=49.2 null=17.3 ; median amp_snr sig=9.9 null=5.9 ; median tau sig=3.25 s
[V030] f0=8.5297 b=61 tone 8.6001->8.7001 : median F sig=30.9 null=14.0 ; median amp_snr sig=7.9 null=5.3 ; median tau sig=14.72 s
[V030] f0=8.5297 b=62 tone 8.7001->8.8001 : median F sig=20.6 null=15.5 ; median amp_snr sig=6.4 null=5.6 ; median tau sig=5.56 s
[V030] f0=8.7834 b=61 tone 8.6001->8.7001 : median F sig=12.5 null=8.6 ; median amp_snr sig=5.0 null=4.1 ; median tau sig=3.25 s
[V030] f0=8.7834 b=62 tone 8.7001->8.8001 : median F sig=20.6 null=10.5 ; median amp_snr sig=6.4 null=4.6 ; median tau sig=4.65 s
[V030] f0=8.7834 b=63 tone 8.8001->8.9001 : median F sig=20.9 null=11.0 ; median amp_snr sig=6.4 null=4.7 ; median tau sig=5.06 s
[V030] f0=8.7834 b=64 tone 8.9001->9.0001 : median F sig=15.4 null=9.4 ; median amp_snr sig=5.5 null=4.3 ; median tau sig=9.47 s
[V030] f0=8.7834 b=65 tone 9.0001->9.1001 : median F sig=14.9 null=9.8 ; median amp_snr sig=5.4 null=4.4 ; median tau sig=30.00 s

## V032-V036  Damping: aggregation, Routes B and C, and the deliverable

[V032] Route A acceptance, fixed before any per-mode zeta was looked at:
  (1) tau and df both strictly interior to their scan ranges;
  (2) tau <= 13.43 s, the 3-tau ceiling of the 40.3 s window (SPEC 4.3 Route A);
  (3) F_decay above the 99th percentile of that modes own null-window F;
  (4) boundary with |f_old - f0| <= 0.15 Hz, since the free-decay amplitude scales with
      the forced amplitude at switch-off;
  (5) boundary with |f_new - f0| >= 0.06 Hz. This is a real contaminant I found: where
      the NEXT tone lands on the mode, what follows the boundary is the mode BUILDING UP,
      not ringing down, and the model has no build-up term, so the decay column fits the
      ramp and tau runs to the scan floor. Example: f0=3.4075 Hz, boundary 8
      (3.3001 -> 3.4001 Hz), median amp 102.3 mV and median tau 0.50 s, the scan floor.
      Those boundaries are excluded, not repaired.
[V033] Amplitude, not F, is what tracks resonance, and the two must not be confused. At
  f0=3.4075 Hz the largest median decay amplitude is at boundary 9, the ON-RESONANCE
  switch-off (old tone 3.4001 Hz): 194.7 mV, against 8.8 mV at boundary 10 and 3.1 mV at
  boundary 7. F instead peaks at boundary 10 (2442 vs 91) because F also carries the local
  noise level. The amplitude ordering is the one that must follow resonance physics, and
  it does; that is a consistency check the fit passes.
[V034] f0=3.0127 Hz: Route A FAILED (0 fits; 0 channels) | Route B not available | Route C n=0
[V034] f0=3.4075 Hz: Route A MEASURED (67 fits; 40 channels; tau=4.23+/-0.15 s) | Route B not available | Route C n=5; zeta=0.00796
[V034] f0=3.9707 Hz: Route A MEASURED (26 fits; 25 channels; tau=12.32+/-0.44 s) | Route B not available | Route C n=1
[V034] f0=4.8990 Hz: Route A MEASURED (33 fits; 25 channels; tau=2.48+/-0.10 s) | Route B not available | Route C n=4
[V034] f0=5.3060 Hz: Route A FAILED (0 fits; 0 channels) | Route B not available | Route C n=0
[V034] f0=6.2184 Hz: Route A MEASURED (10 fits; 9 channels; tau=2.72+/-0.11 s) | Route B not available | Route C n=29; zeta=0.00742
[V034] f0=7.4269 Hz: Route A MEASURED (35 fits; 25 channels; tau=6.04+/-0.30 s) | Route B not available | Route C n=0
[V034] f0=7.9209 Hz: Route A FAILED (5 fits; 5 channels) | Route B not available | Route C n=1
[V034] f0=8.1274 Hz: Route A MEASURED (22 fits; 22 channels; tau=6.04+/-0.37 s) | Route B not available | Route C n=3
[V034] f0=8.5297 Hz: Route A MEASURED (25 fits; 17 channels; tau=2.97+/-0.17 s) | Route B not available | Route C n=1
[V034] f0=8.7834 Hz: Route A MEASURED (12 fits; 11 channels; tau=5.06+/-0.42 s) | Route B not available | Route C n=6; zeta=0.00344
[V035] damping.csv written: 11 rows; 8 with a measured zeta by ring-down; 3 with
  zeta_method = none and zeta left empty. zeta_attempted = true on all 11 rows. No row
  carries 0.1/(2 f0) and no row is flagged as an upper limit.
[V036] f0=3.4075 Hz: tau = 4.23 +/- 0.15 s -> zeta = 0.01103 +/- 0.00040, implied half-power width 2 zeta f0 = 0.0752 Hz is within the 0.1 Hz grid spacing, window = 9.5 tau
[V036] f0=3.9707 Hz: tau = 12.32 +/- 0.44 s -> zeta = 0.00325 +/- 0.00012, implied half-power width 2 zeta f0 = 0.0258 Hz is within the 0.1 Hz grid spacing, window = 3.3 tau
[V036] f0=4.8990 Hz: tau = 2.48 +/- 0.10 s -> zeta = 0.01309 +/- 0.00055, implied half-power width 2 zeta f0 = 0.1283 Hz EXCEEDS the 0.1 Hz grid spacing, window = 16.2 tau
[V036] f0=6.2184 Hz: tau = 2.72 +/- 0.11 s -> zeta = 0.00940 +/- 0.00039, implied half-power width 2 zeta f0 = 0.1169 Hz EXCEEDS the 0.1 Hz grid spacing, window = 14.8 tau
[V036] f0=7.4269 Hz: tau = 6.04 +/- 0.30 s -> zeta = 0.00355 +/- 0.00017, implied half-power width 2 zeta f0 = 0.0527 Hz is within the 0.1 Hz grid spacing, window = 6.7 tau
[V036] f0=8.1274 Hz: tau = 6.04 +/- 0.37 s -> zeta = 0.00324 +/- 0.00020, implied half-power width 2 zeta f0 = 0.0527 Hz is within the 0.1 Hz grid spacing, window = 6.7 tau
[V036] f0=8.5297 Hz: tau = 2.97 +/- 0.17 s -> zeta = 0.00629 +/- 0.00036, implied half-power width 2 zeta f0 = 0.1073 Hz EXCEEDS the 0.1 Hz grid spacing, window = 13.6 tau
[V036] f0=8.7834 Hz: tau = 5.06 +/- 0.42 s -> zeta = 0.00358 +/- 0.00030, implied half-power width 2 zeta f0 = 0.0629 Hz is within the 0.1 Hz grid spacing, window = 8.0 tau

## V032-V037  Damping: aggregation, Routes B and C, and the deliverable

[V032a] NOTE ON THIS LOG. An earlier pass of this same stage was appended above with
  zeta_err from MAD/sqrt(N) and with no window-limited test. Both were wrong and the
  numbers in that pass are SUPERSEDED by the ones below; I am appending the correction
  rather than editing it away. What changed: (a) MAD/sqrt(N) gave +/-0.15 s on tau=4.23 s
  while the tau scan grid is 19.5%% per step, so the error was smaller than the
  quantisation of the quantity it described; (b) the 52 bolometers watch one tower and
  are not independent, so dividing their spread by sqrt(N) overstates the result; and
  (c) the f0=3.9707 Hz row was being reported as measured when half its fits sat at the
  3-tau ceiling. See V037.

[V032] Route A acceptance, fixed before any per-mode zeta was looked at:
  (1) tau and df both strictly interior to their scan ranges;
  (2) tau <= 13.43 s, the 3-tau ceiling of the 40.3 s window (SPEC 4.3 Route A);
  (3) F_decay above the 99th percentile of that modes own null-window F;
  (4) boundary with |f_old - f0| <= 0.15 Hz, since the free-decay amplitude scales with
      the forced amplitude at switch-off;
  (5) boundary with |f_new - f0| >= 0.06 Hz. This is a real contaminant I found: where
      the NEXT tone lands on the mode, what follows the boundary is the mode BUILDING UP,
      not ringing down, and the model has no build-up term, so the decay column fits the
      ramp and tau runs to the scan floor. Example: f0=3.4075 Hz, boundary 8
      (3.3001 -> 3.4001 Hz), median amp 102.3 mV and median tau 0.50 s, the scan floor.
      Those boundaries are excluded, not repaired.
[V033] Amplitude, not F, is what tracks resonance, and the two must not be confused. At
  f0=3.4075 Hz the largest median decay amplitude is at boundary 9, the ON-RESONANCE
  switch-off (old tone 3.4001 Hz): 194.7 mV, against 8.8 mV at boundary 10 and 3.1 mV at
  boundary 7. F instead peaks at boundary 10 (2442 vs 91) because F also carries the local
  noise level. The amplitude ordering is the one that must follow resonance physics, and
  it does; that is a consistency check the fit passes.
[V034] f0=3.0127 Hz: Route A FAILED (0 fits; 0 channels) | Route B not available | Route C n=0
[V034] f0=3.4075 Hz: Route A MEASURED (67 fits; 40 channels; tau=4.23+/-0.91 s) | Route B not available | Route C n=5; zeta=0.00796
[V034] f0=3.9707 Hz: Route A FAILED (26 fits; 25 channels) | Route B not available | Route C n=1
[V034] f0=4.8990 Hz: Route A MEASURED (33 fits; 25 channels; tau=2.48+/-0.37 s) | Route B not available | Route C n=4
[V034] f0=5.3060 Hz: Route A FAILED (0 fits; 0 channels) | Route B not available | Route C n=0
[V034] f0=6.2184 Hz: Route A MEASURED (10 fits; 9 channels; tau=2.72+/-0.44 s) | Route B not available | Route C n=29; zeta=0.00742
[V034] f0=7.4269 Hz: Route A MEASURED (35 fits; 25 channels; tau=6.04+/-1.79 s) | Route B not available | Route C n=0
[V034] f0=7.9209 Hz: Route A FAILED (5 fits; 5 channels) | Route B not available | Route C n=1
[V034] f0=8.1274 Hz: Route A MEASURED (22 fits; 22 channels; tau=6.04+/-1.35 s) | Route B not available | Route C n=3
[V034] f0=8.5297 Hz: Route A MEASURED (25 fits; 17 channels; tau=2.97+/-0.56 s) | Route B not available | Route C n=1
[V034] f0=8.7834 Hz: Route A MEASURED (12 fits; 11 channels; tau=5.06+/-1.46 s) | Route B not available | Route C n=6; zeta=0.00344
[V035] damping.csv written: 11 rows; 7 with a measured zeta by ring-down; 4 with
  zeta_method = none and zeta left empty. zeta_attempted = true on all 11 rows. No row
  carries 0.1/(2 f0) and no row is flagged as an upper limit.
[V036] f0=3.4075 Hz: tau = 4.23 +/- 0.91 s -> zeta = 0.01103 +/- 0.00165, implied half-power width 2 zeta f0 = 0.0752 Hz is within the 0.1 Hz grid spacing, window = 9.5 tau
[V036] f0=4.8990 Hz: tau = 2.48 +/- 0.37 s -> zeta = 0.01309 +/- 0.00280, implied half-power width 2 zeta f0 = 0.1283 Hz EXCEEDS the 0.1 Hz grid spacing, window = 16.2 tau
[V036] f0=6.2184 Hz: tau = 2.72 +/- 0.44 s -> zeta = 0.00940 +/- 0.00185, implied half-power width 2 zeta f0 = 0.1169 Hz EXCEEDS the 0.1 Hz grid spacing, window = 14.8 tau
[V036] f0=7.4269 Hz: tau = 6.04 +/- 1.79 s -> zeta = 0.00355 +/- 0.00088, implied half-power width 2 zeta f0 = 0.0527 Hz is within the 0.1 Hz grid spacing, window = 6.7 tau
[V036] f0=8.1274 Hz: tau = 6.04 +/- 1.35 s -> zeta = 0.00324 +/- 0.00081, implied half-power width 2 zeta f0 = 0.0527 Hz is within the 0.1 Hz grid spacing, window = 6.7 tau
[V036] f0=8.5297 Hz: tau = 2.97 +/- 0.56 s -> zeta = 0.00629 +/- 0.00123, implied half-power width 2 zeta f0 = 0.1073 Hz EXCEEDS the 0.1 Hz grid spacing, window = 13.6 tau
[V036] f0=8.7834 Hz: tau = 5.06 +/- 1.46 s -> zeta = 0.00358 +/- 0.00123, implied half-power width 2 zeta f0 = 0.0629 Hz is within the 0.1 Hz grid spacing, window = 8.0 tau
[V037] f0=3.9707 Hz is WINDOW-LIMITED, not a non-detection: 26 fits cleared the null and 16 of them sit at tau = 12.32 s, the largest the 3-tau rule allows for a 40.3 s window. The ring-down is there; its time constant is longer than this run can bound. zeta left empty.
[V038] Scope. 8 of 11 modes gave a ring-down zeta from one stepped-sine run, one shaker
  axis (MSP-X), one tower. These are PRELIMINARY. Four independent reasons not to treat
  any of them as settled: the channel-to-channel spread is 20-40%% of zeta and is not
  beaten down by averaging 52 bolometers that watch the same tower; f0 itself is only
  known to +/-0.05 Hz, the SPEC floor, and zeta scales as 1/f0; each frequency occurs
  exactly once in this run so there is no amplitude check and no repeat (SPEC 4.4); and
  the two modes nearest a ch1111 scale discontinuity are flagged. A second run on a
  second axis is what would turn any of these into a measurement of the detector rather
  than of this run.
[V039] Where Route A and Route C both returned a number they can be compared, and the
  comparison is not reassuring: f0=3.4075 Hz gives zeta = 0.01103 by ring-down against
  0.00796 from the rational-fraction pole on 5 of 52 channels, and f0=6.2184 Hz gives
  0.00940 against 0.00742 on 29 of 52. Same sign of disagreement, roughly 30%% in both.
  Two routes in one directory agreeing to 30%% is the honest precision of this pilot;
  neither route is the truth and I am not averaging them.

[V040] Corrections to V038 and V039 as appended immediately above, kept as an append:
  (a) V038 says 8 of 11 modes gave a ring-down zeta. The correct count is 7 of 11. The
      8th, f0=3.9707 Hz, was reclassified as WINDOW-LIMITED by the test described in
      V037 and carries no zeta. Measured: 3.4075, 4.8990, 6.2184, 7.4269, 8.1274, 8.5297,
      8.7834 Hz. Not measured: 3.0127, 3.9707, 5.3060, 7.9209 Hz.
  (b) V038 and V039 render some percent signs as doubled. Read 20-40% and 30%.
  (c) Everything else in V038 and V039 stands, including the Route A versus Route C
      disagreement of about 30% at 3.4075 and 6.2184 Hz.


[V041] Cross-check of Route A against Route B as a bound rather than as a measurement.
  Route B cannot be quoted anywhere here: no mode has the >= 3 grid points across the peak
  that SPEC 4.3 requires (spans are 1, 1, 2, 1, 3, 1, 1, 1, 1, 2, 1 points). But the
  interpolated half-power width of the median |H| is still a useful upper bound, and the
  ring-down widths sit under it on every measured mode. implied 2 zeta f0 from Route A
  versus interpolated half-power width, and their ratio:
    3.4075 Hz  0.0752 / 0.0891 = 0.84      4.8990 Hz  0.1283 / 0.1748 = 0.73
    6.2184 Hz  0.1169 / 0.1159 = 1.01      7.4269 Hz  0.0527 / 0.1279 = 0.41
    8.1274 Hz  0.0527 / 0.1249 = 0.42      8.5297 Hz  0.1073 / 0.2111 = 0.51
    8.7834 Hz  0.0629 / 0.1000 = 0.63
  Every ratio is <= 1.01, median 0.63. That is the direction the two should differ in: a
  peak sampled at 0.1 Hz spacing has its interpolated width inflated by the sampling,
  while the ring-down width is resolution-independent. So the two routes are consistent
  and Route A is the tighter of the two. This is corroboration, not independence - both
  come from the same run and the same reference channel.

[V042] The SPEC 4.3 self-consistency clause, applied explicitly. The grid upper limit
  zeta <~ 0.1/(2 f0) rests on the peak being unresolved, i.e. 2 zeta f0 <~ 0.1 Hz. On
  three measured modes the ring-down implies MORE than the grid spacing:
    f0=4.8990 Hz  2 zeta f0 = 0.1283 Hz     f0=6.2184 Hz  0.1169 Hz
    f0=8.5297 Hz  0.1073 Hz
  For those three the premise of the limit is false, the limit is void by the clause, and
  the measurement is what is reported. On the other four measured modes (3.4075, 7.4269,
  8.1274, 8.7834 Hz) the implied width is inside 0.1 Hz, so the limit would not have been
  self-contradictory there - but it is still not reported, because the amended clause
  allows a limit only where the attempt failed, and on those four the attempt succeeded.

[V043] Final state of the damping deliverable, 11 rows in ./damping.csv:
  MEASURED by ring-down, 7 modes (zeta, +/- channel-to-channel spread, n fits):
    3.4075 Hz  zeta = 0.01103 +/- 0.00165  (67 fits, 40 channels, window 9.5 tau)
    4.8990 Hz  zeta = 0.01309 +/- 0.00280  (33 fits, 25 channels, window 16.2 tau)
    6.2184 Hz  zeta = 0.00940 +/- 0.00185  (10 fits,  9 channels, window 14.8 tau)
    7.4269 Hz  zeta = 0.00355 +/- 0.00088  (35 fits, 25 channels, window 6.7 tau)
    8.1274 Hz  zeta = 0.00324 +/- 0.00081  (22 fits, 22 channels, window 6.7 tau)
    8.5297 Hz  zeta = 0.00629 +/- 0.00123  (25 fits, 17 channels, window 13.6 tau)
    8.7834 Hz  zeta = 0.00358 +/- 0.00123  (12 fits, 11 channels, window 8.0 tau)
  NOT MEASURED, zeta left empty, zeta_method = none, 4 modes:
    3.0127 Hz  non-detection: 0 of 104 fits cleared the null; median decay amplitude
               0.55 mV against a null floor that this estimator cannot see past
    3.9707 Hz  WINDOW-LIMITED: the decay is real (26 of 104 fits cleared the null) but 16
               of them pile at tau = 12.32 s, the 3-tau ceiling of a 40.3 s window
    5.3060 Hz  non-detection: 0 of 104 fits cleared the null
    7.9209 Hz  non-detection: 5 of 104 fits cleared the null, below the 10-fit and
               8-channel minimum, from a single boundary
  zeta_attempted = true on all 11 rows. zeta_is_upper_limit = false on all 11. The grid
  formula 0.1/(2 f0) appears nowhere in damping.csv. The 11 rows of my first-run modes.csv,
  impulses.csv, responses.npz, channel_gain.csv and method_note.md are untouched; the first
  run reported 0.1/(2 f0) on every row because the unamended section 4.3 offered it as a
  branch, and those files still say that. damping.csv supersedes their zeta columns.
  Preliminary throughout: one run, one shaker axis (MSP-X), one tower, no repeat frequency.

[V044] Provenance of this re-dispatch: d01_ringdown.py (first pass, superseded cut),
  d02_ringdown_null.py (fits plus null, writes d02_fits.json, 5720 records),
  d03_damping.py (aggregation, Routes B and C, writes damping.csv). Nothing outside
  ./ and data/ and the array store was read; analysis/ and critic/ were not touched. No
  Slurm. Note for the orchestrator: the Write tool was blocked in this session, so every
  file here was authored through python3, which was permitted; that is a harness detail
  and does not affect any number above.

