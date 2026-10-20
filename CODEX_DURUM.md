# TG-03 — Codex durum ve veri yapısı

Tarih: 21 Ekim 2026 (Europe/Istanbul).
İncelenen depo: muratozgur312-cmyk/312-asistan, main, b4045be28190c31a3460b7568f612261127f9ed1.
Kaynaklar: depodaki src/index.js, wrangler.toml, PROJE_KAYDI.md; 20 Ekim tarihli index.html ve tam_yedek.json dışa aktarımları; bu konuşmada doğrulanan kurulum adımları.

## Patron özeti

- Güncel depo okunabildi. Bu not mevcut davranışı belgeliyor; uygulama kodunu değiştirmiyor.
- Botun kaynağında sipariş giriş ekranı veya sipariş kaydetme API'si YOK. D1 siparişlerini okuyor; ayarları ve tedarikçi iş kayıtlarını yazıyor.
- Eski sipariş ekranı Claude artifact içinde ve Claude veritabanına yazıyor. Yeni siparişlerin D1'e otomatik aktığını gösteren bir köprü bu depoda yok.
- TG-03'te dağıtım önerisinden önce yeni siparişin D1'e hangi yoldan yazılacağı çözülmeli. Otomatik öneri, otomatik iş emri gönderimiyle aynı şey değildir.
- Cloudflare panelindeki Edit code kullanılmayacak. Kaynak main; otomatik yayın bağlantısı PROJE_KAYDI.md ve Murat'ın beyanıyla biliniyor. Canlı hesap envanteri ve son deployment burada API ile denetlenmedi.

## A — Sipariş giriş ekranı

### 1. Hangi ekran, hangi adres?
Son doğrulanmış giriş ekranı: 312 Sipariş Defteri, https://claude.ai/artifact/Q6rBpA9cPiCwFLoK1vrE7q.
Murat'ın şu anda yeni siparişleri başka bir ekrandan girip girmediği: BİLİNMİYOR.
Bot adresi: https://312-takip-botu.muratozgur312.workers.dev. İncelenen kodda GET / yalnızca “312 Asistan v6 çalışıyor (GitHub otomatik yayın).” metni döndürür; sipariş formu değildir.

### 2. Kaynak nerede?
Eski ekranın kaynak kopyası mevcut: index.html, tam yedek ZIP içinde kaynak/index.html (1306 satır).
Eski ekran Claude artifact altyapısındadır; ayrı Worker/Pages projesine taşındığı doğrulanmadı.
İncelenen GitHub deposu yalnız src/index.js, wrangler.toml ve PROJE_KAYDI.md içeriyordu; sipariş ekranı kaynağı burada yok.

### 3. D1'e nasıl yazılıyor?
Eski ekran D1'e yazmaz. `const db = await claude.use("db")` kullanır.
Kaydetme: `db.collection("siparisler").doc(id).set(body)`; yeni kayıtta `doc()` kimlik üretir.
Diğer koleksiyonlar: kutuphane ve sorunlar. onSnapshot ile sipariş/kütüphane okuması yapılır.
Botta DB adlı D1 binding var. `belgeYaz()` UPDATE documents SET data=...; eşleşme yoksa INSERT kullanır. Güncel çağrılar ayar ve iş takibi içindir; sipariş giriş endpoint'i yok.
Eski veriler için hazırlanan SQL import dışında Claude → D1 sürekli senkronizasyon mekanizması bu depoda görülmedi.

### 4. Kimlik doğrulama?
Eski ekran Claude oturumuna dayanır ve `user.can("data.write")` kontrolü yapar; ekranda ayrı bağımsız parola girişi yok.
Bot /setup formu SETUP_SECRET ve aynı-origin kontrolüyle webhook kurar; bu bir sipariş giriş sayfası değildir.
/telegram, X-Telegram-Bot-Api-Secret-Token ile korunur. Yönetici komutları ADMIN_USER_ID kontrolünden geçer. Tedarikçi callback ve mesaj işleme yolları ayrıdır.
Yeni/başka bir sipariş ekranının kimlik doğrulaması: BİLİNMİYOR.

## B — Veri yapısı

### 5. Oluşturulan D1 şeması
Aşağıdaki şema bu konuşmada oluşturulup tablo adları doğrulanan şemadır. Depoda migration dosyası yok; canlı PRAGMA çıktısı alınmadığı için sonradan yapılan değişiklikler BİLİNMİYOR.

