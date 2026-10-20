// 312 Asistan — Cloudflare Worker (Telegram bot + D1)
// Sürüm: v6 (20 Ekim 2026) — tedarikçi grupları, iş kartı + durum düğmeleri, /isler; önceki: v5.1 — genel sipariş notu gruplara gitmez, notlardaki para ifadeleri silinir; — bildirimler izin listesiyle (para/iletişim bilgisi asla gitmez), /alanlar

const headers = {
  "Content-Type": "text/plain; charset=utf-8",
  "Cache-Control": "no-store"
};

function text(message, status = 200) {
  return new Response(message, { status, headers });
}

async function telegram(env, method, body) {
  const response = await fetch(
    `https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }
  );
  const result = await response.json();
  if (!response.ok || !result.ok) {
    throw new Error("Telegram işlemi başarısız: " + (result.description || response.status));
  }
  return result.result;
}

// ---------- Yardımcılar ----------

const MAX_LEN = 3900; // Telegram sınırı 4096

async function send(env, chatId, msg) {
  let t = String(msg || "").trim() || "(boş)";
  if (t.length > MAX_LEN) t = t.slice(0, MAX_LEN) + "\n… (devamı kesildi)";
  await telegram(env, "sendMessage", {
    chat_id: chatId,
    text: t,
    disable_web_page_preview: true
  });
}

function parse(row) {
  try { return JSON.parse(row.data); } catch { return {}; }
}

function pick(d, keys) {
  for (const k of keys) {
    const v = d[k];
    if (v !== undefined && v !== null && String(v).trim() !== "") return String(v);
  }
  return "";
}

function tarihKisa(v) {
  if (!v) return "";
  const s = String(v);
  return /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : s;
}

const DURUMLAR = {
  yeni: "Yeni", uretim: "Üretimde", hazir: "Hazır", sevkiyat: "Sevkiyatta",
  teslim: "Teslim edildi", iptal: "İptal", beklemede: "Beklemede"
};
function durumAdi(v) {
  const k = String(v || "").toLowerCase();
  return DURUMLAR[k] || v;
}
const SIPARIS_SIRA = "COALESCE(json_extract(data,'$.siparisNo'), json_extract(data,'$.no'), id) DESC";

function siparisSatiri(row) {
  const d = parse(row);
  const no = pick(d, ["siparisNo", "no", "siparisNumarasi", "kod"]) || row.id;
  const musteri = pick(d, ["musteri", "musteriAdi", "adSoyad", "musteriAdSoyad", "ad"]);
  const durum = durumAdi(pick(d, ["durum", "status", "asama"]));
  const tarih = tarihKisa(pick(d, ["siparisTarihi", "tarih", "olusturma"]));
  return [no, musteri, durum, tarih].filter(Boolean).join(" · ");
}

// Kayıttaki tüm alanları okunur metne çevirir
function detay(d, girinti = "") {
  const satirlar = [];
  for (const [k, v] of Object.entries(d)) {
    if (v === null || v === undefined || v === "") continue;
    if (k === "gecmis") continue; // değişiklik geçmişi uzun, atla
    if (Array.isArray(v)) {
      if (v.length === 0) continue;
      satirlar.push(`${girinti}${k}:`);
      v.forEach((item, i) => {
        if (item && typeof item === "object") {
          const ozet = Object.entries(item)
            .filter(([, x]) => x !== "" && x !== null && typeof x !== "object")
            .map(([a, b]) => `${a}=${b}`).join(", ");
          satirlar.push(`${girinti}  ${i + 1}) ${ozet}`);
        } else {
          satirlar.push(`${girinti}  ${i + 1}) ${item}`);
        }
      });
    } else if (typeof v === "object") {
      satirlar.push(`${girinti}${k}:`);
      satirlar.push(detay(v, girinti + "  "));
    } else {
      satirlar.push(`${girinti}${k}: ${v}`);
    }
  }
  return satirlar.join("\n");
}

const SIPARIS_FILTRE = "(collection LIKE '%sipari%' OR collection = 'orders')";

const YARDIM = [
  "312 Asistan komutları:",
  "",
  "/ozet — veritabanında ne var (koleksiyon ve kayıt sayıları)",
  "/siparisler — son 15 sipariş (numaraya göre)",
  "/siparisler yeni — sadece yeni siparişler (uretim, hazir… de yazılabilir)",
  "/siparisler hepsi — tüm siparişler",
  "/siparis 312-0020 — tek siparişin tüm detayı",
  "/ara kelime — tüm kayıtlarda arama (müşteri, ürün, malzeme…)",
  "/kutuphane — kütüphanedeki ürünler",
  "/kutuphane rotterdam — kütüphanede ürün ara",
  "",
  "Gruplar:",
  "/bildir 312-0025 — siparişi NL ve TR gruplarına gönder",
  "/bildir 312-0025 tr — sadece üretim grubuna",
  "/onizle 312-0025 — gruba gidecek mesajı önce sadece sana gösterir",
  "/gruplar — bağlı grupları göster",
  "/alanlar — siparişlerde hangi bilgiler var (🔒 gizli olanlar)",
  "/baglan nl veya /baglan tr — (grubun içinde yazılır) grubu bağlar",
  "",
  "Tedarikçiler:",
  "/is 312-0025 ozbulut — iş emrini tedarikçiye gönder (fiyat/müşteri gitmez)",
  "/is 312-0025 ozbulut 2,4 | not — sadece 2. ve 4. ürün, ek notla",
  "/isler — açık işler (/isler ozbulut, /isler hepsi)",
  "/tedarikci — bağlı tedarikçiler (grupta: /tedarikci ozbulut Özbulut Metal)",
  "",
  "/kimlik — Telegram kullanıcı numaranız",
  "/dbtest — veritabanı bağlantı testi"
].join("\n");

const KOMUT_MENUSU = [
  { command: "siparisler", description: "Son 15 sipariş" },
  { command: "siparis", description: "Sipariş detayı (ör. /siparis 312-0020)" },
  { command: "ara", description: "Tüm kayıtlarda ara" },
  { command: "kutuphane", description: "Kütüphane ürünleri" },
  { command: "bildir", description: "Siparişi gruplara gönder (ör. /bildir 312-0025)" },
  { command: "onizle", description: "Gruba gidecek mesajın önizlemesi" },
  { command: "gruplar", description: "Bağlı gruplar" },
  { command: "baglan", description: "Grubu bağla (grupta: /baglan nl veya tr)" },
  { command: "is", description: "Tedarikçiye iş emri (ör. /is 312-0025 ozbulut)" },
  { command: "isler", description: "Açık işler" },
  { command: "tedarikci", description: "Tedarikçiler" },
  { command: "ozet", description: "Veritabanı özeti" },
  { command: "yardim", description: "Komut listesi" }
];


// ---------- Gruplar ve bildirim ----------

// Grup numaraları veritabanında saklanır: collection='ayarlar', id='gruplar'
async function gruplariOku(env) {
  const row = await env.DB.prepare(
    "SELECT data FROM documents WHERE collection='ayarlar' AND id='gruplar'"
  ).first();
  return row ? parse(row) : {};
}

async function gruplariYaz(env, g) {
  const data = JSON.stringify(g);
  const r = await env.DB.prepare(
    "UPDATE documents SET data=?1 WHERE collection='ayarlar' AND id='gruplar'"
  ).bind(data).run();
  if (!r.meta || !r.meta.changes) {
    await env.DB.prepare(
      "INSERT INTO documents (collection,id,data) VALUES ('ayarlar','gruplar',?1)"
    ).bind(data).run();
  }
}

// Gruplara SADECE bu listedeki alanlar gider (izin listesi).
// Listede olmayan her alan (fiyat, kapora, alınan, telefon, adres, işaret…) otomatik gizli kalır.
const PARA_ILETISIM = /(tel|phone|gsm|fiyat|price|tutar|odeme|ödeme|odenen|ödenen|kapora|avans|alinan|alınan|kalan|adres|address|posta|email|mail|iban|maliyet|whatsapp|indirim|toplam|ucret|ücret|para|euro|kur|kar|kâr|isaret|işaret)/i;

// Ürün kalemlerinde gösterilecek alanlar ve etiketleri
const KALEM_ALANLARI = [
  ["urun", "Ürün", "Product"], ["ad", "Ürün", "Product"], ["urunAdi", "Ürün", "Product"],
  ["olcu", "Ölçü", "Maat"], ["malzeme", "Malzeme", "Materiaal"], ["tabla", "Tabla", "Blad"],
  ["marka", "Malzeme/plaka", "Plaat"], ["renk", "Renk", "Kleur"], ["boya", "Boya", "Verf"],
  ["ayak", "Ayak", "Poot"], ["ayakEk", "Ayak ek", "Poot extra"], ["ayakAdet", "Ayak adedi", "Aantal poten"],
  ["ayakRenk", "Ayak rengi", "Kleur poot"], ["adet", "Adet", "Aantal"], ["paket", "Paket", "Pakketten"],
  ["uretimYeri", "Üretim yeri", null], ["urunNot", "Not", "Notitie"], ["not", "Not", "Notitie"]
];

// Sipariş genelinde gösterilecek alanlar
const GENEL_ALANLAR = [
  ["siparisTarihi", "Sipariş tarihi", "Besteldatum"], ["teslimTarihi", "Teslim tarihi", "Leverdatum"],
  ["termin", "Termin", "Termijn"], ["acil", "Acil", "Spoed"], ["nakliye", "Nakliye", "Transport"],
  ["montaj", "Montaj", "Montage"], ["paketAdedi", "Paket adedi", "Pakketten"],
  ["uretimNotu", "Üretim notu", null]
  // "not" (genel satış notu) bilerek YOK: içinde fiyat/kapora yazıyor
];

// Serbest yazıdaki para bilgisini temizler:
// - kapora/havale/fiyat/ödeme/kalan/dekont geçen cümleler tamamen çıkarılır
// - 40.000 / 35.000 / 500 TL / €300 gibi tutarlar "…" olur
const PARA_CUMLE = /(kapora|havale|dekont|ödeme|odeme|ödendi|odendi|kalan|avans|tahsil|iban)/i;
const PARA_SAYI = /\(?\s*(?:[€₺]\s*)?\b\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?\b(?:\s*(?:TL|tl|₺|€|euro|eur)\b)?(?:\s*yazıyor)?\s*\)?|\b\d+\s*(?:TL|tl|₺|€|euro|eur)\b|[€₺]\s*\d+/g;
function notTemizle(t) {
  return String(t)
    .split(/(?<=[.!?\n])\s+/)
    .filter(c => !PARA_CUMLE.test(c))
    .map(c => c.replace(PARA_SAYI, "").replace(/\s{2,}/g, " ").replace(/\s+([.,;])/g, "$1").trim())
    .filter(Boolean)
    .join(" ");
}

function deger(v, dil) {
  if (v === true) return dil === "nl" ? "Ja" : "Evet";
  if (v === false) return dil === "nl" ? "Nee" : "Hayır";
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}T/.test(v)) return v.slice(0, 10);
  return String(v);
}

function alanYaz(obj, liste, dil, girinti) {
  const out = [];
  const goruldu = new Set();
  for (const [k, tr, nl] of liste) {
    const etiket = dil === "nl" ? nl : tr;
    if (!etiket || PARA_ILETISIM.test(k)) continue;
    const v = obj[k];
    if (v === undefined || v === null || v === "" || typeof v === "object") continue;
    let yazi = deger(v, dil);
    if (/not/i.test(k)) yazi = notTemizle(yazi);
    if (!yazi) continue;
    const satir = `${girinti}${etiket}: ${yazi}`;
    if (goruldu.has(satir)) continue;
    goruldu.add(satir);
    out.push(satir);
  }
  return out;
}

function kalemleriBul(d) {
  for (const k of ["kalemler", "urunler", "items"]) if (Array.isArray(d[k])) return d[k];
  return [];
}

function siparisMesaji(d, dil) {
  const no = pick(d, ["siparisNo", "no"]);
  const musteri = pick(d, ["musteri", "musteriAdi", "adSoyad", "musteriAdSoyad"]);
  const durum = String(d.durum || "").toLowerCase();
  const satirlar = dil === "nl"
    ? [`🏠 BESTELLING ${no}`, musteri ? `Klant: ${musteri}` : "", d.durum ? `Status: ${NL_DURUM[durum] || d.durum}` : ""]
    : [`🛠 ÜRETİM — Sipariş ${no}`, musteri ? `Müşteri: ${musteri}` : "", d.durum ? `Durum: ${durumAdi(d.durum)}` : ""];
  satirlar.push(...alanYaz(d, GENEL_ALANLAR, dil, ""));
  const kalemler = kalemleriBul(d);
  if (kalemler.length) {
    satirlar.push("", dil === "nl" ? "Producten:" : "Ürünler:");
    kalemler.forEach((k, i) => {
      if (!k || typeof k !== "object") return;
      const alanlar = alanYaz(k, KALEM_ALANLARI, dil, "   ");
      satirlar.push(`${i + 1})` + (alanlar.length ? "\n" + alanlar.join("\n") : ""));
    });
  }
  const ekler = Array.isArray(d.ekler) ? d.ekler.length : 0;
  if (ekler) satirlar.push("", dil === "nl" ? `📎 ${ekler} bijlage(n) in het systeem` : `📎 Sistemde ${ekler} ek var (föy/fotoğraf)`);
  return satirlar.filter((x, i, a) => x !== "" || (i > 0 && a[i - 1] !== "")).join("\n");
}

const NL_DURUM = {
  yeni: "Nieuw", uretim: "In productie", hazir: "Klaar", sevkiyat: "Onderweg",
  teslim: "Geleverd", iptal: "Geannuleerd", beklemede: "In afwachting"
};

async function siparisBul(env, arg) {
  let row = await env.DB.prepare(
    `SELECT id, collection, data FROM documents WHERE ${SIPARIS_FILTRE}
     AND (id = ?1 OR json_extract(data,'$.siparisNo') = ?1 OR json_extract(data,'$.no') = ?1)
     LIMIT 1`
  ).bind(arg).first();
  if (!row) {
    row = await env.DB.prepare(
      `SELECT id, collection, data FROM documents WHERE ${SIPARIS_FILTRE} AND data LIKE ?1 LIMIT 1`
    ).bind(`%${arg}%`).first();
  }
  return row;
}

async function grubaGonder(env, chatId, msg) {
  try {
    await send(env, chatId, msg);
    return true;
  } catch (e) {
    return String(e.message || e);
  }
}


// ---------- Tedarikçiler ve iş takibi ----------

let ORIGIN = ""; // worker adresi (webhook yenilemek için)

async function ayarOku(env, id) {
  const row = await env.DB.prepare(
    "SELECT data FROM documents WHERE collection='ayarlar' AND id=?1"
  ).bind(id).first();
  return row ? parse(row) : {};
}

async function belgeYaz(env, collection, id, obj) {
  const data = JSON.stringify(obj);
  const r = await env.DB.prepare(
    "UPDATE documents SET data=?3 WHERE collection=?1 AND id=?2"
  ).bind(collection, id, data).run();
  if (!r.meta || !r.meta.changes) {
    await env.DB.prepare(
      "INSERT INTO documents (collection,id,data) VALUES (?1,?2,?3)"
    ).bind(collection, id, data).run();
  }
}

function anahtar(s) {
  return String(s || "").toLowerCase()
    .replace(/ı/g, "i").replace(/ğ/g, "g").replace(/ü/g, "u")
    .replace(/ş/g, "s").replace(/ö/g, "o").replace(/ç/g, "c")
    .replace(/[^a-z0-9]/g, "");
}

function zaman(iso) {
  try {
    return new Date(iso).toLocaleString("tr-TR", {
      timeZone: "Europe/Istanbul", day: "2-digit", month: "2-digit",
      hour: "2-digit", minute: "2-digit"
    });
  } catch { return iso; }
}

const IS_DURUM = {
  gonderildi: "📨 Gönderildi",
  basladi: "▶️ Başladı",
  bitti: "✅ Bitti",
  sorun: "⚠️ Sorun var"
};

// İş sırası: bir tedarikçi "Bitti" deyince Murat'a sıradaki adım önerilir
// (ChatGPT TG-02: ozbulut -> statik boya; 13 Ekim: statik boya -> gerekirse boyacı)
const SONRAKI = {
  ozbulut: ["statikboya"],
  statikboya: ["boyaci"]
};

const IS_DUGMELER = id => ({
  inline_keyboard: [[
    { text: "▶️ Başladım", callback_data: `is:${id}:basladi` },
    { text: "✅ Bitti", callback_data: `is:${id}:bitti` }
  ], [
    { text: "⚠️ Sorun var", callback_data: `is:${id}:sorun` }
  ]]
});

// Tedarikçiye giden iş kartı: müşteri adı, fiyat, iletişim YOK
function isKarti(d, kalemNolar, ekNot) {
  const no = pick(d, ["siparisNo", "no"]);
  const satirlar = [`🔧 İŞ EMRİ — Sipariş ${no}`];
  const teslim = pick(d, ["teslimTarihi", "termin"]);
  if (teslim) satirlar.push(`Teslim (sipariş): ${tarihKisa(teslim)}`);
  const kalemler = kalemleriBul(d);
  const secilen = kalemNolar.length ? kalemNolar : kalemler.map((_, i) => i + 1);
  satirlar.push("");
  for (const n of secilen) {
    const k = kalemler[n - 1];
    if (!k || typeof k !== "object") continue;
    const alanlar = alanYaz(k, KALEM_ALANLARI.filter(a => a[0] !== "uretimYeri"), "tr", "   ");
    satirlar.push(`${n})` + (alanlar.length ? "\n" + alanlar.join("\n") : ""));
  }
  if (ekNot) satirlar.push("", "📝 Not: " + notTemizle(ekNot));
  satirlar.push("", "İşe başlayınca ▶️, bitince ✅ basın. Sorun olursa ⚠️ basıp yazın veya fotoğraf atın.");
  return satirlar.join("\n");
}

function durumSatiri(is) {
  const son = is.gecmis && is.gecmis[is.gecmis.length - 1];
  if (!son || is.durum === "gonderildi") return "";
  return `\n\nDurum: ${IS_DURUM[is.durum]} — ${son.kim}, ${zaman(son.tarih)}`;
}

async function geriBildirim(env, cq) {
  const [, id, yeni] = String(cq.data || "").split(":");
  const row = await env.DB.prepare(
    "SELECT data FROM documents WHERE collection='isler' AND id=?1"
  ).bind(id).first();
  if (!row || !IS_DURUM[yeni]) {
    await telegram(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "Bu iş bulunamadı." });
    return;
  }
  const is = parse(row);
  const kim = [cq.from.first_name, cq.from.last_name].filter(Boolean).join(" ") || "—";
  is.durum = yeni;
  is.gecmis = is.gecmis || [];
  is.gecmis.push({ durum: yeni, kim, tarih: new Date().toISOString() });
  await belgeYaz(env, "isler", id, is);

  await telegram(env, "answerCallbackQuery", {
    callback_query_id: cq.id,
    text: yeni === "sorun" ? "Sorunu bu gruba yazın veya fotoğraf atın." : IS_DURUM[yeni] + " olarak kaydedildi."
  });
  try {
    await telegram(env, "editMessageText", {
      chat_id: cq.message.chat.id,
      message_id: cq.message.message_id,
      text: is.metin + durumSatiri(is),
      reply_markup: IS_DUGMELER(id)
    });
  } catch {}
  if (yeni === "sorun") {
    try { await send(env, cq.message.chat.id, "⚠️ Sorunu buraya yazın veya fotoğraf atın, Murat Bey'e iletilecek."); } catch {}
  }
  if (env.ADMIN_USER_ID) {
    let bilgi = `${IS_DURUM[yeni]} — ${is.tedarikciAd}\nSipariş ${is.siparisNo} (iş ${id})\n${kim}, ${zaman(new Date().toISOString())}`;
    if (yeni === "bitti" && SONRAKI[is.tedarikci]) {
      const urun = is.kalemler && is.kalemler.length ? " " + is.kalemler.join(",") : "";
      bilgi += "\n\nSıradaki adım için:\n" +
        SONRAKI[is.tedarikci].map(t => `/is ${is.siparisNo} ${t}${urun}`).join("\n");
    }
    await send(env, String(env.ADMIN_USER_ID).trim(), bilgi);
  }
}

// Grup numarası değişirse (grup "süper grup" olunca) kayıtları güncelle
async function grupNoTasi(env, eski, yeni) {
  for (const id of ["gruplar", "tedarikciler"]) {
    const g = await ayarOku(env, id);
    let degisti = false;
    for (const v of Object.values(g)) {
      if (v && String(v.id) === String(eski)) { v.id = yeni; degisti = true; }
    }
    if (degisti) await belgeYaz(env, "ayarlar", id, g);
  }
}

// Tedarikçi grubunda ustanın yazdığı / attığı her şey Murat'a iletilir
async function tedarikciMesajiIlet(env, message) {
  const ted = await ayarOku(env, "tedarikciler");
  const t = Object.values(ted).find(v => v && String(v.id) === String(message.chat.id));
  if (!t || !env.ADMIN_USER_ID) return;
  const admin = String(env.ADMIN_USER_ID).trim();
  const kim = [message.from.first_name, message.from.last_name].filter(Boolean).join(" ");
  await send(env, admin, `📩 ${t.ad} — ${kim}:`);
  await telegram(env, "forwardMessage", {
    chat_id: admin, from_chat_id: message.chat.id, message_id: message.message_id
  });
}

// ---------- Komutlar ----------

async function komutCalistir(env, command, message) {
  const bosluk = command.indexOf(" ");
  const ad = (bosluk === -1 ? command : command.slice(0, bosluk))
    .toLowerCase().replace(/@.*$/, "");
  const arg = bosluk === -1 ? "" : command.slice(bosluk + 1).trim();

  if (ad === "/start" || ad === "/yardim" || ad === "/help") {
    try { await telegram(env, "setMyCommands", { commands: KOMUT_MENUSU }); } catch {}
    return "312 Asistan çalışıyor ve sipariş sistemine bağlı.\n\n" + YARDIM;
  }

  if (ad === "/kimlik") {
    return "Telegram kullanıcı numaranız: " + message.from.id;
  }

  if (ad === "/tedarikci") {
    if (!message.chat || message.chat.type === "private") {
      const ted = await ayarOku(env, "tedarikciler");
      const l = Object.entries(ted).map(([k, v]) => `• ${v.ad}  (kısa ad: ${k})`);
      return (l.length ? "Bağlı tedarikçiler:\n" + l.join("\n") : "Henüz tedarikçi bağlı değil.") +
        "\n\nYeni tedarikçi: tedarikçinin grubunda /tedarikci ozbulut Özbulut Metal yazın.";
    }
    const parcalar = arg.split(/\s+/).filter(Boolean);
    const kisa = anahtar(parcalar.shift());
    const adTam = parcalar.join(" ") || message.chat.title || kisa;
    if (!kisa) return "Kullanım: /tedarikci ozbulut Özbulut Metal";
    const ted = await ayarOku(env, "tedarikciler");
    ted[kisa] = { id: message.chat.id, ad: adTam, tarih: new Date().toISOString() };
    await belgeYaz(env, "ayarlar", "tedarikciler", ted);
    // Düğmelerin çalışması için webhook'u yenile
    if (ORIGIN && env.WEBHOOK_SECRET) {
      try {
        await telegram(env, "setWebhook", {
          url: ORIGIN + "/telegram", secret_token: env.WEBHOOK_SECRET,
          allowed_updates: ["message", "callback_query"]
        });
      } catch {}
    }
    return `✅ Bu grup tedarikçi olarak bağlandı: ${adTam} (kısa ad: ${kisa}).\nİş göndermek için bota özelden: /is 312-0025 ${kisa}`;
  }

  if (ad === "/is") {
    // /is 312-0025 ozbulut            -> tüm ürünler
    // /is 312-0025 ozbulut 2,4        -> sadece 2. ve 4. ürün
    // /is 312-0025 ozbulut 2 | not    -> ek not
    const [solKisim, ...notP] = arg.split("|");
    const ekNot = notP.join("|").trim();
    const [no, tKisa, kalemStr] = solKisim.trim().split(/\s+/);
    if (!no || !tKisa) return "Kullanım: /is 312-0025 ozbulut  (belirli ürünler: /is 312-0025 ozbulut 2,4 | ek not)";
    const ted = await ayarOku(env, "tedarikciler");
    const t = ted[anahtar(tKisa)];
    if (!t) return `"${tKisa}" adında tedarikçi yok. Liste için /tedarikci yazın.`;
    const row = await siparisBul(env, no);
    if (!row) return `"${no}" numaralı sipariş bulunamadı.`;
    const d = parse(row);
    const kalemNolar = (kalemStr || "").split(/[,\s]+/).map(Number).filter(n => n > 0);
    const metin = isKarti(d, kalemNolar, ekNot);
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
    const gonderilen = await telegram(env, "sendMessage", {
      chat_id: t.id, text: metin, reply_markup: IS_DUGMELER(id), disable_web_page_preview: true
    });
    const siparisNo = pick(d, ["siparisNo", "no"]) || no;
    await belgeYaz(env, "isler", id, {
      siparisNo, tedarikci: anahtar(tKisa), tedarikciAd: t.ad, kalemler: kalemNolar,
      metin, durum: "gonderildi", chatId: t.id, messageId: gonderilen.message_id,
      gecmis: [{ durum: "gonderildi", kim: "Murat", tarih: new Date().toISOString() }]
    });
    return `📨 İş emri gönderildi → ${t.ad}\nSipariş ${siparisNo}` +
      (kalemNolar.length ? ` (ürün ${kalemNolar.join(", ")})` : " (tüm ürünler)") + `\nİş no: ${id}`;
  }

  if (ad === "/isler") {
    const a = anahtar(arg);
    const hepsi = a === "hepsi";
    const { results } = await env.DB.prepare(
      "SELECT id, data FROM documents WHERE collection='isler' ORDER BY rowid DESC LIMIT 200"
    ).all();
    let isler = results.map(r => ({ id: r.id, ...parse(r) }));
    if (!hepsi) isler = isler.filter(i => i.durum !== "bitti");
    if (a && !hepsi) isler = isler.filter(i => i.tedarikci === a);
    if (!isler.length) return hepsi ? "Kayıtlı iş yok." : "Açık iş yok 👍";
    const gruplu = {};
    for (const i of isler) (gruplu[i.tedarikciAd] = gruplu[i.tedarikciAd] || []).push(i);
    const out = [hepsi ? "Tüm işler:" : "Açık işler:"];
    for (const [tAd, l] of Object.entries(gruplu)) {
      out.push("", `🏭 ${tAd}`);
      for (const i of l) {
        const son = i.gecmis && i.gecmis[i.gecmis.length - 1];
        out.push(`• ${i.siparisNo}${i.kalemler && i.kalemler.length ? " (ürün " + i.kalemler.join(",") + ")" : ""} — ${IS_DURUM[i.durum] || i.durum}` +
          (son ? ` · ${zaman(son.tarih)}` : ""));
      }
    }
    return out.join("\n");
  }

  if (ad === "/baglan") {
    if (!message.chat || message.chat.type === "private") {
      return "Bu komutu grubun içinde yazın:\n• 312 NL Winkel grubunda: /baglan nl\n• 312 TR Üretim grubunda: /baglan tr";
    }
    const tur = arg.toLowerCase();
    if (tur !== "nl" && tur !== "tr") return "Kullanım: /baglan nl  veya  /baglan tr";
    const g = await gruplariOku(env);
    g[tur] = { id: message.chat.id, ad: message.chat.title || "", tarih: new Date().toISOString() };
    await gruplariYaz(env, g);
    return tur === "nl"
      ? `✅ Bu grup Hollanda mağaza grubu olarak bağlandı (${message.chat.title}).`
      : `✅ Bu grup Türkiye üretim grubu olarak bağlandı (${message.chat.title}).`;
  }

  if (ad === "/gruplar") {
    const g = await gruplariOku(env);
    return "Bağlı gruplar:\n" +
      `• Hollanda (NL): ${g.nl ? g.nl.ad + " ✅" : "bağlı değil ❌"}\n` +
      `• Türkiye üretim (TR): ${g.tr ? g.tr.ad + " ✅" : "bağlı değil ❌"}`;
  }

  if (ad === "/bildir") {
    // /bildir 312-0025        -> iki gruba
    // /bildir 312-0025 tr     -> sadece üretim
    // /bildir 312-0025 nl     -> sadece mağaza
    const [no, hedefRaw] = arg.split(/\s+/);
    if (!no) return "Kullanım: /bildir 312-0025  (sadece üretime: /bildir 312-0025 tr)";
    const hedef = (hedefRaw || "").toLowerCase();
    const row = await siparisBul(env, no);
    if (!row) return `"${no}" numaralı sipariş bulunamadı.`;
    const d = parse(row);
    const g = await gruplariOku(env);
    const sonuc = [];
    if (hedef !== "nl") {
      if (!g.tr) sonuc.push("TR üretim: grup bağlı değil ❌");
      else {
        const r = await grubaGonder(env, g.tr.id, siparisMesaji(d, "tr"));
        sonuc.push("TR üretim: " + (r === true ? "gönderildi ✅" : "hata ❌ " + r));
      }
    }
    if (hedef !== "tr") {
      if (!g.nl) sonuc.push("NL mağaza: grup bağlı değil ❌");
      else {
        const r = await grubaGonder(env, g.nl.id, siparisMesaji(d, "nl"));
        sonuc.push("NL mağaza: " + (r === true ? "gönderildi ✅" : "hata ❌ " + r));
      }
    }
    return `Sipariş ${pick(d, ["siparisNo", "no"]) || no} bildirimi:\n` + sonuc.join("\n");
  }

  if (ad === "/alanlar") {
    const ust = await env.DB.prepare(
      `SELECT j.key AS k, COUNT(*) AS n FROM documents, json_each(documents.data) j
       WHERE ${SIPARIS_FILTRE} GROUP BY j.key ORDER BY j.key`).all();
    const alt = await env.DB.prepare(
      `SELECT j2.key AS k, COUNT(*) AS n FROM documents,
         json_each(documents.data, '$.kalemler') j1, json_each(j1.value) j2
       WHERE ${SIPARIS_FILTRE} GROUP BY j2.key ORDER BY j2.key`).all();
    const isaretle = k => PARA_ILETISIM.test(k) ? " 🔒" : "";
    return "Sipariş alanları (🔒 = gruplara asla gitmez):\n" +
      ust.results.map(r => `• ${r.k} (${r.n})${isaretle(r.k)}`).join("\n") +
      "\n\nÜrün kalemi alanları:\n" +
      (alt.results.map(r => `• ${r.k} (${r.n})${isaretle(r.k)}`).join("\n") || "(yok)");
  }

  if (ad === "/onizle") {
    const [no, dil] = arg.split(/\s+/);
    if (!no) return "Kullanım: /onizle 312-0025  (Hollandaca için: /onizle 312-0025 nl)";
    const row = await siparisBul(env, no);
    if (!row) return `"${no}" numaralı sipariş bulunamadı.`;
    return "ÖNİZLEME (gruba gönderilmedi):\n\n" + siparisMesaji(parse(row), (dil || "tr").toLowerCase() === "nl" ? "nl" : "tr");
  }

  if (ad === "/dbtest") {
    const row = await env.DB.prepare("SELECT COUNT(*) AS total FROM documents").first();
    return "Veritabanı bağlantısı çalışıyor. Kayıt sayısı: " + row.total;
  }

  if (ad === "/ozet") {
    const { results } = await env.DB.prepare(
      "SELECT collection, COUNT(*) AS n FROM documents GROUP BY collection ORDER BY n DESC"
    ).all();
    if (!results.length) return "Veritabanında kayıt yok.";
    return "Veritabanı özeti:\n" + results.map(r => `• ${r.collection}: ${r.n}`).join("\n");
  }

  if (ad === "/siparisler") {
    // /siparisler            -> son 15
    // /siparisler hepsi      -> tümü
    // /siparisler yeni|uretim|hazir... -> duruma göre
    const a = arg.toLowerCase();
    const hepsi = a === "hepsi" || a === "tumu" || a === "tümü";
    const durumKey = !hepsi && a
      ? (Object.keys(DURUMLAR).find(k => k === a || DURUMLAR[k].toLowerCase().startsWith(a)) || a)
      : "";
    let sql = `SELECT id, data FROM documents WHERE ${SIPARIS_FILTRE}`;
    if (durumKey) sql += " AND lower(json_extract(data,'$.durum')) = ?1";
    sql += ` ORDER BY ${SIPARIS_SIRA}` + (hepsi || durumKey ? " LIMIT 100" : " LIMIT 15");
    const stmt = env.DB.prepare(sql);
    const { results } = await (durumKey ? stmt.bind(durumKey) : stmt).all();
    const toplam = await env.DB.prepare(
      `SELECT COUNT(*) AS n FROM documents WHERE ${SIPARIS_FILTRE}`).first();
    if (!results.length) {
      return durumKey ? `"${durumAdi(durumKey)}" durumunda sipariş yok.` : "Sipariş kaydı bulunamadı.";
    }
    const baslik = durumKey
      ? `${durumAdi(durumKey)} siparişler (${results.length}):`
      : hepsi ? `Tüm siparişler (${results.length}):` : `Son ${results.length} sipariş (toplam ${toplam.n}):`;
    return baslik + "\n" + results.map((r, i) => `${i + 1}. ${siparisSatiri(r)}`).join("\n") +
      "\n\nDetay: /siparis <numara>\nFiltre: /siparisler yeni · /siparisler uretim · /siparisler hepsi";
  }

  if (ad === "/siparis") {
    if (!arg) return "Sipariş numarası yazın. Örnek: /siparis 312-0020";
    const row = await siparisBul(env, arg);
    if (!row) return `"${arg}" numaralı sipariş bulunamadı.`;
    const d = parse(row);
    if (d.durum) d.durum = durumAdi(d.durum);
    return "Sipariş detayı:\n" + detay(d) + `\n\nGruplara göndermek için: /bildir ${pick(d, ["siparisNo","no"]) || arg}`;
  }

  if (ad === "/ara") {
    if (arg.length < 2) return "En az 2 harf yazın. Örnek: /ara rotterdam";
    const { results } = await env.DB.prepare(
      "SELECT id, collection, data FROM documents WHERE data LIKE ?1 ORDER BY collection DESC, rowid DESC LIMIT 20"
    ).bind(`%${arg}%`).all();
    if (!results.length) return `"${arg}" için sonuç yok.`;
    return `"${arg}" için ${results.length} sonuç:\n` + results.map((r, i) => {
      const d = parse(r);
      const baslik = /sipari|orders/.test(r.collection)
        ? siparisSatiri(r)
        : [pick(d, ["ad", "urunAdi", "isim"]), pick(d, ["olcu"])].filter(Boolean).join(" · ") || r.id;
      return `${i + 1}. [${r.collection}] ${baslik}`;
    }).join("\n");
  }

  if (ad === "/kutuphane") {
    const sql = arg
      ? "SELECT id, data FROM documents WHERE collection='kutuphane' AND data LIKE ?1 ORDER BY json_extract(data,'$.ad') LIMIT 40"
      : "SELECT id, data FROM documents WHERE collection='kutuphane' ORDER BY json_extract(data,'$.ad') LIMIT 40";
    const stmt = env.DB.prepare(sql);
    const { results } = await (arg ? stmt.bind(`%${arg}%`) : stmt).all();
    if (!results.length) return arg ? `Kütüphanede "${arg}" bulunamadı.` : "Kütüphane boş.";
    if (arg && results.length === 1) return "Kütüphane ürünü:\n" + detay(parse(results[0]));
    return "Kütüphane:\n" + results.map((r, i) => {
      const d = parse(r);
      return `${i + 1}. ` + [pick(d, ["ad"]), pick(d, ["olcu"]), pick(d, ["malzeme"])].filter(Boolean).join(" · ");
    }).join("\n") + (arg ? "" : "\n\nDetay için: /kutuphane <ürün adı>");
  }

  return null; // bilinmeyen komut
}

// ---------- Worker ----------

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    ORIGIN = url.origin;

    try {
      if (url.pathname === "/setup") {
        if (request.method === "GET") {
          return new Response(`<!doctype html>
