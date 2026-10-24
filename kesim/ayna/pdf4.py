import json, ezdxf, collections, math
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MP
from shapely.geometry import Polygon
from PIL import Image
import numpy as np
d = json.load(open('v4/liste.json'))
SX, SY = 1220, 2800
TR = {'Yuvarlak': 'Yuvarlak ayna', 'Oval': 'Oval ayna', 'Kapsul': 'Kapsül ayna', 'Yumusak dikdortgen': 'Yumuşak dikdörtgen ayna', 'MINI AYNA': 'Mini ayna'}
def lab(r):
    m = r['model']
    if m.startswith('KALP') or m.startswith('YONCA'):
        n, s = m.split(); return ('Kalp altlık' if n == 'KALP' else 'Yonca altlık') + ' %s cm' % s
    if r['w'] == r['h']: return '%s Ø%d' % (TR.get(m, m), round(r['w'] / 10))
    return '%s %d×%d' % (TR.get(m, m), round(r['w'] / 10), round(r['h'] / 10))
pdf = PdfPages('v4/AYNA_HEDIYELIK_PLAN.pdf')
fig = plt.figure(figsize=(11.69, 8.27)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
ax.imshow(Image.open('v4/AYNA4_PLAKALAR.png'))
pdf.savefig(fig); plt.close(fig)
tot = collections.Counter()
for name, rows in d.items():
    doc = ezdxf.readfile('v4/%s.dxf' % name); ms = doc.modelspace()
    outs = [e for e in ms if e.dxf.layer == 'DIS_KENAR_V91_Z3']
    opens = [Polygon([p[:2] for p in e.get_points()]) for e in ms if e.dxf.layer == 'ACIKLIK']
    fig = plt.figure(figsize=(8.27, 11.69)); ax = fig.add_axes([0.03, 0.05, 0.55, 0.88])
    ax.add_patch(MP([(0, 0), (SX, 0), (SX, SY), (0, SY)], fc='#3a3a3a', ec='k'))
    cnt = collections.Counter()
    for e, r in zip(outs, rows):
        P = Polygon([p[:2] for p in e.get_points()])
        isg = r['model'].startswith('KALP') or r['model'].startswith('YONCA')
        ax.add_patch(MP(list(P.exterior.coords), fc='#d4b26a' if not isg else ('#c9a24a' if r['model'].startswith('KALP') else '#e2c46e'), ec='#6b5320', lw=.4))
        if not isg:
            ins = [o for o in opens if P.contains(o.representative_point()) and o.area < P.area and o.area > P.area * 0.5]
            if ins: ax.add_patch(MP(list(ins[0].exterior.coords), fc='#cfd8dc', ec='#6b5320', lw=.3))
        b = P.bounds; c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        if isg: ax.text(*c, ('K' if r['model'].startswith('KALP') else 'Y') + r['model'].split()[1], ha='center', va='center', fontsize=4.5)
        elif r['model'] == 'MINI AYNA': ax.text(c[0], b[3] - 8, 'mini', ha='center', va='top', fontsize=4)
        else: ax.text(c[0], b[3] - 8, (('Ø%d' % round(r['w'] / 10)) if r['w'] == r['h'] else '%d×%d' % (round(r['w'] / 10), round(r['h'] / 10))), ha='center', va='top', fontsize=4.5)
        cnt[lab(r)] += 1; tot[lab(r)] += 1
    ax.set_xlim(-10, SX + 10); ax.set_ylim(-10, SY + 10); ax.set_aspect('equal'); ax.axis('off')
    tx = fig.add_axes([0.60, 0.05, 0.38, 0.88]); tx.axis('off')
    lines = ['%s' % name.replace('AYNA4_', '').replace('_', ' '), 'Plaka 1220×2800×10 altın laminat', 'Altın yüz AŞAĞIDA', '', 'BU PLAKADAN ÇIKANLAR:']
    for k, v in sorted(cnt.items(), key=lambda kv: (kv[0].split()[0], kv[0])): lines.append('  %2d × %s' % (v, k))
    lines += ['', 'Toplam %d parça' % sum(cnt.values()), '', 'Program: %s.anc' % name, 'Sıra: T3 askı delikleri > T6 V91 Z3', '> T4 ayna yuvası Z4 > T8 kesim', 'T8: içten dışa, önce küçükler', 'Küçük parçalar 0.2 et (maket bıçağı)']
    tx.text(0, 1, '\n'.join(lines), va='top', fontsize=9, family='DejaVu Sans')
    pdf.savefig(fig); plt.close(fig)
import importlib.util
spec = importlib.util.spec_from_file_location('a4', 'ayna4.py'); a4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(a4)
fig = plt.figure(figsize=(11.69, 8.27))
for i, (n, D) in enumerate((('KALP', 140), ('YONCA', 140), ('KALP', 100), ('YONCA', 100))):
    ax = fig.add_axes([0.03 + i * 0.245, 0.45, 0.22, 0.45]); g = a4.gift_shape(n, D, 0, 0); b = g.bounds
    ax.add_patch(MP(list(g.exterior.coords), fc='#d4b26a', ec='#6b5320')); ax.add_patch(MP(list(g.buffer(-7).exterior.coords), fill=False, ec='#6b5320', ls='--', lw=.6))
    ax.set_xlim(-85, 85); ax.set_ylim(-85, 85); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('%s altlık\n%d × %d mm' % ('Kalp' if n == 'KALP' else 'Yonca', round(b[2] - b[0]), round(b[3] - b[1])), fontsize=11)
ax = fig.add_axes([0.03, 0.05, 0.94, 0.35]); ax.axis('off')
ax.text(0, 1, 'HEDİYELİK ALTLIKLAR\n'
        '• 14 cm kalp / yonca: kupa, kahve fincanı, mum. 10 cm: çay bardağı, küçük mum.\n'
        '• Kenar aynalarla aynı: V91 7 mm dalış, önden 3 mm ince altın kenar (kesik çizgi = pah başlangıcı).\n'
        '• Kenar köşeleri R6 yuvarlatıldı (8 mm bıçak ve V91 temiz döner, kırılmaz).\n'
        '• Kesimde 0.2 mm et kalır; arkadan maket bıçağıyla ayırın, altına 4 keçe yapıştırın.\n'
        '• Kalp ve yonca simetrik: altın yüz aşağıda kesilse de şekil ters dönmez.', va='top', fontsize=11)
pdf.savefig(fig); plt.close(fig)
for img in ('AYNA_HALKA_KESITI.png',):
    fig = plt.figure(figsize=(11.69, 8.27)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off'); ax.imshow(Image.open(img)); pdf.savefig(fig); plt.close(fig)
rows = []
for name, rs in d.items():
    c = collections.Counter()
    for r in rs:
        if r['gw']: c[(lab(r), ('Ø%d' % r['gw']) if r['w'] == r['h'] else '%d×%d' % (r['gw'], r['gh']))] += 1
    for (l, cam), n in sorted(c.items()): rows.append([name.replace('AYNA4_', '').split('_')[0], l, str(n), cam])
fig = plt.figure(figsize=(8.27, 11.69)); ax = fig.add_axes([0.03, 0.02, 0.94, 0.93]); ax.axis('off')
tb = ax.table(cellText=rows, colLabels=['Plaka', 'Ayna', 'Adet', 'CAM ölçüsü (mm)'], loc='upper center', cellLoc='center'); tb.auto_set_font_size(False); tb.set_fontsize(8); tb.scale(1, 1.25)
ax.set_title('CAM LİSTESİ (her plaka 1 kez kesildiğinde)', fontsize=12, weight='bold')
pdf.savefig(fig); plt.close(fig)
fig = plt.figure(figsize=(8.27, 11.69)); ax = fig.add_axes([0.05, 0.05, 0.9, 0.9]); ax.axis('off')
ax.text(0, 1, 'TOPLAM (4 plaka birer kez)\n\n' + '\n'.join('%3d × %s' % (v, k) for k, v in sorted(tot.items())) + '\n\nToplam %d parça' % sum(tot.values()), va='top', fontsize=10)
pdf.savefig(fig); plt.close(fig)
pdf.close(); print(sum(tot.values()), dict(tot))
