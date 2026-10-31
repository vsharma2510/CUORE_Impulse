"""Per-channel H1 transfer function (ref ch1111), quiet-noise estimator, and post-step ring-down segments."""
import numpy as np, sys, pickle
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *
from scipy.signal import butter,sosfiltfilt
from multiprocessing import Pool
st=np.load(SCR+'/steps_found.npz'); TB=st['tb']; FK=np.round(st['fk'],1)   # drive grid is exactly k*0.1 Hz (recovered 1.6e-4 Hz agreement)
FKfit=st['fk']
NS=17770000
TE=np.r_[TB[1:],min(TB[-1]+250.0,3990+NS/FS)]
SOS=butter(4,[1.5,11.0],btype='band',fs=FS,output='sos')
PULSE=pulser_in_window(NS)
GOOD=None; YREF=None
WLEN=20.0; GUARD=60.0; RD_LEN=40.0; RD_FS=25.0; SSFIT_START=100.0
F_PT=1.39443*np.arange(2,7)     # pulse-tube lines 2.789,4.183,5.577,6.972,8.366 Hz (measured in quiet3, fundamental 1.39443 Hz)
QUIET={'quiet1':0.0,'quiet2':1275.0,'quiet3':48025.0}
def init():
    global GOOD,YREF
    GOOD=pulser_mask(NS,PULSE)
    YREF=sosfiltfilt(SOS,np.asarray(load('excitation','aux',1111),dtype=np.float64))
def win_starts(tb,te):
    a=tb+GUARD; s=[]
    while a+WLEN<=te-1.0: s.append(a); a+=WLEN/2
    return np.array(s)
def dft_windows(y,good,starts_arr_s,f):
    """Hann*mask weighted DFT at exactly f (tone-rms-normalised: |X|=rms of a pure tone). returns complex array"""
    n=int(WLEN*FS); w0=np.hanning(n); t=np.arange(n)/FS; e=np.exp(-2j*np.pi*f*t)
    out=[]
    for s in starts_arr_s:
        i=int(round(s*FS)); w=w0*good[i:i+n]
        sw=w.sum()
        # phase referenced to absolute time so that ref and response share the same phase origin
        out.append((w*y[i:i+n]*e).sum()*np.sqrt(2)/sw*np.exp(-2j*np.pi*f*s))
    return np.array(out)
def design(tt,fdrive):
    cols=[np.cos(2*np.pi*fdrive*tt),np.sin(2*np.pi*fdrive*tt)]
    for fl in F_PT: cols+= [np.cos(2*np.pi*fl*tt),np.sin(2*np.pi*fl*tt)]
    return np.stack(cols,1)
def clean_dwell(y,k,tb,te):
    """joint LS of drive tone + 5 pulse-tube lines on [tb+GUARD,te-2] (pulser-masked); subtracts the PT lines from y[tb:te] IN PLACE; returns drive (cos,sin) coeffs"""
    a=int(round((tb+GUARD)*FS)); b=int(round((te-2)*FS)); idx=np.arange(a,b,4); idx=idx[GOOD[idx]]
    c=np.linalg.lstsq(design(idx/FS,FKfit[k]),y[idx],rcond=None)[0]
    a2=int(round(tb*FS)); b2=int(round(te*FS)); tt=np.arange(a2,b2)/FS
    D=design(tt,FKfit[k]); D[:,:2]=0
    y[a2:b2]-=D@c
    return c[:2]
