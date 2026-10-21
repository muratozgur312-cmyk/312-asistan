# 312 Asistan — Proje Kaydı

Ortak kayıt: Murat (patron), Claude, Codex. Kodu değiştiren herkes bu dosyayı günceller.

## Mimari
- Telegram botu: `@interiors312_asistan_bot` (312 Asistan)
- Sunucu: Cloudflare Worker `312-takip-botu` (`src/index.js`)
- Veritabanı: Cloudflare D1 `312-siparisler`, tablo `documents(collection, id, data JSON)` + `document_history`
  - koleksiyonlar: `siparisler` (27), `kutuphane` (31), `ayarlar` (grup numaraları)
- Gizli ayarlar (Cloudflare Secrets): `BOT_TOKEN`, `WEBHOOK_SECRET`, `SETUP_SECRET`; değişken: `ADMIN_USER_ID`
- Bot yalnızca `ADMIN_USER_ID` (Murat) komutlarını çalıştırır.

## Gruplar
- `312 NL Winkel` — Hollanda mağaza (Hollandaca bildirim)
- `312 TR Üretim` — Türkiye üretim (Türkçe bildirim)
- Bağlama: grupta `/baglan nl` veya `/baglan tr`

## Güvenlik kuralı (değişmez)
Gruplara ve tedarikçilere **izin listesi** dışında hiçbir alan gitmez.
Fiyat, kapora, alınan, kalan, telefon, adres, işaret ve genel satış notu (`not`) ASLA gönderilmez.
Ürün notlarındaki tutarlar ve kapora/havale/ödeme cümleleri otomatik silinir.

## Sürümler
- v1 (Codex): /start, /kimlik, /dbtest
- v2: /siparisler, /siparis, /ara, /kutuphane, /ozet
- v3: sipariş no sıralaması, durum filtresi
- v4: NL/TR grup bağlantısı, /bildir
- v5: izin listesi ile bildirim, /onizle, /alanlar
- v5.1: genel not gönderilmez, notlardaki para ifadeleri temizlenir
- v6: tedarikçi grupları (/tedarikci), iş kartı + ▶️/✅/⚠️ düğmeleri (/is), /isler, ustanın mesaj/fotoğrafı Murat'a iletilir, süper grup numara taşıma  ← CANLI (20 Ekim 2026)

## Tedarikçiler (TG-02, ChatGPT + 13 Ekim listesi)
| kısa ad | firma | iş | sonra |
|---|---|---|---|
| ozbulut | Özbulut Metal | metal ayak imalatı | statikboya |
| statikboya | Statik boya (firma adı BİLİNMİYOR) | metal parça statik boya | gerekirse boyaci |
| boyaci | Boyacı | tabla rengine boya | — |
| satinalma | 312 Satın Alma | Artmob'un malzemesini alır (plaka, MDF, kaplama) | artmob |
| artmob | Artmob | ahşap işleri | gerekirse boyaci |
Diğerleri (13 Ekim): camcı, sineklik (Emir), perde (Davillo), Decolux, Dörtdivan çerçeve. Malzemeciler: Yıldız Entegre, Starwood, 18 mm MDF.
Akışlar (Murat, 20 Ekim): Ahşap: satinalma → artmob → (gerekirse) boyaci. Metal: ozbulut → statikboya → (gerekirse) boyaci.
Özbulut, statik boya ve boyacı kendi malzemesini kendisi alır; satın alma sadece Artmob için.
Bilinmeyenler: teslim süreleri, şehirler, Telegram kullanımı, kişi sayıları.
Not: ChatGPT "boyaci" = statik boya demiş; 13 Ekim listesinde statik boya ile boyacı ayrı → ayrı tutuldu.

