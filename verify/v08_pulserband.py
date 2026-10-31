#!/usr/bin/env python3
"""How much pulser is actually IN BAND?

For a periodic train x(t) = sum_n p(t - nT) with T = 10 s, the Fourier series
coefficient at f_k = k/T is c_k = P(f_k)/T, so the sinusoid AMPLITUDE at f_k is
2|P(f_k)|/T. P is the transform of the measured single-pulse shape. The pulse is a
slow thermal feature (~1.3 s rise), so its content at 2.5-9.5 Hz may be tiny --
measure it, do not assume it.
"""
import json
import numpy as np
OUT="<HOME>/CUORE_ImpulsePilot/verify"
v1=json.load(open(OUT+"/v01_steps.json"))
m=np.array(v1["pulse_mean_mV"]); tau=np.array(v1["pulse_tau_s"])
FS=1000.0; T=10.0
sel=(tau>=-0.5)&(tau<=8.0)            # the whole pulse, baseline already removed
p=m[sel]; t=tau[sel]
d=np.load(OUT+"/responses.npz"); f=d["f_drive_hz"]
NOISE=d["noise_rms_mV_quiet3"]; kind=d["channel_kind"]
bolo=np.where(kind=="bolo")[0]
print("[V021] pulser in-band amplitude from the MEASURED pulse shape (ch0937, 76 pulses):")
print("%7s %14s %14s %12s"%("f (Hz)","pulser amp mV","pulser mV rms","/noise rms"))
amps=[]
for fk in (2.5,3.4,4.9,6.2,8.1,9.5):
    P=np.trapezoid(p*np.exp(-2j*np.pi*fk*t),t)
    a=2.0*abs(P)/T; ar=a/np.sqrt(2.0)
    k=int(np.argmin(np.abs(f-fk))); nz=float(np.median(NOISE[bolo,k]))
    amps.append(ar/nz)
    print("%7.2f %14.6f %14.6f %12.3f"%(fk,a,ar,ar/nz))
print("[V021] baseline check: same integral at 0.1 Hz (the comb fundamental) = %.4f mV amplitude"
      %(2.0*abs(np.trapezoid(p*np.exp(-2j*np.pi*0.1*t),t))/T))
print("[V021] pulse peak is %.2f mV but its 2.5-9.5 Hz content is %.1e-%.1e of the noise rms:"
      " the heater pulse is a SLOW thermal feature (1.3 s rise) with almost no power above ~1 Hz."
      %(float(np.max(np.abs(p))),min(amps),max(amps)))
