#!/usr/bin/env python3
"""TEST pulser masking. On quiet3 the shaker is off, so any coherent amplitude the
lock-in reports at a drive frequency is contamination. Every drive frequency is a
multiple of 0.1 Hz, so the pulser comb sits exactly on it and adds COHERENTLY.
Compare the masked estimator against the identical estimator with no mask."""
import numpy as np
ARR="<SCRATCH>/CUORE_ImpulsePilot_data"
DATA="<HOME>/CUORE_ImpulsePilot/data"
FS=1000.0; T0=48025.0
pt=np.load(DATA+"/pulser_times.npy")-T0
NS=5600; MPRE,MPOST=0.2,4.2
def design(f,t):
    A=np.empty((t.size,4)); w=2*np.pi*f
    A[:,0]=np.cos(w*t); A[:,1]=np.sin(w*t); A[:,2]=1.0; A[:,3]=t-t.mean(); return A
def amps(x,f,starts,n):
    out=[]
    for s in starts:
        k=int(round(s*FS)); t=s+np.arange(n)/FS
        c=np.linalg.lstsq(design(f,t),x[k:k+n],rcond=None)[0]
        out.append(c[0]-1j*c[1])
    return np.array(out)
masked=[p+MPOST for p in pt if 2<=p+MPOST and p+MPOST+NS/FS<=773]
unmask=[2.0+10.0*i for i in range(77) if 2.0+10.0*i+10.0<=773]   # same cadence, no mask
print("%-8s %12s %12s %10s"%("freq","masked|A|","unmasked|A|","ratio"))
tot=[]
for ch in (937,945,963,975,988):
    x=np.asarray(np.load(ARR+"/quiet3/bolo/ch%04d.npy"%ch),dtype=np.float64)
    for f in (3.4,4.9,8.1):
        am=np.abs(np.mean(amps(x,f,masked,NS)))
        au=np.abs(np.mean(amps(x,f,unmask,10000)))
        tot.append(au/am)
        print("ch%04d %.1fHz %12.5f %12.5f %10.2f"%(ch,f,am,au,au/am))
print("median unmasked/masked coherent amplitude ratio = %.2f over %d cases"%(np.median(tot),len(tot)))