```sql
CREATE TABLE IF NOT EXISTS documents (
  collection TEXT NOT NULL,
  id TEXT NOT NULL,
  data TEXT NOT NULL CHECK (json_valid(data)),
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TEXT,
  PRIMARY KEY (collection, id)
);

CREATE TABLE IF NOT EXISTS document_history (
  collection TEXT NOT NULL,
  document_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  data TEXT NOT NULL CHECK (json_valid(data)),
  changed_by TEXT NOT NULL,
  changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (collection, document_id, version)
);
```

`data` SQL JSON türü değil, JSON geçerlilik kontrollü TEXT'tir.
`version` otomatik artmaz; şemada trigger yok. İncelenen botta version artırımı ve document_history yazımı yok. UPDATE işlemleri updated_at sütununu da otomatik değiştirmez. JSON içindeki guncelleme alanı bunlardan ayrıdır.
Kütüphanenin JSON içindeki surum/gecmis alanları ise eski ekranda uygulama koduyla güncellenir; D1 version ile aynı şey değildir.

### 6. Sipariş alanları — eski ekran/yedek
D1 yerleşimi: collection='siparisler', id=belge kimliği, data=sipariş JSON'u. id ile sipariş numarası her zaman aynı değildir.

| Alan | Anlam |
|---|---|
| no | Eski ekranın gerçek sipariş numarası alanı, ör. 312-0001. siparisNo bu yedeğin standart alanı değil. Bot geriye uyumluluk için ikisini de okur. |
| tur | satis veya ssh (satış sonrası hizmet) |
| ilgili | SSH için bağlı/ilk sipariş numarası |
| tarih | Sipariş tarihi, YYYY-MM-DD |
| durum | yeni, uretim, hazir, teslim |
| acil | Eski formda boş metin=hayır, "1"=evet; boolean varsayılmamalı |
| teslimTarihi | Planlanan teslim tarihi, YYYY-MM-DD |
| teslimOto | Otomatik teslim hesabını kullanma durumu; elle tarih düzenlendiğinde false olur |
| musteri | Müşteri adı |
| telefon | Müşteri telefonu |
| adres | Adres |
| posta | Posta kodu |
| sehir | Şehir |
| ulke | Ülke; ülke kodu olmak zorunda değil, ör. Hollanda |
| nakliye | dahil, ayri veya yok |
| nakUcret | Ayrı nakliye ücreti |
| alinan | Alınan ödeme/kapora |
| odeme | Ödeme yöntemi |
| cizim | Çizim bağlantısı için metin alanı |
| uretimNot | Üretime yönelik serbest not |
| not | Genel/satış notu; özel bilgi veya tutar içerebilir |
| ekler[] | Dosya referansları: id, name, type |
| isaret | Alan bazlı kontrol uyarıları: ör. alan: {tur: pembe/sari, neden: açıklama} |
| yoksay[] | Kullanıcının bilerek geçtiği uyarı anahtarları |
| olusturma | İlk kayıt ISO zaman damgası |
| guncelleme | Son kayıt ISO zaman damgası |
| kalemler[] | Ürün satırları |

Kalem alanları:

| Alan | Anlam |
|---|---|
| urun, olcu, adet | Ürün adı, metin ölçü açıklaması, ürün adedi |
| uretimYeri | Serbest metin üretim yeri/tedarikçi ataması |
| malzeme, marka, renk | Ana malzeme, marka/dekor kodu, renk/yüzey |
| ayak, ayakEk, ayakAdet, ayakRenk | Ayak modeli, ek tanım, satır toplam ayak adedi, renk |
| fiyat | Bir ürünün fiyatı; toplam hesapta adet ile çarpılır |
| paket | Satırdaki toplam paket adedi |
| m3, m3Oto | Satır hacmi ve otomatik hesap durumu |
| urunNot | Ürün serbest notu; hassas içerik barındırabilir |
| libId | Kütüphane belge kimliği |
| tekSeferlik | Kütüphaneye eklenmeden tek seferlik üretim tercihi |
| malzemeler[] | Bir ürün için BOM: ad, miktar, birim, isteğe bağlı not |
| isaret, yoksay[] | Kalem alanlarının kontrol uyarıları ve geçilen uyarılar |

Boş sayısal alanlar eski kayıtlarda boş metin olabilir. Toplam/kalan bağımsız sipariş alanları değil, ekranda hesaplanır. Standart otomatik teslim hesabı tarih +42 gün; acil +28 gündür. Bunlar tedarikçi terminleri değildir.

