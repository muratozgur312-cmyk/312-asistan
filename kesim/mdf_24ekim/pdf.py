import pickle, json, math, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MP, Rectangle, Circle
from PIL import Image
from shapely.geometry import Point, Polygon
from shapely import affinity
from nc_all import geo, X, WIN
plates = pickle.load(open('plates_out.pkl', 'rb'))
def sure(fn):
    for l in open(fn, encoding='iso-8859-9'):
        if l.startswith(';SURE'): return l.split('=')[1].strip()
pdf = PdfPages('MDF_KESIM_PLANI_24EKIM.pdf')
fig = plt.figure(figsize=(8.27, 11.69)); fig.text(.07, .93, 'MDF KESİM PLANI — 24 Ekim', fontsize=18, weight='bold')
rows = [['EKSIKLER_PLAKA_1.anc', '2100×2800', sure('EKSIKLER_PLAKA_1.anc'), '1900×1200, Ø900/Ø700 gönyeli, kanallı oval, G taramalı panel, diskler (G taraması et 1.3 + 18 mm pay olarak düzeltildi)'],
        ['EKSIKLER_FIRE_1.anc', 'fire ~1830', sure('EKSIKLER_FIRE_1.anc'), 'U oval + 2×Ø200 + Ø100 (fotoğraftaki fire)'],
        ['MDF_1_WINSTON_BONBON.anc', '2100×2800', sure('MDF_1_WINSTON_BONBON.anc'), 'Winston Ø60/Ø39 kapaklar + kalınlaştırma + TV tabla ×2, TV/duvar karkası, alt takoz, konsol tabla 1'],
        ['MDF_2_BONBON.anc', '2100×2800', sure('MDF_2_BONBON.anc'), 'Konsol tabla 2, baza, uç paneller, 2 kapak, raf; TV kapak, dikme; EKSİK E oval + G2 taramalı panel'],
        ['MDF_3_BONBON.anc', '2100×2800', sure('MDF_3_BONBON.anc'), 'Konsol kapak 3, dikmeler ×3, raf sağ; TV kapak 2, uç paneller, dikmeler']]
ax = fig.add_axes([.05, .55, .9, .33]); ax.axis('off')
tb = ax.table(cellText=rows, colLabels=['Program', 'Plaka', 'Süre', 'İçerik'], loc='upper left', cellLoc='left', colWidths=[.27, .11, .12, .5]); tb.auto_set_font_size(False); tb.set_fontsize(7); tb.scale(1, 3.2)
fig.text(.07, .5, '\n'.join(['KESİM SIRASI (her programda):', '1) T6 V91: karkasların 45° kenarı, G2 üst kenarı (Z-0.5)', '2) T4 10 mm: tablalarda 18,5 mm cep (Z12 > Z6), konsol arkalık lambası (Z12), tarama (Z1.3, her oluk ayrı)',
    '3) T8: dübel Ø8×14 (Z4), menteşe çanağı Ø35×13, Winston delikleri, kırım çizgileri (Z1.5 — 1.5 mm et)', '4) T8 koparma: küçükten büyüğe (küçükler Z0.2 et), taramalı paneller EN SON 3 paso F3500',
    '', 'Bütün plakalarda görünen yüz AŞAĞIDA. Plaka masada oynatılmadan program bitirilsin.', 'Arkalıklar 6 mm MDF — bu programlarda yok (TV 1662×342, konsol 1462×856).',
    'Konsol 3 kapak; TV askı: TV karkası + duvar karkası 45° (duvar karkası 25 mm kısa).']), fontsize=9.5, va='top')
pdf.savefig(fig); plt.close(fig)
for name, img in (('EKSIKLER_PLAKA_1', 'p1.png'), ('EKSIKLER_FIRE_1', '../eks/fire1.png')):
    fig = plt.figure(figsize=(8.27, 11.69)); fig.text(.05, .96, name + '.anc — ' + str(sure(name + '.anc')), fontsize=13, weight='bold')
    ax = fig.add_axes([.04, .05, .92, .88]); ax.imshow(Image.open(img)); ax.axis('off'); pdf.savefig(fig); plt.close(fig)
