import math, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MP, Rectangle, Circle
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
T = 18; R = 200; LIP = 6; PKD = 12; BAND = 18.5; GAP = 3; TAIL = 30; RB_W = 10; RB_D = 6; ARK = 6; KUS = 96
COL = dict(skin='#f1e8d8', band='#8ec1ea', rab='#c9a6e0', dub='#1e9e5c', tar='#e74c3c', hinge='#e67e22', cable='#7f8c8d', cut='#222')
def P_(W, D): return unary_union([box(0, 0, W, D - R), box(R, 0, W - R, D), Point(R, D - R).buffer(R, resolution=96), Point(W - R, D - R).buffer(R, resolution=96)]).intersection(box(0, 0, W, D))
def spec(name, W, D, H, BZ, nd, dusur, tv):
    Hb = H - BZ; Hi = Hb - 2 * T; p0, p1 = R + TAIL, W - R - TAIL
    dw = (p1 - p0 - 2 * GAP - GAP * (nd - 1)) / nd; dh = Hb - 2 * LIP - 2 * 2
    dy0 = ARK + (T if tv else 0); dy1 = D - T - 2
    if tv: dik = [p0, W / 2 - T / 2, p1 - T]
    elif nd == 2: dik = [p0, p1 - T]
    else: dik = [p0, p0 + GAP + dw + GAP / 2 - T / 2, p1 - T]
    return dict(name=name, W=W, D=D, H=H, BZ=BZ, Hb=Hb, Hi=Hi, nd=nd, dusur=dusur, tv=tv, p0=p0, p1=p1, dw=dw, dh=dh, dy0=dy0, dy1=dy1, dik=dik,
                arc=math.pi / 2 * R, tp=round(TAIL + math.pi / 2 * R + (D - R)), th=Hb - 2 * LIP - 1)
def dim(ax, x0, y0, x1, y1, t, fs=7.5):
    ax.annotate('', (x0, y0), (x1, y1), arrowprops=dict(arrowstyle='<->', lw=.6, color='#333'))
    v = abs(x0 - x1) < 1e-6
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, t, ha='center', va='center', fontsize=fs, rotation=90 if v else 0, bbox=dict(fc='white', ec='none', pad=.3))
def tag(ax, x, y, t, c, fs=7, **k): ax.text(x, y, t, fontsize=fs, ha='center', va='center', color='k', bbox=dict(fc='white', ec=c, lw=1, pad=1.5, alpha=.92), **k)
def fin(ax, W, H, pad): ax.set_xlim(-pad, W + pad); ax.set_ylim(-pad * 1.1, H + pad); ax.set_aspect('equal'); ax.axis('off')
def notes(fig, y, lines, x=.04, fs=8.6): fig.text(x, y, '\n'.join(lines), fontsize=fs, va='top')
def tabla(fig, s, title):
    W, D = s['W'], s['D']; P = P_(W, D)
    band = P.difference(P.buffer(-BAND, join_style=1)).difference(box(BAND, -1, W - BAND, BAND + 0.1))
    ax = fig.add_axes([.03, .42, .94, .48])
    ax.add_patch(MP(list(P.exterior.coords), fc=COL['skin'], ec=COL['cut'], lw=1.3))
    for g in getattr(band, 'geoms', [band]): ax.add_patch(MP(list(g.exterior.coords), fc=COL['band'], ec='#2e86c1', lw=.6))
    if not s['tv']: ax.add_patch(Rectangle((BAND, 0), W - 2 * BAND, RB_W, fc=COL['rab'], ec='#8e44ad', lw=.6))
    for x in s['dik']:
        for y in (s['dy0'] + 40, s['dy1'] - 40): ax.add_patch(Circle((x + T / 2, y), 7, fc=COL['dub']))
        ax.add_patch(Rectangle((x, s['dy0']), T, s['dy1'] - s['dy0'], fill=False, ec=COL['dub'], ls=':', lw=.7))
    tag(ax, W / 2, D - 9, 'CEP 18,5 mm — kapak burada çalışır (önden 6 mm et görünür)', '#2e86c1')
    tag(ax, R * .55, D - R * .45, 'CEP — kavisli\nuç panel\nburaya oturur', '#2e86c1', 6.5)
    tag(ax, W - R * .55, D - R * .45, 'CEP — kavisli\nuç panel\nburaya oturur', '#2e86c1', 6.5)
    if not s['tv']: tag(ax, W / 2, RB_W + 20, 'ARKALIK LAMBASI 10 × 6 (Z12) — arkalık sonradan arkadan vidalanır', '#8e44ad', 6.5)
    else: tag(ax, W / 2, 30, 'ARKA 18 mm: karkas boşluğu (lamba yok) — arkalık 18 mm içeride', '#999', 6.5)
    tag(ax, s['dik'][0] + 60, (s['dy0'] + s['dy1']) / 2, 'dikme yeri\nØ8×14 dübel', COL['dub'], 6.5)
    tag(ax, W / 2, D / 2, 'DOLU — üstte 6 mm et, cep altta', '#999', 7)
    dim(ax, 0, -45, W, -45, '%d' % W, 8); dim(ax, W + 45, 0, W + 45, D, '%d' % D, 8)
    dim(ax, 0, D + 32, s['p0'], D + 32, '%d' % s['p0'], 6.5); dim(ax, s['p0'], D + 32, s['p1'], D + 32, 'kapak açıklığı %d' % (s['p1'] - s['p0']), 6.5); dim(ax, s['p1'], D + 32, W, D + 32, '%d' % (W - s['p1']), 6.5)
    for i, x in enumerate(s['dik']): ax.text(x + T / 2, -18, 'x=%d' % round(x), ha='center', fontsize=6, color=COL['dub'])
    ax.text(R * .3, D - R * .15, 'R%d' % R, fontsize=7)
    fin(ax, W, D, 90); ax.set_title(title, fontsize=11, loc='left', weight='bold')
    notes(fig, .38, ['NE VAR, NEREDE:',
        '• Dış hat (siyah): T8 8 mm Antesan, 4 mm dıştan, 2 paso (Z9 > Z0). Ön köşeler R200, arka dümdüz (duvar tarafı).',
        '• MAVİ — ÇEVRE CEBİ: T4 10 mm, 18,5 mm genişlik, Z6 (12 mm derin, 6 mm et kalır). Önde kapak çalışır; köşe ve yanlarda kavisli uç panel',
        '  12 mm içine oturur. Önden bakınca tablanın sadece 6 mm eti görünür.',
        ('• TV: arka lamba YOK — arkada 18 mm karkas boşluğu, arkalık 18 mm içeride karkasların önüne vidalanır.' if s['tv'] else '• MOR — ARKALIK LAMBASI: T4 10 mm, arka kenarda 10 genişlik, Z12 (6 mm derin). Arkalık gövde toplandıktan sonra arkadan oturur, vidalanır.'),
        '• YEŞİL — DÜBEL: T8, Ø8 × 14 (Z4), her dikmeye 2 adet. Noktalı kutu = dikmenin oturduğu yer.',
        '• Üst ve alt tabla AYNI parça, aynı program: kesimde görünen yüz AŞAĞIDA, cep/lamba/dübel üstten (iç yüz).',
        '  Alt tabla montajda ters çevrilir; cepler yine içe bakar.'])
