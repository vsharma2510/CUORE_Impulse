import numpy as np, pickle, sys, csv
sys.path.insert(0,'<HOME>/CUORE_ImpulsePilot/analysis')
from common import *; import s03_era as E
st=np.load(SCR+'/steps_found.npz'); TB=st['tb']; FK=np.round(st['fk'],1)
TE=np.r_[TB[1:],TB[-1]+250.0]; D=E.D
chans=[('bolo',c) for c in BOLO]+[('aux',c) for c in AUX]
log=[]
# ---------------- impulses.csv
x=np.asarray(load('excitation','aux',1111),dtype=np.float64)
with open('analysis/impulses.csv','w') as fh:
    w=csv.writer(fh); w.writerow('step_index,t_start_s,t_end_s,f_drive_hz,force_rms_mV,n_samples_used,method'.split(','))
    for k in range(71):
        a,b=run_to_idx(TB[k]),run_to_idx(TE[k])
        w.writerow([k,f'{TB[k]:.2f}',f'{TE[k]:.2f}',f'{FK[k]:.1f}',f'{x[a:b].std():.2f}',int(D[("aux",1111)]["nuse"][k]),'bandpass-1111 spectral-peak threshold + two-tone residual scan; run coords; n_samples_used = pulser-unmasked samples inside H1 windows (t0+60 s .. t1-1 s)'])
# ---------------- responses.npz
ids=np.array([c for _,c in chans]); kind=np.array([k for k,_ in chans])
g=lambda key: np.stack([D[c][key] for c in chans])
np.savez_compressed('analysis/responses.npz',channel=ids,kind=kind,f_drive_hz=FK,t_start_run_s=TB,t_end_run_s=TE,
  H=g('H'),H_se_abs=g('Hse'),coherence=g('coh'),n_windows=g('nwin'),n_samples_used=g('nuse'),response_tone_rms_mV=g('amp'),
  force_tone_rms_mV=g('famp'),quiet_noise_equiv_rms_mV=g('noise'),
  ringdown_t_s=np.arange(1000)/25.0,ringdown=g('RD'),ringdown_se=g('RDse'),
  notes=np.array(['H = S_fb/S_ff (ch1111 ref); H_se_abs = |H| sqrt((1-g2)/(2 n g2)), n=non-overlapping-equivalent windows; ringdown = band-passed (1.5-11 Hz) response minus fitted drive tone and 5 pulse-tube lines, 25 Hz samples starting at the step boundary, NaN where pulser-masked [tp-0.1,tp+1.0] s; ringdown_se = per-sample rms of the same residual in 120 s..end of dwell; units mV at ADC input; H dimensionless (mV/mV)']))
# ---------------- ERA stabilisation -> modes
P,fl,orders,shp=E.run([(0,135),(193,328)])
sf=[];sz=[];so=[]
for n in orders[1:]:
    for f,z,s in zip(P[n]['f'],P[n]['z'],fl[n]):
        if s and n>=8: sf.append(f);sz.append(z);so.append(n)
sf=np.array(sf);sz=np.array(sz);o=np.argsort(sf);sf,sz=sf[o],sz[o]
cl=[];cur=[0]
for i in range(1,len(sf)):
    if sf[i]-sf[i-1]>0.03: cl.append(cur);cur=[]
    cur.append(i)
