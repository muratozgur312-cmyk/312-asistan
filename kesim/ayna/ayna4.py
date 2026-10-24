import math, json, numpy as np, ezdxf
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from scipy import ndimage
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
import ayna as A
SX, SY = 1220.0, 2800.0
A.SX, A.SY = SX, SY
RING, BEV, WALL, LAP, GCLR = A.RING, A.BEV, A.WALL, A.LAP, A.GCLR
GAP = 12.0
off = A.off

def fam(kind, W, H, cx, cy):
    ch = A.chain(kind, W, H, cx, cy)
    for m in ch: m['typ'] = 'ayna'
    return ch

PLATES = {
 'AYNA4_P1_YUVARLAK': [('YUVARLAK', 900, 900, 460, 460), ('YUVARLAK', 900, 900, 460, 1382), ('YUVARLAK', 900, 900, 460, 2304)],
 'AYNA4_P2_OVAL': [('OVAL', 800, 1200, 410, 610), ('OVAL', 800, 1200, 410, 1822), ('OVAL', 380, 600, 1020, 310), ('OVAL', 380, 600, 1020, 922), ('OVAL', 380, 600, 1020, 1534), ('OVAL', 380, 600, 1020, 2146)],
 'AYNA4_P3_KAPSUL': [('KAPSUL', 590, 1380, 304, 699), ('KAPSUL', 590, 1380, 916, 699), ('KAPSUL', 590, 1380, 304, 2091), ('KAPSUL', 590, 1380, 916, 2091)],
 'AYNA4_P4_YUMUSAK_DIKDORTGEN': [('YUMUSAK', 800, 1200, 410, 610), ('YUMUSAK', 800, 1200, 410, 1822), ('YUMUSAK', 380, 600, 1020, 310), ('YUMUSAK', 380, 600, 1020, 922), ('YUMUSAK', 380, 600, 1020, 1534), ('YUMUSAK', 380, 600, 1020, 2146)],
}
GIFTS = [('MINI AYNA', 250), ('KALP', 140), ('YONCA', 140), ('KALP', 100), ('YONCA', 100)]
from shapely import affinity
def gift_shape(name, D, cx, cy):
    if name == 'KALP':
        t = np.linspace(0, 2 * np.pi, 400, endpoint=False)
        x = 16 * np.sin(t) ** 3; y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
        p = Polygon(np.c_[x, y]).buffer(0)
    else:
        t = np.linspace(0, 2 * np.pi, 400, endpoint=False)
        hx = 16 * np.sin(t) ** 3; hy = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
        h = Polygon(np.c_[0.72 * hx, hy - hy.min()]).buffer(0)   # kalp yaprak, ucu merkezde
        leaves = [affinity.rotate(h, a - 90, origin=(0, 0)) for a in (45, 135, 225, 315)]
        p = unary_union(leaves + [Point(0, 0).buffer(4)])
    b = p.bounds; sc = D / max(b[2] - b[0], b[3] - b[1])
    p = affinity.scale(affinity.translate(p, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2), sc, sc, origin=(0, 0))
    p = p.buffer(6, resolution=16).buffer(-12, resolution=16).buffer(6, resolution=16)   # ic ve dis koseler R6 (8 mm bicak + V91 uyumlu)
    return affinity.translate(p, cx, cy)
def gift_R(name, D):
    if name == 'MINI AYNA': return D / 2
    g = gift_shape(name, D, 0, 0); return max(math.hypot(x, y) for x, y in g.exterior.coords)
RES = 2.0

def zone(m):
    if m['typ'] == 'ayna': return off(m['O'], GAP).difference(off(m['O'], -(RING + GAP)))
    return off(m['O'], GAP)