def panel(fig, s, rect, title):
    L, Hh = s['tp'], s['th']; a0, a1 = TAIL, TAIL + s['arc']
    ax = fig.add_axes(rect); ax.add_patch(Rectangle((0, 0), L, Hh, fc=COL['skin'], ec=COL['cut'], lw=1.2))
    ax.add_patch(Rectangle((a0, 0), a1 - a0, Hh, fc='#fadbd8', ec='none'))
    n = round((a1 - a0) / 20); pit = (a1 - a0) / n
    for k in range(n + 1): ax.plot([a0 + k * pit] * 2, [-12, Hh + 12], c=COL['tar'], lw=.9)
    tag(ax, (a0 + a1) / 2, Hh / 2, 'TARAMA\n%d oluk, aralık %.1f\nT4 10 mm, Z1.3\n(et 1.3)' % (n + 1, pit), COL['tar'], 6.5)
    tag(ax, a0 / 2 + 2, Hh * .8, 'ön\nuç\n%d' % TAIL, '#999', 6); tag(ax, (a1 + L) / 2, Hh / 2, 'YAN — düz\narkaya kadar\n%d' % round(L - a1), '#999', 6.5)
    dim(ax, 0, -40, L, -40, '%d' % L, 8); dim(ax, L + 40, 0, L + 40, Hh, '%d' % Hh, 8)
    fin(ax, L, Hh, 70); ax.set_title(title, fontsize=10, loc='left', weight='bold')