cl.append(cur)
Hn=np.array([abs(D[c]['H']) for c in chans if c[0]=='bolo']); Cn=np.array([D[c]['coh'] for c in chans if c[0]=='bolo'])
SN=np.array([D[c]['amp']/D[c]['noise'] for c in chans if c[0]=='bolo'])
medH=np.median(Hn/np.median(Hn,axis=1,keepdims=True),0)
fd=FK
rows=[]
for c in cl:
    if len(c)<8: continue
    f=sf[c];z=sz[c]; f0=np.median(f); zm=np.median(z); zs=1.4826*np.median(abs(z-zm))
    zerr=max(zs,np.std(z)); ferr=max(0.05,np.std(f))
    # channels showing: bolometer with coherent, significant drive response within +-0.15 Hz of f0
    near=np.where(abs(fd-f0)<=0.15)[0]
    show=[BOLO[i] for i in range(52) if (Cn[i,near]>0.9).any() and (SN[i,near]>3).any()]
    # half-power points on the median-normalised H1 (information only)
    j=near[np.argmax(medH[near])]; hp=medH>=medH[j]/np.sqrt(2); npts=0; a=j
    while a>=0 and hp[a]: npts+=1;a-=1
    a=j+1
    while a<71 and hp[a]: npts+=1;a+=1
    resolved=(zerr/zm<0.5) and zm>0.001
    # upper limit when ring-down zeta is not determined (relative scatter >50%) or is ~0 (non-decaying)
    zeta=zm if resolved else float(np.percentile(z,84)); 
    pt=bool(np.any(abs(f0-1.4*np.arange(1,8))<=ferr))
    rows.append(dict(f0_hz=f0,f0_err_hz=ferr,zeta=zeta,zeta_err=zerr if resolved else np.nan,zeta_is_upper_limit=not resolved,n_channels_showing=len(show),channels=' '.join(map(str,show)),
       method=f'ERA ring-down (A:0-5.4s,B:7.7-13.1s after each step, 142 experiments x 71 outputs); {len(c)} stable poles orders 8-60; H1 half-power points on channel-median |H| = {npts} (<3 so no HPBW zeta)' if npts<3 else f'ERA ring-down; {len(c)} stable poles; H1 half-power points={npts}',pt_harmonic_flag=pt,nstable=len(c)))
rows.sort(key=lambda r:r['f0_hz'])
with open('analysis/modes.csv','w') as fh:
    w=csv.writer(fh); w.writerow('f0_hz,f0_err_hz,zeta,zeta_err,zeta_is_upper_limit,n_channels_showing,channels,method,pt_harmonic_flag'.split(','))
    for r in rows: w.writerow([f"{r['f0_hz']:.3f}",f"{r['f0_err_hz']:.3f}",f"{r['zeta']:.4f}",'' if np.isnan(r['zeta_err']) else f"{r['zeta_err']:.4f}",str(r['zeta_is_upper_limit']).lower(),r['n_channels_showing'],r['channels'],r['method'],str(r['pt_harmonic_flag']).lower()])
    for r in rows: print(f"{r['f0_hz']:.3f} +-{r['f0_err_hz']:.3f} zeta {r['zeta']*100:.2f}% err {r['zeta_err']*100:.2f}% UL={r['zeta_is_upper_limit']} nch={r['n_channels_showing']} nstable={r['nstable']} pt={r['pt_harmonic_flag']} | {r['method'][-60:]}")
# ---------------- channel_gain.csv
with open('analysis/channel_gain.csv','w') as fh:
    fh.write('# amplitudes in mV AT THE ADC INPUT (21000/2**18 mV per count); NOT bolometer volts, temperature or energy. peak_response = |H| (mV/mV, ratio to ch1111 force channel) at the step with largest |H| among steps with coherence>=0.5; inband_noise_rms_mV = median over the 71 drive frequencies of the quiet-window noise in the same 20 s Hann tone-rms estimator; snr = response tone rms (mV) at peak step / noise at that frequency; median_coherence over 71 steps\n')
    w=csv.writer(fh); w.writerow('channel,peak_response,peak_f_hz,inband_noise_rms_mV,snr,median_coherence'.split(','))
    for c in chans:
        if c[0]!='bolo': continue
        d=D[c]; H=abs(d['H']); ok=d['coh']>=0.5
        kk=int(np.argmax(np.where(ok,H,-1))) if ok.any() else int(np.argmax(H))
        w.writerow([c[1],f'{H[kk]:.5g}',f'{FK[kk]:.1f}',f'{np.median(d["noise"]):.4g}',f'{d["amp"][kk]/d["noise"][kk]:.4g}',f'{np.median(d["coh"]):.3f}'])
print('bolo median coherence overall',np.median(Cn),'min/max per-channel median',np.median(Cn,1).min(),np.median(Cn,1).max())