## Sıradaki işler
1. ✅ GitHub → Cloudflare otomatik yayın (Workers Builds) bağlandı (20 Ekim 2026). Artık `main`e gönderilen her değişiklik otomatik yayınlanır; panelde Edit code ile elle değişiklik YAPILMAZ (bir sonraki yayında silinir).
2. ✅ Tedarikçi sistemi (v6) yayında ve CANLI TEST EDİLDİ (21 Ekim 2026 00:00): 5 grup bağlı
   (312 Satın Alma, 312 Artmob Ahşap, 312 Özbulut Metal, 312 Statik Boya, 312 Boyacı);
   /is 312-0025 ozbulut 2 → kart gitti, ▶️/✅ çalıştı, Murat'a bildirim geldi. (Test işi: mvh61zcvbjx)
   Bekleyen: botu tedarikçi gruplarında yönetici yapmak (ustaların düz yazı/fotoğrafı iletilsin diye) — ustalar eklenirken.
3. Sipariş girilince/durum değişince otomatik bildirim (cron)
4. İleride (bütçe olunca): yapay zekâ API ile serbest yazı anlama

## Maliyet kararı (20 Ekim 2026)
Şimdilik tamamen ücretsiz katmanlar: Telegram, Cloudflare Free, GitHub Free. Ücretli API yok.

