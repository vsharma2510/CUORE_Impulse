"""Tests for the causality estimator and boundary finder (synthetic data with known truth)."""
import numpy as np
fs=1000; W=20.0
def design(t,freqs):
    cols=[np.ones_like(t),(t-t.mean())/W]
    for f in freqs: cols+=[np.cos(2*np.pi*f*t),np.sin(2*np.pi*f*t)]
    return np.stack(cols,1)
def amps(x,freqs,good=None):
    t=np.arange(len(x))/fs; g=np.ones(len(x),bool) if good is None else good
    c=np.linalg.lstsq(design(t[g],freqs),x[g],rcond=None)[0]
    return np.array([np.hypot(c[2+2*j],c[3+2*j]) for j in range(len(freqs))])
def make(f_old,f_new,tb,pre_leak_start=None,n=200*fs,seed=0):
    rng=np.random.default_rng(seed); t=np.arange(n)/fs
    x=np.where(t<tb,np.cos(2*np.pi*f_old*t+0.3),np.cos(2*np.pi*f_new*t+1.1))+0.01*rng.standard_normal(n)
    if pre_leak_start is not None:
        m=(t>=pre_leak_start)&(t<tb); x[m]+=0.5*np.cos(2*np.pi*f_new*t[m])
    return t,x
def test_causal_data_gives_zero_ratio():
    t,x=make(5.0,5.1,100.0)
    pre=amps(x[int(78.5*fs):int(98.5*fs)],[5.1,5.0])[0]; post=amps(x[int(101.5*fs):int(121.5*fs)],[5.1,5.0])[0]
    assert pre/post<0.02
def test_acausal_injection_detected():
    t,x=make(5.0,5.1,100.0,pre_leak_start=70.0)   # new tone at 0.5 amp before the switch
    pre=amps(x[int(78.5*fs):int(98.5*fs)],[5.1,5.0])[0]; post=amps(x[int(101.5*fs):int(121.5*fs)],[5.1,5.0])[0]
    assert 0.4<pre/post<0.6 and pre/post>0.2
def test_leakage_of_old_tone_small_with_joint_fit_but_large_without():
    t=np.arange(int(W*fs))/fs; x=np.cos(2*np.pi*5.0*t+0.7)
    assert amps(x,[5.1,5.0])[0]<1e-6          # Df*W=2 integer: orthogonal
    assert amps(x[:int(13.3*fs)],[5.1])[0]>0.05 # a short single-tone window leaks badly
def test_pulser_mask_keeps_leak_small():
    t=np.arange(int(W*fs))/fs; x=np.cos(2*np.pi*5.0*t+0.7)
    g=np.ones(len(t),bool)
    for p in (5.5,15.5): g[int((p-.1)*fs):int((p+1.0)*fs)+1]=False
    assert amps(x,[5.1,5.0],g)[0]<0.05
def test_boundary_finder_recovers_known_time_and_offset():
    # offset-3990 convention: run coordinate -> array coordinate
    from common import run_to_idx
    assert run_to_idx(4015.0)==25000
    t,x=make(5.0,5.1,100.37,n=200*fs)
    cand=100.37+np.arange(-3,3,0.02); s=[]
    for c in cand:
        L=t<c; r=0
        for m,f in ((L,5.0),(~L,5.1)):
            A=np.c_[np.cos(2*np.pi*f*t[m]),np.sin(2*np.pi*f*t[m]),np.ones(m.sum())]
            res=x[m]-A@np.linalg.lstsq(A,x[m],rcond=None)[0]; r+=res@res
        s.append(r)
    assert abs(cand[int(np.argmin(s))]-100.37)<0.05