def fill(items):
    free = box(10, 10, SX - 10, SY - 10).difference(unary_union([zone(m) for m in items]))
    W, H = int(SX / RES), int(SY / RES)
    gifts = []
    def raster(g):
        from matplotlib.path import Path
        im = np.zeros((H, W), bool)
        ys, xs = np.mgrid[0:H, 0:W]; pts = np.c_[(xs.ravel() + .5) * RES, (ys.ravel() + .5) * RES]
        for p in getattr(g, 'geoms', [g]):
            if p.is_empty: continue
            m = Path(np.array(p.exterior.coords)).contains_points(pts)
            for h in p.interiors: m &= ~Path(np.array(h.coords)).contains_points(pts)
            im |= m.reshape(H, W)
        return im
    mask = raster(free)
    GROUPS = [[('MINI AYNA', 250)], [('KALP', 140), ('YONCA', 140)], [('KALP', 100), ('YONCA', 100)]]
    for grp in GROUPS:
        dead = set(); i = 0
        while len(dead) < len(grp):
            name, D = grp[i % len(grp)]; i += 1
            if (name, D) in dead: continue
            R = gift_R(name, D)
            dt = ndimage.distance_transform_edt(mask) * RES
            ok = np.argwhere(dt >= R + 1)
            if not len(ok): dead.add((name, D)); continue
            k = np.lexsort((ok[:, 1], ok[:, 0]))[0]; y, x = ok[k]
            cx, cy = (x + .5) * RES, (y + .5) * RES
            if name == 'MINI AYNA':
                m = dict(kind='YUVARLAK', O=Point(cx, cy).buffer(D / 2, resolution=90), w=D, h=D, c=(cx, cy), shared=False, typ='ayna', gift=name)
            else:
                g = gift_shape(name, D, cx, cy); gb = g.bounds
                m = dict(kind='DISK', O=g, w=gb[2] - gb[0], h=gb[3] - gb[1], c=(cx, cy), shared=False, typ='disk', gift=name)
            gifts.append(m)
            yy, xx = np.mgrid[0:H, 0:W]; d2 = ((xx + .5) * RES - cx) ** 2 + ((yy + .5) * RES - cy) ** 2
            if m['typ'] == 'ayna':
                mask &= ~((d2 <= (D / 2 + GAP) ** 2) & (d2 >= (D / 2 - RING - GAP) ** 2))
            else:
                mask &= ~(d2 <= (R + GAP) ** 2)
    return gifts

