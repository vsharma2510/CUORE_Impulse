"""Shared helpers for the analyst pipeline (ANALYST methods of SPEC.md section 5)."""
import numpy as np, json, os
ROOT='<HOME>/CUORE_ImpulsePilot'
OFFSET=3990.0          # arrays begin at t=3990 s of run RUNA
FS=1000.0
def run_to_idx(t_run, offset=OFFSET, fs=FS):
    """run-coordinate seconds -> index in the excitation arrays. Subtracts the 3990 s offset."""
    return np.rint((np.asarray(t_run, float)-offset)*fs).astype(np.int64)
def pulser_in_window(n_samples=17770000, offset=OFFSET):
    p=np.load(f'{ROOT}/data/pulser_times.npy')
    t=p-offset
    return t[(t>=0)&(t<n_samples/FS)]          # ARRAY-coordinate seconds
def pulser_mask(n, tp_array_s, pre=0.1, post=1.0, fs=FS):
    """boolean good-sample mask (True=usable). Masks [tp-pre, tp+post] around every pulser time
    (tp already in array coordinates)."""
    good=np.ones(n,bool)
    for tp in tp_array_s:
        a=max(int(round((tp-pre)*fs)),0); b=min(int(round((tp+post)*fs))+1,n)
        if b>a: good[a:b]=False
    return good
def load(window,kind,ch):
    return np.load(f'{ROOT}/data/arrays/{window}/{kind}/ch{ch:04d}.npy',mmap_mode='r')
BOLO=list(range(937,989))
AUX=[1018,1019,1020]+list(range(1101,1124))
SCR='/tmp/claude-76977/-global-u2-v-<USER>-CUORE-ImpulsePilot/cc2192c3-04d3-4ec3-836a-f26239b28825/scratchpad'
