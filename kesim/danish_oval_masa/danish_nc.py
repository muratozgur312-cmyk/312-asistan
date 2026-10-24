import math, ezdxf, numpy as np
from shapely.geometry import Point, Polygon, box, LineString
from shapely import affinity
from ncbase import NC, ccw, off, F
import importlib.util, sys
L, W = 1800.0, 900.0
LEG_X, R_DEL, DEL_Z = 400.0, 215.0, 4.0     # 2 ayak ±400, baklava 430 (R215), Ø10x14 -> Z4
PW, PH = 2100.0, 2800.0
def shape(L, W):
    k = L / 1400; a, b = L / 2, W / 2; h = 245 * k; e = 35 * k; r = 110 * k
    s = b - h; Rs = (a * a + s * s) / (2 * s); Re = (h * h + e * e) / (2 * e); res = 4096
    p = Point(0, b - Rs).buffer(Rs, resolution=res).intersection(Point(0, -b + Rs).buffer(Rs, resolution=res))
    p = p.intersection(Point(a - Re, 0).buffer(Re, resolution=res)).intersection(Point(-a + Re, 0).buffer(Re, resolution=res))
    return p.buffer(-r, resolution=256).buffer(r, resolution=256).simplify(0.05)
T0 = shape(L, W)                                       # ürün koordinatı: merkez 0,0, uzun eksen X
holes0 = [(sx * LEG_X + R_DEL * math.cos(math.radians(a)), R_DEL * math.sin(math.radians(a))) for sx in (-1, 1) for a in (0, 90, 180, 270)]
# plakada: uzun kenar Y boyunca (meşe kaplama su yönü), sol-alt
OX, OY = 40 + W / 2, 40 + L / 2
T = affinity.translate(affinity.rotate(T0, 90, origin=(0, 0)), OX, OY)
holes = [(OX - y, OY + x) for x, y in holes0]
assert all(T.buffer(-60).contains(Point(p)) for p in holes)
nc = NC('DANISH_OVAL_MASA_180x90_MESE')
nc.tc(4, 'MATKAP DEL 10 LUK ', 17500)
# kısa yol: önce bir ayağın 4 deliği, sonra diğerinin
for x, y in sorted(holes, key=lambda p: (p[1] > OY, p[0] + p[1])): nc.drill(x, y, DEL_Z, 2000)
nc.tc(6, 'V91 JİLETBICAK ( 312 MOB )', 16000)
nc.path(ccw(T), 4.0, 6000)                                  # V91 net hattan, 14 mm dalış (Z4)
nc.tc(8, 'ANTESAN BÇK 8 LIK Y', 16000)
nc.path(ccw(off(T, 4)), 0.0, 5000)                           # pahlı kontur: tek paso Z0
mm = nc.save([(4, 'MATKAP DEL 10 LUK ', 10), (6, 'V91 JİLETBICAK ( 312 MOB )', 64), (8, 'ANTESAN BÇK 8 LIK Y', 8)],
             '18 MM MESE KAPLAMA - DANISH OVAL MASA 1800x900 (GORUNEN YUZ ASAGIDA) V91 PAH 14 + AYAK DELIK D10x14')
print('süre', mm, 'dk', 'tabla', [round(v, 1) for v in T.bounds], 'boş X', round(PW - T.bounds[2] - 40))
def dxf(fn, layers):
    d = ezdxf.new('R2010', setup=True); d.units = ezdxf.units.MM; m = d.modelspace()
    for ln, col, gs in layers:
        d.layers.add(ln, color=col)
        for g in gs:
            if isinstance(g, tuple): m.add_circle(g, 5.0, dxfattribs={'layer': ln})
            else: m.add_lwpolyline(list(g.exterior.coords)[:-1], close=True, dxfattribs={'layer': ln})
    d.saveas(fn)
dxf('DANISH_OVAL_MASA_180x90_MESE_PLAKA.dxf', [('PLAKA', 8, [box(0, 0, PW, PH)]), ('TABLA_NET_V91_Z4', 1, [T]),
    ('KESIM_T8_DIS4', 5, [off(T, 4)]), ('AYAK_DELIK_D10x14', 6, holes)])
dxf('DANISH_OVAL_MASA_180x90_KUTUPHANE.dxf', [('TABLA', 1, [affinity.translate(T0, L / 2, W / 2)]), ('PAH_V91_ALT_14', 3, [affinity.translate(T0.buffer(-14.3), L / 2, W / 2)]),
    ('AYAK_DELIK_D10x14', 6, [(x + L / 2, y + W / 2) for x, y in holes0])])
import json; json.dump(dict(T=list(T.exterior.coords), holes=holes, T0=list(T0.exterior.coords), holes0=holes0), open('danish_geo.json', 'w'))
