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
- v5.1: genel not gönderilmez, notlardaki para ifadeleri temizlenir  ← CANLI (20 Ekim 2026)

## Sıradaki işler
1. GitHub → Cloudflare otomatik yayın (Workers Builds) bağlantısı
2. Tedarikçi grupları (Özbulut, Artmob, boyacı): iş kartı + Başladım/Bitti/Sorun var düğmeleri
3. Sipariş girilince/durum değişince otomatik bildirim (cron)
4. İleride (bütçe olunca): yapay zekâ API ile serbest yazı anlama

## Maliyet kararı (20 Ekim 2026)
Şimdilik tamamen ücretsiz katmanlar: Telegram, Cloudflare Free, GitHub Free. Ücretli API yok.
