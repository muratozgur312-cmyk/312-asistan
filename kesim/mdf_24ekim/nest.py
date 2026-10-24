import json, math, pickle, numpy as np
from shapely.geometry import Point, box, Polygon
from shapely.ops import unary_union
from shapely import affinity
from scipy.signal import fftconvolve
from PIL import Image, ImageDraw
from parts import bonbon_parts, eksik_parts
PW, PH, RES = 2100.0, 2800.0, 5.0
def margin(p):
    if p['v91']: return 22
    if p['tarama']: return 16
    return 7
W_ = int(PW / RES); H_ = int(PH / RES)
def raster(poly, ox, oy, w, h):
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    for q in getattr(poly, 'geoms', [poly]): d.polygon([((x - ox) / RES, (y - oy) / RES) for x, y in q.exterior.coords], fill=1)
    return np.array(im, np.float32)
# Winston plakasındaki dolu bölge
wn = json.load(open('../win/winston_nest.json'))
wocc = [Polygon(c).buffer(8 + 7) for _, c in wn['placed']] + [Point(*c).buffer(300 + 8 + 7) for ad, c in wn['items'] if 'D60' in ad]
plates = [dict(name='MDF_1_WINSTON_BONBON', occ=unary_union(wocc), items=[]), dict(name='MDF_2_BONBON', occ=None, items=[]), dict(name='MDF_3_BONBON', occ=None, items=[])]
for pl in plates:
    blk = raster(pl['occ'], 0, 0, W_, H_) if pl['occ'] is not None else np.zeros((H_, W_), np.float32)
    m = int(12 / RES); blk[:m] = 1; blk[-m:] = 1; blk[:, :m] = 1; blk[:, -m:] = 1; pl['blk'] = blk
b, tv, k = bonbon_parts(); parts = b + eksik_parts()
parts.sort(key=lambda p: -max(p['poly'].bounds[2] - p['poly'].bounds[0], p['poly'].bounds[3] - p['poly'].bounds[1]) * 1e4 - p['poly'].area / 100)
for p in parts:
    done = False
    for pl in plates:
        best = None
        for rot in (0, 90, 180, 270):
            g = affinity.rotate(p['poly'], rot, origin=(0, 0)); s = g.buffer(margin(p) + 4, join_style=2); bb = s.bounds
            pm = raster(s, bb[0], bb[1], int(math.ceil((bb[2] - bb[0]) / RES)) + 1, int(math.ceil((bb[3] - bb[1]) / RES)) + 1)
            if pm.shape[0] >= H_ or pm.shape[1] >= W_: continue
            ok = np.argwhere(fftconvolve(pl['blk'], pm[::-1, ::-1], mode='valid') < 0.5)
            if not len(ok): continue
            kk = np.lexsort((ok[:, 1], ok[:, 0]))[0]; yy, xx = ok[kk]
            dx, dy = xx * RES - bb[0], yy * RES - bb[1]
            key = (dy + bb[1], dx + bb[0])
            if best is None or key < best[0]: best = (key, rot, dx, dy, s)
        if best:
            _, rot, dx, dy, s = best
            pl['items'].append(dict(p=p, rot=rot, dx=dx, dy=dy))
            pl['blk'] = np.maximum(pl['blk'], raster(affinity.translate(s, dx, dy).buffer(RES), 0, 0, W_, H_)); done = True; break
    if not done: print('SIĞMADI', p['name'])
for pl in plates: print(pl['name'], len(pl['items']), [i['p']['name'] for i in pl['items']])
pickle.dump([dict(name=pl['name'], items=pl['items']) for pl in plates], open('nest.pkl', 'wb'))
pickle.dump((tv, k), open('specs.pkl', 'wb'))
