import re, math, numpy as np
def arc(p0,p1,R,cw,n=60):
    (x0,y0),(x1,y1)=p0,p1; dx,dy=x1-x0,y1-y0; d=math.hypot(dx,dy); h=math.sqrt(max(R*R-d*d/4,0))
    mx,my=(x0+x1)/2,(y0+y1)/2; ux,uy=-dy/d,dx/d
    s=1 if (not cw)==(R>0) else -1
    cx,cy=mx+s*h*ux,my+s*h*uy
    a0=math.atan2(y0-cy,x0-cx); a1=math.atan2(y1-cy,x1-cx)
    if cw:
        if a1>a0: a1-=2*math.pi
    else:
        if a1<a0: a1+=2*math.pi
    return [(cx+abs(R)*math.cos(a),cy+abs(R)*math.sin(a)) for a in np.linspace(a0,a1,n)][1:]
def parse(fn):
    tool=None;x=y=z=0.0;paths=[];cur=None
    for l in open(fn,encoding='latin-1'):
        m=re.search(r'M6T(\d+)',l)
        if m: tool=int(m.group(1)); continue
        d=dict(re.findall(r'([GXYZRF])(-?[\d.]+)',l.split(';')[0]))
        if 'G' not in d: continue
        g=int(float(d['G'])); nx=float(d.get('X',x)); ny=float(d.get('Y',y)); nz=float(d.get('Z',z))
        if g==0:
            if cur and len(cur['p'])>1: paths.append(cur)
            cur=None
        else:
            if cur is None or cur['z']!=nz and ('X' not in d and 'Y' not in d):
                if cur and len(cur['p'])>1: paths.append(cur)
                cur=dict(t=tool,z=nz,p=[(nx,ny)])
            elif g in (2,3): cur['p']+=arc((x,y),(nx,ny),float(d['R']),g==2); cur['z']=nz
            else: cur['p'].append((nx,ny)); cur['z']=nz
        x,y,z=nx,ny,nz
    if cur and len(cur['p'])>1: paths.append(cur)
    return paths
if __name__=='__main__':
    for f in ('P2.anc','P3.anc'):
        P=parse(f); print(f,len(P))
        for p in P:
            a=np.array(p['p']); print(' T%s Z%s n=%d x%.0f-%.0f y%.0f-%.0f'%(p['t'],p['z'],len(a),a[:,0].min(),a[:,0].max(),a[:,1].min(),a[:,1].max()))
