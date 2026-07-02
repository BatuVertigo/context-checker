# Routine Prompt — Release History Tablosunu Güncelle

Bu prompt bir Claude Routine (thrice daily) tarafından çalıştırılır. Görevin: iki Slack
kanalını (`#pa-releasehistory` ve `#cs-releasehistory`) okuyup **her birinin kendi tablosunu**
güncel tutmak. İki kanal ayrı ayrı, aynı mantıkla işlenir.

## Hedef dosyalar (kanal → dosya eşlemesi)

1. `#pa-releasehistory` → `/Users/vertigo/Desktop/Code/Reflex/reflex/Release History/pa_release_history_table.md`
2. `#cs-releasehistory` → `/Users/vertigo/Desktop/Code/Reflex/reflex/Release History/cs_release_history_table.md`

Her kanalı kendi dosyasına yaz. Tabloyu **bu dosyaların içinde** güncelle. Başka yere yazma,
mempalace'e ekleme yapma. Sadece bu iki dosyayı Edit/Write ile değiştir.

## Kaynak

İki kanal, iki ayrı channel id:

| Kanal | channel_id | Sürüm formatı | Track adları |
|-------|-----------|---------------|--------------|
| `#pa-releasehistory` | `C0AT9U4UYF2` | `v1.XXXX` | closed testing / open testing (CT/OT) |
| `#cs-releasehistory` | `C05UUFSS3NY` | `v14.XXXX` | closed-beta / open-beta (CB/OB) |

- Her kanalı `slack_read_channel` ile oku (channel_id = yukarıdaki id, limit=100,
  response_format=`detailed`). `detailed` formatta her mesajın `Message TS` değeri gelir;
  Slack thread linkini bundan üreteceksin (aşağıya bak).
- Kanal bulunamazsa önce `slack_search_channels` ile id'yi doğrula.
- Her release postu bir sürümü temsil eder ve genelde şu bloğu içerir: başlıkta
  `<sürüm> (<build>)` satırları (`:apple:` iOS, `:android:` Android — sıra kanala göre
  değişebilir), ardından `*RELEASE PROCESS*` altında `:apple: IOS` / `:android: Android`
  bullet'ları (`<tarih saat> || <açıklama>` formatında).