F = A.F
def build(name, fams):
    chains = [fam(*f) for f in fams]
    for ch in chains:
        for k, m in enumerate(ch): m['idx'] = k
    items = [m for ch in chains for m in ch]
    gifts = fill(items)
    allp = items + gifts
    errs = []
    for m in allp:
        if not box(0, 0, SX, SY).contains(off(m['O'], 8)): errs.append('plaka disi')
    loops = []
    for ch in chains:
        for k, m in enumerate(ch):
            loops.append(A.ring_pts(off(m['O'], 4), True))
            nxt_shared = k + 1 < len(ch) and ch[k + 1]['shared']
            if not nxt_shared: loops.append(A.ring_pts(off(m['O'], -(RING + 4)), False))
    for g in gifts:
        loops.append(A.ring_pts(off(g['O'], 4), True))
        if g['typ'] == 'ayna': loops.append(A.ring_pts(off(g['O'], -(RING + 4)), False))
    SMALL = math.pi * 130 ** 2
    L = [dict(p=p, poly=Polygon(p), small=Polygon(p).area < SMALL and Polygon(p).exterior.is_ccw) for p in loops]
    for a in L:
        a['inside'] = [b for b in L if b is not a and b['poly'].area < a['poly'].area and a['poly'].contains(b['poly'].representative_point())]
    done = set(); order = []; cur = (0.0, 0.0)
    while len(order) < len(L):
        av = [a for a in L if id(a) not in done and all(id(b) in done for b in a['inside'])]
        a = min(av, key=lambda a: (not a['small'], math.dist(cur, a['p'][0])))
        order.append(a); done.add(id(a)); cur = a['p'][0]
    loops = order
    mirrors = [m for m in allp if m['typ'] == 'ayna']
    o = [';NC', ';' + name.replace('_', ' '), ';SURE_X', ';Tool=3 3 MM BICAK D3', ';Tool=6 V91 JILETBICAK ( 312 MOB ) D64', ';Tool=4 10 MM BICAK D10', ';Tool=8 ANTESAN BICAK 8 LIK Y D8',
         '#@PIECE_X=%d' % SX, '#@PIECE_Y=%d' % SY, 'E90=2', 'G79 Z0.', 'M10', '(DLY,2)', 'M12']
    t = [0.0]; cur = [(0.0, 0.0)]
    def cut(pts, z, fz, fc):
        pts = list(LineString(pts).simplify(0.05).coords)
        o.extend(['G0 X%s Y%s' % (F(pts[0][0]), F(pts[0][1])), 'G0 Z40', 'G1 X%s Y%s Z%s F%d' % (F(pts[0][0]), F(pts[0][1]), F(z), fz)])
        o.extend('G1 X%s Y%s F%d' % (F(x), F(y), fc) for x, y in pts[1:]); o.append('G0 Z40')
        t[0] += LineString(pts).length / fc + 0.03 + math.dist(cur[0], pts[0]) / 20000; cur[0] = pts[-1]
    def nn(lst, key):
        lst = lst[:]; out = []; c = (0, 0)
        while lst:
            j = min(range(len(lst)), key=lambda i: math.dist(c, key(lst[i]))); it = lst.pop(j); out.append(it); c = key(it)
        return out
    o += ['M6T3 ;Tool Name:3 MM BICAK', 'S17500 M03', 'h3']
    holes = [h for m in mirrors for h in A.hanger_holes(m['O'])]
    for x, y in nn(holes, lambda h: h):
        o += ['G0 X%s Y%s' % (F(x), F(y)), 'G0 Z40', 'G1 Z5 F800', 'G0 Z40']; t[0] += 0.03
    o.append('M5')
    o += ['M6T6 ;Tool Name:V91 JILETBICAK ( 312 MOB )', 'S16000 M03', 'h6']
    for m in nn(sorted(allp, key=lambda m: m['O'].area), lambda m: A.ring_pts(m['O'], True)[0]): cut(A.ring_pts(m['O'], True), 3.0, 1500, 6000)
    o.append('M5')
    o += ['M6T4 ;Tool Name:10 MM BICAK', 'S17500 M03', 'h4']
    for m in nn(mirrors, lambda m: A.ring_pts(m['O'], True)[0]):
        p = A.ring_pts(off(m['O'], -(BEV + WALL + LAP / 2)), True)
        cut(p, 4.0, 1500, 4000)
    o.append('M5')
    o += ['M6T8 ;Tool Name:ANTESAN BICAK 8 LIK Y', 'S16000 M03', 'h8']
    for a in loops:
        cut(a['p'], 5.0, 1500, 6000)
        cut(a['p'], 0.2 if a['small'] else -0.2, 1500, 4000)
    o += ['M5', 'M11', 'M13', 'G0 G79 Z0.', 'M14', ';Cut Time ~%d dk' % math.ceil(t[0] + 2)]
    open('v4/' + name + '.anc', 'w', newline='').write('\r\n'.join(o).replace(';SURE_X', ';SURE ~%d dk' % math.ceil(t[0] + 2)) + '\r\n')
    doc = ezdxf.new('R2010'); ms = doc.modelspace()
    for l, c in (('DIS_KENAR_V91_Z3', 1), ('LAMBA_T4_Z4', 3), ('ACIKLIK', 5), ('CAM_SABLON', 4), ('ASKI_DELIK', 6)): doc.layers.add(l, color=c)
    rows = []
    for m in allp:
        ms.add_lwpolyline(list(m['O'].exterior.coords), close=True, dxfattribs={'layer': 'DIS_KENAR_V91_Z3'})
        if m['typ'] == 'ayna':
            ms.add_lwpolyline(list(off(m['O'], -(BEV + WALL)).exterior.coords), close=True, dxfattribs={'layer': 'LAMBA_T4_Z4'})
            ms.add_lwpolyline(list(off(m['O'], -RING).exterior.coords), close=True, dxfattribs={'layer': 'ACIKLIK'})
            g = off(m['O'], -(BEV + WALL + GCLR)); gb = g.bounds
            ms.add_lwpolyline(list(g.exterior.coords), close=True, dxfattribs={'layer': 'CAM_SABLON'})
            for x, y in A.hanger_holes(m['O']): ms.add_circle((x, y), 1.5, dxfattribs={'layer': 'ASKI_DELIK'})
            rows.append(dict(model=m.get('gift') or A.ADI[m['kind']], w=round(m['w']), h=round(m['h']), gw=round(gb[2] - gb[0]), gh=round(gb[3] - gb[1])))
        else:
            rows.append(dict(model='%s %d' % (m['gift'], round(max(m['w'], m['h']) / 10)), w=round(m['w']), h=round(m['h']), gw=0, gh=0))
    doc.saveas('v4/' + name + '.dxf')
    return chains, gifts, rows, errs, t[0] + 2

