import random, json, numpy as np, sys, pickle
from nest import parts, H, z, V, T
from shapely.geometry import box
from shapely.ops import unary_union
from shapely import affinity
from shapely.prepared import prep
P={p[0]:p for p in parts}
def place(names,fixed,step=10,seed=None):
    occ=[f.buffer(V) for f in fixed]; out=[]
    for nm in names:
        _,s,m,rots=P[nm]; best=None
        O=prep(unary_union(occ)) if occ else None
        for r in rots:
            ss=z(affinity.rotate(s,r,origin='centroid')); sw=ss.buffer(m); b=sw.bounds; found=None
            for y in np.arange(-b[1],2800-b[3]+1e-6,step):
                for x in np.arange(-b[0],2100-b[2]+1e-6,step):
                    if O is None or not O.intersects(affinity.translate(sw,x,y)): found=(y,x);break
                if found: break
            if found:
                key=(found[0]+b[1],found[1]+b[0])
                if best is None or key<best[0]: best=(key,r,found,ss,m)
        if not best: return None,nm
        _,r,(y,x),ss,m=best; g=affinity.translate(ss,x,y); occ.append(g.buffer(m)); out.append((nm,r,g))
    return out,None
if __name__=='__main__':
    which=sys.argv[1]
    if which=='3':
        r,f=place(['DANISH','W_PANEL','C1','C2'],[H]); print('P3',f, [(n,rr,[round(v) for v in g.bounds]) for n,rr,g in (r or [])])
        if r: pickle.dump(r,open('p3.pkl','wb'))
    else:
        base=['B','F','W_TABLA','A','D1','D2','G','E1','E2']; random.seed(1); tried=set()
        for it in range(400):
            o=base[:] if it==0 else random.sample(base,len(base))
            if tuple(o) in tried: continue
            tried.add(tuple(o))
            r,f=place(o,[],step=15)
            if r: print('OK',o); pickle.dump(r,open('p2.pkl','wb')); [print(n,rr,[round(v) for v in g.bounds]) for n,rr,g in r]; break
        else: print('yok')
