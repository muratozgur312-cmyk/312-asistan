import math, json
from shapely.geometry import box, Point, Polygon, LineString
from shapely.ops import unary_union
T=18; R=200; LIP=6; BAND=18.5; GAP=3; TAIL=30; ARK=6; KUS=96; ET=1.3
def P_(W,D): return unary_union([box(0,0,W,D-R),box(R,0,W-R,D),Point(R,D-R).buffer(R,resolution=96),Point(W-R,D-R).buffer(R,resolution=96)]).intersection(box(0,0,W,D))
def spec(W,D,H,BZ,nd,tv):
    Hb=H-BZ; Hi=Hb-2*T; p0,p1=R+TAIL,W-R-TAIL
    dw=(p1-p0-2*GAP-GAP*(nd-1))/nd; dh=Hb-2*LIP-4; th=Hb-2*LIP-1
    dy0=ARK+(T if tv else 0); dy1=D-T-2
    dik=[p0,W/2-T/2,p1-T] if tv else ([p0,p1-T] if nd==2 else [p0,p0+GAP+dw+GAP/2-T/2,p1-T])
    return dict(W=W,D=D,H=H,BZ=BZ,Hb=Hb,Hi=Hi,nd=nd,tv=tv,p0=p0,p1=p1,dw=dw,dh=dh,th=th,dy0=dy0,dy1=dy1,dik=dik,tp=round(TAIL+math.pi/2*R+(D-R)))
def part(name,poly,**f):
    d=dict(name=name,poly=poly,pocket=[],lamba=[],drill=[],hinge=[],grooves=[],v91=[],t8open=None,tarama=False,small=False); d.update(f); return d
def tabla(s,nm):
    W,D=s['W'],s['D']; P=P_(W,D); pk=[]
    for d in (5.0,13.5):
        ring=LineString(P.buffer(-d,join_style=1,resolution=64).exterior.coords)
        r=ring.difference(box(-1,-10,W+1,d+0.5))
        segs=list(getattr(r,'geoms',[r])); line=max(segs,key=lambda g:g.length)
        c=list(line.coords)
        # uçları arka kenara uzat
        if c[0][1]>c[-1][1]: c=c[::-1]
        c=[(c[0][0],-2)]+c+[(c[-1][0],-2)]
        pk.append(c)
    lam=[] if s['tv'] else [[(BAND,5),(W-BAND,5)]]
    dr=[(x+T/2,y) for x in s['dik'] for y in (s['dy0']+40,s['dy1']-40)]
    return part(nm,P,pocket=pk,lamba=lam,drill=dr)
def uc(s,nm):
    L,H=s['tp'],s['th']; a0,a1=TAIL,TAIL+math.pi/2*R; n=round((a1-a0)/20); pit=(a1-a0)/n
    g=[[(a0+k*pit,-10),(a0+k*pit,H+10)] for k in range(n+1)]
    return part(nm,box(0,0,L,H),grooves=g,tarama=True)
def bonbon_parts():
    out=[]
    tv=spec(1700,350,380,0,2,True); k=spec(1500,450,900,18,3,False)
    for i in (1,2): out.append(tabla(tv,'TV TABLA %d'%i))
    for i in (1,2): out.append(uc(tv,'TV UC PANEL %d'%i))
    for i in range(3): out.append(part('TV DIKME %d'%(i+1),box(0,0,tv['dy1']-tv['dy0'],tv['Hi'])))
    for i in range(2): out.append(part('TV KAPAK %d'%(i+1),box(0,0,tv['dw'],tv['dh']),hinge=[(100,22.5),(tv['dw']-100,22.5)]))
    L=tv['W']-2*T
    out.append(part('TV KARKASI 45',box(0,0,L,KUS),v91=[[(0,0),(L,0)]],t8open=[(0,-4),(-4,-4),(-4,KUS+4),(L+4,KUS+4),(L+4,-4),(L,-4)]))
    out.append(part('TV ALT TAKOZ',box(0,0,L,60),small=True))
    Lw=L-25
    out.append(part('DUVAR KARKASI 45',box(0,0,Lw,KUS),v91=[[(0,0),(Lw,0)]],t8open=[(0,-4),(-4,-4),(-4,KUS+4),(Lw+4,KUS+4),(Lw+4,-4),(Lw,-4)]))
    for i in (1,2): out.append(tabla(k,'KONSOL TABLA %d'%i))
    for i in (1,2): out.append(uc(k,'KONSOL UC PANEL %d'%i))
    for i in range(3): out.append(part('KONSOL DIKME %d'%(i+1),box(0,0,k['dy1']-k['dy0'],k['Hi'])))
    for i in range(3):
        hx=22.5 if i<2 else k['dw']-22.5
        out.append(part('KONSOL KAPAK %d'%(i+1),box(0,0,k['dw'],k['dh']),hinge=[(hx,100),(hx,k['dh']-100)]))
    d1=k['dik'][1]; rd=k['dy1']-k['dy0']-15
    out.append(part('KONSOL RAF SOL',box(0,0,d1-(k['p0']+T)-2,rd)))
    out.append(part('KONSOL RAF SAG',box(0,0,(k['p1']-T)-(d1+T)-2,rd)))
    out.append(part('KONSOL BAZA',P_(1500,450).buffer(-30,join_style=1,resolution=64)))
    return out,tv,k
def eksik_parts():
    P=json.load(open('../eks/parts.json'))
    # E: T8 yolu -> net
    import sys; sys.path.insert(0,'../eks')
    from geomh import pts
    g=P['E'][0]; p=[]
    for s_ in g['segs']:
        q=pts(s_,1.0); p+=q if not p else q[1:]
    E=Polygon(p).buffer(0).buffer(-4); E=Polygon(E.exterior.coords)
    from shapely import affinity
    E=affinity.translate(E,-E.bounds[0],-E.bounds[1])
    # G2: net 1058 x 430, V91 üst kenar, T8 3 kenar, tarama yeniden (18 mm pay, et 1.3)
    W2,H2=1058.0,430.0; n=round((W2-46)/20); pit=(W2-46)/n
    gr=[[(23+k_*pit,-13),(23+k_*pit,H2+13)] for k_ in range(n+1)]
    G2=part('EKSIK G2 TARAMA PANEL',box(0,0,W2,H2),grooves=gr,tarama=True,v91=[[(W2+1,H2),(-1,H2)]],t8open=[(-4,H2),(-4,-4),(W2+4,-4),(W2+4,H2)])
    return [part('EKSIK E OVAL',E),G2]