if __name__ == '__main__':
    res = {}
    fig, axs = plt.subplots(1, 4, figsize=(20, 12.5))
    col = {'KALP': '#c9a24a', 'YONCA': '#e2c46e'}
    for ax, (name, fams) in zip(axs, PLATES.items()):
        chains, gifts, rows, errs, tm = build(name, fams); res[name] = rows
        ax.add_patch(MP([(0, 0), (SX, 0), (SX, SY), (0, SY)], fc='#3a3a3a', ec='k'))
        for m in [m for ch in chains for m in ch] + gifts:
            if m['typ'] == 'ayna':
                r = m['O'].difference(off(m['O'], -RING))
                for g in getattr(r, 'geoms', [r]):
                    ax.add_patch(MP(list(g.exterior.coords), fc='#d4b26a', ec='#7a5f22', lw=.4))
                    for h in g.interiors: ax.add_patch(MP(list(h.coords), fc='#cfd8dc', ec='#7a5f22', lw=.4))
                b = m['O'].bounds
                if 'gift' not in m: ax.text((b[0] + b[2]) / 2, b[3] - 14, ('Ø%d' % round(m['w'] / 10)) if m['kind'] == 'YUVARLAK' else '%dx%d' % (round(m['w'] / 10), round(m['h'] / 10)), ha='center', va='top', fontsize=5.5)
                else: ax.text(*m['c'], 'mini\nØ25', ha='center', va='center', fontsize=5)
            else:
                ax.add_patch(MP(list(m['O'].exterior.coords), fc=col[m['gift']], ec='#7a5f22', lw=.4))
                ax.text(*m['c'], '%s\n%d' % ('K' if m['gift'] == 'KALP' else 'Y', round(max(m['w'], m['h']) / 10)), ha='center', va='center', fontsize=5)
        nA = sum(1 for r in rows if r['gw'] and r['model'] != 'MINI AYNA'); nm = sum(1 for r in rows if r['model'] == 'MINI AYNA')
        nM = sum(1 for r in rows if r['model'].startswith('KALP')); nB = sum(1 for r in rows if r['model'].startswith('YONCA'))
        ax.set_title('%s\n%d ayna + %d mini ayna + %d kalp + %d yonca\n~%d dk' % (name.replace('AYNA4_', '').replace('_', ' '), nA, nm, nM, nB, tm), fontsize=9)
        ax.set_xlim(-10, SX + 10); ax.set_ylim(-10, SY + 10); ax.set_aspect('equal'); ax.axis('off')
        print(name, nA, nm, nM, nB, 'hata', errs, round(tm))
    plt.suptitle('312 INTERIORS · ince halka ayna · 1220x2800x10 altin laminat · K = kalp altlik, Y = yonca altlik (14 / 10 cm)', fontsize=12)
    plt.tight_layout(); plt.savefig('v4/AYNA4_PLAKALAR.png', dpi=110)
    json.dump(res, open('v4/liste.json', 'w'))