<html lang="tr">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>312 Asistan bağlantısı</title>
<h2>312 Asistan Telegram bağlantısı</h2>
<p>Cloudflare'a kaydettiğiniz SETUP_SECRET değerini girin.</p>
<form method="post" action="/setup">
<input type="password" name="secret" required
 autocomplete="off" placeholder="Kurulum şifresi">
<button type="submit">Telegram bağlantısını kur</button>
</form>
</html>`, {
            headers: {
              "Content-Type": "text/html; charset=utf-8",
              "Cache-Control": "no-store",
              "Referrer-Policy": "same-origin",
              "Content-Security-Policy":
                "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
            }
          });
        }

        if (request.method !== "POST") return text("Yöntem geçersiz", 405);
        if (request.headers.get("Origin") !== url.origin) {
          return text("İstek reddedildi", 403);
        }
        if (!env.SETUP_SECRET || !env.BOT_TOKEN || !env.WEBHOOK_SECRET) {
          return text("Üç gizli ayarı kontrol edin.", 503);
        }

        const form = await request.formData();
        if (form.get("secret") !== env.SETUP_SECRET) {
          return text("Kurulum şifresi yanlış.", 403);
        }

        if (!/^[A-Za-z0-9_-]{32,256}$/.test(env.WEBHOOK_SECRET)) {
          return text("WEBHOOK_SECRET: 32–256 İngilizce harf veya rakam kullanın.", 400);
        }

        const bot = await telegram(env, "getMe", {});
        if (bot.username !== "interiors312_asistan_bot") {
          return text("BOT_TOKEN beklenen bota ait değil.", 400);
        }

        await telegram(env, "setWebhook", {
          url: url.origin + "/telegram",
          secret_token: env.WEBHOOK_SECRET,
          allowed_updates: ["message", "callback_query"]
        });
        await telegram(env, "setMyCommands", { commands: KOMUT_MENUSU });

        return text("Bağlantı kuruldu. Telegram'da 312 Asistan'a /start gönderin.");
      }

      if (url.pathname === "/telegram") {
        if (request.method !== "POST") return text("Yöntem geçersiz", 405);
        if (!env.WEBHOOK_SECRET ||
            request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) {
          return text("Yetkisiz", 403);
        }

        const update = await request.json();

        // Düğmeye basıldı (tedarikçi iş kartı)
        if (update.callback_query) {
          try { await geriBildirim(env, update.callback_query); } catch {}
          return text("OK");
        }

        const message = update.message;
        if (!message || message.from?.is_bot) return text("OK");

        // Grup süper gruba dönüştü: numarayı güncelle
        if (message.migrate_to_chat_id) {
          try { await grupNoTasi(env, message.chat.id, message.migrate_to_chat_id); } catch {}
          return text("OK");
        }
        if (message.migrate_from_chat_id) {
          try { await grupNoTasi(env, message.migrate_from_chat_id, message.chat.id); } catch {}
          return text("OK");
        }

        const ozel = message.chat?.type === "private";
        const grup = message.chat?.type === "group" || message.chat?.type === "supergroup";
        if (!ozel && !grup) return text("OK");
        const yonetici = !!env.ADMIN_USER_ID &&
          String(message.from.id) === String(env.ADMIN_USER_ID).trim();

        // Tedarikçi grubunda ustanın mesajı/fotoğrafı -> Murat'a ilet
        if (grup && !yonetici) {
          try { await tedarikciMesajiIlet(env, message); } catch {}
          return text("OK");
        }
        // Sadece yetkili kullanıcı (ADMIN_USER_ID) komut verebilir
        if (!yonetici) return text("OK");

        const command = (message.text || "").trim();
        if (!command.startsWith("/")) {
          if (ozel) await send(env, message.chat.id, "Komut listesi için /yardim yazın.");
          return text("OK");
        }
        // Grupta sadece grup komutları çalışır (sipariş bilgisi gruba yazılmasın)
        if (grup && !/^\/(baglan|gruplar|kimlik|tedarikci)(@\w+)?(\s|$)/i.test(command)) {
          return text("OK");
        }

        try {
          const reply = await komutCalistir(env, command, message);
          await send(env, message.chat.id, reply ?? "Bilinmeyen komut. /yardim yazın.");
        } catch (err) {
          // Hata olursa sessiz kalmasın, yöneticiye bildirsin
          try {
            await send(env, message.chat.id, "Hata oluştu: " + (err?.message || err));
          } catch {}
        }
        return text("OK");
      }

      if (url.pathname === "/" && request.method === "GET") {
        return text("312 Asistan v6 çalışıyor (GitHub otomatik yayın).");
      }

      return text("Bulunamadı", 404);
    } catch {
      return text("İşlem tamamlanamadı. Gizli ayarları kontrol edin.", 502);
    }
  }
};