def rect(fig, r, w, h, title, feats=(), tags=()):
    ax = fig.add_axes(r); ax.add_patch(Rectangle((0, 0), w, h, fc=COL['skin'], ec=COL['cut'], lw=1.2))
    for kind, (x, y) in feats:
        if kind == 'h': ax.add_patch(Circle((x, y), 17.5, fc=COL['hinge'], ec='#a04000'))
        if kind == 'c': ax.add_patch(Circle((x, y), 30, fc=COL['cable'], ec='k'))
        if kind == 'd': ax.add_patch(Circle((x, y), 6, fc=COL['dub']))
    for x, y, t, c in tags: tag(ax, x, y, t, c, 6.5)
    m = max(w, h) * .07 + 15
    dim(ax, 0, -m, w, -m, '%d' % round(w), 8); dim(ax, w + m, 0, w + m, h, '%d' % round(h), 8)
    fin(ax, w, h, m * 2); ax.set_title(title, fontsize=10, loc='left', weight='bold')
def kesit(fig, r, s):
    ax = fig.add_axes(r); D = 140
    ax.add_patch(Rectangle((0, 0), D, T, fc=COL['skin'], ec='k')); ax.add_patch(Rectangle((D - BAND, LIP), BAND, PKD, fc='white', ec='#2e86c1'))
    ax.add_patch(Rectangle((0, 150), D, T, fc=COL['skin'], ec='k')); ax.add_patch(Rectangle((D - BAND, 150), BAND, PKD, fc='white', ec='#2e86c1'))
    ax.add_patch(Rectangle((D - T, LIP + 2), T, 150 + PKD - LIP - 4, fc='#d6c5ab', ec='k'))
    tag(ax, D - 60, 9, 'alt tabla — 6 mm et', '#999', 6); tag(ax, D - 60, 159, 'üst tabla — 6 mm et', '#999', 6); tag(ax, D - 9, 85, 'kapak /\nuç panel', '#e67e22', 6)
    ax.annotate('önden bakınca\n6 mm', (D + 2, 3), (D + 40, -25), fontsize=6, arrowprops=dict(arrowstyle='->', lw=.5))
    ax.set_xlim(-10, D + 70); ax.set_ylim(-45, 185); ax.set_aspect('equal'); ax.axis('off'); ax.set_title('Ön kenar kesiti (ölçeksiz kısaltılmış)', fontsize=8, loc='left')
def build(pdf, s, kapak_txt, extra):
    W, D = s['W'], s['D']
    fig = plt.figure(figsize=(11.69, 8.27)); fig.text(.03, .955, s['name'], fontsize=15, weight='bold')
    tabla(fig, s, '1) TABLA — 2 adet (üst + alt aynı)'); kesit(fig, [.72, .02, .26, .2], s); pdf.savefig(fig); plt.close(fig)
    fig = plt.figure(figsize=(11.69, 8.27)); fig.text(.03, .955, s['name'] + ' — devam', fontsize=15, weight='bold')
    panel(fig, s, [.03, .55, .55, .36], '2) KAVİSLİ UÇ PANELİ — 2 adet')
    notes(fig, .52, ['• Dış hat: T8, 3 paso (Z12 > Z6 > Z0) F3500 — EN SON koparılır.', '• KIRMIZI: tarama İÇ yüzde, dış yüz düz kalır. Panel R200 köşeye bükülür, üst ve alt',
        '  tablanın mavi cebine 12 mm girer (yükseklik %d = gövde %d − 2×6 et − 1 boşluk).' % (s['th'], s['Hb']), '• Ön uç %d mm kapak açıklığına kadar gelir; yan kısım arkaya kadar düz gider.' % TAIL, '• 2. panel 180° çevrilerek diğer uca takılır (aynı parça).'], x=.04, fs=8)
    dd = s['dy1'] - s['dy0']
    rect(fig, [.62, .55, .35, .36], dd, s['Hi'], '3) DİKME — %d adet' % len(s['dik']), tags=[(dd / 2, s['Hi'] / 2, 'T8 2 paso\nkenarlara Ø8 dübel\n(elde, tablaya göre)', COL['dub'])])
    notes(fig, .52, ['• Tablaların arasına (cebe değil, iç yüze) oturur, yükseklik %d.' % s['Hi'], '• Derinlik %d: arkalık%s önünden kapak arkasına (2 mm boşluk).' % (dd, ' + kuşak' if s['tv'] else '')], x=.63, fs=8)
    extra(fig, s)
    pdf.savefig(fig); plt.close(fig)
