import json, math, pickle, numpy as np, ezdxf
from shapely.geometry import Polygon, Point, LineString, MultiLineString, box
from shapely.ops import unary_union
from shapely import affinity
from scipy.signal import fftconvolve
from PIL import Image, ImageDraw
import sys; sys.path.insert(0, '../danish')
from ncbase import NC, ccw, off, F
PW, PH = 2100.0, 2800.0
ET, EDGE, PITCH = 1.3, 23.0, 20.0
p2 = {n: (r, g) for n, r, g in pickle.load(open('p2.pkl', 'rb'))}
p3 = {n: (r, g) for n, r, g in pickle.load(open('p3.pkl', 'rb'))}
# ---- dönüşüm: orijinal şekil -> yerleşim (nest.py ile aynı)
def z(p): return affinity.translate(p, -p.bounds[0], -p.bounds[1])
def mover(s, r, placed):
    ss = z(affinity.rotate(s, r, origin='centroid')); c = s.centroid; b0 = affinity.rotate(s, r, origin='centroid').bounds
    dx, dy = placed.bounds[0] - ss.bounds[0], placed.bounds[1] - ss.bounds[1]
    def f(pt):
        q = affinity.rotate(Point(pt), r, origin=c); return (q.x - b0[0] + dx, q.y - b0[1] + dy)
    return f
wg = json.load(open('../win/winston_geo.json')); WT = Polygon(wg['T'])
dg = json.load(open('../danish/danish_geo.json')); DN = Polygon(dg['T0'])
F_HOLES = [(66, 340.6), (354, 340.6), (92, 655.6), (28, 655.6), (28, 1289.3), (92, 1289.3), (66, 1620.2), (354, 1620.2)]
E_HOLE = {'E1': (35, 479), 'E2': (365, 479)}
def panel(name, g, ov, vside):
    x0, y0, x1, y1 = g.bounds; h = y1 - y0; n = round((h - 2 * EDGE) / PITCH); pit = (h - 2 * EDGE) / n
    return dict(ad=name, box=box(x0, y0, x1, y1), ov=ov, v=vside, grooves=[y0 + EDGE + k * pit for k in range(n + 1)], pitch=pit)
# ================= parça listeleri =================
PL = {2: dict(), 3: dict()}
P = PL[2]
P['panels'] = [panel('A', p2['A'][1], 6, True), panel('B', p2['B'][1], 6, True)]
P['vcircles'] = []
P['t8'] = []   # (ad, poly, zlist)
for n in ('D1', 'D2'): P['t8'].append((n, p2[n][1], (9.0, 0.2)))
for n in ('E1', 'E2'): P['t8'].append((n, p2[n][1], (9.0, 0.2)))
P['t8'].append(('F', p2['F'][1], (9.0, 0.0))); P['t8'].append(('G', p2['G'][1], (9.0, 0.0)))
P['t8'].append(('W_TABLA', p2['W_TABLA'][1], (9.0, 0.0)))
P['d10'] = [mover(box(0, 0, 400, 1963), p2['F'][0], p2['F'][1])(h) for h in F_HOLES] + \
           [mover(box(0, 0, 400, 488), p2[n][0], p2[n][1])(E_HOLE[n]) for n in ('E1', 'E2')]
fw = mover(z(WT), p2['W_TABLA'][0], p2['W_TABLA'][1]); wt0 = WT.bounds
P['d3'] = [fw((x - wt0[0], y - wt0[1])) for x, y in wg['holes']]
P['danish'] = None
P = PL[3]
H = box(15.218, 6.805, 365.218, 2521.805)
P['panels'] = [panel('H', H, 6, True), panel('W_PANEL', p3['W_PANEL'][1], 15, False)]
P['vcircles'] = [('C1', p3['C1'][1]), ('C2', p3['C2'][1])]
P['t8'] = []; P['d3'] = []
dz = z(affinity.rotate(DN, 90)); fd = mover(dz, p3['DANISH'][0], p3['DANISH'][1])
dzb = affinity.rotate(DN, 90).bounds
P['danish'] = p3['DANISH'][1]
P['d10'] = [fd((affinity.rotate(Point(h), 90, origin=(0, 0)).x - dzb[0], affinity.rotate(Point(h), 90, origin=(0, 0)).y - dzb[1])) for h in dg['holes0']]
# ================= servis tahtası + altlık (boşluklara) =================
def board(L, W, hl=110, hw=46):
    bl = L - hl
    body = box(-L / 2, -W / 2, -L / 2 + bl, W / 2).buffer(-min(W, bl) * 0.2).buffer(min(W, bl) * 0.2, resolution=32)
    handle = LineString([(-L / 2 + bl - 30, 0), (L / 2 - hw / 2, 0)]).buffer(hw / 2, resolution=32)
    g = unary_union([body, handle]).buffer(-15, resolution=16).buffer(15, resolution=16).buffer(15, resolution=16).buffer(-15, resolution=16)
    return g, Point(L / 2 - hw / 2, 0).buffer(9, resolution=32)
