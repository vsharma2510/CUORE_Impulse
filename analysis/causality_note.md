# Causality test (SPEC 4.5) - PARTIAL AND PRELIMINARY (one run, one shaker axis, one tower)

**Boundaries.** I measured all 70 from ch1111 by scanning a two-segment model (sinusoid at f_old then f_new, free amplitude/phase/offset) over a 0.02 s grid. Result: t_boundary = steps.csv t_start - 6.356 s (robust sigma 0.147 s); spacing 250.0011 s (sigma 0.017 s). The orchestrator's frequency-crossing value is 0.37 s later (-5.986 s); I could not resolve that systematic, so I take +-0.4 s as the boundary uncertainty and use a 1.5 s guard (0.2 and 0.5 s also in causality.csv). A pre-response confined within 0.4 s of the boundary would be timing, not acausality; none was isolated at that scale. The 3990 s offset is applied (tested).

**Estimator** (differs from the verifier's per-step lock-in): a 20 s time-domain joint least-squares fit of const, linear, and cos/sin at BOTH f_new and f_old, pulser samples masked (-0.1..+1.0 s). Pre window ends at boundary minus guard; post window starts at boundary plus guard. Ratio = pre amp(f_new)/post amp(f_new). Fail threshold 0.2.

**Leakage.** delta f x W = 2, so the old tone is exactly orthogonal to the new one: a synthetic f_old tone leaks <=1e-11 into f_new in the joint fit (small by construction). Without the joint term, single-tone leakage is 0.12 (max 0.128). That figure is not subtracted; it is why f_old is in the model. A non-stationary real old tone can still leak, and only the nulls measure that.

**Nulls.** (a) f_new amplitude in a window 130-150 s before the boundary; (b) mirror frequency f_old-(f_new-f_old) in the pre window. Trusted cells: post > 5x per-channel median null_far (2528 of 5460).

**Results** (guard 1.5 s, trusted cells): pre/post median 0.049, p90 0.215, frac>0.2 = 11.5%. Nulls: median 0.052/0.052, frac>0.2 = 11.3%/10.4%. Pre/post is indistinguishable from the estimator floor, so a per-cell 0.2 threshold is noise-limited here. On strong channels (post > 50x floor, n=660): median 0.010, p99 0.18, max 0.33, 0.9% above 0.2. Per boundary (median over trusted channels), 68 of 70 are under 0.2. Boundaries 16 and 17 (f_new 4.10, 4.20 Hz) exceed it (max 0.78) but their null fails the same way; 4.20 Hz is 0.017 Hz from the 4.18329 Hz pulse-tube line, a stationary signal present before and after.

**Conclusion (not settled).** No coherent f_new response before the switch was found above the estimator's own floor; but the test cannot demonstrate a ratio below 0.2 per cell, only per boundary and on strong channels, and boundaries 16-17 are confounded by the PT line. Unresolved: the 0.37 s boundary disagreement; no linearity or repeat check.

**Files.** ringdown_precausal.npz: segment_mV[ch,boundary,i], 100 Hz block means (not pulser-masked), t_s[boundary,i] from -30 to +40 s with t=0 at the measured boundary. responses.npz untouched. Tests: test_causality.py (synthetic causal, injected acausal at 0.5 -> detected, leakage, mask, boundary recovery, offset).