COL = {'TABLA': '#e6d9c3', 'UC': '#f2c6b8', 'DIKME': '#d6c19a', 'KAPAK': '#c9b28c', 'KARKASI': '#8fb0c4', 'TAKOZ': '#b5a58e', 'RAF': '#ddd0b5', 'BAZA': '#a8987f', 'EKSIK': '#c7d9b0'}
for pi, pl in enumerate(plates):
    fig = plt.figure(figsize=(8.27, 11.69)); fig.text(.05, .96, pl['name'] + '.anc — ' + str(sure(pl['name'] + '.anc')), fontsize=13, weight='bold')
    ax = fig.add_axes([.06, .1, .9, .84]); ax.add_patch(Rectangle((0, 0), 2100, 2800, fc='#f7f3ec', ec='#888'))
    if pi == 0:
        for s in WIN['strips']: ax.add_patch(MP(list(s.exterior.coords), fc='#cfd8dc', ec='k', lw=.5))
        for ad, c in WIN['items']:
            r = 300 if 'D60' in ad else 195; ax.add_patch(Circle(c, r, fc='#cfd8dc' if 'D60' in ad else '#b0bec5', ec='k', lw=.5))
            ax.add_patch(Circle(c, 220 if 'D60' in ad else 125, fc='#f7f3ec', ec='k', lw=.5))
        ax.text(640, 600, 'WINSTON\nkapak Ø60/Ø39 + kalınlaştırma', ha='center', fontsize=8, weight='bold', bbox=dict(fc='white', alpha=.8, ec='none'))
    for it in pl['items']:
        p = it['p']; g = geo(it); f = X(it); key = next((k for k in COL if k in p['name']), 'TABLA')
        ax.add_patch(MP(list(g.exterior.coords), fc=COL[key], ec='k', lw=.7))
        for ln in p['pocket']: ax.plot(*zip(*[f(q) for q in ln]), c='#2e86c1', lw=1.2)
        for ln in p['lamba']: ax.plot(*zip(*[f(q) for q in ln]), c='#8e44ad', lw=2)
        for ln in p['grooves']: ax.plot(*zip(*[f(q) for q in ln]), c='#e74c3c', lw=.4)
        for ln in p['v91']: ax.plot(*zip(*[f(q) for q in ln]), c='#1f3fbf', lw=2.2)
        for q in p['drill']: ax.add_patch(Circle(f(q), 9, fc='#1e9e5c'))
        for q in p['hinge']: ax.add_patch(Circle(f(q), 17.5, fc='#e67e22'))
        b = g.bounds; ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, p['name'].replace('KONSOL', 'KONS.') + '\n%d×%d' % (round(p['poly'].bounds[2]), round(p['poly'].bounds[3])),
            ha='center', va='center', fontsize=6, weight='bold', rotation=90 if (b[3] - b[1]) > 2.2 * (b[2] - b[0]) else 0, bbox=dict(fc='white', alpha=.75, ec='none', pad=.5))
    for s in pl['fire']: ax.plot(*zip(*s), c='#1565c0', ls='--', lw=1)
    ax.set_xlim(-30, 2130); ax.set_ylim(-30, 2830); ax.set_aspect('equal'); ax.tick_params(labelsize=6)
    fig.text(.06, .03, 'Mavi çizgi: tabla cebi Z6 · Mor: arkalık lambası · Kırmızı: tarama Z1.3 · Lacivert kalın: V91 45° · Yeşil: dübel Ø8×14 · Turuncu: menteşe Ø35 · Kesikli mavi: kırım çizgisi (1.5 mm et)', fontsize=7)
    pdf.savefig(fig); plt.close(fig)
pdf.close()
