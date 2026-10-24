"""WINSTON ORTA SEHPA — geometri + DXF + NC (MDF plakası ve meşe parçaları)"""
import json, math, numpy as np, ezdxf
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import split, unary_union
from shapely import affinity
from shapely.prepared import prep
from scipy.interpolate import CubicSpline

# ---------------- ölçüler ----------------
LONG = 1300.0          # tabla uzun ölçü
STRIP = 65.0           # kalınlaştırma şerit genişliği
NSEG = 5               # kat başına şerit parçası
D60, H60 = 600.0, 440.0   # Ø60 ayak kapağı dış / iç boşluk
D39, H39 = 390.0, 250.0   # Ø39 kapak (Ø60'ın boşluğundan bedava) dış / iç boşluk
R_H60, R_H39 = 260.0, 155.0   # kapak bağlantı delikleri (baklava, 4 adet) yarıçapı
AYAK_H = 382.0         # Como sehpa ayak yüksekliği (382 + 18 tabla = 400)
ET = 1.1               # tarama eti
PITCH = 20.0           # tarama aralığı
PW, PH = 2100.0, 2800.0

# ---------------- tabla formu (dosyadaki Tabla 1) ----------------
pl = json.load(open('emf_pl.json'))
cand = [p for c, p in pl if c == 0xff00 and len(p) > 50 and 500 < min(x for x, y in p) < 520 and min(y for x, y in p) < 200]
pts = np.array(cand[0], float)
sx = 2100 / 529; sy = 2800 / 705
pts = np.c_[(pts[:, 0] - 507) * sx, (767 - pts[:, 1]) * sy]
if np.allclose(pts[0], pts[-1]): pts = pts[:-1]
# yumuşat: periyodik spline (her 2. nokta ile kontrol, küçük titreşimleri ezer)
d = np.r_[0, np.cumsum(np.hypot(*np.diff(np.r_[pts, pts[:1]], axis=0).T))]
P = np.r_[pts, pts[:1]]
csx = CubicSpline(d, P[:, 0], bc_type='periodic'); csy = CubicSpline(d, P[:, 1], bc_type='periodic')
tt = np.linspace(0, d[-1], 36, endpoint=False)          # 36 kontrol noktası -> pürüzsüz
Q = np.c_[csx(tt), csy(tt)]; Q = np.r_[Q, Q[:1]]
dq = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]
c2x = CubicSpline(dq, Q[:, 0], bc_type='periodic'); c2y = CubicSpline(dq, Q[:, 1], bc_type='periodic')
ts = np.linspace(0, dq[-1], 1400, endpoint=False)
T = Polygon(np.c_[c2x(ts), c2y(ts)]).buffer(0)
b = T.bounds; T = affinity.translate(T, -b[0], -b[1]); b = T.bounds
sc = LONG / max(b[2], b[3]); T = affinity.scale(T, sc, sc, origin=(0, 0))
if T.bounds[2] > T.bounds[3]: T = affinity.rotate(T, 90, origin=(0, 0)); T = affinity.translate(T, -T.bounds[0], -T.bounds[1])
T = T.simplify(0.05)
TW, TH = T.bounds[2], T.bounds[3]

# ayak merkezi: tablanın en iç noktası değil, ağırlık merkezi (denge)
from shapely.ops import polylabel
C0 = T.centroid
C = polylabel(T.buffer(-STRIP), 0.5)  # şeritlere en uzak nokta (ayak şeride değmesin)
leg_outer = Point(C.x, C.y).buffer(D60 / 2 + 18 + 2)   # tarama paneli dışı
inner_edge = T.buffer(-STRIP)
clear = inner_edge.exterior.distance(Point(C.x, C.y)) - (D60 / 2 + 18)

# ---------------- kalınlaştırma halkası + parçalara bölme ----------------
ring = T.difference(T.buffer(-STRIP, join_style=1))
ext = LineString(T.exterior.coords); L = ext.length
def cut_line(s):
    p = ext.interpolate(s % L); q = ext.interpolate((s + 1) % L)
    tx, ty = q.x - p.x, q.y - p.y; n = math.hypot(tx, ty); nx, ny = -ty / n, tx / n
    return LineString([(p.x + nx * 150, p.y + ny * 150), (p.x - nx * 150, p.y - ny * 150)])
def layer(offset):
    cuts = unary_union([cut_line(offset + k * L / NSEG).buffer(0.01) for k in range(NSEG)])
    r = ring.difference(cuts)
    pieces = [g.buffer(0.01).buffer(-0.01) for g in getattr(r, 'geoms', [r]) if g.area > 50]
    return sorted(pieces, key=lambda g: -g.area)
start = 0.0
K1 = layer(start); K2 = layer(start + L / NSEG / 2)       # 2. kat ekleri yarım parça kaydırılmış
assert len(K1) == NSEG and len(K2) == NSEG, (len(K1), len(K2))

# ---------------- delikler ----------------
def baklava(cx, cy, r): return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (0, 90, 180, 270)]
tabla_holes = baklava(C.x, C.y, R_H60)

info = dict(tabla=(round(TW, 1), round(TH, 1)), cevre=round(L), ayak_merkez=(round(C.x, 1), round(C.y, 1)), ayak_serit_mesafe=round(clear, 1),
            parca1=[round(g.area / 1e6, 4) for g in K1], parca2=[round(g.area / 1e6, 4) for g in K2])
print(json.dumps(info))
json.dump(dict(T=list(T.exterior.coords), C=(C.x, C.y), K1=[list(g.exterior.coords) for g in K1], K2=[list(g.exterior.coords) for g in K2],
               holes=tabla_holes), open('winston_geo.json', 'w'))
