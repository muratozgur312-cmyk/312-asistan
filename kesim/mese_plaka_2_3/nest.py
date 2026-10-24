import json, numpy as np, itertools, sys
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
from shapely.prepared import prep
g=json.load(open('../win/winston_geo.json')); WT=Polygon(g['T'])
dg=json.load(open('../danish/danish_geo.json')); DN=Polygon(dg['T0'])
def z(p): return affinity.translate(p,-p.bounds[0],-p.bounds[1])
V=15; T=6
parts=[ # ad, şekil(net), marj, izinli açılar
 ('DANISH',z(affinity.rotate(DN,90)),V,(0,180)),
 ('W_PANEL',box(0,0,382,1893),V,(0,180)),
 ('B',box(0,0,430,1890),V,(0,180)),
 ('F',box(0,0,400,1963),T,(0,90)),
 ('D1',box(0,0,66,1965),T,(0,90)),('D2',box(0,0,66,1965),T,(0,90)),
 ('W_TABLA',z(WT),T,(0,180)),
 ('A',box(0,0,382,1233),V,(0,180)),
 ('G',Point(500,500).buffer(499.5,128),T,(0,)),
 ('C1',Point(400,400).buffer(400,128),V,(0,)),('C2',Point(400,400).buffer(400,128),V,(0,)),
 ('E1',box(0,0,400,488),T,(0,90)),('E2',box(0,0,400,488),T,(0,90))]
H=box(15.2,6.8,365.2,2521.8)
def run(order,prefer):
    occ={2:[],3:[H.buffer(V)]}; pl={2:[],3:[('H',H)]}
    for name in order:
        nm,s,m,rots=[p for p in parts if p[0]==name][0]; best=None
        for P in prefer(nm):
            O=prep(unary_union(occ[P])) if occ[P] else None
            for r in rots:
                ss=z(affinity.rotate(s,r,origin='centroid')); sw=ss.buffer(m); b=sw.bounds
                found=None
                for y in np.arange(-b[1]+2,2800-b[3]-2+1e-6,10):
                    for x in np.arange(-b[0]+2,2100-b[2]-2+1e-6,10):
                        if O is None or not O.intersects(affinity.translate(sw,x,y)): found=(y,x);break
                    if found: break
                if found:
                    key=(found[0]+b[1],found[1]+b[0])
                    if best is None or key<best[0]: best=(key,P,r,found)
            if best: break
        if not best: return None,nm,pl
        _,P,r,(y,x)=best; ss=affinity.translate(z(affinity.rotate(s,r,origin='centroid')),x,y)
        occ[P].append(ss.buffer(m)); pl[P].append((nm,ss,r))
    return True,None,pl
if __name__=='__main__':
    order=['DANISH','W_PANEL','B','F','D1','D2','W_TABLA','A','G','C1','C2','E1','E2']
    ok,fail,pl=run(order,lambda n:(3,2))
    print(ok,fail); 
    for P in pl:
        for nm,s,r in pl[P]: print(P,nm,r,[round(v) for v in s.bounds])
