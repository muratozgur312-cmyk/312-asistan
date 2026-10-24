import json, math, numpy as np, ezdxf
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
from shapely.prepared import prep
G = json.load(open('winston_geo.json'))
T = Polygon(G['T']); C = Point(*G['C'])
K = [('K1-%d' % (i + 1), Polygon(p)) for i, p in enumerate(G['K1'])] + [('K2-%d' % (i + 1), Polygon(p)) for i, p in enumerate(G['K2'])]
PW, PH, M, GAP = 2100.0, 2800.0, 10.0, 20.0
D60, H60, D39, H39, R_H60, R_H39 = 600.0, 440.0, 390.0, 250.0, 260.0, 155.0
AYAK_H, ET = 382.0, 1.1
F = lambda v: ('%.3f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'

def ccw(p, want=True):
    c = list(p.exterior.coords)
    if Polygon(c).exterior.is_ccw != want: c = c[::-1]
    return c
def off(p, d): return p.buffer(d, resolution=64, join_style=1)

class NC:
    def __init__(s, name): s.name = name; s.o = []; s.t = 0.0; s.cur = (0.0, 0.0); s.tool = None
    def tc(s, t, name, rpm):
        if s.tool is not None: s.o.append('M5')
        s.o += ['M6T%d ;Tool Name:%s' % (t, name), 'S%d M03' % rpm, 'h%d' % t]; s.tool = t
    def path(s, pts, z, fc, fz=2000, closed=True):
        pts = list(LineString(pts).simplify(0.03).coords)
        s.o += ['G0 X%s Y%s' % (F(pts[0][0]), F(pts[0][1])), 'G0 Z40', 'G1 Z%s F%d' % (F(z), fz)]
        s.o += ['G1 X%s Y%s Z%s F%d' % (F(x), F(y), F(z), fc) for x, y in pts[1:]]
        s.o.append('G0 Z40')
        s.t += LineString(pts).length / fc + math.dist(s.cur, pts[0]) / 25000 + 0.04; s.cur = pts[-1]
    def drill(s, x, y, z, fz=1500):
        s.o += ['G0 X%s Y%s' % (F(x), F(y)), 'G0 Z40', 'G1 Z%s F%d' % (F(z), fz), 'G0 Z40']; s.t += 0.05 + math.dist(s.cur, (x, y)) / 25000; s.cur = (x, y)
    def save(s, tools, desc):
        dk = s.t + 2; mm = int(dk); ss = int((dk - mm) * 60)
        head = [';NC', ';' + s.name, ';' + desc, ';SURE = %dDK %dSN' % (mm, ss)] + [';Tool=%d, Name=%s, Diameter=%s' % t for t in tools] + \
               ['#@PIECE_X=2100', '#@PIECE_Y=2800', 'E90=2']
        body = ['G79 Z0.', 'M10', '(DLY,2)', 'M12'] + s.o + ['M5', 'M11', 'M13', 'G0 G79 Z0.', 'M14']
        n = 0; out = []
        for l in body:
            if l.startswith('('): out.append(l); continue
            n += 1; out.append('N%d %s' % (n, l))
        open(s.name + '.anc', 'w', encoding='iso-8859-9', newline='').write('\r\n'.join(head + out + ['', ';Cut Time=%dMins %dSecs' % (mm, ss)]) + '\r\n')
        return mm

# =============== 1) MDF PLAKA: kapaklar + kalınlaştırma ===============
items = []   # (ad, polygon(net), extra)
cx1 = M + 4 + D60 / 2 + 4; cy1 = cx1
cx2 = cx1 + D60 + 8 + GAP
for i, (x, y) in enumerate(((cx1, cy1), (cx2, cy1))):
    items.append(dict(ad='KAPAK_D60_%d' % (i + 1), O=Point(x, y).buffer(D60 / 2, 256), I=Point(x, y).buffer(H60 / 2, 256), c=(x, y), r_h=R_H60))
    items.append(dict(ad='KAPAK_D39_%d' % (i + 1), O=Point(x, y).buffer(D39 / 2, 256), I=Point(x, y).buffer(H39 / 2, 256), c=(x, y), r_h=R_H39))
occ = unary_union([off(it['O'], 4 + GAP / 2) for it in items if it['ad'].startswith('KAPAK_D60')])
plate = box(M, M, PW - M, PH - M)
placed = []
for ad, g in sorted(K, key=lambda kv: -kv[1].area):
    mr = g.minimum_rotated_rectangle; cc = list(mr.exterior.coords)
    ang = math.degrees(math.atan2(cc[1][1] - cc[0][1], cc[1][0] - cc[0][0]))
    best = None
    for a in (-ang, -ang + 90, -ang + 180, -ang + 270):
        h = affinity.rotate(g, a, origin='centroid'); sw = off(h, 4 + GAP / 2); b = sw.bounds
        po = prep(occ)
        for y in np.arange(M - b[1] + 0, PH - M - b[3] + 1e-6 - 0, 10):
            if best and y + b[1] > best[0] + 1e-6: break
            found = None
            for x in np.arange(M - b[0], PW - M - b[2] + 1e-6, 10):
                cand = affinity.translate(sw, x, y)
                if not po.intersects(cand): found = x; break
            if found is not None:
                key = (y + b[1], found + b[0])
                if best is None or key < best[:2]: best = (key[0], key[1], a, found, y)
                break
    _, _, a, x, y = best
    h = affinity.translate(affinity.rotate(g, a, origin='centroid'), x, y)
    placed.append(dict(ad=ad, O=h, rot=a)); occ = occ.union(off(h, 4 + GAP / 2))
allsw = unary_union([off(it['O'], 4) for it in items] + [off(p['O'], 4) for p in placed])
print('MDF kapsam', [round(v) for v in allsw.bounds], 'plaka içinde', plate.buffer(M - 1).contains(allsw))

nc = NC('WINSTON_MDF_KAPAK_KALINLASTIRMA')
nc.tc(8, 'ANTESAN BÇK 8 LIK Y', 16000)
holes = [h for it in items for h in [(it['c'][0] + it['r_h'] * math.cos(math.radians(a)), it['c'][1] + it['r_h'] * math.sin(math.radians(a))) for a in (0, 90, 180, 270)]]
for x, y in holes: nc.drill(x, y, 0.0, 1000)
# içten dışa: Ø39 iç boşluk > Ø39 dış > Ø60 iç boşluk > şeritler (küçükten büyüğe) > Ø60 dış
for it in [i for i in items if 'D39' in i['ad']]:
    p = ccw(off(it['I'], -4), False)
    for z in (9.0, 0.0): nc.path(p, z, 7000)
for it in [i for i in items if 'D39' in i['ad']]:
    p = ccw(off(it['O'], 4))
    for z in (9.0, 0.2): nc.path(p, z, 7000 if z > 1 else 4500)
for it in [i for i in items if 'D60' in i['ad']]:
    p = ccw(off(it['I'], -4), False)
    for z in (9.0, 0.0): nc.path(p, z, 7000)
rest = sorted(placed, key=lambda q: q['O'].area); cur = nc.cur
while rest:
    q = min(rest, key=lambda q: math.dist(nc.cur, ccw(off(q['O'], 4))[0])); rest.remove(q)
    p = ccw(off(q['O'], 4))
    for z in (9.0, 0.2): nc.path(p, z, 7000 if z > 1 else 4500)
for it in [i for i in items if 'D60' in i['ad']]:
    p = ccw(off(it['O'], 4))
    for z in (9.0, 0.0): nc.path(p, z, 7000 if z > 1 else 5000)
m1 = nc.save([(8, 'ANTESAN BÇK 8 LIK Y', 8)], '18 MM MDF 2100x2800 - WINSTON KAPAK D60x2 + D39x2 (STOK) + KALINLASTIRMA 2 KAT x5')

# =============== 2) MEŞE: tabla + ayak tarama paneli ===============
PL = round(math.pi * (D60 + 2 * ET))          # panel boyu (Komu formülü: Ø390 -> 1233)
EDGE = 18 + 5                                 # 18 mm kenar payı + 10 mm bıçak yarıçapı = ilk/son oluk merkezi
nG = round((PL - 2 * EDGE) / 20); pitch = (PL - 2 * EDGE) / nG
tb = T.bounds
Tm = affinity.translate(T, M + 4 + 4 - tb[0], M + 4 + 4 - tb[1])   # tabla sol-alt
Cm = (C.x + M + 8 - tb[0], C.y + M + 8 - tb[1])
th = [(Cm[0] + R_H60 * math.cos(math.radians(a)), Cm[1] + R_H60 * math.sin(math.radians(a))) for a in (0, 90, 180, 270)]
px0 = Tm.bounds[2] + 8 + GAP + 15 + 6         # panel DİKİNE (kaplama su yönü), tablanın sağında
py0 = M + 8
panel = box(px0, py0, px0 + AYAK_H, py0 + PL)
print('MESE panel', PL, 'oluk', nG + 1, 'aralık', round(pitch, 3), 'panel sağ', round(px0 + AYAK_H + 15 + 5), 'panel üst', round(py0 + PL + 8), 'tabla', [round(v) for v in Tm.bounds])
assert px0 + AYAK_H + 15 + 5 < PW - M and py0 + PL + 8 < PH - M
ms = NC('WINSTON_MESE_TABLA_TARAMA')
ms.tc(3, '3 MM BICAK', 17500)
for x, y in th: ms.drill(x, y, 6.0, 800)                      # Ø3 x 12 vida kılavuz (tabla altı)
ms.tc(4, 'MATKAP DEL 10 LUK ', 17500)
for k in range(nG + 1):
    y = py0 + EDGE + k * pitch; a, bb = (px0 - 15, px0 + AYAK_H + 15) if k % 2 == 0 else (px0 + AYAK_H + 15, px0 - 15)
    ms.path([(a, y), (bb, y)], ET, 6000, closed=False)
ms.tc(8, 'ANTESAN BÇK 8 LIK Y', 16000)
for z in (9.0, 0.0): ms.path(ccw(off(Tm, 4)), z, 7000 if z > 1 else 5000)
for z in (12.0, 6.0, 0.0): ms.path(ccw(off(panel, 4).envelope if False else box(*off(panel, 4).bounds)), z, 3500)
m2 = ms.save([(3, '3 MM BICAK', 3), (4, 'MATKAP DEL 10 LUK ', 10), (8, 'ANTESAN BÇK 8 LIK Y', 8)], '18 MM MESE KAPLAMA - WINSTON TABLA (GORUNEN YUZ ASAGIDA) + AYAK TARAMA %dx%d DIKINE' % (AYAK_H, PL))
print('süre MDF', m1, 'dk  MESE', m2, 'dk')

# =============== DXF'ler ===============
def dxf_plate(fn, layers):
    doc = ezdxf.new('R2010'); msp = doc.modelspace()
    for ln, col, geoms in layers:
        doc.layers.add(ln, color=col)
        for g in geoms:
            if isinstance(g, tuple): msp.add_circle(g[0], g[1], dxfattribs={'layer': ln}); continue
            if isinstance(g, LineString): msp.add_lwpolyline(list(g.coords), dxfattribs={'layer': ln}); continue
            msp.add_lwpolyline(list(g.exterior.coords), close=True, dxfattribs={'layer': ln})
            for h in g.interiors: msp.add_lwpolyline(list(h.coords), close=True, dxfattribs={'layer': ln})
    doc.saveas(fn)
dxf_plate('WINSTON_MDF_KAPAK_KALINLASTIRMA.dxf', [
    ('PLAKA', 8, [box(0, 0, PW, PH)]),
    ('KAPAK_D60', 1, [it['O'] for it in items if 'D60' in it['ad']] + [it['I'] for it in items if 'D60' in it['ad']]),
    ('KAPAK_D39_STOK', 3, [it['O'] for it in items if 'D39' in it['ad']] + [it['I'] for it in items if 'D39' in it['ad']]),
    ('DELIK_D8', 6, [((x, y), 4.0) for x, y in holes]),
    ('KALINLASTIRMA', 5, [p['O'] for p in placed])])
for p in placed:
    pass
dxf_plate('WINSTON_MESE_TABLA_TARAMA.dxf', [
    ('PLAKA', 8, [box(0, 0, PW, PH)]), ('TABLA', 1, [Tm]), ('VIDA_D3x12', 6, [((x, y), 1.5) for x, y in th]),
    ('TARAMA_PANEL', 5, [panel]), ('TARAMA_OLUK_Z1.1', 3, [LineString([(px0 - 15, py0 + EDGE + k * pitch), (px0 + AYAK_H + 15, py0 + EDGE + k * pitch)]) for k in range(nG + 1)])])
# kütüphane: ürün geometrisi (tabla koordinatında, alttan bakış)
dxf_plate('WINSTON_ORTA_SEHPA_KUTUPHANE.dxf', [
    ('TABLA_1300', 1, [T]), ('KALINLASTIRMA_KAT1', 5, [g for a, g in K if a.startswith('K1')]), ('KALINLASTIRMA_KAT2', 4, [g for a, g in K if a.startswith('K2')]),
    ('AYAK_D60_KAPAK', 3, [Point(C.x, C.y).buffer(D60 / 2, 256)]), ('AYAK_DIS_D636', 2, [Point(C.x, C.y).buffer(D60 / 2 + 18, 256)]),
    ('VIDA_DELIK', 6, [((C.x + R_H60 * math.cos(math.radians(a)), C.y + R_H60 * math.sin(math.radians(a))), 1.5) for a in (0, 90, 180, 270)])])
json.dump(dict(placed=[(p['ad'], list(p['O'].exterior.coords)) for p in placed], items=[(it['ad'], it['c']) for it in items],
               Tm=list(Tm.exterior.coords), panel=list(panel.exterior.coords), PL=PL, nG=nG), open('winston_nest.json', 'w'))
