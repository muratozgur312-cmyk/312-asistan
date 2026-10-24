import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
def polar(f, n=360):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); r = f(t); return Polygon(np.c_[r * np.cos(t), r * np.sin(t)])
def norm(p):
    p = p.buffer(0); b = p.bounds; s = 1.0 / max(b[2] - b[0], b[3] - b[1])
    p = affinity.scale(p, s, s, origin=(0, 0)); c = p.centroid; return affinity.translate(p, -c.x, -c.y)
def soft(p, r): return p.buffer(-r, resolution=24).buffer(2 * r, resolution=24).buffer(-r, resolution=24)
S = {}
t = None
S['01'] = norm(polar(lambda t: 1 / np.sqrt((np.cos(t) / 1.0) ** 2 + (np.sin(t) / (0.62 * (1 + 0.08 * np.cos(t)))) ** 2)))   # yumurta oval
S['02'] = norm(LineString([(-0.28, 0), (0.28, 0)]).buffer(0.22, resolution=48))                                       # kapsül
S['03'] = norm(box(-0.5, -0.31, 0.5, 0.31).buffer(-0.1).buffer(0.1, resolution=24))                                   # yumuşak dikdörtgen
S['04'] = norm(polar(lambda t: 1 + 0.16 * np.cos(2 * t + 0.5) + 0.07 * np.cos(3 * t + 2.2)))                          # çakıl
k5 = polar(lambda t: 1 + 0.18 * np.cos(2 * t))
S['05'] = norm(soft(k5.difference(Point(0.2, -1.55).buffer(0.85, resolution=64)), 0.18))                              # böbrek
S['13'] = norm(soft(unary_union([Point(-0.25, 0).buffer(0.42, resolution=48), Point(0.3, -0.05).buffer(0.2, resolution=48)]).convex_hull, 0.05))  # damla
S['14'] = norm(Polygon([(-0.5, -0.36), (0.5, -0.36), (0.05, 0.5)]).buffer(-0.08).buffer(0.17, resolution=32))        # yuvarlak üçgen
S['17'] = norm(soft(unary_union([Point(-0.24, 0).buffer(0.26, resolution=48), Point(0.24, 0).buffer(0.26, resolution=48)]), 0.13))  # fıstık
S['18'] = norm(soft(affinity.skew(Point(0, -0.45).buffer(0.75, resolution=64).intersection(Point(0, 0.45).buffer(0.75, resolution=64)), 0, 0), 0.06))  # yaprak
S['16'] = norm(polar(lambda t: (np.abs(np.cos(t)) ** 4 + np.abs(np.sin(t) / 0.92) ** 4) ** -0.25))                     # squircle
S['24'] = norm(polar(lambda t: 1 / np.sqrt(np.cos(t) ** 2 + (np.sin(t) / 0.5) ** 2)))                                  # set: büyük oval
NAMES = {'01': 'Oval', '02': 'Kapsül', '03': 'Dikdörtgen', '04': 'Çakıl', '05': 'Böbrek', '13': 'Damla', '14': 'Üçgen', '17': 'Fıstık', '18': 'Yaprak', '16': 'Kare', '24': 'Elips'}
if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(3, 4, figsize=(10, 7))
    for ax, (k, p) in zip(axs.flat, S.items()):
        ax.fill(*p.exterior.xy, fc='#5a3a22'); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(k + ' ' + NAMES[k])
    axs.flat[-1].axis('off'); plt.tight_layout(); plt.savefig('shapes.png', dpi=60)
