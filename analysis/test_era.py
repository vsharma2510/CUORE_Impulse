import numpy as np, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from era import *
def synth(noise=0.02,seed=0):
    rng=np.random.default_rng(seed); dt=0.04; L=155; t=np.arange(L)*dt
    modes=[(3.43,0.02),(4.9,0.01),(8.5,0.03)]; no=20; ne=30
    Y=np.zeros((L,no,ne))
    for f,z in modes:
        s=-z*2*np.pi*f+1j*2*np.pi*f*np.sqrt(1-z*z)
        ph=rng.normal(size=(no,1))+1j*rng.normal(size=(no,1)); ex=rng.normal(size=(1,ne))+1j*rng.normal(size=(1,ne))
        Y+=np.real(np.exp(s*t)[:,None,None]*ph[None]*ex[None])
    return Y+noise*rng.normal(size=Y.shape),modes
def test_era_recovers_known_modes():
    Y,modes=synth(); G0,G1,no=build_hankel_products(Y,40,100)
    orders=list(range(2,21,2)); P=era_poles(G0,G1,no,0.04,orders); fl=stabilise(P,orders)
    p=P[8]; 
    for f,z in modes:
        i=np.argmin(abs(p['f']-f)); assert abs(p['f'][i]-f)<0.03 and abs(p['z'][i]-z)<0.4*z,(f,z,p['f'][i],p['z'][i])
    assert fl[8].sum()>=3
def test_noise_only_has_few_stable_poles():
    rng=np.random.default_rng(1); Y=rng.normal(size=(155,20,30)); G0,G1,no=build_hankel_products(Y,40,100)
    orders=list(range(2,21,2)); P=era_poles(G0,G1,no,0.04,orders); fl=stabilise(P,orders)
    assert sum(v.sum() for v in fl.values())<=0.2*sum(len(v) for v in fl.values())+3
