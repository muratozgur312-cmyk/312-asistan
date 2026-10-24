import pickle
from nest2 import *
from shapely.geometry import Point
def at(nm,r,x,y):
    _,s,m,_=P[nm]; ss=z(affinity.rotate(s,r,origin='centroid')); return (nm,r,affinity.translate(ss,x,y))
L=[at('DANISH',0,405,15),at('W_PANEL',0,1340,15),at('C1',0,398,1845),at('C2',0,1262,1950)]
items=[('H',None,H)]+L
ok=True
for i,(a,_,g) in enumerate(items):
    ma=V if a!='DANISH' else V
    if not box(0,0,2100,2800).contains(g.buffer(5)): print('plaka dışı',a,g.bounds); ok=False
    for b,_,h in items[i+1:]:
        d=g.distance(h)
        if d<29: print('yakın',a,b,round(d,1)); ok=False
print('P3 ok' if ok else 'P3 HATA'); pickle.dump(L,open('p3.pkl','wb'))
for n,r,g in L: print(n,[round(v) for v in g.bounds])
