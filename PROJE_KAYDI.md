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
