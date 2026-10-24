import json, math, pickle
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity
from ncbase import NC, ccw, off, F
PW, PH = 2100.0, 2800.0; ET = 1.3
plates = pickle.load(open('nest.pkl', 'rb'))
def X(it):
    rot, dx, dy = it['rot'], it['dx'], it['dy']
    def f(pt): q = affinity.rotate(Point(pt), rot, origin=(0, 0)); return (q.x + dx, q.y + dy)
    return f
def geo(it): return affinity.translate(affinity.rotate(it['p']['poly'], it['rot'], origin=(0, 0)), it['dx'], it['dy'])
wn = json.load(open('../win/winston_nest.json'))
WIN = dict(strips=[Polygon(c) for _, c in wn['placed']], items=wn['items'])
def winston_ops(nc, phase):
    # phase 'drill' / 'cut'
    D = {'D60': (300, 220, 260), 'D39': (195, 125, 155)}
    if phase == 'drill':
        for ad, c in WIN['items']:
            o, i, rh = D[ad.split('_')[1]]
            for a in (0, 90, 180, 270): nc.drill(c[0] + rh * math.cos(math.radians(a)), c[1] + rh * math.sin(math.radians(a)), 0.0, 1000)
        return
    for kind, zs in (('D39I', (9.0, 0.0)), ('D39O', (9.0, 0.2)), ('D60I', (9.0, 0.0))):
        for ad, c in WIN['items']:
            if kind[:3] not in ad: continue
            o, i, rh = D[ad.split('_')[1]]
            if kind.endswith('I'): p = ccw(off(Point(*c).buffer(i, 256), -4), False)
            else: p = ccw(off(Point(*c).buffer(o, 256), 4))
            for z in zs: nc.path(p, z, 7000 if z > 1 else 4500)
    for s in sorted(WIN['strips'], key=lambda q: q.area):
        p = ccw(off(s, 4))
        for z in (9.0, 0.2): nc.path(p, z, 7000 if z > 1 else 4500)
    for ad, c in WIN['items']:
        if 'D60' in ad:
            p = ccw(off(Point(*c).buffer(300, 256), 4))
            for z in (9.0, 0.0): nc.path(p, z, 7000 if z > 1 else 5000)
def excl(pl, win):
    g = []
    for it in pl['items']:
        p = it['p']; m = 22 if p['v91'] else (18 if p['tarama'] else 12)
        g.append(geo(it).buffer(m + 8))
    if win: g += [s.buffer(16) for s in WIN['strips']] + [Point(*c).buffer(300 + 16) for ad, c in WIN['items'] if 'D60' in ad]
    return unary_union(g)
def fire(pl, win):
    ex = excl(pl, win); out = []
    for x in (500, 1000, 1500): segs = [LineString([(x, 0), (x, PH)])]; out += segs
    for y in (500, 1000, 1500, 2000, 2500): out.append(LineString([(0, y), (PW, y)]))
    res = []
    for s in out:
        r = s.difference(ex)
        for q in getattr(r, 'geoms', [r]):
            if q.length >= 60: res.append(list(q.coords))
    return res
def check(pl, win):
    errs = []; G = [(it['p']['name'], geo(it), it['p']) for it in pl['items']]
    if win: G += [('WINSTON şerit', s, dict(v91=[], tarama=False)) for s in WIN['strips']] + [('WINSTON kapak', Point(*c).buffer(300), dict(v91=[], tarama=False)) for ad, c in WIN['items'] if 'D60' in ad]
    for i, (a, ga, pa) in enumerate(G):
        if not box(0, 0, PW, PH).buffer(-4).contains(ga): errs.append('plaka dışı ' + a)
        for b, gb, pb in G[i + 1:]:
            need = 25 if (pa['v91'] or pb['v91']) else (20 if (pa['tarama'] or pb['tarama']) else 9)
            d = ga.distance(gb)
            if d < need: errs.append('%s / %s %.0f<%d' % (a, b, d, need))
    return errs