def tv_extra(fig, s):
    rect(fig, [.03, .03, .3, .33], s['dw'], s['dh'], '4) DÜŞER KAPAK — 2 adet', [('h', (100, 22)), ('h', (s['dw'] - 100, 22))],
         [(s['dw'] / 2, s['dh'] * .6, 'üst ve alt 6 mm\netin arasında çalışır', '#999'), (s['dw'] / 2, 70, 'TURUNCU: menteşe çanağı\nØ35 × 13 (T8 dairesel, Z5)', COL['hinge'])])
    rect(fig, [.35, .30, .3, .12], s['W'] - 38, s['Hi'] - 2, '5) ARKALIK 6 mm — 1 adet', [('c', ((s['W'] - 38) / 2, (s['Hi'] - 2) / 2))], [((s['W'] - 38) / 2 + 260, (s['Hi'] - 2) / 2, 'Ø60 kablo deliği; karkasların önüne vidalanır', COL['cable'])])
    rect(fig, [.35, .19, .3, .08], s['W'] - 36, KUS, '6) TV KARKASI — 1 adet', tags=[((s['W'] - 36) / 2, KUS / 2, 'ALT kenar 45° gönye burun — T6 V91 Z-0.5 (duvar tarafı aşağı)', '#1f5fbf')])
    rect(fig, [.35, .105, .3, .07], s['W'] - 36, 60, '7) ALT TAKOZ — 1 adet', tags=[((s['W'] - 36) / 2, 30, 'düz; duvara dayanır, TV dik durur', '#999')])
    rect(fig, [.35, .01, .3, .08], s['W'] - 36 - 25, KUS, '8) DUVAR KARKASI — 1 adet (25 mm kısa)', tags=[((s['W'] - 61) / 2, KUS / 2, 'ÜST kenar 45° gönye burun — T6 V91 Z-0.5; önce duvara vidalanır', '#1f5fbf')])
    notes(fig, .44, ['Kapak hırdavatı (kapak başı): 2 menteşe + 1 amortisör + 1 bas-aç.', 'Kapak ölçüsü: açıklık %d, aralar 3 mm.' % (s['p1'] - s['p0'])], x=.69, fs=8)
def kon_extra(fig, s):
    n = s['nd']
    rect(fig, [.03, .03, .2, .35], s['dw'], s['dh'], '4) KAPAK — %d adet, bas-aç' % n, [('h', (22, 100)), ('h', (22, s['dh'] - 100))],
         [(s['dw'] / 2, s['dh'] / 2, 'yana açılır\nüst/alt 6 mm\netin arasında', '#999'), (s['dw'] / 2 + 30, 160, 'menteşe\nØ35×13', COL['hinge'])])
    rw = (s['p1'] - s['p0'] - 2 * T - 2) if n == 2 else (s['p1'] - s['dik'][1] - 2 * T - 2)
    rect(fig, [.25, .23, .4, .15], rw, s['dy1'] - s['dy0'] - 15, '5) RAF — %d adet' % (1 if n == 2 else 2) + ('' if n == 2 else ' (sol bölme %d)' % round(s['dik'][1] - s['p0'] - T - 2)), tags=[(rw / 2, (s['dy1'] - s['dy0'] - 15) / 2, 'raf pimi Ø5 — 4 adet', '#999')])
    B = P_(s['W'], s['D']).buffer(-30, join_style=1); ax = fig.add_axes([.25, .03, .4, .17]); ax.add_patch(MP(list(B.exterior.coords), fc=COL['skin'], ec='k')); b = B.bounds
    tag(ax, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, 'BAZA 18 mm — tablanın 30 mm içinde (R170)', '#999'); dim(ax, b[0], b[1] - 35, b[2], b[1] - 35, '%d' % round(b[2] - b[0]), 7); dim(ax, b[2] + 35, b[1], b[2] + 35, b[3], '%d' % round(b[3] - b[1]), 7)
    fin(ax, s['W'], s['D'], 60); ax.set_title('6) BAZA — 1 adet', fontsize=10, loc='left', weight='bold')
    notes(fig, .44, ['7) ARKALIK 6 mm: %d × %d,' % (s['W'] - 38, s['Hi'] + 10), '   arkadan lambaya oturur, vidalanır.', 'Kapak başı: 2 menteşe + 1 bas-aç.'], x=.69, fs=8)
def montaj(pdf, s, lines):
    fig = plt.figure(figsize=(11.69, 8.27)); fig.text(.03, .955, s['name'] + ' — MONTAJ SIRASI (tek seferde toplanır)', fontsize=15, weight='bold')
    notes(fig, .9, lines, fs=10.5); pdf.savefig(fig); plt.close(fig)