def coaster(): return Point(0, 0).buffer(50, resolution=48), None
def oval(): return affinity.scale(Point(0, 0).buffer(1, resolution=64), 180, 90), None   # 36x18 oval tepsi
KINDS = [('T48', lambda: board(480, 240)), ('T40', lambda: board(400, 200)), ('OV36', oval), ('T32', lambda: board(320, 165)), ('A10', coaster)]
LIM = {'T48': 3, 'T40': 4, 'OV36': 3, 'T32': 6, 'A10': 12}
RES = 4.0
def occupied(k):
    P = PL[k]; g = []
    for p in P['panels']:
        b = p['box']; g.append(box(b.bounds[0] - p['ov'] - 5, b.bounds[1] - 8, b.bounds[2] + p['ov'] + 5, b.bounds[3] + 8).buffer(26 if p['v'] else 18))
    g += [c.buffer(19 + 26) for _, c in P['vcircles']]
    g += [q.buffer(8 + 18) for _, q, _ in P['t8']]
    if P['danish'] is not None: g.append(P['danish'].buffer(15 + 26))
    return unary_union(g)
def raster(poly, ox, oy, w, h):
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    for q in getattr(poly, 'geoms', [poly]): d.polygon([((x - ox) / RES, (y - oy) / RES) for x, y in q.exterior.coords], fill=1)
    return np.array(im, np.float32)
from shapes import S as SH
RES = 4.0
SCALES = [700, 640, 580, 520, 470, 420, 380, 340, 300, 260, 220, 190, 160]
for k in (2, 3):
    W_, H_ = int(PW / RES), int(PH / RES); blk = raster(occupied(k), 0, 0, W_, H_)
    m = int(14 / RES); blk[:m] = 1; blk[-m:] = 1; blk[:, :m] = 1; blk[:, -m:] = 1
    gifts = []; cnt = {}
    while True:
        done = False
        for L_ in SCALES:
            cands = []
            for key, shp in SH.items():
                g0 = affinity.scale(shp, L_, L_, origin=(0, 0))
                for rot in range(0, 180 if key in ('02', '03', '16', '24', '17', '18', '01') else 360, 15):
                    g = affinity.rotate(g0, rot, origin=(0, 0)); s_ = g.buffer(8 + 6); bb = s_.bounds
                    pm = raster(s_, bb[0], bb[1], int(math.ceil((bb[2] - bb[0]) / RES)) + 1, int(math.ceil((bb[3] - bb[1]) / RES)) + 1)
                    if pm.shape[0] >= H_ or pm.shape[1] >= W_: continue
                    ok = np.argwhere(fftconvolve(blk, pm[::-1, ::-1], mode='valid') < 0.5)
                    if not len(ok): continue
                    kk = np.lexsort((ok[:, 1], ok[:, 0]))[0]; yy, xx = ok[kk]
                    score = g.area * (0.45 ** cnt.get(key, 0))
                    cands.append((score, key, rot, xx * RES - bb[0], yy * RES - bb[1], s_, g0))
                    break
            if cands:
                score, key, rot, dx, dy, s_, g0 = max(cands, key=lambda c: c[0])
                g = affinity.translate(affinity.rotate(g0, rot, origin=(0, 0)), dx, dy)
                gifts.append(dict(n=key, L=L_, g=g, h=None)); cnt[key] = cnt.get(key, 0) + 1
                blk = np.maximum(blk, raster(affinity.translate(s_, dx, dy).buffer(RES + 8), 0, 0, W_, H_)); done = True; break
        if not done: break
    PL[k]['gifts'] = gifts; print('plaka', k, [(q['n'], q['L']) for q in gifts])
pickle.dump({k: {kk: v for kk, v in PL[k].items()} for k in PL}, open('layout.pkl', 'wb'))
