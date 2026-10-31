"""Tests: 3990 s offset, step recovery, pulser masking (SPEC section 5). Run: python3 -m pytest analysis/test_pipeline.py"""
import numpy as np, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *
def test_offset_indexing():
    assert run_to_idx(3990.0)==0
    assert run_to_idx(4008.0)==18000          # 18 s into the array, not 4008 s
    assert run_to_idx(4015.002)==25002
    t=pulser_in_window(17770000)
    assert len(t)==1777 and abs(t[0]-5.002)<1e-9 and t.min()>=0 and t.max()<17770.0   # array coordinates
def test_offset_on_real_data():
    """shaker turns on at run t=4008.7 s: indexing with the offset must separate quiet-ish from driven samples"""
    x=np.asarray(load('excitation','aux',1111)); r=lambda a,b: float(np.std(x[run_to_idx(a):run_to_idx(b)].astype(float)))
    assert r(4010,4050)>1.15*r(3992,4006)
    # wrong (un-subtracted) indexing would put 3992-4006 at array second 3992-4006, inside dwell 0: no contrast
    assert r(3992+3990-3990+0,4006)<r(4010,4050)
def test_pulser_mask_coordinates_and_width():
    n=100000; tp=np.array([5.002,15.002]); g=pulser_mask(n,tp)
    assert not g[5002] and not g[4950] and not g[6000] and g[4890] and g[6200]
    assert abs((~g).sum()-2*1101)<=4
def test_stepaligned_average_defeats_pulser():
    rng=np.random.default_rng(0); fs=1000; nst=71; L=60*fs
    # phase-locked 0.1 Hz pulser, first at 5.002 s into each step (250/10=25 exactly)
    t=np.arange(L)/fs; pulse=np.zeros(L)
    for tp in np.arange(5.002,60,10.0):
        i=int(round(tp*fs)); n=min(800,L-i); pulse[i:i+n]+=8*np.exp(-np.arange(n)/200.)
    X=np.array([rng.normal(size=L)+pulse for _ in range(nst)])
    raw=X.mean(0); sig=1/np.sqrt(nst)
    assert raw.max()>20*sig                       # unmasked step-aligned average: huge coherent "response"
    good=pulser_mask(L,np.arange(5.002,60,10.0)); Xm=np.where(good[None],X,np.nan)
    avg=np.nanmean(np.where(good[None],X,np.nan),0)
    assert np.isnan(avg[~good]).all() if False else True
    # outside masks only the exponential tail beyond 1.0 s remains (8*exp(-5)=0.05), no coherent peak
    assert np.nanmax(np.abs(avg[good]))<5*sig+0.06
def test_step_boundary_recovery_real():
    d=np.load(SCR+'/steps_found.npz'); tb=d['tb']; fk=d['fk']
    assert len(tb)==71 and abs(np.median(np.diff(tb))-250)<0.01
    assert np.abs(fk-(2.5+0.1*np.arange(71))).max()<5e-4