TV = spec('BONBON TV 170 × 35 × 38 — duvara monte', 1700, 350, 380, 0, 2, True, True)
K2 = spec('BONBON KONSOL 150 × 45 × 90 — 2 kapak', 1500, 450, 900, 18, 2, False, False)
K3 = spec('BONBON KONSOL 150 × 45 × 90 — 3 kapak', 1500, 450, 900, 18, 3, False, False)
pdf = PdfPages('BONBON_KESIM_RENKLI_YILMAZ_ERGUN.pdf')
fig = plt.figure(figsize=(11.69, 8.27)); fig.text(.03, .93, 'RENK ANAHTARI — CNC\'den toplar gibi', fontsize=16, weight='bold')
ax = fig.add_axes([.05, .3, .5, .55]); ax.axis('off')
for i, (c, t) in enumerate([(COL['skin'], 'Krem: dolu malzeme (18 mm)'), (COL['band'], 'Mavi: CEP — T4 10 mm, Z6 (6 mm et kalır)'), (COL['rab'], 'Mor: ARKALIK LAMBASI — T4 10 mm, Z12 (6 mm derin)'),
                          (COL['tar'], 'Kırmızı: TARAMA — T4 10 mm, Z1.3 (et 1.3), her oluk ayrı'), (COL['dub'], 'Yeşil: DÜBEL Ø8 × 14 — T8, Z4'), (COL['hinge'], 'Turuncu: MENTEŞE ÇANAĞI Ø35 × 13 — T8 dairesel, Z5'),
                          (COL['cable'], 'Gri: KABLO DELİĞİ Ø60 — T8 boydan'), ('#1f5fbf', 'Lacivert yazı: 45° GÖNYE BURUN — T6 V91, Z-0.5 (TV karkası + duvar karkası)'), (COL['cut'], 'Siyah çizgi: DIŞ KESİM — T8 8 mm Antesan, 4 mm dıştan')]):
    ax.add_patch(Rectangle((0, -i * 1.2), 1, .8, fc=c, ec='k')); ax.text(1.3, -i * 1.2 + .4, t, va='center', fontsize=11)
ax.set_xlim(0, 12); ax.set_ylim(-9.5, 1)
notes(fig, .25, ['Bıçaklar (makine kafa tablosu): T3 3 mm · T4 10 mm · T6 V91 · T8 8 mm Antesan · T10 6 mm.', 'T6 V91 sadece TV ve duvar karkasının 45° kenarında; T10 kullanılmıyor.',
    'ARKALIK KARARI: kanal yerine LAMBA. Gövde (tablalar + dikmeler + uç paneller) önce toplanır, arkalık en son arkadan lambaya oturup vidalanır.',
    'Kanalda arkalığı toplarken içeri sokmak gerekir, montajcıyı zorlar; lambada gövde gönyesini de arkalık tutar.'], fs=10)
pdf.savefig(fig); plt.close(fig)
build(pdf, TV, '', tv_extra)
montaj(pdf, TV, ['1. Alt tablayı cebi yukarı bakacak şekilde masaya koy.', '2. Dikmeleri dübelle alt tablaya tak (tutkal).', '3. Kavisli uç panelleri iç yüzden hafif nemlendir / tutkalla; köşeye bükerek mavi cebe oturt.',
    '4. Üst tablayı cebi aşağı bakacak şekilde dikmelere ve uç panellere oturt (dübel + tutkal). İşkence ile sık, 1 saat beklet.', '5. Duvar kuşaklarını üst ve alt tabla altına, arka kenara vidala.',
    '6. Arkalığı arkadan lambaya oturt, vidala (Ø60 kablo deliği ortada).', '7. Kapakları menteşele (alttan), amortisör ve bas-aç tak; ayarla.', '', 'EVDE MONTAJ: Duvar karkasını (üst kenarı 45°, yüksek taraf duvardan uzakta) teraziyle duvara vidala (en az 4 vida + dübel).', 'TV\'yi kaldırıp arkasındaki 45° karkasıyla duvar karkasının üstüne bindir; 25 mm boşluk sayesinde sağa sola kaydırıp ortala.'])
for K in (K2, K3):
    build(pdf, K, '', kon_extra)
montaj(pdf, K2, ['1. Bazayı alt tablanın altına vidala (30 mm içeride, iz kalıbı ile).', '2. Alt tablayı cebi yukarı bakacak şekilde koy; dikmeleri dübel + tutkal ile tak.', '3. Kavisli uç panelleri köşeye bükerek mavi cebe oturt.',
    '4. Üst tablayı oturt, işkenceyle sık.', '5. Arkalığı arkadan lambaya oturt, vidala.', '6. Raf pimleri ve rafı tak.', '7. Kapakları menteşele, bas-açları tak, ayarla.', '', 'Konsol tek seferde toplanır; sökülmeden gönderilir.'])
pdf.close()
for s in (TV, K2, K3): print(s['name'], s['tp'], s['th'], round(s['dw']), s['dh'], s['dy1'] - s['dy0'], s['Hi'])
