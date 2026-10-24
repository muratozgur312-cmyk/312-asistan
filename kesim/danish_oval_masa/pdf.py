import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
g = json.load(open('danish_geo.json'))
pdf = PdfPages('DANISH_OVAL_MASA_180x90_PLAN.pdf')
# 1) ürün + delikler + kesit
fig = plt.figure(figsize=(11.69, 8.27)); ax = fig.add_axes([0.04, 0.30, 0.92, 0.60])
T0 = np.array(g['T0']); ax.fill(T0[:, 0], T0[:, 1], fc='#c9a77c', ec='#5a3e1b', lw=2)
from shapely.geometry import Polygon
P = Polygon(T0).buffer(-14.3); ax.plot(*P.exterior.xy, ls='--', c='#5a3e1b', lw=.8)
for x, y in g['holes0']: ax.add_patch(plt.Circle((x, y), 5, fc='k'))
for sx in (-400, 400):
    ax.add_patch(plt.Circle((sx, 0), 215, fill=False, ls=':', ec='#444'))
    ax.text(sx, -250, 'ayak %+d\nbaklava 430 (R215)\n4× Ø10×14' % sx, ha='center', va='top', fontsize=8)
ax.annotate('', (-900, -520), (900, -520), arrowprops=dict(arrowstyle='<->')); ax.text(0, -560, '1800', ha='center', va='top', fontsize=12, weight='bold')
ax.annotate('', (960, -450), (960, 450), arrowprops=dict(arrowstyle='<->')); ax.text(990, 0, '900', rotation=90, va='center', fontsize=12, weight='bold')
ax.annotate('', (-400, 300), (400, 300), arrowprops=dict(arrowstyle='<->')); ax.text(0, 315, '800 (ayak merkezleri)', ha='center', fontsize=9)
ax.set_xlim(-950, 1050); ax.set_ylim(-640, 480); ax.set_aspect('equal'); ax.axis('off')
fig.text(.04, .94, 'DANISH OVAL MASA 180 × 90 — 18 mm meşe kaplama — üstten görünüş (tabla altı delikleri)', fontsize=15, weight='bold')
ax2 = fig.add_axes([0.06, 0.04, 0.28, 0.2]); ax2.fill([0, 60, 60, 14, 0], [18, 18, 0, 0, 14], fc='#c9a77c', ec='k'); ax2.plot([0, 14], [14, 0], c='r', lw=1.5)
ax2.text(-3, 16, '4 mm\ngörünen', ha='right', va='center', fontsize=8); ax2.text(9, -1, '14 mm V91 pah (altta)', fontsize=8, va='top')
ax2.set_xlim(-25, 65); ax2.set_ylim(-4, 26); ax2.set_aspect('equal'); ax2.axis('off'); ax2.set_title('Kenar kesiti (masa normal duruşta)', fontsize=9)
fig.text(.40, .05, 'Kenar: V91 ile alttan 14 mm pah, üstte 4 mm görünen kenar. Kalınlaştırma YOK.\n'
         'Ayak delikleri her zaman standart: 2 ayak ±400, her biri 4 delik baklava 430, Ø10 × 14 mm (alttan; üstte 4 mm sağlam).\n'
         'Spider tek ayak bu siparişte; delikler ileride Como/Tweety 2 ayak isteyen müşteri için de hazır.', fontsize=9)
pdf.savefig(fig); plt.close(fig)
# 2) plaka
fig = plt.figure(figsize=(8.27, 11.69)); ax = fig.add_axes([0.03, 0.14, 0.94, 0.80]); ax.axis('off'); ax.imshow(Image.open('plaka.png'))
fig.text(.05, .95, 'PLAKA 2100 × 2800 — DANISH_OVAL_MASA_180x90_MESE.anc (~4.5 dk)', fontsize=12, weight='bold')
fig.text(.05, .04, 'GÖRÜNEN YÜZ AŞAĞIDA. Tabla dikine (uzun kenar Y, kaplama su yönünde), sol-alt köşede.\n'
         'Sıra: T4 ayak delikleri Z4 (8 adet) > T6 V91 net hattan Z4 (14 mm pah) > T8 4 mm dıştan tek paso Z0.\n'
         'Sağda ~1120 × 2800 boş: diğer meşe parçaları buraya yerleşecek (nesting).', fontsize=9)
pdf.savefig(fig); plt.close(fig); pdf.close()