- **Kanal formatı farklılıkları:**
  - PA: bullet'lar düz. `%100'e açıldı` / `forcelandı` gibi ortak satırlar platform başlığı
    olmadan en altta olabilir.
  - CS: her bullet'ın başında durum işareti var — `:white_check_mark:` = adım gerçekleşti,
    `:x:` = adım **iptal/geçersiz** (o adım OLMADI, sonraki build ile değiştirildi). Force için
    kritik: yalnızca `:white_check_mark:` olan `Sürüm forcelandı` gerçek force'tur; `:x:` olan
    force sayılmaz. CS ayrıca `Git Branch:` satırı ve `Closed-Beta/Open-Beta/Production` kullanır.

## Thread'leri de oku (önemli)

Release process adımları bazen ana posta **edit'lenmez**, sadece o postun **thread yanıtlarında**
yazılır (ör. `1 Temmuz 17:10 || IOS Android %100 yayınlandı`, `1 Temmuz 20:05 || IOS ve Android
forcelandı`). Bu yüzden kontrol ettiğin her sürüm için `slack_read_thread` (channel_id + parent
`Message TS`) ile thread'i de oku ve **son gelişmeyi ana post + thread'in tamamı üzerinden** belirle.

- Thread yanıtlarında da aynı `<tarih saat> || <açıklama>` kalıbını ve "%100 açıldı / forcelandı /
  Prod %X yayınlandı / phased rollout" gibi ifadeleri ara; en geç tarihli **gerçek** gelişmeyi al.
- **Force çoğu zaman yalnızca thread'de duyurulur.** Thread'de yeni bir force görürsen o sürüm yeni
  "son force" olur; Durum akışını (madde 6) uygula.
- Sıradan sohbet, checklist dosyaları, sentry/crash tartışmaları release adımı değildir; bunları
  "son gelişme" olarak alma.

## Güncelleme mantığı (VERİMLİ — hepsini tarama)

Amaç: Slack ile tabloyu karşılaştırıp sadece değişenleri güncellemek. Eski sürümlerin
Slack postları artık değişmez; bu yüzden hepsini tek tek kontrol etmek gereksiz.

1. **Mevcut dosyayı oku.** Tablodaki satırları ve sıralamayı koru; hiçbir satırı silme.
2. **En son forcelanan sürümü belirle:** O tablodaki "Force tarihi" dolu olan en yeni sürüm.
   (Referans örnekleri: PA'da v1.3008, CS'te v14.7008.) Bu sürüm bir **sınır**dır.
3. **Sadece bu sınır sürüm VE ondan yeni olan sürümleri kontrol et.** Bu sürümlerin **hem ana
   postunu hem de thread'ini** oku (`slack_read_thread`) ve tablodaki karşılık gelen satırla
   karşılaştır (bkz. "Thread'leri de oku"). Sınırdan **eski** sürümlerin satırlarına dokunma
   (onlar dondu; Slack'te değişmezler) — thread'lerini de okumaya gerek yok.
4. **Farklılık varsa güncelle:** Kontrol edilen bir sürümün Slack postu tablodakinden
   farklıysa (yeni rollout %'si, %100 açılması, yeni son gelişme, force eklenmesi vb.)
   ilgili satırın hücrelerini güncelle.
5. **Yeni sürüm ekle:** Tabloda hiç olmayan yeni bir sürüm çıkmışsa, en üste (en yeni en
   üstte) yeni bir satır ekle.
6. **Yeni force olduğunda:** forcelanan sürüm yeni "sınır" olur. Bundan önce Prod'a açılmış
   ve o an 🟢 Yayın olan tüm satırların Durum'unu ⚫ (artık yayında değil) yap; forcelanan
   sürümün kendisini `🟢👊🏻 Yayın (son force)` yap. (Bu, sınırdan eski satırlara dokunmanın tek
   istisnasıdır.)
7. Dosyanın en üstündeki **"Son güncelleme"** tarih-saatini güncelle.
8. Hiç değişiklik yoksa dosyayı olduğu gibi bırak (gereksiz düzenleme yapma).

## Kolon yapısı (bu sırayı koru)

`Sürüm | Slack thread | Build (iOS/Android) | Son gelişme (iOS) | Son gelişme (Android) | %100 açıldı | Force tarihi | Durum`

- **Sürüm:** kalın. PA'da `v1.XXXX`, CS'te `v14.XXXX`. Bir platformun sürümü farklıysa hücrede
  kısa not bırak (ör. `**v1.1705**<br>(Android 1.1704)`).
- **Slack thread:** İlgili release postunun linki, `[Link](URL)` şeklinde gömülü. URL'yi
  mesajın `Message TS` değerinden üret:
  `https://vertigohq.slack.com/archives/<channel_id>/p<TS>` — `<channel_id>` o kanalın id'si
  (PA: `C0AT9U4UYF2`, CS: `C05UUFSS3NY`); `<TS>`, TS'ten noktayı çıkararak elde edilir.
  Örn. TS `1782225723.900559` → link sonu `p1782225723900559`.
- **Build (iOS/Android):** `<iOS build> / <Android build>` (ör. `529 / 834`). Bir platformun
  build'i yoksa o tarafa `—` yaz (ör. `— / 208449`).
- **Son gelişme (iOS) / (Android):** İlgili platformun **en son gelişmesini** tek satırda yaz:
  `• <tarih saat> — <açıklama>`. Bunu belirlerken:
  - Önce platformun kendi bölümündeki (`:apple: IOS` / `:android: Android`) **son maddeye** bak.
  - **AMA** postun altında platform başlığı olmadan yazılmış **ortak satırlar** olabilir
    (ör. `24 Haziran 16:25 || IOS/Android %100'e açıldı`, `25 Haziran 16:35 || IOS/android
    forcelandı`). Bu ortak satırlar hem iOS hem Android için geçerlidir ve genelde en son
    gelişmedir. Böyle bir satır varsa, ilgili platformun son gelişmesi olarak **onu** yaz
    (ör. Son gelişme (Android) = `• 25 Haz 2026 16:35 — Android forcelandı`,
    Son gelişme (iOS) = `• 25 Haz 2026 16:35 — iOS forcelandı`).
  - Yani her platform için "en geç tarihli gelişme" hangisiyse onu yaz — bu gelişme ana postta
    olabileceği gibi **thread yanıtlarında** da olabilir (bkz. "Thread'leri de oku").
  - **CS'te `:x:` ile işaretli satırları atla** — bunlar iptal edilmiş/gerçekleşmemiş adımlardır,
    "gelişme" sayılmaz. Son gelişme olarak yalnızca `:white_check_mark:` olan satırları dikkate al.
  - İlgili platformda hiç gelişme yoksa sadece `—` koy.