### 7. Tedarikçi / üretim yeri / parça bilgisi
Eski kalem alanı: `kalemler[].uretimYeri`. Kütüphanede: `uretimYeri`.
Eski şemada ayrı parça kimliği, çok aşamalı tedarikçi rotası veya ayak tedarikçisi alanı yok. Ayak bilgileri ayrı özellik alanlarında; üretim yeri tek metindir.
Güncel bot ayrıca collection='isler' içinde tedarikci, tedarikciAd, siparisNo ve seçili 1 tabanlı kalem numaralarını kalemler alanında tutar. Bu iş kaydındaki kalemler ile sipariş JSON'undaki ürün nesnelerinden oluşan kalemler aynı veri tipi değildir.

### 8. Durum değerleri
Eski sipariş ekranında tam liste: yeni → Yeni; uretim → Üretimde; hazir → Hazır; teslim → Teslim edildi.
Tedarikçi işlerinin durumları ayrı iş kayıtlarıdır; sipariş durumuyla birleştirilmemeli.

### 9. Ekler nerede?
Eski ekran: `assets = await claude.use("assets")`; `assets.upload(file)` dönüşü `{id, contentType}`; ekler içine `{id,name,type}` yazılır. Görüntüleme yolu `/_blob/<id>`; Claude artifact ortamına aittir.
Tam yedek ZIP'te dosyalar/ altında 17 dosya ve dosya_dizini.csv eşlemesi var. Eski referansları D1'e yazmak dosya baytlarını taşımaz.
İncelenen wrangler.toml içinde R2 veya KV binding yok. Başka yerde oluşturulmuş R2/KV: BİLİNMİYOR. Güncel dosya taşıması: BİLİNMİYOR.
Botun erişimi için dosyaların erişebildiği depoya gerçekten taşınması ve eski asset id → yeni anahtar eşlemesi gerekir. Özel dosyalar yetkili Worker üzerinden sunulmalı; eski /_blob yolu Worker alan adına eklenerek çalışmaz. Tedarikçi kartlarına orijinal müşteri föyü otomatik gönderilmemeli.

### 10. Kütüphane ve reçete
`fillFromLib()` olcu, uretimYeri, malzeme, marka, renk ve ayak alanlarını ürün satırına kopyalar. Normalde boş alanları doldurur; kullanıcı 'Kütüphaneden doldur' dediğinde force ile mevcut değerleri de değiştirebilir.
`malzemeler[]` bir ürün için reçetedir; satıra derin kopyalanır. malzemeler[].miktar, sipariş kaleminin adet alanıyla ihtiyaç hesabında çarpılır. Aynı üretim yeri + normalize malzeme adı + birim için toplanır.
`matNeeds()` varsayılan olarak yeni ve uretim durumlarını kapsar; kullanıcı filtreyi değiştirebilir. Eksik reçete/miktar uyarılır. Örnek: 1 ürün için 4 menteşe, 3 ürün → 12 menteşe.
Bu sistem girilmiş reçeteyi toplar. Teknik çizimden plaka kesim optimizasyonu, stok düşümü, fire hesabı veya otomatik gerçek satın alma yok.
Kütüphaneden kopyalanan ayakAdet ve paket ürün adediyle çarpılır; BOM miktarını bu aşamada tekrar çarpmayın.

## C — Envanter ve import

### 11. Bilinen kaynaklar
| Kaynak | Bilinen |
|---|---|
| Worker | 312-takip-botu; src/index.js |
| D1 | 312-siparisler; binding DB; id 6032f827-6f53-4522-b285-371d4f6b9d39 |
| D1 koleksiyonları | Eski: siparisler, kutuphane, sorunlar. Güncel kodda ayrıca ayarlar ve isler kullanılıyor. Canlı sayılar sorgulanmadı. |
| Pages / başka Worker | BİLİNMİYOR; bu depoda tanım yok |
| R2 / KV | Bu depoda binding yok; hesap genelinde varlığı BİLİNMİYOR |
| Cron | wrangler.toml içinde triggers.crons yok; export default içinde scheduled handler yok. Panelde başka Cron olup olmadığı BİLİNMİYOR. |

PROJE_KAYDI.md'de otomatik bildirim/Cron hâlâ yapılacak iş olarak kayıtlı. Hesap genelini göremediğimiz için 'hiç başka kaynak yok' sonucu çıkarılamaz.

