import math, numpy as np, ezdxf
from shapely.geometry import Polygon, Point, LineString, box
from shapely import affinity
from scipy.interpolate import CubicSpline
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP

SX, SY, T = 800.0, 1220.0, 10.0
BEV = 7.0      # V91 dalis -> 3 mm gorunen kenar (Z3)
WALL = 10.0    # cam civisi + aski vidasi icin tam kalinlik bant
LAP = 10.0     # cam bindirme (lamba) genisligi
GCLR = 1.0     # cam bosluk
STEP = BEV + WALL + LAP + 8.0   # ic ice adim (8 = ortak 8 mm kesim)
RING = BEV + WALL + LAP          # gorunen halka 27 mm
MINSIDE = 300.0
SMOOTH = 30.0

def spline_shape(pts, n=400):
    p = np.array(pts + [pts[0]], float); t = np.linspace(0, 1, len(p))
    cx = CubicSpline(t, p[:, 0], bc_type='periodic'); cy = CubicSpline(t, p[:, 1], bc_type='periodic')
    tt = np.linspace(0, 1, n, endpoint=False); return Polygon(np.c_[cx(tt), cy(tt)]).buffer(0)
def fit(poly, W, H, cx, cy):
    b = poly.bounds; p = affinity.translate(poly, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
    p = affinity.scale(p, W / (b[2] - b[0]), H / (b[3] - b[1]), origin=(0, 0)); return affinity.translate(p, cx, cy)
def shape(kind, W, H, cx, cy):
    if kind == 'YUVARLAK': return Point(cx, cy).buffer(W / 2, resolution=180)
    if kind == 'OVAL': return fit(Point(0, 0).buffer(1, resolution=180), W, H, cx, cy)
    if kind == 'KAPSUL':
        r = W / 2; return LineString([(cx, cy - H / 2 + r), (cx, cy + H / 2 - r)]).buffer(r, resolution=90)
    if kind == 'YUMUSAK':
        r = 0.14 * W; return box(cx - W / 2 + r, cy - H / 2 + r, cx + W / 2 - r, cy + H / 2 - r).buffer(r, resolution=60)

def smooth(p, s=SMOOTH):
    return p.buffer(-s, resolution=32).buffer(s, resolution=32)

def chain(kind, W, H, cx, cy):
    """YUVARLAK/KAPSUL: tam ofset (ortak tek kesim). Digerleri: ayni formun kucultulmusu, en az 10 mm bosluk (iki ayri kesim)."""
    out = []; O = shape(kind, W, H, cx, cy); w, h = W, H; shared = False
    while True:
        b = O.bounds
        out.append(dict(kind=kind, O=O, w=b[2] - b[0], h=b[3] - b[1], c=(cx, cy), shared=shared))
        I = O.buffer(-RING, resolution=32)
        if kind in ('YUVARLAK', 'KAPSUL'):
            nw, nh = w - 2 * STEP, h - 2 * STEP; shared = True
            if min(nw, nh) < MINSIDE: break
            nxt = shape(kind, nw, nh, cx, cy)
        else:
            best = (0, cx, cy)
            for dx in range(-80, 81, 20):
                for dy in range(-120, 121, 20):
                    lo, hi = best[0], 1.0
                    if not I.contains(shape(kind, w * max(lo, .3), h * max(lo, .3), cx + dx, cy + dy).buffer(10, resolution=16)): continue
                    lo = max(lo, .3)
                    for _ in range(18):
                        f = (lo + hi) / 2
                        if I.contains(shape(kind, w * f, h * f, cx + dx, cy + dy).buffer(10, resolution=16)): lo = f
                        else: hi = f
                    if lo > best[0]: best = (lo, cx + dx, cy + dy)
            lo, cx, cy = best
            nw, nh = w * lo, h * lo; shared = False
            if min(nw, nh) < MINSIDE: break
            nxt = shape(kind, nw, nh, cx, cy)
        O = nxt; w, h = nw, nh
    # en icteki bosluga yuvarlak ayna sigiyorsa ekle
    from shapely.ops import polylabel
    core = out[-1]['O'].buffer(-(RING + 10), resolution=32)
    if not core.is_empty and core.geom_type == 'Polygon':
        pc = polylabel(core, 1.0); r = core.exterior.distance(pc)
        D = math.floor(2 * r / 10) * 10
        if D >= MINSIDE:
            for m in chain('YUVARLAK', D, D, pc.x, pc.y): m['shared'] = m['shared'] if m is not None else False; out.append(m)
            out[-len(chain('YUVARLAK', D, D, pc.x, pc.y))]['shared'] = False
    return out

ADI = {'YUVARLAK': 'Yuvarlak', 'OVAL': 'Oval', 'KAPSUL': 'Kapsul', 'YUMUSAK': 'Yumusak dikdortgen'}
F = lambda v: ('%.3f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'
def ring_pts(p, ccw=True):
    c = list(p.exterior.coords)
    if Polygon(c).exterior.is_ccw != ccw: c = c[::-1]
    return c
def off(p, d): return p.buffer(d, resolution=32)

def hanger_holes(O):
    b = O.bounds; cx = (b[0] + b[2]) / 2; w = b[2] - b[0]
    mid = off(O, -(BEV + WALL / 2)).exterior; hs = []
    for x in (cx - w / 4, cx + w / 4):
        g = mid.intersection(LineString([(x, b[1] - 10), (x, b[3] + 10)]))
        ys = [q.y for q in getattr(g, 'geoms', [g]) if not q.is_empty]
        if ys: hs.append((x, max(ys)))
    return hs
