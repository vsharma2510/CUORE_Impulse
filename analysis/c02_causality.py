import numpy as np, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *
st=np.genfromtxt(f'{ROOT}/data/steps.csv',delimiter=',',names=True)
tb=np.load(f'{SCR}/tb_meas.npy'); fm=st['f_drive_hz_measured']
chs=[('bolo',c) for c in BOLO]+[('aux',c) for c in AUX]
tp=pulser_in_window(); W=20.0; fs=1000
def design(t,freqs):
    cols=[np.ones_like(t),(t-t.mean())/W]
    for f in freqs: cols+= [np.cos(2*np.pi*f*t),np.sin(2*np.pi*f*t)]
    return np.stack(cols,1)
def amps(x,t0,freqs,good):
    """joint LS in window [t0,t0+W) for tones at freqs (+const+linear), pulser samples masked.
    time-domain linear LS (not per-step lock-in over a whole dwell): short window, joint model, explicit leakage terms."""
    i0=int(round(t0*fs)); n=int(W*fs)
    xx=x[i0:i0+n]; g=good[i0:i0+n]; t=(i0+np.arange(n))/fs
    A=design(t[g],freqs); c=np.linalg.lstsq(A,xx[g]-0,rcond=None)[0]
    return np.hypot(c[2::2],c[3::2])[:len(freqs)] if False else np.array([np.hypot(c[2+2*j],c[3+2*j]) for j in range(len(freqs))])
def goodmask(a0,n):
    g=np.ones(n,bool)
    for p in tp[(tp>a0/fs-2)&(tp<(a0+n)/fs+2)]:
        a=int(round((p-0.1)*fs))-a0; b=int(round((p+1.0)*fs))-a0+1
        g[max(a,0):max(min(b,n),0)]=False
    return g
GUARDS=[0.2,0.5,1.5]
R={}  # arrays [boundary, channel, guard]
names=['pre_new','post_new','pre_old','null_far_new','null_mirror','post_old']
out={n:np.full((70,78,3),np.nan) for n in names}
leak=np.zeros((70,3)); leak_mirror=np.zeros((70,3))
PRE=170.0; POST=40.0
prec=np.zeros((78,70,7000),np.float32); tax=np.zeros((70,7000)); 
for k in range(1,71):
    f_old,f_new=fm[k-1],fm[k]; f_mir=f_old-(f_new-f_old)
    a0=int(round((tb[k-1]-PRE)*fs)); n=int((PRE+POST)*fs); g=goodmask(a0,n)
    # synthetic leakage: unit tone at f_old through identical window/mask/joint fit
    for gi,gd in enumerate(GUARDS):
        t0=tb[k-1]-gd-W
        i0=int(round(t0*fs)); gg=goodmask(i0,int(W*fs)); t=(i0+np.arange(int(W*fs)))/fs
        ls=[];lm=[]
        for ph in np.linspace(0,2*np.pi,8,endpoint=False):
            xs=np.cos(2*np.pi*f_old*t+ph)
            A=design(t[gg],[f_old,f_new,f_mir]); c=np.linalg.lstsq(A,xs[gg],rcond=None)[0]
            ls.append(np.hypot(c[4],c[5])); lm.append(np.hypot(c[6],c[7]))
        leak[k-1,gi]=max(ls); leak_mirror[k-1,gi]=max(lm)
    for ci,(kind,c) in enumerate(chs):
        x=np.asarray(load('excitation',kind,c)[a0:a0+n],np.float64)
        x=x-np.median(x)
        for gi,gd in enumerate(GUARDS):
            tr=tb[k-1]; r=lambda t0,fr: amps(np.pad(x,0),t0-a0/fs,fr,g)
            xa=x
            def A(t0,fr):
                i0=int(round((t0)*fs))-a0
                return amps(xa,i0/fs,fr,g)  # window start relative; times absolute offset below
            # amps uses absolute time = index/fs; shift consistent because masks are index-based
            out['pre_new'][k-1,ci,gi],out['pre_old'][k-1,ci,gi]=A(tr-gd-W,[f_new,f_old])[0],A(tr-gd-W,[f_new,f_old])[1]
            out['post_new'][k-1,ci,gi],out['post_old'][k-1,ci,gi]=A(tr+gd,[f_new,f_old])
            out['null_far_new'][k-1,ci,gi]=A(tr-130-W,[f_new,f_old])[0]
            out['null_mirror'][k-1,ci,gi]=A(tr-gd-W,[f_mir,f_old])[0]
        # store decimated segment, t=0 at measured boundary
        s=int(round((tb[k-1]-30)*fs))-a0
        prec[ci,k-1]=x[s:s+70000].reshape(7000,10).mean(1)
    tax[k-1]=((a0+int(round((tb[k-1]-30)*fs))-a0)+np.arange(7000)*10+4.5)/fs-tb[k-1]
    print(k,flush=True)
np.savez_compressed(f'{ROOT}/analysis/ringdown_precausal.npz',
  channel=np.array([c for _,c in chs]),kind=np.array([kk for kk,_ in chs]),step_boundary_index=np.arange(1,71),
  f_old_hz=fm[:70],f_new_hz=fm[1:71],boundary_t_array_s=tb,boundary_t_run_s=tb+OFFSET,
  t_s=tax,segment_mV=prec,
  notes=np.array(['segment_mV[ch,boundary,i]: 100 Hz block-mean (10 x 1 kHz) of median-removed raw data, NOT pulser-masked; t_s[boundary,i] time of block centre in s with t=0 at the MEASURED boundary; spans -30..+40 s. boundary_t_array_s is array coordinates (arrays start at run t=3990 s); boundary_t_run_s adds 3990.']))
np.savez(f'{SCR}/causality_out.npz',leak=leak,leak_mirror=leak_mirror,**out)