### 12. Yedekten import
Kaynak tam_yedek.json: koleksiyonlar.siparisler (27), kutuphane (31), sorunlar (0).
Python ile SQL üretildi. Her belge için:
1. Aynı collection/id yoksa documents'a INSERT, kaynak JSON alanları aynen korunur.
2. Aynı collection/document_id/version geçmişi yoksa mevcut belgeden history satırı INSERT; changed_by='backup-import-2026-10-20'.
Mevcut belge varsa üzerine yazmaz; tekrar çalıştırma güncelleme/senkronizasyon değildir. Önceden var olan belge için history o mevcut belgeyi alır.
Yerel SQLite doğrulaması: 58 kayıt, 58 geçmiş satırı; iki kez çalıştırmada çoğalma yok; JSON kaynakla eşit.
İlk SQL dosyasının başındaki '--' açıklamalar Cloudflare Console'a yapıştırılırken sorun çıkardı ('No SQL statements detected'); açıklamasız 312-aktarim-duzeltilmis.txt verildi. Son çoklu sorgu sonucundaki 'This query returned no data' tek başına toplu aktarım sonucunu kanıtlamaz.
Sonraki proje kaydı D1'de 27/31 bulunduğunu ve botun okuduğunu bildiriyor; bu notta canlı veritabanı yeniden sorgulanmadı.
Tekrar kullanılabilir üretilmiş SQL/TXT mevcut, fakat üretici Python betiği önceki oturumda geçici komut olarak çalıştırılmıştı ve incelenen GitHub deposuna eklenmemişti. Depoda import aracı/migration yok. Yeniden aktarım öncesi canlı yedek ve collection/id sayımını kontrol edin; yeni siparişlerin üzerine eski yedeği yazmayın.

## Maskelenmiş örnek kayıt
Eski yedekteki 312-0001 kaydından seçilmiş alanlar. Hassas değerler maskelendi; bu üretim/tedarikçiye gönderilecek payload değildir. _id SQL id sütunundadır, data içine eklenmedi.

```json
{
  "no": "312-0001",
  "tur": "satis",
  "ilgili": "",
  "tarih": "2026-08-11",
  "durum": "uretim",
  "acil": "",
  "teslimTarihi": "2026-09-22",
  "teslimOto": true,
  "musteri": "***",
  "telefon": "***",
  "adres": "***",
  "posta": "***",
  "sehir": "***",
  "ulke": "Hollanda",
  "nakliye": "dahil",
  "nakUcret": "***",
  "alinan": "***",
  "odeme": "***",
  "cizim": "",
  "uretimNot": "",
  "not": "***",
  "ekler": [],
  "isaret": {},
  "yoksay": [],
  "olusturma": "2026-10-07T19:30:00Z",
  "guncelleme": "2026-10-13T10:34:26.898Z",
  "kalemler": [
    {
      "urun": "Rotterdam masa tablası",
      "olcu": "170x100",
      "adet": 1,
      "uretimYeri": "artmob",
      "malzeme": "Black beton",
      "marka": "hazır",
      "renk": "yok",
      "ayak": "Ayak yok",
      "ayakEk": "",
      "ayakAdet": "",
      "ayakRenk": "",
      "fiyat": "***",
      "paket": 1,
      "m3": 0.18,
      "m3Oto": false,
      "libId": "qhm01dkmtmwiyqgji01j",
      "tekSeferlik": false,
      "urunNot": "",
      "yoksay": ["y:bom"]
    },
    {
      "urun": "Rotterdam orta sehpa tablası",
      "olcu": "140x80",
      "adet": 1,
      "uretimYeri": "artmob",
      "malzeme": "Black beton",
      "marka": "hazır",
      "renk": "yok",
      "ayak": "Ayak yok",
      "ayakEk": "",
      "ayakAdet": "",
      "ayakRenk": "",
      "fiyat": "***",
      "paket": 1,
      "m3": 0.12,
      "m3Oto": false,
      "libId": "s6lvq0piozbrvi0vbf35",
      "tekSeferlik": false,
      "urunNot": "",
      "yoksay": ["y:bom"]
    }
  ]
}
```

## TG-03 için önerilen sonraki uygulama adımı (henüz yapılmadı)
Önce gerçek giriş ekranı/otoritatif yazma yolu netleştirilmeli. Yeni sipariş ve revizyonu ortak, kimlik doğrulamalı kayıt fonksiyonuyla D1'e yazın; sürümü ve geçmişi atomik güncelleyin. Aynı collection/id/version için bir kez dağıtım önerisi oluşturun, Murat onayıyla iş emrine dönüştürün. Cron seçilirse ilk çalışmada mevcut 27 siparişi yeni sayıp toplu göndermesin; başlangıç durumu ve tekrar önleme kaydı olsun.
Tedarikçi payload'ı izin listesiyle üretilsin. Müşteri adı/telefon/adres/e-posta, fiyat/kapora/tahsilat, ham serbest notlar ve orijinal föy fotoğrafları tedarikçiye gitmesin. Statik boya ve boyacı ayrı aktörlerdir; rota için güncel PROJE_KAYDI.md esas alınsın.