## Gün sonu — 21 Ekim 2026 00:05
Yarın sırası:
1. Codex/ChatGPT cevabı: siparişler nereden giriliyor (giriş ekranı?), tedarikçi/üretim yeri alanı var mı → otomatik bildirim tasarımı.
2. Botta /alanlar çıktısı (Murat).
3. GitHub köprüsü (ücretsiz): bot günlük raporu depoya yazar; Claude/Codex okur; isteğe bağlı sabah özeti. Gerekli: GitHub fine-grained token (yalnız 312-asistan, Contents: read/write) → Cloudflare Secret.
4. Ustaları gruplara ekleme + botu tedarikçi gruplarında yönetici yapma.
4b. KALEM KALEM BİTTİ (Murat isteği, 21 Ekim): çok kalemli iş kartında her kalem için ayrı düğme (✅ 1, ✅ 2 … 5'li sıralar),
    tekrar basınca geri alınır; kartta "12/20 bitti" ilerlemesi; "Hepsi bitti" düğmesi; Murat'a her kalemde değil,
    yarım saatte bir toplu + hepsi bitince bildirim (gürültü olmasın). Kısmi teslim için "bitenleri sonraki adıma gönder" önerisi.
5. Otomatik bildirim (Cloudflare Cron) — sipariş girilince/durum değişince NL/TR/tedarikçi gruplarına.
İleride (bütçe olunca): Claude API ile serbest yazı/fotoğraf anlama — tahmini 100 sipariş/ay için ~5–10 $/ay (Haiku 5.5 + Sonnet 5.5 karışık).

## ÖNEMLİ BULGU — TG-03 (Codex, 21 Ekim 00:28) → ayrıntı: CODEX_DURUM.md
- Sipariş giriş ekranı = "312 Sipariş Defteri" Claude artifact'ı (claude.ai/artifact/Q6rBpA9cPiCwFLoK1vrE7q).
  Kendi Claude veritabanına yazıyor, D1'e DEĞİL. D1'deki 27 sipariş + 31 kütüphane 20 Ekim yedeğinden TEK SEFERLİK kopya.
  → 20 Ekim'den sonra girilen siparişler botta GÖRÜNMEZ.
- Kalemlerde `uretimYeri` alanı zaten var (ör. "artmob") → otomatik dağıtım önerisi için yönlendirme hazır.
- Kütüphanede `malzemeler[]` reçetesi var → satın alma ihtiyaç listesi hesaplanabilir.
- Karar önerisi (Claude): Sipariş Defteri'ni Cloudflare Worker'a taşı (aynı ekran, parola korumalı, D1'e yazar,
  ekler R2'ye). Tek doğru kaynak D1 olur; kayıt anında bot dağıtım önerisi gönderir (Cron gerekmez). Ücretsiz katman yeter.
  Geçiş günü: artifact'tan son yedek → D1'e üzerine yazmadan aktar; artifact salt-okunur arşiv olur.
- v6.1: bildirimlerde eski ekranın gerçek alan adları (uretimNot, acil "1", cizim) desteklendi.

## KARAR GÜNCELLEMESİ — 21 Ekim 00:35 (Claude)
Sipariş Defteri'ni Cloudflare'e TAŞIMAYALIM: defter `sample` (Claude) ile "Kağıttan fotoğrafla gir" özelliğini
abonelik içinde ücretsiz kullanıyor; taşınırsa bu özellik ücretli API ister.
Yeni plan (TG-03): Defter Claude artifact'ında kalır. Bot Worker'ına küçük bir MCP sunucusu (ör. /mcp/<gizli-yol>,
araç: siparis_kaydet) eklenir; Murat claude.ai'de "custom connector" olarak ekler; defter `mcp` capability ile
Kaydet anında siparişi D1'e de yazar (upsert, version+history). Bot kayıt anında dağıtım önerisi gönderir.
Geçişte artifact db'deki tüm siparişler (20 Ekim sonrası dahil) üzerine yazmadan D1'e aktarılır.

## v7 — 21 Ekim 2026 sabah (Claude)
- Sipariş Defteri köprüsü: Worker'da MCP sunucusu, yol = /mcp/<HMAC(WEBHOOK_SECRET)> (adres: botta /baglanti, gizli).
  Araçlar: siparis_kaydet {id, siparis, sessiz?}, siparis_sil {id}, kutuphane_kaydet {id, urun}.
  D1'e sürümlü yazım: version +1, document_history satırı (changed_by='defter'). Aynı veri → "ayni", yazılmaz.
- Yeni sipariş → Murat'a "🆕 YENİ SİPARİŞ" + dağıtım önerisi düğmeleri (tedarikçi başına + Hepsini gönder).
  Kural: kalem.uretimYeri → tedarikçi; artmob → +satinalma; ayak (Ayak yok değilse) → +ozbulut.
  Üretim yeri boş kalem → uyarı, elle /is. Onay düğmelerine sadece ADMIN basabilir.
- Durum değişince Murat'a "🔄 Yeni → Üretimde" bildirimi.
- /is komutu isGonder() ortak fonksiyonuna taşındı.
- Sipariş Defteri (artifact Q6rBpA9cPiCwFLoK1vrE7q) sürüm 12: `mcp` capability ("312 Asistan": siparis_kaydet, siparis_sil, kutuphane_kaydet).
  Kaydet/sil/kütüphane kayıtlarında bota da yazar (hata olursa defterin kendi kaydı etkilenmez, uyarı gösterir).
  "Tümünü bota aktar" düğmesi: tüm sipariş+kütüphaneyi sessiz modda aktarır. Kaynak kopyası: defter/index.html
  (artifact'ın asıl kaynağı claude.ai'dedir; depo kopyası yedek/inceleme içindir).
- v7.1: köprüye `sistem_durumu` (salt okunur) — Claude botun durumunu doğrudan okuyabilir.
- v7.2: KALEM KALEM BİTTİ: çok kalemli kartta her ürün için ▫️/✅ düğmesi (5'li sıra), tekrar basınca geri alır,
  kartta "İlerleme: x/y"; hepsi bitince otomatik ✅ Bitti + Murat'a TEK bildirim + sıradaki adım önerisi.
  "✅ Hepsi bitti" düğmesi tümünü işaretler. Eski (liste alanı olmayan) kartlar tek düğmeyle çalışmaya devam eder.
  Sipariş silinince bağlı iş kartları "❌ İPTAL" olur, düğmeleri kalkar. Kalem başına bildirim yerine
  yarım saatlik toplu özet → sonraki iş (Cron ile).
- v7.3: "Bitti" bildiriminde sıradaki adım için tek dokunuş düğmesi ("📨 Gönder → Statik Boya"); sistem_durumu son 10 işi gösterir.
  Not: Bitmiş (✅) iş, sipariş silinince İPTAL yapılmaz (iş zaten yapılmış).