summary = {}
for pi, pl in enumerate(plates):
    win = pi == 0; nc = NC(pl['name']); tools = []
    its = pl['items']
    v = [(it, X(it)) for it in its if it['p']['v91']]
    if v:
        nc.tc(6, 'V91 JİLETBICAK ( 312 MOB )', 16000); tools.append((6, 'V91 JİLETBICAK ( 312 MOB )', 64))
        for it, f in v:
            for ln in it['p']['v91']: nc.path([f(q) for q in ln], -0.5, 6000, 1500)
    t4 = [it for it in its if it['p']['pocket'] or it['p']['lamba'] or it['p']['grooves']]
    if t4:
        nc.tc(4, 'MATKAP DEL 10 LUK ', 17500); tools.append((4, 'MATKAP DEL 10 LUK ', 10))
        for it in t4:
            f = X(it)
            for z in (12.0, 6.0):
                for i, ln in enumerate(it['p']['pocket']):
                    pts = [f(q) for q in (ln if i % 2 == 0 else ln[::-1])]; nc.path(pts, z, 5000)
            for ln in it['p']['lamba']: nc.path([f(q) for q in ln], 12.0, 5000)
        for it in t4:
            f = X(it)
            for i, ln in enumerate(it['p']['grooves']):
                pts = [f(q) for q in (ln if i % 2 == 0 else ln[::-1])]; nc.path(pts, ET, 7500)
    nc.tc(8, 'ANTESAN BÇK 8 LIK Y', 16000); tools.append((8, 'ANTESAN BÇK 8 LIK Y', 8))
    if win: winston_ops(nc, 'drill')
    for it in its:
        f = X(it)
        for q in it['p']['drill']: nc.drill(*f(q), 4.0, 2000)
        for q in it['p']['hinge']:
            c = f(q)
            for z in (9.0, 5.0):
                for r in (13.5, 9.5, 5.5):
                    ring = list(Point(c).buffer(r, 32).exterior.coords); nc.path(ring, z, 3000, 1000)
    fl = fire(pl, win)
    for s in fl:
        for z in (9.0, 1.5): nc.path(s, z, 7000)
    if win: winston_ops(nc, 'cut')
    norm = sorted([it for it in its if not it['p']['tarama']], key=lambda it: it['p']['poly'].area)
    for it in norm:
        p = it['p']; g = geo(it)
        if p['t8open']:
            f = X(it); pts = [f(q) for q in p['t8open']]
            for z in (9.0, 0.0): nc.path(pts, z, 7000 if z > 1 else 5000)
        else:
            c = ccw(off(g, 4)); zs = (9.0, 0.2) if (p['small'] or g.area < 120000) else (9.0, 0.0)
            for z in zs: nc.path(c, z, 7000 if z > 1 else 5000)
    for it in sorted([it for it in its if it['p']['tarama']], key=lambda it: it['p']['poly'].area):
        p = it['p']; f = X(it)
        if p['t8open']: pts = [f(q) for q in p['t8open']]
        else: pts = ccw(off(geo(it), 4))
        for z in (12.0, 6.0, 0.0): nc.path(pts, z, 3500)
    desc = '18 MM MDF - %s (BONBON TV + KONSOL 3K%s)' % (pl['name'], ' + WINSTON KAPAK/KALINLASTIRMA' if win else (' + EKSIK E/G2' if any('EKSIK' in it['p']['name'] for it in its) else ''))
    mm = nc.save(tools, desc); errs = check(pl, win)
    summary[pl['name']] = dict(min=mm, n=len(its), fire=len(fl), errs=errs)
    print(pl['name'], mm, 'dk', len(its), 'parça', 'kırım', len(fl), 'HATA' if errs else 'ok', errs[:6])
    pl['fire'] = fl
pickle.dump(plates, open('plates_out.pkl', 'wb'))
