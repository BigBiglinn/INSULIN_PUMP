# 2-D Laplace (finite difference) microstrip/CPWG solver: Z0 from C with and without dielectric.
import numpy as np, sys
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
c0=299792458.; e0=8.854e-12
def solve(w,g,h,er,t=0.035,dx=0.01,sm=0.0,er_sm=4.2,W=1.6,Ha=1.2):
    # domain half-width 3 mm, height 3 mm air; symmetric via x=0 (Neumann)
    nx=int(W/dx)+1;ny=int((h+Ha)/dx)+1
    def C(diel):
        eps=np.ones((ny-1,nx-1))
        jh=int(round(h/dx))
        if diel:
            eps[:jh,:]=er
            if sm>0:
                js=int(round((h+t+sm)/dx)); eps[jh:js,:]=er_sm
        fixed=np.zeros((ny,nx),bool);v=np.zeros((ny,nx))
        fixed[0,:]=True  # ground plane
        fixed[-1,:]=True; fixed[:,-1]=True
        jt=int(round(t/dx))
        i1=int(round(w/2/dx)); i2=int(round((w/2+g)/dx)) if g is not None else nx
        for j in range(jh,jh+jt+1):
            fixed[j,:i1+1]=True; v[j,:i1+1]=1.0
            if g is not None: fixed[j,i2:]=True
        idx=-np.ones((ny,nx),int); free=np.where(~fixed); idx[free]=np.arange(len(free[0]))
        n=len(free[0]);rows=[];cols=[];vals=[];b=np.zeros(n)
        def ee(j,i):
            return eps[min(max(j,0),ny-2),min(max(i,0),nx-2)]
        for k,(j,i) in enumerate(zip(*free)):
            ej=[(j+1,i,0.5*(ee(j,i)+ee(j,i-1))),(j-1,i,0.5*(ee(j-1,i)+ee(j-1,i-1))),
                (j,i+1,0.5*(ee(j,i)+ee(j-1,i))),(j,i-1,0.5*(ee(j,i-1)+ee(j-1,i-1)))]
            d=0.0
            for jj,ii,e in ej:
                if ii<0: ii=1   # symmetry
                d+=e
                if fixed[jj,ii]: b[k]+=e*v[jj,ii]
                else: rows.append(k);cols.append(idx[jj,ii]);vals.append(-e)
            rows.append(k);cols.append(k);vals.append(d)
        A=csr_matrix((vals,(rows,cols)),shape=(n,n))
        x=spsolve(A,b); v[free]=x
        # charge via energy: C = eps0 * sum eps |grad v|^2 (full width = 2x half)
        ex=(v[:-1,1:]-v[:-1,:-1]+v[1:,1:]-v[1:,:-1])/2
        ey=(v[1:,:-1]-v[:-1,:-1]+v[1:,1:]-v[:-1,1:])/2
        return 2*e0*np.sum(eps*(ex**2+ey**2))
    Cd=C(True);Ca=C(False)
    return 1/(c0*np.sqrt(Cd*Ca)),Cd/Ca

print("ST w.45 g.13 over In1:",[round(x,1) for x in solve(.45,.13,.076,3.7,t=.04,dx=.0127,W=1.2,Ha=1.0)])
print("ST w.45 g.13 over L3 (In1 void):",[round(x,1) for x in solve(.45,.13,1.385,4.4,t=.04,dx=.02,W=3,Ha=2)])
print("ST MLPF w.30 g.15 over L3:",[round(x,1) for x in solve(.30,.15,1.385,4.4,t=.04,dx=.02,W=3,Ha=2)])
for w,g in ((.25,.25),(.25,.30),(.22,.25),(.28,.25),(.36,.25),(.36,.30),(.33,.25),(.38,.30)):
    a=solve(w,g,.2104,4.4,dx=.01); b=solve(w,g,.2104,4.4,dx=.01,sm=.02)
    print("JLC7628 w %.2f g %.2f Z %.1f, with mask %.1f, eeff %.2f"%(w,g,a[0],b[0],b[1]),flush=True)
for er in (4.0,4.8):
    print("er",er,"w.25 %.1f; w.36 %.1f"%(solve(.25,.25,.2104,er,dx=.01,sm=.02)[0],solve(.36,.25,.2104,er,dx=.01,sm=.02)[0]),flush=True)