def process(args):
    kind,ch=args
    y=sosfiltfilt(SOS,np.asarray(load('excitation',kind,ch),dtype=np.float64))
    yr=YREF.copy()
    nst=len(TB); H=np.zeros(nst,complex); Hse=np.zeros(nst); coh=np.zeros(nst); nwin=np.zeros(nst,int)
    nuse=np.zeros(nst,int); amp=np.zeros(nst); famp=np.zeros(nst)
    RD=np.full((nst,int(RD_LEN*RD_FS)),np.nan,np.float32); RDse=np.zeros(nst,np.float32)
    nrd=int(RD_LEN*RD_FS)
    for k in range(nst):
        tb=TB[k]-OFFSET; te=TE[k]-OFFSET; f=FK[k]
        st_=win_starts(tb,te); nwin[k]=len(st_)
        clean_dwell(yr,k,tb,te); c=clean_dwell(y,k,tb,te)
        Xf=dft_windows(yr,GOOD,st_,f); Xb=dft_windows(y,GOOD,st_,f)
        Sff=np.mean(abs(Xf)**2); Sbb=np.mean(abs(Xb)**2); Sfb=np.mean(np.conj(Xf)*Xb)
        H[k]=Sfb/Sff; g2=abs(Sfb)**2/(Sff*Sbb); coh[k]=g2
        neff=max(int((te-1-(tb+GUARD))//WLEN),1)       # non-overlapping-equivalent count (conservative)
        Hse[k]=abs(H[k])*np.sqrt(max(1-g2,0)/(2*neff*max(g2,1e-6)))
        amp[k]=np.sqrt(Sbb); famp[k]=np.sqrt(Sff)       # tone-rms (mV) of response / force at f
        i0=int(round((tb+GUARD)*FS)); i1=int(round((te-1)*FS)); nuse[k]=int(GOOD[i0:i1].sum())
        # ---- ring-down: remove the NEW steady-state tone (LS on late part of dwell, masked), keep residual
        a=int(round((tb+SSFIT_START)*FS)); b=int(round((te-2)*FS)); idx=np.arange(a,b)[GOOD[a:b]]
        j=np.arange(int(round(tb*FS)),int(round(tb*FS))+int(RD_LEN*FS),int(FS/RD_FS))
        tj=j/FS; r=y[j]-(c[0]*np.cos(2*np.pi*FKfit[k]*tj)+c[1]*np.sin(2*np.pi*FKfit[k]*tj))
        r=np.where(GOOD[j],r,np.nan); RD[k]=r[:nrd]
        jj=idx[::int(FS/RD_FS)]; rt=y[jj]-(c[0]*np.cos(2*np.pi*FKfit[k]*jj/FS)+c[1]*np.sin(2*np.pi*FKfit[k]*jj/FS))
        RDse[k]=np.std(rt[(jj/FS>tb+120)])
    # ---- quiet noise: same estimator (tone-rms-normalised hann DFT at each drive freq), all quiet windows
    nz=np.zeros(len(FK))
    acc=[[] for _ in FK]
    for w,t0 in QUIET.items():
        q=sosfiltfilt(SOS,np.asarray(load(w,kind,ch),dtype=np.float64)); n=len(q)
        tq=np.arange(n)/FS; Dq=np.stack([f(2*np.pi*fl*tq) for fl in F_PT for f in (np.cos,np.sin)],1)
        ii=np.arange(5000,n-5000,4); q-=Dq@np.linalg.lstsq(Dq[ii],q[ii],rcond=None)[0]
        pt=PULSE_RUN[(PULSE_RUN>=t0)&(PULSE_RUN<t0+n/FS)]-t0
        gq=pulser_mask(n,pt)
        ss=np.arange(0.0,n/FS-WLEN,WLEN/2)
        # skip the first/last 5 s (filter edges)
        ss=ss[(ss>=5)&(ss+WLEN<=n/FS-5)]
        for kf,f in enumerate(FK): acc[kf].append(np.abs(dft_windows(q,gq,ss,f))**2)
    for kf in range(len(FK)): nz[kf]=np.sqrt(np.mean(np.concatenate(acc[kf])))
    return (kind,ch,dict(H=H,Hse=Hse,coh=coh,nwin=nwin,nuse=nuse,amp=amp,famp=famp,noise=nz,RD=RD,RDse=RDse))
PULSE_RUN=np.load(f'{ROOT}/data/pulser_times.npy')
if __name__=='__main__':
    jobs=[('bolo',c) for c in BOLO]+[('aux',c) for c in AUX]
    if len(sys.argv)>1: jobs=jobs[:int(sys.argv[1])]
    with Pool(12,initializer=init) as p: res=p.map(process,jobs,chunksize=1)
    pickle.dump(res,open(SCR+'/chan_results.pkl','wb'))
    print('done',len(res))
