"""Eigensystem realization algorithm for multi-output, multi-experiment free decays, plus stabilisation diagram."""
import numpy as np
def build_hankel_products(Y, p, q):
    """Y: array (L, n_out, n_exp) of free-decay samples Y_k = C A^k X0. Returns G0=H0 H0^T, G1=H1 H0^T (sizes (n_out p)^2)
    where H0[i,j]=Y_{i+j}, H1[i,j]=Y_{i+j+1}, i<p, j<q."""
    L,no,ne=Y.shape; assert p+q<=L-1+1
    H0=np.concatenate([np.concatenate([Y[i+j] for j in range(q)],axis=1) for i in range(p)],axis=0)      # (no*p, ne*q)
    H1=np.concatenate([np.concatenate([Y[i+j+1] for j in range(q)],axis=1) for i in range(p)],axis=0)
    return H0@H0.T, H1@H0.T, no
def era_poles(G0,G1,no,dt,orders):
    w,U=np.linalg.eigh(G0); idx=np.argsort(w)[::-1]; w=np.clip(w[idx],1e-30,None); U=U[:,idx]
    s=np.sqrt(w)                       # singular values of H0
    out={}
    for n in orders:
        Un=U[:,:n]; sn=s[:n]
        # A = S^-1/2 U^T H1 V S^-1/2 ; V=H0^T U S^-1  ->  A = S^-1/2 U^T (H1 H0^T) U S^-3/2
        A=(Un.T@G1@Un)/np.sqrt(sn)[:,None]/(sn**1.5)[None,:]
        lam,vec=np.linalg.eig(A)
        C=(Un*np.sqrt(sn)[None,:])[:no,:]       # first block row of observability matrix O = U S^1/2
        shapes=C@vec
        sc=np.log(lam.astype(complex))/dt
        f=np.abs(sc.imag)/(2*np.pi); z=-sc.real/np.abs(sc)
        keep=sc.imag>0
        out[n]=dict(f=f[keep],z=z[keep],shape=shapes[:,keep],sv=s)
    return out
def mac(a,b):
    return abs(np.vdot(a,b))**2/(np.vdot(a,a).real*np.vdot(b,b).real)
def stabilise(poles,orders,df_rel=0.01,dz_rel=0.2,mac_min=0.9,fmin=2.5,fmax=9.5):
    """mark pole at order n stable if a pole at the previous order matches f within df_rel, zeta within dz_rel, MAC>mac_min"""
    flags={}
    for a,b in zip(orders[:-1],orders[1:]):
        pa,pb=poles[a],poles[b]; fl=np.zeros(len(pb['f']),bool)
        for i,(f,z) in enumerate(zip(pb['f'],pb['z'])):
            if not (fmin<=f<=fmax) or z<=0: continue
            for j,(f2,z2) in enumerate(zip(pa['f'],pa['z'])):
                if abs(f-f2)<df_rel*f and abs(z-z2)<dz_rel*z and mac(pb['shape'][:,i],pa['shape'][:,j])>mac_min:
                    fl[i]=True;break
        flags[b]=fl
    return flags
