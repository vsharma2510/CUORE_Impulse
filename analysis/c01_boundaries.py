import numpy as np, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *
st=np.genfromtxt(f'{ROOT}/data/steps.csv',delimiter=',',names=True)
x=np.asarray(load('excitation','aux',1111),float)
fs=1000; dec=5
tb=[];unc=[]
for k in range(1,71):
    tn=st['t_start_s_run'][k]-OFFSET-5.986
    f1,f2=st['f_drive_hz_measured'][k-1],st['f_drive_hz_measured'][k]
    a=int((tn-40)*fs); b=int((tn+40)*fs)
    seg=x[a:b].reshape(-1,dec).mean(1); t=(a+np.arange(0,b-a,dec)+(dec-1)/2)/fs
    seg=seg-seg.mean()
    cand=tn+np.arange(-14,14,0.02); sse=[]
    for c in cand:
        L=t<c; R=~L; s=0
        for m,f in ((L,f1),(R,f2)):
            A=np.c_[np.cos(2*np.pi*f*t[m]),np.sin(2*np.pi*f*t[m]),np.ones(m.sum())]
            r=seg[m]-A@np.linalg.lstsq(A,seg[m],rcond=None)[0]; s+=r@r
        sse.append(s)
    sse=np.array(sse); i=int(np.argmin(sse)); i=min(max(i,1),len(cand)-2)
    p=np.polyfit(cand[i-1:i+2]-cand[i],sse[i-1:i+2],2); tb.append(cand[i]-p[1]/(2*p[0]))
tb=np.array(tb); np.save(f'{SCR}/tb_meas.npy',tb)
nom=st['t_start_s_run'][1:71]-OFFSET
d=tb-nom
print('meas - steps.csv t_start: median',np.median(d),'robust sigma',1.4826*np.median(abs(d-np.median(d))))
sp=np.diff(tb); print('spacing median',np.median(sp),'rsig',1.4826*np.median(abs(sp-np.median(sp))))
print('edge-hits',(abs(tb-(nom-5.986))>13.5).sum())