- **%100 açıldı:** Prod %100 açıldığı tarih + yanına `(iOS & Android)` / `(iOS)` / `(Android)`.
  İki platform farklı saatte açıldıysa ikisini de belirt (ör. `10 Haz 2026 (Android 18:38, iOS 21:51)`).
  Açılmadıysa `—`.
- **Force tarihi:** `forcelandı` olduğu tarih + `(iOS & Android)` vb. Yoksa `—`.
- **Durum:** aşağıdaki kurallara göre (emoji ile).

## Tarih / kısaltma kuralları

- **Tarihe her zaman yıl yaz:** `1 Tem 2026 11:57`, `13 May 2026 23:20`. Ay kısaltmaları
  Türkçe (Oca, Şub, Mar, Nis, May, Haz, Tem, Ağu, Eyl, Eki, Kas, Ara). Gün adını (Salı,
  Perşembe vb.) yazma; CS postlarında olsa bile at.
- Kısaltmalar: PA → **CT** = closed testing, **OT** = open testing. CS → **CB** = closed-beta,
  **OB** = open-beta. Her ikisinde **Prod** = production.
- Yüzdeleri Slack'teki gibi koru (`Prod %5`, `%100` vb.).

## Durum kuralları

"Son force" = o tablodaki "Force tarihi" dolu olan en yeni sürüm (PA örn. v1.3008, CS örn.
v14.7008). Bir sürümün "hâlâ yayında" olması demek: Prod'a açılmış olması VE kendisinden daha
yeni bir sürümün henüz forcelanmamış olması (yani son force'un kendisi ya da ondan yeni bir sürüm olması).

- **🧪 Prod'a hiç açılmadı** — sürüm hiç Prod'a çıkmamış (release process yok ya da yalnızca
  closed/open testing'de kalmış, Prod %0). Örnek metinler: `🧪 Release process yok`,
  `🧪 Sadece closed testing`.
- **🟡 Yayına hazırlanıyor** — Prod'a henüz %0; ama aktif yayın sürecinde (review'a atılmış /
  phased rollout için review isteniyor), henüz hiçbir yüzdede yayınlanmamış. Parantez içinde
  her iki platformun durumunu belirt. Örnek:
  `🟡 Yayına hazırlanıyor (Android %1 review'a atıldı, iOS review'da)`.
- **🟢 Yayın** — Prod'a en az %1 açılmış VE hâlâ yayında. Parantez içinde durumu belirt:
  - Forcelanmış ve hâlâ yayındaysa (yani son force): `🟢👊🏻 Yayın (son force)`.
  - Forcelanmamış ama hâlâ yayındaysa güncel rollout: `🟢 Yayın (Android %100, iOS %100)` ya da
    `🟢 Yayın (Android %50, iOS roll out)` gibi.
- **⚫ Artık yayında değil** — Prod'a açılmıştı ama sonraki bir sürüm forcelandığı için artık
  yayında değil. Açıklayıcı metinle:
  - Hiç forcelanmamış ve şu an yayında değilse, en son ulaştığı durumu + forcelayan sürümü yaz:
    `⚫ Android %100, iOS %100 açılmıştı, sonra v1.3008 forcelandı` veya
    `⚫ Android %10 açılmıştı, iOS review istenmişti, sonra v1.3008 forcelandı`.
  - Eskiden kendisi forcelanmış ama şimdi yayında değilse (sonraki bir force geldi):
    `⚫👊🏻 Forcelanmıştı, sonra v1.3008 forcelandı`.

**👊🏻 kuralı:** Bir sürüm forcelandıysa (kendi "Force tarihi" dolu), Durum'daki emojinin hemen
yanına 👊🏻 ekle (ör. `🟢👊🏻 …`, `⚫👊🏻 …`). Forcelanmamış sürümlerde 👊🏻 olmaz.

## Notlar

- Sadece iki hedef dosyayı düzenle; başka dosya/servis dokunma.
- Emin olmadığın veri için satırı bozma; mevcut değeri koru ve gerekirse hücrede kısa not bırak.
- Tabloyu geçerli bir Markdown tablosu olarak tut (hücre içi satır sonu gerekiyorsa `<br>`).
