import json,math
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MP, Circle, Rectangle
from shapely.geometry import Polygon,Point
G=json.load(open('winston_geo.json'));N=json.load(open('winston_nest.json'))
T=Polygon(G['T']);C=G['C']
pdf=PdfPages('WINSTON_ORTA_SEHPA_PLAN.pdf')
# 1 montaj
fig,axs=plt.subplots(1,2,figsize=(11.69,8.27))
for ax,key,tit,colr in ((axs[0],'K1','1. KAT (tablanın hemen altına)','#9ecae1'),(axs[1],'K2','2. KAT (1. katın üstüne, ekler kaydırılmış)','#a1d99b')):
    ax.add_patch(MP(list(T.exterior.coords),fc='#e8d2a8',ec='k',lw=1))
    for i,p in enumerate(G[key]):
        P=Polygon(p);ax.add_patch(MP(p,fc=colr,ec='k',lw=.8));c=P.representative_point();ax.text(c.x,c.y,'%s-%d'%(key,i+1),ha='center',va='center',fontsize=8,weight='bold')
    if key=='K1':
        for i,p in enumerate(G['K2']): ax.add_patch(MP(p,fill=False,ec='#2a2',lw=.5,ls='--'))
    ax.add_patch(Circle(C,318,fill=False,ec='#c00',lw=1.2,ls='--'));ax.add_patch(Circle(C,300,fill=False,ec='#c00',lw=.6))
    for a in (0,90,180,270): ax.plot(C[0]+260*math.cos(math.radians(a)),C[1]+260*math.sin(math.radians(a)),'ko',ms=3)
    ax.text(C[0],C[1],'Ø60 ayak\n(Ø636 dış)',ha='center',va='center',color='#c00',fontsize=8)
    ax.set_aspect('equal');ax.axis('off');ax.set_title(tit,fontsize=10,weight='bold')
fig.suptitle('WINSTON ORTA SEHPA — MONTAJ (tablanın ALTINDAN bakış) · tabla 18 meşe + 2 kat 18 MDF şerit = 54 mm kenar · şerit 65 mm',fontsize=11)
fig.text(.02,.02,'Kesimden sonra şeritlerin üstüne kurşun kalemle K1-1… numarasını yazın (plaka yerleşim sayfasında hangisinin hangisi olduğu var).\n'
 '1. kat ekleri ile 2. kat ekleri yarım parça kaydırıldı: ekler üst üste gelmez, yolda darbede çatlamaz. Şeritler tabla kenarıyla SIFIR (aynı hizada), tutkal + zımba.\n'
 'Ayak: 4 adet Ø8 delikten (Ø520 daire, baklava) tablaya vida; tablada Ø3×12 kılavuz delikler hazır. Ayak şeritlere 21 mm mesafede, değmez.',fontsize=8.5)
pdf.savefig(fig);plt.close(fig)
# 2-3 plakalar
for img,t in (('mdf.png','MDF 18 mm — kapaklar + kalınlaştırma'),('mese.png','MEŞE KAPLAMA 18 mm — tabla (görünen yüz AŞAĞIDA) + ayak taraması')):
    fig=plt.figure(figsize=(8.27,11.69));ax=fig.add_axes([0.03,0.1,0.94,0.85]);ax.axis('off');ax.imshow(plt.imread(img));ax.set_title(t,fontsize=11,weight='bold')
    if img=='mdf.png':
        fig.text(.04,.03,'Sıra: Ø8 delikler > Ø39 iç/dış (STOK, 0.2 et) > Ø60 iç > şeritler (küçükten büyüğe, 0.2 et) > Ø60 dış en son.\nØ39 kapaklar Ø60 kapakların boşluğundan bedava çıkar → Ø39 sehpa ayağı için stoğa.',fontsize=9)
    else:
        fig.text(.04,.03,'Sıra: T3 Ø3×12 vida kılavuzları > T4 tarama (her oluk ayrı, et 1.1) > T8 tabla (2 paso) > T8 tarama paneli en son (3 paso, F3500).\nTarama paneli 382×1892 DİKİNE yerleştirildi (meşe kaplama su yönü): Ø60 kapak çevresine (π×602.2) göre. Uçlar yarım oluk: ek yeri oluk ortasında.',fontsize=9)
    pdf.savefig(fig);plt.close(fig)
# 4 parça listesi
fig=plt.figure(figsize=(8.27,11.69));ax=fig.add_axes([.05,.05,.9,.9]);ax.axis('off')
txt='''WINSTON ORTA SEHPA — PARÇA LİSTESİ (1 adet sehpa)

MEŞE KAPLAMA 18 mm (WINSTON_MESE_TABLA_TARAMA.anc)
  1 × Tabla, organik form %d × %d mm, altında 4 × Ø3×12 vida kılavuzu
  1 × Ayak tarama paneli 382 × 1892 mm (dikine, su yönünde), 96 oluk (aralık 19.9, 10 mm bıçak, et 1.1)

MDF 18 mm (WINSTON_MDF_KAPAK_KALINLASTIRMA.anc)
  2 × Ø60 ayak kapağı (alt + üst şapka), Ø600 / iç boşluk Ø440, 4 × Ø8 delik (Ø520 daire)
  2 × Ø39 ayak kapağı — STOK (bedava), Ø390 / iç boşluk Ø250, 4 × Ø8 delik (Ø310 daire)
  5 × 1. kat kalınlaştırma şeridi (K1-1 … K1-5), 65 mm
  5 × 2. kat kalınlaştırma şeridi (K2-1 … K2-5), 65 mm

ÖLÇÜLER
  Toplam yükseklik 400 = ayak 382 + tabla 18 · görünen kenar 54 mm
  Ayak dış çapı ≈ Ø636 (Ø600 kapak + 18 mm taramalı panel)
  Tabla çevresi %d mm

HIRDAVAT
  4 × vida 4×40 (üst kapak → tabla), keçe 4 adet (alt kapak altına), tutkal + zımba (şeritler)
'''%(round(T.bounds[2]-T.bounds[0]),round(T.bounds[3]-T.bounds[1]),round(T.length))
ax.text(0,1,txt,va='top',fontsize=10.5,family='DejaVu Sans')
pdf.savefig(fig);plt.close(fig);pdf.close()
