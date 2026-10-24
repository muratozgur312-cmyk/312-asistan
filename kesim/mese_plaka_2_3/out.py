import pickle, ezdxf, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon as MP, Circle
from PIL import Image
L = pickle.load(open('layout2.pkl', 'rb'))
LAB = {'A': 'A Ø39 tarama\n382×1233', 'B': 'B Ø60 tarama\n430×1890', 'H': 'H Ø80 tarama\n350×2515\n(YERİ SABİT)', 'W_PANEL': 'WINSTON\nØ60 tarama\n382×1893',
       'C1': 'C1 Ø800 gönye', 'C2': 'C2 Ø800 gönye', 'D1': 'D1', 'D2': 'D2', 'E1': 'E1', 'E2': 'E2', 'F': 'F 400×1963 (yatay)', 'G': 'G Ø1000', 'W_TABLA': 'WINSTON\nTABLA', 'DANISH': 'DANISH 180×90\nYılmaz Ergün'}
GL = {'T48': 'Tahta\n48×24', 'T40': 'Tahta\n40×20', 'T32': 'Tahta\n32×16', 'A10': 'Ø10', 'OV36': 'Tepsi'}
SEQ = ('Sıra: (T3 Winston vida Ø3×12) > T6 V91: panel gönyeleri Z-0.5, Danish pah Z4, hediyelik pah Z13, Ø800 daireler Z-0.5 >\n'
       'T4: Ø10×14 ayak/bağlantı delikleri, tarama (her oluk ayrı, yön değiştirerek, et 1.3, uçlarda 18 mm pay) >\n'
       'T8: asma delikleri > kırım çizgileri (Z1.5, 1.5 mm et) > hediyelikler (Z0.2 et) > çıta/E (Z0.2) > F, G, tabla > Danish (tek paso) > tarama panelleri EN SON 3 paso F3500.')
pdf = PdfPages('MESE_PLAKA_2_3_REV_PLAN.pdf')
for k in (2, 3):
    P = L[k]; fig = plt.figure(figsize=(8.27, 11.69)); ax = fig.add_axes([.06, .17, .9, .76])
    ax.add_patch(Rectangle((0, 0), 2100, 2800, fc='#f4efe6', ec='#888'))
    def put(g, t, c, fs=7):
        ax.add_patch(MP(list(g.exterior.coords), fc=c, ec='k', lw=.7)); b = g.bounds
        ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, t, ha='center', va='center', fontsize=fs, weight='bold', bbox=dict(fc='white', ec='none', alpha=.75, pad=.8))
    for p in P['panels']:
        put(p['box'], LAB[p['ad']], '#e8c9a0'); x0, _, x1, _ = p['box'].bounds
        for y in p['grooves']: ax.plot([x0 - p['ov'], x1 + p['ov']], [y, y], c='#c0392b', lw=.2)
    for n, c in P['vcircles']: put(c, LAB[n], '#d9b98c')
    for n, q, _ in P['t8']: put(q, LAB[n], '#9fd29a' if n == 'W_TABLA' else '#d8c3a0', 6 if n in ('D1', 'D2') else 7)
    if P['danish'] is not None: put(P['danish'], LAB['DANISH'], '#9fd29a')
    for q in P['gifts']:
        put(q['g'], GL[q['n']], '#8b5a2b', 5.5)
        if q['h'] is not None: ax.add_patch(MP(list(q['h'].exterior.coords), fc='white', ec='k', lw=.4))
    for x, y in P['d10']: ax.add_patch(Circle((x, y), 9, fc='k'))
    for x, y in P['d3']: ax.add_patch(Circle((x, y), 7, fc='purple'))
    for s in P['fire']: ax.plot(*zip(*s), c='#1565c0', lw=1.4, ls='--')
    ax.set_xlim(-30, 2130); ax.set_ylim(-30, 2830); ax.set_aspect('equal'); ax.tick_params(labelsize=7)
    m = open('MESE_PLAKA_%d_REV.anc' % k, encoding='iso-8859-9').read().split(';SURE = ')[1].split('\n')[0]
    fig.text(.06, .95, 'MEŞE PLAKA %d — MESE_PLAKA_%d_REV.anc (%s)' % (k, k, m.strip()), fontsize=13, weight='bold')
    fig.text(.06, .02, 'Kahverengi = hediyelik (servis tahtası / tepsi / Ø10 altlık)   Mavi kesikli = kırım çizgisi (1.5 mm et)   Siyah nokta = Ø10×14 delik\n' + SEQ, fontsize=7.3)
    pdf.savefig(fig); plt.close(fig)
    d = ezdxf.new('R2010', setup=True); d.units = ezdxf.units.MM; ms = d.modelspace()
    def lay(n, c):
        if n not in d.layers: d.layers.add(n, color=c)
    def poly(g, n, c): lay(n, c); ms.add_lwpolyline(list(g.exterior.coords)[:-1], close=True, dxfattribs={'layer': n})
    from shapely.geometry import box
    poly(box(0, 0, 2100, 2800), 'PLAKA', 8)
    for p in P['panels']:
        poly(p['box'], 'TARAMA_PANEL', 5); lay('TARAMA_OLUK_Z1.3', 3)
        x0, _, x1, _ = p['box'].bounds
        for y in p['grooves']: ms.add_line((x0 - p['ov'], y), (x1 + p['ov'], y), dxfattribs={'layer': 'TARAMA_OLUK_Z1.3'})
    for n, c in P['vcircles']: poly(c, 'V91_GONYE_DAIRE', 1)
    for n, q, _ in P['t8']: poly(q, 'PARCA_' + n, 7)
    if P['danish'] is not None: poly(P['danish'], 'DANISH_V91_Z4', 1)
    for q in P['gifts']:
        poly(q['g'], 'HEDIYELIK_' + q['n'], 30)
        if q['h'] is not None: poly(q['h'], 'ASMA_DELIK', 6)
    lay('DELIK_D10x14', 6); lay('KIRIM_Z1.5', 4)
    for x, y in P['d10']: ms.add_circle((x, y), 5, dxfattribs={'layer': 'DELIK_D10x14'})
    for x, y in P['d3']: ms.add_circle((x, y), 1.5, dxfattribs={'layer': 'DELIK_D10x14'})
    for s in P['fire']: ms.add_lwpolyline(s, dxfattribs={'layer': 'KIRIM_Z1.5'})
    d.saveas('MESE_PLAKA_%d_REV.dxf' % k)
pdf.close()
