import numpy as np, pickle, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *; from era import *
res=pickle.load(open(SCR+'/chan_results.pkl','rb')); D={(k,c):v for k,c,v in res}
ERA_AUX=[c for c in AUX if c>=1101 and c not in (1111,1112)]
outs=[('bolo',c) for c in BOLO]+[('aux',c) for c in ERA_AUX]
dt=1/25.
def build(segs):
    cols=[]
    for (a,b) in segs:
        Yk=np.stack([D[o]['RD'][:,a:b]/np.median(D[o]['RDse']) for o in outs],axis=0)   # (no, nstep, L)
        cols.append(Yk)
    Y=np.concatenate(cols,axis=1)           # (no, nexp, L)
    return np.transpose(Y,(2,0,1)).astype(np.float64)
def run(segs,p=40,orders=range(2,61,2),tag=''):
    Y=build(segs); assert np.isfinite(Y).all()
    q=Y.shape[0]-p-1
    G0,G1,no=build_hankel_products(Y,p,q)
    orders=list(orders); P=era_poles(G0,G1,no,dt,orders); fl=stabilise(P,orders)
    return P,fl,orders,Y.shape
if __name__=='__main__':
    P,fl,orders,shp=run([(0,135),(193,328)])
    print(shp)
    allf=[];allz=[];alln=[]
    for n in orders[1:]:
        for f,z,s in zip(P[n]['f'],P[n]['z'],fl[n]):
            if s: allf.append(f);allz.append(z);alln.append(n)
    allf=np.array(allf);allz=np.array(allz)
    h,e=np.histogram(allf,bins=np.arange(2.5,9.6,0.05))
    for a,b in zip(e[:-1],h):
        if b>0: 
            m=(allf>=a)&(allf<a+0.05); print(f'{a:.2f} n={b} zeta med {np.median(allz[m])*100:.2f}% f med {np.median(allf[m]):.3f}')
