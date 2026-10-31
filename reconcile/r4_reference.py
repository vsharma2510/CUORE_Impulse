#!/usr/bin/env python3
"""R4: is the 5.4->5.5 Hz jump in |H| instrumental (in ch1111) or physical?

The critic showed the jump cannot be cancelled by a ratio to ch1111 because it IS in ch1111. A ratio
to an INDEPENDENT drive monitor can cancel it: ch1112 is the shaker accelerometer, a different sensor
on a different DAQ range. If |H| referenced to ch1112 is smooth across the boundary while |H|
referenced to ch1111 steps, the step is a ch1111 scale change. If both step, it is physical.

Uses only the analyst's own per-step tone amplitudes, so no re-extraction is needed.
"""
import numpy as np

A = np.load("analysis/responses.npz", allow_pickle=True)
f = A["f_drive_hz"]
ch, kind = A["channel"], A["kind"]
amp = A["response_tone_rms_mV"]                      # per channel, per step, mV at the ADC
force = A["force_tone_rms_mV"][0]                    # ch1111 tone RMS, identical on every row
bolo = amp[kind == "bolo"]
i1112 = int(np.where(ch == 1112)[0][0])
a1112 = amp[i1112]

med = np.median(bolo, 0)
H_1111 = med / force
H_1112 = med / a1112


def jump(x, i):
    return x[i + 1] / x[i]


for fb in (5.4, 7.4):
    i = int(np.argmin(np.abs(f - fb)))
    print(f"\n=== boundary {f[i]:.2f} -> {f[i+1]:.2f} Hz  (steps {i} -> {i+1})")
    print(f"  ch1111 force tone        {force[i]:9.2f} -> {force[i+1]:9.2f} mV   x{jump(force,i):.3f}")
    print(f"  ch1112 shaker accel      {a1112[i]:9.2f} -> {a1112[i+1]:9.2f} mV   x{jump(a1112,i):.3f}")
    print(f"  bolometer median tone    {med[i]:9.4f} -> {med[i+1]:9.4f} mV   x{jump(med,i):.3f}")
    print(f"  |H| ref ch1111                                            x{jump(H_1111,i):.3f}")
    print(f"  |H| ref ch1112  (independent)                             x{jump(H_1112,i):.3f}")

# how unusual is each jump against the ordinary step-to-step scatter of the same quantity?
for name, x in (("force ch1111", force), ("accel ch1112", a1112),
                ("|H| ref 1111", H_1111), ("|H| ref 1112", H_1112)):
    r = np.log(x[1:] / x[:-1])
    s = 1.4826 * np.median(np.abs(r - np.median(r)))          # robust sigma of log step ratios
    i54, i74 = int(np.argmin(np.abs(f - 5.4))), int(np.argmin(np.abs(f - 7.4)))
    print(f"\n{name:13s} robust sigma of log step ratio {s:.3f}"
          f"   5.45 boundary {r[i54]/s:+6.1f} sigma   7.45 boundary {r[i74]/s:+6.1f} sigma")

print("\nsmoothness of |H| across 5.3-5.7 Hz, each curve normalised at 5.3 Hz")
s = slice(int(np.argmin(np.abs(f - 5.2))), int(np.argmin(np.abs(f - 5.8))) + 1)
print("  f      ", np.round(f[s], 2))
print("  ref1111", np.round(H_1111[s] / H_1111[s][1], 3))
print("  ref1112", np.round(H_1112[s] / H_1112[s][1], 3))
