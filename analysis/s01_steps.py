import numpy as np, json, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *
from scipy.signal import butter,sosfiltfilt,spectrogram
x=np.asarray(load('excitation','aux',1111)).astype(float)
sos=butter(4,[2,11],btype='band',fs=1000,output='sos')
y=sosfiltfilt(sos,x)[::10]          # 100 Hz, zero-phase band-passed drive channel
# 1) coarse threshold on spectrogram peak frequency jump (8 s windows)
f,t,S=spectrogram(y,fs=100,nperseg=800,noverlap=700,nfft=8192)
m=(f>2.3)&(f<9.8); ff=f[m]; fp=ff[S[m].argmax(0)]; T=t+OFFSET    # run coords (window centre)
cand=[]
for k in range(20,len(fp)-3):
    ref=np.median(fp[k-12:k-4])
    if all(abs(fp[k+j]-ref)>0.04 for j in range(3)) and (not cand or T[k]-cand[-1]>60): cand.append(T[k])
cand=np.array(cand); assert len(cand)==71, len(cand)
# 2) per-dwell frequency by DFT peak in the interior, then boundary refinement by 2-tone residual scan
tt=np.arange(len(y))/100.0+OFFSET       # run coordinates of each decimated sample
def tone_fit(seg_t,seg_y,f):
    A=np.c_[np.cos(2*np.pi*f*seg_t),np.sin(2*np.pi*f*seg_t)]
    c,res,_,_=np.linalg.lstsq(A,seg_y,rcond=None); r=seg_y-A@c
    return c,(r**2).sum()
fk=[]
for k in range(71):
    a=cand[k]+10; b=(cand[k+1]-15) if k<70 else cand[k]+200
    i0,i1=int((a-OFFSET)*100),int((b-OFFSET)*100)
    ts,ys=tt[i0:i1],y[i0:i1]
    g=np.arange(fp[int((cand[k]+20-OFFSET))]-0.04,fp[int((cand[k]+20-OFFSET))]+0.04,0.0005)
    P=[tone_fit(ts,ys,fg)[1] for fg in g]; j=int(np.argmin(P))
    g2=np.arange(g[j]-0.001,g[j]+0.001,0.00002)
    P2=[tone_fit(ts,ys,fg)[1] for fg in g2]; fk.append(g2[int(np.argmin(P2))])
fk=np.array(fk)
tb=[]
for k in range(71):
    # boundary k = start of step k; search the 2-tone model around (cand[k]-5.5)
    f1=fk[k-1] if k>0 else None; f2=fk[k]
    c0=cand[k]-5.5; W=25.0 if k>0 else 12.0
    best=None
    for tb_ in np.arange(c0-8,c0+8,0.02):
        i=int(round((tb_-OFFSET)*100))
        iw=int(W*100)
        r=0
        if f1 is not None:
            r+=tone_fit(tt[i-iw:i],y[i-iw:i],f1)[1]
        else:
            r+=((y[i-iw:i]-y[i-iw:i].mean())**2).sum()
        r+=tone_fit(tt[i:i+iw],y[i:i+iw],f2)[1]
        if best is None or r<best[0]: best=(r,tb_)
    tb.append(best[1])
tb=np.array(tb)
kk=np.arange(71); r=tb-250*kk; inl=np.abs(r-np.median(r))<0.4
co=np.polyfit(kk[inl],tb[inl],1)
print('grid fit: period',co[0],'t0',co[1],'n outliers replaced by grid',int((~inl).sum()),np.where(~inl)[0])
tb_scan=tb.copy(); tb=np.where(inl,tb,np.polyval(co,kk))
np.savez(SCR+'/steps_found.npz',tb=tb,tb_scan=tb_scan,fk=fk,cand=cand)
sc=np.genfromtxt(f'{ROOT}/data/steps.csv',delimiter=',',names=True)
print('first tb',tb[:4],'diffs',np.unique(np.round(np.diff(tb),1),return_counts=True))
print('csv t0 - tb: mean',np.mean(sc['t_start_s_run']-tb),'min',np.min(sc['t_start_s_run']-tb),'max',np.max(sc['t_start_s_run']-tb))
print('f found - f csv: ',np.round(fk-sc['f_drive_hz_measured'],3)[:20], 'max abs',np.abs(fk-sc['f_drive_hz_measured']).max())
print(np.round(fk[:12],4))
