import pickle, math, ezdxf
from shapely.geometry import Polygon, Point, LineString, box, MultiLineString
from shapely.ops import unary_union
import sys; sys.path.insert(0, '../danish')
from ncbase import NC, ccw, off, F
PW, PH = 2100.0, 2800.0; ET = 1.3
L = pickle.load(open('layout.pkl', 'rb'))
NAMES = {2: 'MESE_PLAKA_2_REV', 3: 'MESE_PLAKA_3_REV'}
def excl(P):
    g = []
    for p in P['panels']:
        x0, y0, x1, y1 = p['box'].bounds; g.append(box(x0 - p['ov'] - 6, y0 - 10, x1 + p['ov'] + 6, y1 + 10).buffer(20 if p['v'] else 12))
    g += [c.buffer(19 + 12) for _, c in P['vcircles']]
    g += [q.buffer(8 + 10) for _, q, _ in P['t8']]
    g += [q['g'].buffer(8 + 10) for q in P['gifts']]
    if P['danish'] is not None: g.append(P['danish'].buffer(15 + 12))
    return unary_union(g)
def fire_lines(P):
    ex = excl(P); segs = []
    for x in (500, 1000, 1500):
        segs.append(LineString([(x, 0), (x, PH)]))
    for y in (500, 1000, 1500, 2000, 2500):
        segs.append(LineString([(0, y), (PW, y)]))
    out = []
    for s in segs:
        r = s.difference(ex)
        for q in getattr(r, 'geoms', [r]):
            if q.length >= 60: out.append(list(q.coords))
    return out
def check(P):
    errs = []
    items = [('panel ' + p['ad'], p['box'], 'V' if p['v'] else 'T') for p in P['panels']] + [(n, c, 'V') for n, c in P['vcircles']] + \
            [(n, q, 'T') for n, q, _ in P['t8']] + [(q['n'], q['g'], 'G') for q in P['gifts']] + ([('DANISH', P['danish'], 'V')] if P['danish'] is not None else [])
    for i, (a, ga, ta) in enumerate(items):
        if not box(0, 0, PW, PH).buffer(-2).contains(ga): errs.append('plaka dışı ' + a)
        for b, gb, tb in items[i + 1:]:
            d = ga.distance(gb); need = 25 if 'V' in (ta, tb) else (14 if 'G' in (ta, tb) else 8)
            if d < need: errs.append('%s-%s %.1f<%d' % (a, b, d, need))
    return errs
res = {}
for k in (2, 3):
    P = L[k]; nc = NC(NAMES[k]); tools = []
    if P['d3']:
        nc.tc(3, '3 MM BICAK', 17500); tools.append((3, '3 MM BICAK', 3))
        for x, y in P['d3']: nc.drill(x, y, 6.0, 800)
    nc.tc(6, 'V91 JİLETBICAK ( 312 MOB )', 16000); tools.append((6, 'V91 JİLETBICAK ( 312 MOB )', 64))
    for p in P['panels']:
        if p['v']:
            x0, y0, x1, y1 = p['box'].bounds
            nc.path([(x0, y0), (x0, y1)], -0.5, 6000, 1500, closed=False); nc.path([(x1, y1), (x1, y0)], -0.5, 6000, 1500, closed=False)
    if P['danish'] is not None: nc.path(ccw(P['danish']), 4.0, 6000)
    for q in sorted(P['gifts'], key=lambda q: (q['g'].centroid.y, q['g'].centroid.x)): nc.path(ccw(q['g']), 13.0, 6000)
    for _, c in P['vcircles']: nc.path(ccw(c), -0.5, 6000, 1500)
    nc.tc(4, 'MATKAP DEL 10 LUK ', 17500); tools.append((4, 'MATKAP DEL 10 LUK ', 10))
    for x, y in P['d10']: nc.drill(x, y, 4.0, 2000)
    for p in P['panels']:
        x0, y0, x1, y1 = p['box'].bounds
        for i, y in enumerate(p['grooves']):
            a, b = (x0 - p['ov'], x1 + p['ov']) if i % 2 == 0 else (x1 + p['ov'], x0 - p['ov'])
            nc.path([(a, y), (b, y)], ET, 7500, closed=False)
    nc.tc(8, 'ANTESAN BÇK 8 LIK Y', 16000); tools.append((8, 'ANTESAN BÇK 8 LIK Y', 8))
    for q in P['gifts']:
        if q['h'] is not None:
            c = ccw(off(q['h'], -4), False)
            for zz in (9.0, 0.0): nc.path(c, zz, 3000, 1500)
    for s in fire_lines(P):
        for zz in (9.0, 1.5): nc.path(s, zz, 7000, closed=False)
    P['fire'] = fire_lines(P)
    for q in sorted(P['gifts'], key=lambda q: q['g'].area):
        c = ccw(off(q['g'], 4))
        for zz in (9.0, 0.2): nc.path(c, zz, 7000 if zz > 1 else 4500)
    for n, q, zs in sorted(P['t8'], key=lambda t: t[1].area):
        c = ccw(off(q, 4))
        for zz in zs: nc.path(c, zz, 7000 if zz > 1 else (4500 if zz > 0 else 5000))
    if P['danish'] is not None: nc.path(ccw(off(P['danish'], 4)), 0.0, 5000)
    for p in sorted(P['panels'], key=lambda p: p['box'].area):
        x0, y0, x1, y1 = p['box'].bounds
        for zz in (12.0, 6.0, 0.0):
            if p['v']:
                nc.path([(x0, y0 - 4), (x1, y0 - 4)], zz, 3500, closed=False); nc.path([(x1, y1 + 4), (x0, y1 + 4)], zz, 3500, closed=False)
            else:
                nc.path(ccw(box(x0 - 4, y0 - 4, x1 + 4, y1 + 4)), zz, 3500)
    desc = '18 MM MESE KAPLAMA - PLAKA %d REVIZE (TARAMA ET 1.3, 18 MM PAY, HEDIYELIK, KIRIM CIZGILERI)' % k
    m = nc.save(tools, desc); res[k] = m
    print('PLAKA', k, 'süre', m, 'dk', 'kırım', len(P['fire']), 'hata', check(P))
pickle.dump(L, open('layout2.pkl', 'wb'))
