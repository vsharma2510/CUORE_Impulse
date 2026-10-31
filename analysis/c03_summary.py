import numpy as np, sys
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *
d=np.load(f'{SCR}/causality_out.npz'); tb=np.load(f'{SCR}/tb_meas.npy')
st=np.genfromtxt(f'{ROOT}/data/steps.csv',delimiter=',',names=True); fm=st['f_drive_hz_measured']
chs=BOLO+AUX; G=[0.2,0.5,1.5]
lines=[]
def P(s): print(s); lines.append(s)
P(f"leakage coeff (synthetic unit f_old tone, same window/mask/joint fit) at f_new: max over boundaries & phases, per guard {G}: {d['leak'].max(0)}; median {np.median(d['leak'],0)}")
P(f"leakage coeff at mirror null freq: max {d['leak_mirror'].max(0)}")
rows=[]
from common import pulser_in_window
tp=pulser_in_window(); W=20.0; fs=1000; L1=[]
for k in range(1,71):
    i0=int(round((tb[k-1]-1.5-W)*fs)); t=(i0+np.arange(int(W*fs)))/fs; g=np.ones(len(t),bool)
    for p in tp[(tp>t[0]-2)&(tp<t[-1]+2)]: g[max(int(round((p-.1)*fs))-i0,0):max(int(round((p+1.0)*fs))-i0+1,0)]=False
    for ph in np.linspace(0,2*np.pi,8,endpoint=False):
        x=np.cos(2*np.pi*fm[k-1]*t+ph); tt=t[g]; A=np.c_[np.ones(g.sum()),np.cos(2*np.pi*fm[k]*tt),np.sin(2*np.pi*fm[k]*tt)]
        c=np.linalg.lstsq(A,x[g],rcond=None)[0]; L1.append(np.hypot(c[1],c[2]))
P(f"SINGLE-TONE (f_new only, no joint f_old term) leakage of unit f_old tone, 20 s window, pulser-masked: median {np.median(L1):.4f} max {np.max(L1):.4f}")

for gi,g in enumerate(G):
    pn,po,nf,nm,pol=[d[k][:,:,gi] for k in ('pre_new','post_new','null_far_new','null_mirror','pre_old')]
    # trusted post response: post amplitude > 5 x the null-far floor of the same boundary/channel
    floor=np.median(nf,0)[None,:]   # per-channel floor = median over boundaries (not this cell's own null value)
    ok=po>5*floor
    r=pn/po; rf=nf/po; rm=nm/po; lk=d['leak'][:,gi][:,None]*pol/po
    P(f"guard {g}s: n(boundary,channel) with post>5*per-channel median null_far = {ok.sum()} of {ok.size}")
    for nm_,a in (('pre/post',r),('null_far/post',rf),('null_mirror/post',rm),('leak_term/post',lk)):
        v=a[ok]; P(f"   {nm_:18s} median {np.median(v):.4f}  p90 {np.percentile(v,90):.4f}  p99 {np.percentile(v,99):.4f}  max {v.max():.4f}  frac>0.2 {(v>0.2).mean():.4f}")
    # per-boundary: median ratio over trusted channels
    mb=np.array([np.median(r[k][ok[k]]) if ok[k].sum()>=3 else np.nan for k in range(70)])
    P(f"   per-boundary median pre/post (>=3 trusted ch): n={np.isfinite(mb).sum()} max {np.nanmax(mb):.4f} median {np.nanmedian(mb):.4f}; boundaries with median>0.2: {int((mb>0.2).sum())}")
    # the strongest channels only: post>50*null_far
    ok2=po>50*floor; v=r[ok2]; P(f"   strong (post>50*null): n={ok2.sum()} median pre/post {np.median(v):.4f} p99 {np.percentile(v,99):.4f} max {v.max():.4f} frac>0.2 {(v>0.2).mean():.4f}")
    if gi==2: prim=(r,ok,rf,rm,lk)
r,ok,rf,rm,lk=prim
with open(f'{ROOT}/analysis/causality.csv','w') as f:
    f.write('# PARTIAL AND PRELIMINARY: one run, one shaker axis, one tower. primary guard 1.5 s; windows 20 s; boundaries measured (see causality_note.md). amplitudes mV at ADC input.\n')
    f.write('boundary_index,t_boundary_run_s,f_old_hz,f_new_hz,channel,pre_amp_new_mV,post_amp_new_mV,pre_over_post,null_far_over_post,null_mirror_over_post,leak_term_over_post,post_trusted,pre_over_post_g0p2,pre_over_post_g0p5,fail_gt_0p2\n')
    for k in range(70):
        for ci,c in enumerate(chs):
            f.write(f"{k+1},{tb[k]+OFFSET:.3f},{fm[k]:.5f},{fm[k+1]:.5f},{c},{d['pre_new'][k,ci,2]:.6g},{d['post_new'][k,ci,2]:.6g},{r[k,ci]:.5g},{rf[k,ci]:.5g},{rm[k,ci]:.5g},{lk[k,ci]:.5g},{int(ok[k,ci])},{d['pre_new'][k,ci,0]/d['post_new'][k,ci,0]:.5g},{d['pre_new'][k,ci,1]/d['post_new'][k,ci,1]:.5g},{int(ok[k,ci] and r[k,ci]>0.2)}\n")
open(f'{SCR}/summary.txt','w').write('\n'.join(lines))
