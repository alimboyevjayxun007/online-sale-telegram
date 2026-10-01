# 💎 Premium Market Bot — To'liq loyiha hujjati va ish rejasi

> **Holat:** 📝 Tasdiqlash kutilmoqda (v1.0)
> **Sana:** 2026-10-01
> **Owner / Bosh admin:** Siz
> **Stek:** Python 3.13 · FastAPI · aiogram 3 · PostgreSQL · Redis · Next.js 16 · TON · Telegram Stars
> **Deploy:** Dockersiz (Ubuntu + systemd + Nginx)
>
> Bu hujjat loyihaning **yagona manbasi** (single source of truth). Siz tasdiqlaganingizdan so'ng kod
> shu reja bo'yicha bosqichma-bosqich yoziladi. Har bir bosqich oxirida natija sizga ko'rsatiladi va
> keyingi bosqichga faqat oldingisi "Tayyor" (DoD) shartlarini bajargandan keyin o'tiladi.
>
> 👉 **Avval 2-bo'limni (muhim cheklovlar) va oxirgi 21-bo'limni (siz javob beradigan savollar) o'qing.**

---

## Mundarija

1. [Loyiha maqsadi va imkoniyatlari](#1-loyiha-maqsadi-va-imkoniyatlari)
2. [⚠️ Muhim texnik haqiqatlar va cheklovlar](#2-️-muhim-texnik-haqiqatlar-va-cheklovlar)
3. [Biznes mantiq: hamyonlar, pul oqimi, narxlash](#3-biznes-mantiq-hamyonlar-pul-oqimi-narxlash)
4. [Texnologiyalar steki](#4-texnologiyalar-steki)
5. [Tizim arxitekturasi (yuqori daraja)](#5-tizim-arxitekturasi-yuqori-daraja)
6. [Texnik arxitektura](#6-texnik-arxitektura)
7. [Jarayon arxitekturasi (process architecture)](#7-jarayon-arxitekturasi-process-architecture)
8. [Class diagrammalar](#8-class-diagrammalar)
9. [Ma'lumotlar bazasi (PostgreSQL)](#9-malumotlar-bazasi-postgresql)
10. [Backend API (barcha endpointlar)](#10-backend-api-barcha-endpointlar)
11. [Telegram bot: buyruqlar, ekranlar, tugmalar va ranglar](#11-telegram-bot-buyruqlar-ekranlar-tugmalar-va-ranglar)
12. [Mini App (Next.js): UI/UX dizayn va arxitektura](#12-mini-app-nextjs-uiux-dizayn-va-arxitektura)
13. [Analitika va statistika](#13-analitika-va-statistika)
14. [Xavfsizlik](#14-xavfsizlik)
15. [Kerakli secret kalitlar va ularni olish yo'li](#15-kerakli-secret-kalitlar-va-ularni-olish-yoli)
16. [Deploy (Dockersiz)](#16-deploy-dockersiz)
17. [Testlash strategiyasi](#17-testlash-strategiyasi)
18. [Bosqichma-bosqich ish rejasi](#18-bosqichma-bosqich-ish-rejasi)
19. [Xavflar va ularni kamaytirish](#19-xavflar-va-ularni-kamaytirish)
20. [Kelajakdagi imkoniyatlar](#20-kelajakdagi-imkoniyatlar)
21. [❓ Tasdiqlash uchun savollar (siz javob berasiz)](#21--tasdiqlash-uchun-savollar-siz-javob-berasiz)

---

## 1. Loyiha maqsadi va imkoniyatlari

### 1.1 Maqsad

Foydalanuvchilarga **Telegram Premium** va **Telegram Stars**'ni bozordagi eng arzon narxda, tez (1–3 daqiqa)
va xavfsiz tarzda sotib olish imkonini beruvchi Telegram bot + Mini App yaratish. Bot egasi (siz) esa butun
biznesni — narxlar, to'lovlar, hamyon, foydalanuvchilar, statistika — **botning o'zidan (BotFather uslubida)**
va **Mini App'dan** to'liq boshqaradi.

### 1.2 Asosiy imkoniyatlar

**👤 Foydalanuvchi paneli (bot + Mini App):**

| # | Imkoniyat | Izoh |
|---|-----------|------|
| 1 | Premium sotib olish | 3, 6, 12 oy (1 oy — 2.1-bandga qarang). O'ziga yoki boshqa odamga (@username) |
| 2 | Stars sotib olish | Tayyor paketlar (50, 100, 250, 500, 1000, 2500, 5000, 10000) yoki o'z miqdori (min 50) |
| 3 | TON bilan to'lash | TON Connect (Mini App: Tonkeeper, Telegram Wallet, MyTonWallet…) yoki manzil + izoh orqali |
| 4 | Stars bilan to'lash | Telegram'ning rasmiy Stars to'lov oynasi (XTR invoice) |
| 5 | Ichki balans (bot hamyoni) | Balansni TON yoki Stars bilan to'ldirish, balansdan xarid qilish, qaytarilgan pullar shu yerga tushadi |
| 6 | Buyurtmalar tarixi | Holati (kutilmoqda → to'landi → bajarilmoqda → tayyor), chek |
| 7 | Referal tizimi | Taklif havolasi, do'stlar xaridlaridan % bonus balansga |
| 8 | Promokodlar | Chegirma kodlari |
| 9 | Ko'p tillilik | O'zbek (asosiy), Rus, Ingliz |
| 10 | Yordam | FAQ + support bilan bog'lanish |

**🛠 Admin paneli (bot ichida + Mini App ichida, ikkalasida ham bir xil imkoniyat):**

| # | Bo'lim | Imkoniyatlar |
|---|--------|--------------|
| 1 | Dashboard | Bugungi kirim/chiqim/foyda, buyurtmalar, yangi foydalanuvchilar, hamyon balanslari, ogohlantirishlar |
| 2 | Statistika | Kunlik / haftalik / oylik / yillik / ixtiyoriy davr; oldingi davr bilan solishtirish; grafiklar; Excel eksport |
| 3 | Buyurtmalar | Ro'yxat, filtr, qidiruv, tafsilot, qayta urinish, pulni qaytarish, qo'lda bajarildi deb belgilash |
| 4 | Foydalanuvchilar | Qidiruv (ID / @username), profil, balansni +/−, ban/unban, xabar yozish, buyurtmalari |
| 5 | Moliya | Hot wallet (TON) balansi, Stars balansi, sizning Telegram Wallet'ingizga pul yechish, avto-o'tkazish, xarajatlar |
| 6 | Narxlar | Har bir tarif uchun ustama %, qat'iy narx, Stars narxi, yoqish/o'chirish; Stars paketlari |
| 7 | To'lov usullari | TON / Stars / Balans / (kelajakda USDT, Click, Payme) yoqish-o'chirish |
| 8 | Xabar yuborish | Matn/rasm/video + tugmalar, segmentlar, rejalashtirish, progress, to'xtatish |
| 9 | Promokodlar | Yaratish, limitlar, muddat, statistika |
| 10 | Referal | Foiz, yoqish/o'chirish, top referallar |
| 11 | Majburiy obuna | Kanallar qo'shish/olib tashlash (ixtiyoriy) |
| 12 | Sozlamalar | Matnlar, support, texnik ishlar rejimi, Fragment sozlamalari, til |
| 13 | Adminlar | Admin qo'shish/o'chirish, rollar (owner / admin / support) |
| 14 | Audit log | Har bir admin amalining tarixi |

### 1.3 Rollar

| Rol | Kim | Huquqlar |
|-----|-----|----------|
| `owner` | Siz (`.env` dagi `OWNER_TELEGRAM_ID`) | Hamma narsa, shu jumladan pul yechish va adminlarni boshqarish |
| `admin` | Siz tayinlagan yordamchilar | Pul yechish va adminlarni boshqarishdan tashqari hamma narsa |
| `support` | Qo'llab-quvvatlash xodimi | Buyurtmalar va foydalanuvchilarni ko'rish, qayta urinish, xabar yozish |
| `user` | Oddiy foydalanuvchi | Xarid, balans, referal |

> To'liq huquqlar matritsasi — [14.3](#143-rbac-huquqlar-matritsasi).

### 1.4 Atamalar lug'ati

| Atama | Ma'nosi |
|-------|---------|
| **Hot wallet** | Serverda turadigan, bot boshqaradigan TON hamyon. Foydalanuvchi TON to'lovlari shu yerga tushadi, Fragment'ga to'lov shu yerdan ketadi |
| **Admin wallet** | Sizning shaxsiy hamyoningiz (Telegram Wallet / Tonkeeper). Foyda shu yerga yechiladi |
| **Stars balans** | Telegram ichida botga tegishli Stars balansi (Stars to'lovlar shu yerga tushadi) |
| **Ichki balans** | Har bir foydalanuvchining bot ichidagi balansi (USD hisobida, bazada yuritiladi) |
| **Fragment** | fragment.com — Telegram'ning rasmiy platformasi; Premium va Stars'ni TON evaziga istalgan @username'ga sotib olish mumkin |
| **Fulfillment / yetkazish** | To'lovdan keyin Premium/Stars'ni haqiqatda qabul qiluvchiga faollashtirish jarayoni |
| **Provider** | Yetkazish usuli (Fragment, Bot Stars, Mock) |
| **Invoice / to'lov hisobi** | Foydalanuvchiga ko'rsatilgan aniq summa + muddat (TON uchun izoh/comment bilan) |
| **initData** | Mini App ochilganda Telegram beradigan imzolangan ma'lumot — foydalanuvchini aniqlash uchun |
| **DoD** | Definition of Done — bosqich tugadi deyish uchun bajarilishi shart bo'lgan mezonlar |

---

## 2. ⚠️ Muhim texnik haqiqatlar va cheklovlar

Bu bo'lim rejaning eng muhim qismi — loyiha Telegram'ning real imkoniyatlariga moslab qurilgan.

### 2.1 1 oylik Premium'ni sovg'a qilib bo'lmaydi

Telegram rasmiy ravishda Premium'ni **boshqa odamga faqat 3, 6 va 12 oylik** muddatga beradi:

- **Fragment.com** orqali sovg'a: faqat 3 / 6 / 12 oy.
- **Bot API `giftPremiumSubscription`** metodi: `month_count` faqat `3`, `6` yoki `12`; `star_count` mos ravishda
  `1000`, `1500`, `2500` ⭐.
- 1 oylik obunani faqat foydalanuvchining **o'zi** Telegram ilovasi ichida (App Store / Google Play) sotib oladi.

**Rejadagi yechim:**

- Bazada 1 oylik tarif yaratiladi, lekin `is_enabled = false`, `provider_supported = false`.
- Botda va Mini App'da "1 oy — tez kunda" (kulrang, bosilmaydigan) holatda ko'rsatiladi yoki umuman
  ko'rsatilmaydi — **sizning tanlovingiz** ([21-bo'lim, 1-savol](#21--tasdiqlash-uchun-savollar-siz-javob-berasiz)).
- Agar Telegram kelajakda 1 oylik sovg'ani qo'shsa — admin paneldan bitta tugma bilan yoqiladi, kod
  o'zgarmaydi (provider `supports()` metodi yangilanadi).
- ❌ Foydalanuvchi akkauntiga kirib (SMS kod / sessiya orqali) premium ulash usuli **ishlatilmaydi**: bu
  Telegram qoidalariga zid, akkaunt bloklanishi va foydalanuvchi ma'lumotlari o'g'irlanishi xavfi bor.

### 2.2 Premium/Stars'ni yetkazishning 2 ta qonuniy yo'li

| | **A. Fragment (TON bilan)** | **B. Bot Stars (`giftPremiumSubscription`)** |
|---|---|---|
| Qanday ishlaydi | Bot hot wallet'idan TON to'lab, Fragment orqali `@username`'ga sovg'a qiladi | Botning Stars balansidan to'lab, Bot API orqali `user_id`'ga sovg'a qiladi |
| Premium | ✅ 3 / 6 / 12 oy | ✅ 3 / 6 / 12 oy |
| Stars sotish | ✅ (min 50 ⭐) | ❌ (bot Stars'ni foydalanuvchiga o'tkaza olmaydi) |
| Kerak | Qabul qiluvchining `@username`'i, Fragment akkaunt (KYC talab qilinishi mumkin), hot wallet'da TON | Qabul qiluvchining `user_id`'i, botda yetarli Stars |
| Tannarx (taxminan) | 3 oy ≈ $11.99 · 6 oy ≈ $15.99 · 12 oy ≈ $28.99 (TON'da, kursga bog'liq) | 1000 ⭐ · 1500 ⭐ · 2500 ⭐ |
| Rasmiylik | Fragment rasmiy, lekin **ochiq API'si yo'q** (2.5-band) | 100% rasmiy Bot API |
| Qachon ishlatiladi | TON / balans bilan to'langan buyurtmalar (eng arzon tannarx) | Stars bilan to'langan buyurtmalar (strategiyaga qarab, 3.5-band) |

Kod **Strategy pattern** bilan yoziladi: har bir yetkazish usuli alohida `FulfillmentProvider` klassi. Admin
paneldan ustuvorlik tartibi belgilanadi (masalan: avval Fragment, ishlamasa Bot Stars).

### 2.3 Fragment uchun `@username` shart

Fragment faqat username bo'yicha ishlaydi. Shuning uchun:

- Foydalanuvchi **o'ziga** olsa va username'i bo'lmasa → B usul (Bot Stars, `user_id` orqali) taklif qilinadi
  yoki username o'rnatish bo'yicha qisqa yo'riqnoma ko'rsatiladi.
- **Boshqa odamga** olinsa → username majburiy; buyurtmadan oldin Fragment orqali qabul qiluvchi tekshiriladi
  (topildimi, ismi, premium olishi mumkinmi) va foydalanuvchiga tasdiqlash uchun ko'rsatiladi.
- Yetkazishdan oldin username **qayta tekshiriladi** (to'lov va yetkazish orasida username o'zgargan bo'lishi mumkin).

### 2.4 Stars bilan to'lovlar haqida

- Stars to'lovlar botning **Stars balansiga** tushadi.
- Ularni TON'ga almashtirish (withdraw) Fragment orqali, **olingan kundan 21 kun o'tgach**, minimal 1000 ⭐ dan,
  faqat **bot egasi tomonidan qo'lda** (BotFather → Fragment) qilinadi. Bu jarayonni API orqali avtomatlashtirib bo'lmaydi.
- Bot Stars balansini `getMyStarBalance` orqali ko'rib turamiz va admin panelda ko'rsatamiz.
- Stars to'lovni bot qaytarishi mumkin: `refundStarPayment` (yetkazish muvaffaqiyatsiz bo'lsa).
- Telegram ba'zan to'lovni o'zi qaytaradi (`refunded_payment` update) — bunday holat ham qayd qilinadi va adminga xabar boradi.

### 2.5 Fragment'ning rasmiy ochiq API'si yo'q

Fragment uchun ochiq hujjatlashtirilgan API yo'q. Bozorda ishlaydigan yondashuvlar:

| Rejim | Qanday | Afzallik | Kamchilik |
|-------|--------|----------|-----------|
| `fragment_direct` | O'z Fragment akkauntingiz sessiya cookie'lari (`stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`) + hot wallet imzosi | Vositachi komissiyasi yo'q → **eng arzon** | Cookie'lar vaqti-vaqti bilan eskiradi; KYC talab qilinishi mumkin |
| `fragment_api` | Uchinchi tomon API servisi / kutubxona (masalan `fragment-api-lib`, `pyfragment` ekotizimi) — tranzaksiya sizning seed'ingiz bilan lokal imzolanadi | Oson ulanadi, KYC'siz ishlashi mumkin | Bir necha % komissiya; uchinchi tomonga bog'liqlik |

**Rejadagi yechim:** `FragmentDirectProvider` va `FragmentApiProvider` — ikkalasi ham yoziladi, bitta
interfeys orqali. Qaysi biri asosiy, qaysi biri zaxira — admin panel sozlamasi. 8-bosqichda ikkalasi ham
kichik summa bilan real sinovdan o'tkaziladi va yakuniy kutubxona tanlanadi. Cookie eskirganda bot sizga
darhol ogohlantirish yuboradi va yangi cookie'ni admin panel orqali (shifrlangan holda) kiritasiz.

### 2.6 Tugma ranglari (Bot API `style`)

- Telegram Bot API tugmalarga `style` maydonini qo'llaydi: `primary` (🟦 ko'k), `success` (🟩 yashil),
  `danger` (🟥 qizil). Ko'rsatilmasa — ilovaning standart rangi (⬜).
- Bu `InlineKeyboardButton` va `KeyboardButton` uchun ishlaydi. Eski Telegram versiyalarida rang ko'rinmasligi
  mumkin — tugma baribir to'liq ishlaydi.
- `icon_custom_emoji_id` (tugmadagi custom emoji) faqat bot egasida Premium bo'lsa yoki bot Fragment'dan
  qo'shimcha username sotib olgan bo'lsa ishlaydi. Biz oddiy emoji ishlatamiz; custom emoji — ixtiyoriy qo'shimcha.
- aiogram **3.31+** bu maydonlarni to'liq qo'llaydi (Bot API 10.3).

### 2.7 TON kursi o'zgaruvchan

- Har bir TON invoice yaratilganda TON miqdori **20 daqiqaga muzlatiladi** (sozlanadi).
- Muddat o'tsa invoice `expired` bo'ladi, foydalanuvchi yangi kurs bilan qayta yaratadi.
- **Kech kelgan to'lov yo'qolmaydi:** foydalanuvchi ichki balansiga USD ekvivalentida tushadi va xabar yuboriladi.
- **Kam to'lov** (summa yetmasa) → kelgan summa balansga tushadi, buyurtma to'lanmagan qoladi, foydalanuvchiga
  "yana X TON yuboring yoki balansdan to'ldiring" deb xabar beriladi.
- **Ortiqcha to'lov** → buyurtma bajariladi, ortiqchasi balansga tushadi.

### 2.8 Hot wallet xavfsizligi

- Hot wallet'da faqat ishlash uchun zarur **rezerv** turadi (masalan 30 TON); ortiqchasi avtomatik yoki qo'lda
  sizning hamyoningizga o'tkaziladi.
- Pul **faqat** `.env` dagi `ADMIN_TON_ADDRESS` manziliga yechilishi mumkin. Admin panel orqali boshqa
  manzilga pul jo'natish **imkonsiz** — hatto admin akkaunti o'g'irlansa ham pul begona manzilga ketmaydi.
- Seed (mnemonic) hech qachon chatga, git'ga yoki loglarga tushmaydi — u serverning o'zida yaratiladi (15-bo'lim).

### 2.9 Telegram Wallet (@wallet) haqida eslatma

"Pullar mening Telegram hamyonimga o'tsin" talabi uchun `ADMIN_TON_ADDRESS` sifatida Telegram Wallet ichidagi
TON manzilingiz ishlatiladi. @wallet ichidagi custodial (kripto) hisobga o'tkazmada izoh (memo) talab qilinishi
mumkin — shuning uchun eng ishonchli variant **@wallet ichidagi o'z-o'zini saqlovchi TON hamyon** yoki Tonkeeper
manzili. Birinchi yechish **1 TON** bilan sinab ko'riladi. Agar izoh kerak bo'lsa — `ADMIN_TON_MEMO` sozlamasi bor.

---

## 3. Biznes mantiq: hamyonlar, pul oqimi, narxlash

### 3.1 To'rt hamyon modeli

| # | Hamyon | Qayerda | Nima tushadi | Nima chiqadi | Kim boshqaradi |
|---|--------|---------|--------------|--------------|----------------|
| 1 | **Hot wallet (TON)** | TON blokcheyn, seed serverda | Foydalanuvchilarning TON to'lovlari | Fragment'ga to'lovlar, sizga yechish | Bot (avtomatik) + Owner (yechish) |
| 2 | **Bot Stars balansi** | Telegram ichida | Foydalanuvchilarning Stars to'lovlari | `giftPremiumSubscription`, refund | Bot (avtomatik) + Owner (Fragment orqali qo'lda yechish) |
| 3 | **Admin wallet** | Sizning Telegram Wallet / Tonkeeper | Hot wallet'dan foyda | — | Siz |
| 4 | **Ichki balans** | PostgreSQL (`users.balance_usd` + ledger) | To'ldirishlar, qaytarishlar, referal bonuslari | Xaridlar | Bot + Admin (qo'lda tuzatish) |

### 3.2 Pul oqimi

```mermaid
flowchart LR
    U["👤 Foydalanuvchi"]
    HW[("💎 Hot wallet<br/>TON")]
    SB[("⭐ Bot Stars<br/>balansi")]
    UB[("💼 Ichki balans<br/>USD")]
    FR["Fragment.com"]
    TG["Telegram Bot API<br/>giftPremiumSubscription"]
    R["🎁 Qabul qiluvchi<br/>Premium / Stars"]
    AW[("🏦 Sizning<br/>Telegram Wallet")]

    U -- "TON to'lov" --> HW
    U -- "Stars to'lov" --> SB
    U -- "Balansdan to'lov" --> UB
    HW -- "To'ldirish (TON)" --> UB
    SB -- "To'ldirish (Stars)" --> UB
    HW -- "TON to'laydi" --> FR
    SB -- "Stars to'laydi" --> TG
    FR --> R
    TG --> R
    HW -- "Avto-o'tkazish / qo'lda yechish" --> AW
    SB -- "21 kundan keyin, qo'lda (Fragment)" --> AW
```

> Ichki balans — bu buxgalteriya yozuvi. Balans bilan to'langanda haqiqiy pul allaqachon hot wallet yoki
> Stars balansida turgan bo'ladi (to'ldirish paytida tushgan).

### 3.3 Narxlash mexanizmi (Pricing engine)

Barcha narxlar **serverda** hisoblanadi — klient (bot/Mini App) hech qachon narx yubormaydi.

**Kirish ma'lumotlari:**

| Belgi | Ma'nosi | Manba | Yangilanish |
|-------|---------|-------|-------------|
| `ton_usd` | 1 TON = ? USD | TonAPI rates (zaxira: CoinGecko) | har 1 daqiqa |
| `usd_uzs` | 1 USD = ? so'm | CBU.uz (Markaziy bank) | har kuni 1 marta |
| `cost_ton(plan)` | Fragment'da tarif narxi (TON) | Fragment provider | har 10 daqiqa |
| `network_fee_ton` | Tarmoq komissiyasi | sozlama (standart 0.05 TON) | qo'lda |
| `markup_percent` | Ustama foizi | admin (har tarif uchun) | qo'lda |
| `fixed_markup_usd` | Qat'iy ustama | admin | qo'lda |
| `fixed_price_usd` | Qat'iy narx (ixtiyoriy) | admin | qo'lda |
| `min_margin_percent` | Minimal foyda (zararga sotmaslik) | admin (standart 2%) | qo'lda |
| `round_step_usd` | Yaxlitlash qadami | admin (standart 0.05) | qo'lda |

**Formula (Premium):**

```text
cost_usd   = (cost_ton(plan) + network_fee_ton) × ton_usd
raw_price  = fixed_price_usd  YOKI  cost_usd × (1 + markup_percent/100) + fixed_markup_usd
min_price  = cost_usd × (1 + min_margin_percent/100)
price_usd  = round_up( max(raw_price, min_price), round_step_usd )      ← zararga sotish imkonsiz

price_ton  = ceil( price_usd / ton_usd , 2 xona )                         ← invoice'da 20 daqiqa muzlatiladi
price_uzs  = round( price_usd × usd_uzs , 1000 so'm )                     ← faqat ko'rsatish uchun
price_xtr  = plan.price_stars  YOKI  ceil( price_usd / star_usd_rate )    ← 3.5-bandga qarang
discount   = promokod (agar bo'lsa): foiz yoki qat'iy, lekin price ≥ min_price
saving_pct = (reference_price_usd − price_usd) / reference_price_usd     ← "Telegram'dan X% arzon" belgisi
```

**Misol** (taxminiy: 1 TON = $3.00, 1 USD = 12 800 so'm, ustama 8%):

| Tarif | Fragment tannarxi | cost_usd (+fee) | Narx (USD) | TON | So'm | Foyda |
|-------|-------------------|-----------------|------------|-----|------|-------|
| 3 oy | 4.00 TON ($11.99) | $12.15 | **$13.15** | 4.39 | ≈ 168 000 | ≈ $1.00 |
| 6 oy | 5.33 TON ($15.99) | $16.14 | **$17.45** | 5.82 | ≈ 223 000 | ≈ $1.31 |
| 12 oy | 9.66 TON ($28.99) | $29.13 | **$31.50** | 10.50 | ≈ 403 000 | ≈ $2.37 |

> Raqamlar faqat misol. Haqiqiy narxlar Fragment va TON kursiga qarab avtomatik hisoblanadi.
> Admin istalgan tarifga qat'iy narx qo'yishi mumkin; agar u minimal foydadan past bo'lsa, tizim ruxsat bermaydi
> va ogohlantiradi.

### 3.4 Stars sotish narxi

```text
star_cost_usd = Fragment'dagi 1 ⭐ narxi (TON → USD), har 10 daqiqada yangilanadi
price_usd(N)  = round_up( N × star_cost_usd × (1 + stars_markup_percent/100), 0.01 )
cheklovlar    : N ≥ 50 (Fragment minimal), N ≤ stars_max_amount (sozlama)
to'lov usuli  : TON yoki ichki balans (Stars'ni Stars bilan sotib bo'lmaydi)
```

Paketlar: 50, 100, 250, 500, 1000, 2500, 5000, 10000 (admin o'zgartiradi, "🔥 Ommabop" belgisi qo'yadi) +
"O'z miqdorim" (50 dan katta istalgan son).

### 3.5 Stars bilan to'langan Premium — 2 strategiya

| Strategiya | Qanday | Stars narxi (foydalanuvchi uchun) | Sizga ta'siri |
|------------|--------|-----------------------------------|---------------|
| `bot_stars` (**tavsiya**) | Foydalanuvchi to'lagan Stars bilan bot `giftPremiumSubscription` qiladi | min: 1000/1500/2500 ⭐ + ustama (masalan 1100 / 1650 / 2750 ⭐) | Hot wallet TON'i ishlatilmaydi; ustama Stars balansida qoladi |
| `fragment` | Stars bot balansida qoladi, premium hot wallet TON'i bilan Fragment orqali olinadi | `price_usd / star_usd_rate` (masalan $13.15 / 0.013 ≈ 1012 ⭐) | Hot wallet'dan TON darhol ketadi, Stars 21 kundan keyin yechiladi |

`star_usd_rate` — 1 ⭐ ning sizga yechishdagi qiymati (standart $0.013, admin o'zgartiradi). Bu stavka
statistikada Stars tushumini USD'ga o'girish uchun ham ishlatiladi.

### 3.6 Referal tizimi

- Har bir foydalanuvchida havola: `https://t.me/<bot>?start=ref_<user_id>`.
- Taklif qilgan odam (referrer) taklif qilingan odamning **har bir bajarilgan** xaridi narxidan `referral_percent`
  (standart 2%) miqdorida bonusni ichki balansga oladi.
- Bonus faqat buyurtma `completed` bo'lganda yoziladi; refund bo'lsa — bonus qaytarib olinadi.
- Himoya: o'zini o'zi taklif qila olmaydi; referrer faqat birinchi `/start` da biriktiriladi va keyin o'zgarmaydi;
  bonuslar `referral_rewards` jadvalida alohida qayd etiladi.

### 3.7 Promokodlar

- Turlari: `percent` (masalan 5%) yoki `fixed_usd` (masalan $0.50).
- Cheklovlar: umumiy foydalanish limiti, bitta foydalanuvchiga limit, amal qilish muddati, mahsulot turi
  (premium / stars / hammasi), minimal buyurtma summasi.
- Chegirmadan keyin ham narx `min_price` dan past tushmaydi.

### 3.8 Pulni qaytarish (refund) siyosati

| Holat | Qaytarish |
|-------|-----------|
| Yetkazish 3 urinishdan keyin ham bajarilmadi | Avtomatik: Stars → `refundStarPayment`; TON / balans → ichki balansga |
| Natija noaniq (pul yuborildi, javob kelmadi) | **Avtomatik qaytarilmaydi** → `needs_review`, admin tekshiradi (ikki marta yetkazish xavfining oldini olish) |
| Admin qo'lda | Admin buyurtma kartasidan "↩️ Pulni qaytarish" (balansga yoki Stars'ga) |
| Ichki balansni naqd pulga yechish | ❌ Yo'q (balans faqat xarid uchun) — 21-bo'lim, 11-savol |

---

## 4. Texnologiyalar steki

| Qatlam | Texnologiya | Versiya | Nima uchun |
|--------|-------------|---------|------------|
| Til (backend) | Python | 3.13 | Asinxron, barqaror, kutubxonalar ko'p |
| Paket menejer | uv | so'nggi | Tez o'rnatish, `uv.lock` bilan aniq versiyalar, Python'ni ham o'rnatadi |
| API | FastAPI + uvicorn[standard] | so'nggi barqaror | Tez, Pydantic v2, avtomatik OpenAPI hujjat |
| Bot | aiogram | 3.31+ | Bot API 10.3, `style` tugmalar, FSM, i18n, O'zbekistonda eng ommabop |
| ORM | SQLAlchemy 2.x (async) + asyncpg | so'nggi | Typed modellar, asinxron, `FOR UPDATE SKIP LOCKED` |
| Migratsiya | Alembic | so'nggi | Sxema versiyalari |
| Konfiguratsiya / validatsiya | pydantic-settings, Pydantic v2 | so'nggi | `.env` dan typed sozlamalar |
| Ma'lumotlar bazasi | PostgreSQL | 18 (min 16) | Tranzaksiyalar, `NUMERIC` pul turlari, JSONB, kuchli indekslar |
| Kesh / FSM / rate-limit | Redis | 7.x | aiogram FSM storage, kesh, throttling, worker heartbeat |
| HTTP klient | httpx | so'nggi | Asinxron, timeout/retry |
| TON | tonutils (+ pytoniq-core) | so'nggi | W5/v4R2 hamyon, TonAPI/Toncenter klient, comment parsing |
| Fragment | O'z adapterimiz + `fragment-api-lib` / `pyfragment` (8-bosqichda tanlanadi) | — | 2.5-band |
| Excel | openpyxl | so'nggi | Statistika eksporti |
| CLI | typer | so'nggi | `python -m app.cli ...` buyruqlari |
| Loglash | structlog (JSON) → journald | so'nggi | Strukturali loglar |
| Shifrlash | cryptography (Fernet) | so'nggi | Bazadagi maxfiy sozlamalar (Fragment cookie) |
| Test | pytest, pytest-asyncio, httpx, time-machine, respx | so'nggi | Unit + integratsion testlar |
| Sifat | ruff (lint + format), mypy (strict) | so'nggi | Kod sifati |
| Til (frontend) | TypeScript | 5.x | Tiplar |
| Frontend framework | Next.js (App Router) | 16.x | Talab qilingan; `output: "standalone"` bilan Node'da ishlaydi |
| UI | React 19, Tailwind CSS 4, shadcn/ui, lucide-react | so'nggi | Tez, chiroyli, moslashuvchan |
| Telegram Mini App SDK | `@tma.js/sdk-react` (oldingi nomi `@telegram-apps/sdk-react`), `@telegram-apps/telegram-ui` | so'nggi | MainButton, BackButton, theme, haptics, initData |
| TON (frontend) | `@tonconnect/ui-react`, `@ton/core` | so'nggi | Hamyon ulash, tranzaksiya yuborish, comment payload |
| Ma'lumot olish | TanStack Query 5, Zustand, zod, react-hook-form | so'nggi | Kesh, holat, forma validatsiyasi |
| Grafiklar | Recharts | so'nggi | Admin statistika grafiklari |
| i18n | next-intl | so'nggi | uz / ru / en |
| Animatsiya | motion (framer-motion), lottie-react | so'nggi | Premium/Stars animatsiyalari, muvaffaqiyat effekti |
| Node.js | Node | 24 LTS | Next.js serveri |
| JS paket menejer | pnpm | 10.x | Tez, `pnpm-lock.yaml` |
| Web server | Nginx + Certbot (Let's Encrypt) | OS paketi | HTTPS (Mini App uchun majburiy), reverse proxy |
| Jarayon menejeri | systemd | OS | **Docker o'rniga**: avtomatik restart, loglar, timerlar |
| Server OS | Ubuntu | 24.04 LTS | Barqaror, uzoq qo'llab-quvvatlash |
| Tashqi servislar | Telegram Bot API, TonAPI (tonconsole.com), Toncenter (zaxira), Fragment, CBU.uz, CoinGecko (zaxira) | — | — |

---

## 5. Tizim arxitekturasi (yuqori daraja)

### 5.1 Kontekst diagrammasi (kim bilan bog'lanadi)

```mermaid
flowchart TB
    subgraph Users["Foydalanuvchilar"]
        U["👤 Foydalanuvchi"]
        A["🛠 Admin / Owner"]
    end

    subgraph TG["Telegram ekotizimi"]
        TGAPP["Telegram ilova<br/>iOS · Android · Desktop · Web"]
        BOTAPI["Telegram Bot API"]
        STARS["Telegram Stars"]
    end

    SYS["💎 Premium Market tizimi<br/>Bot + Mini App + Backend"]

    subgraph EXT["Tashqi servislar"]
        FR["Fragment.com"]
        TONAPI["TonAPI / Toncenter"]
        TONNET["TON blokcheyn"]
        CBU["CBU.uz kurslar"]
        WAL["Foydalanuvchi hamyonlari<br/>Tonkeeper · Telegram Wallet"]
    end

    U --> TGAPP
    A --> TGAPP
    TGAPP <--> BOTAPI
    TGAPP -- "Mini App (HTTPS)" --> SYS
    BOTAPI -- "webhook" --> SYS
    SYS -- "Bot API metodlari" --> BOTAPI
    STARS --- BOTAPI
    SYS -- "Premium / Stars sotib olish" --> FR
    SYS -- "tranzaksiyalarni kuzatish, yuborish" --> TONAPI
    TONAPI --- TONNET
    FR --- TONNET
    WAL -- "TON to'lov" --> TONNET
    TGAPP -- "TON Connect" --> WAL
    SYS -- "USD/UZS kursi" --> CBU
```

### 5.2 Konteyner diagrammasi (tizim ichida nima bor)

> "Konteyner" bu yerda C4 modelidagi ma'noda — alohida ishlaydigan dastur. Docker **ishlatilmaydi**;
> har biri systemd servis.

```mermaid
flowchart LR
    TG["Telegram"]
    BR["Mini App<br/>(Telegram WebView)"]

    subgraph Server["Ubuntu 24.04 server"]
        NG["Nginx :443<br/>TLS, reverse proxy"]
        WEB["premium-web<br/>Next.js 16 standalone<br/>127.0.0.1:3000"]
        API["premium-api<br/>FastAPI + aiogram webhook<br/>127.0.0.1:8000"]
        WK["premium-worker<br/>fon vazifalari"]
        PG[("PostgreSQL 18<br/>127.0.0.1:5432")]
        RD[("Redis 7<br/>127.0.0.1:6379")]
        BK["premium-backup.timer<br/>pg_dump har kuni"]
    end

    EXT["Fragment · TonAPI · CBU"]

    BR -- "HTTPS /" --> NG
    BR -- "HTTPS /api/*" --> NG
    TG -- "HTTPS /tg/webhook" --> NG
    NG --> WEB
    NG --> API
    API --> PG
    API --> RD
    API -- "Bot API metodlari" --> TG
    WK --> PG
    WK --> RD
    WK -- "Bot API (xabarlar, gift)" --> TG
    WK --> EXT
    API --> EXT
    BK --> PG
```

---

## 6. Texnik arxitektura

### 6.1 Qatlamlar (Clean / Layered architecture)

```mermaid
flowchart TB
    subgraph Presentation["1. Taqdimot qatlami (kirish nuqtalari)"]
        R1["FastAPI routerlar<br/>api/v1/*, api/v1/admin/*"]
        R2["aiogram handlerlar<br/>bot/handlers/user/*, admin/*"]
        R3["Worker joblar<br/>workers/jobs/*"]
        R4["CLI<br/>app/cli.py"]
    end
    subgraph Application["2. Servis qatlami (biznes mantiq)"]
        S["OrderService · PaymentService · PricingService · FulfillmentService<br/>BalanceService · HotWalletService · AnalyticsService · BroadcastService<br/>ReferralService · PromoService · SettingsService · RateService · AuditService · NotificationService"]
    end
    subgraph Domain["3. Domen (modellar, enumlar, qoidalar)"]
        D["ORM modellar · Enumlar · State machine qoidalari · Money (Decimal) yordamchilari"]
    end
    subgraph Infra["4. Infratuzilma"]
        REPO["Repository'lar<br/>(SQLAlchemy)"]
        PROV["Providerlar<br/>Fragment · BotStars · TonAPI · CBU"]
        CACHE["Redis kesh"]
    end
    R1 --> S
    R2 --> S
    R3 --> S
    R4 --> S
    S --> D
    S --> REPO
    S --> PROV
    S --> CACHE
```

**Qoidalar:**

1. Handler/router **hech qachon** to'g'ridan-to'g'ri bazaga yozmaydi — faqat servis orqali.
2. Bot va Mini App **bir xil servislarni** chaqiradi → mantiq bitta joyda, ikki interfeys bir xil ishlaydi.
3. Tashqi API'lar faqat `providers/` ichida; servislar interfeys (`Protocol`/`ABC`) orqali ishlaydi → test
   uchun `Mock` provider qo'yiladi.
4. Pul hisob-kitoblari faqat `Decimal` bilan (`float` taqiqlanadi), bazada `NUMERIC`.
5. Har bir pul harakati ledger jadvaliga yoziladi (balans, hot wallet, stars).

### 6.2 Monorepo papka tuzilmasi

```text
online-sale-telegram/
├── ISH_REJASI.md                    # ushbu hujjat
├── README.md                        # qisqa ishga tushirish yo'riqnomasi
├── Makefile                         # dev/test/lint/deploy buyruqlari
├── .editorconfig  .gitignore
├── .github/workflows/ci.yml         # lint + test (Docker'siz, runner'dagi PostgreSQL)
│
├── backend/
│   ├── pyproject.toml  uv.lock  alembic.ini  .env.example
│   ├── migrations/                  # Alembic (env.py, versions/)
│   ├── locales/{uz,ru,en}/LC_MESSAGES/messages.po   # bot matnlari
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, lifespan (db, redis, bot)
│   │   ├── cli.py                   # typer: seed, create-owner, wallet, set-webhook, stats...
│   │   ├── core/
│   │   │   ├── config.py            # Settings (pydantic-settings)
│   │   │   ├── db.py                # async engine, session factory
│   │   │   ├── redis.py
│   │   │   ├── logging.py           # structlog
│   │   │   ├── security.py          # initData tekshiruv, Fernet shifrlash
│   │   │   ├── errors.py            # AppError ierarxiyasi + kodlar
│   │   │   ├── enums.py             # barcha enumlar
│   │   │   ├── money.py             # Decimal, yaxlitlash, nano-TON konvertatsiya
│   │   │   └── timeutil.py          # Asia/Tashkent bilan ishlash
│   │   ├── models/                  # SQLAlchemy ORM (9-bo'lim)
│   │   ├── schemas/                 # Pydantic DTO (request/response)
│   │   ├── repositories/            # bazaga so'rovlar
│   │   ├── services/
│   │   │   ├── user_service.py  settings_service.py  rate_service.py
│   │   │   ├── pricing_service.py  catalog_service.py  order_service.py
│   │   │   ├── payment_service.py
│   │   │   ├── payments/            # base.py, ton.py, stars.py, balance.py
│   │   │   ├── balance_service.py  fulfillment_service.py  hot_wallet_service.py
│   │   │   ├── referral_service.py  promo_service.py  analytics_service.py
│   │   │   ├── broadcast_service.py  notification_service.py
│   │   │   └── admin_service.py  audit_service.py  export_service.py
│   │   ├── providers/
│   │   │   ├── fulfillment/         # base.py, fragment_direct.py, fragment_api.py, bot_stars.py, mock.py
│   │   │   ├── ton/                 # base.py, tonapi.py, toncenter.py
│   │   │   └── rates/               # tonapi_rates.py, coingecko.py, cbu.py
│   │   ├── api/
│   │   │   ├── deps.py              # get_session, current_user, require_role
│   │   │   ├── router.py
│   │   │   ├── webhooks.py          # POST /tg/webhook
│   │   │   └── v1/
│   │   │       ├── me.py catalog.py recipients.py orders.py payments.py
│   │   │       ├── wallet.py referral.py promo.py
│   │   │       └── admin/           # dashboard, stats, orders, users, pricing, finance,
│   │   │                            # expenses, broadcasts, promo, settings, admins, channels, audit
│   │   ├── bot/
│   │   │   ├── setup.py             # Bot, Dispatcher, routerlarni ulash
│   │   │   ├── commands.py          # setMyCommands (user va admin scope)
│   │   │   ├── callbacks.py         # CallbackData fabrikalari
│   │   │   ├── states.py            # FSM holatlari
│   │   │   ├── middlewares/         # throttling, db, user, i18n, ban, maintenance, subscription, activity
│   │   │   ├── filters/             # IsAdmin, HasRole
│   │   │   ├── keyboards/           # builder.py (rangli tugma), user.py, admin.py, common.py
│   │   │   ├── texts.py             # matn shablonlari (format funksiyalari)
│   │   │   └── handlers/
│   │   │       ├── user/            # start, menu, premium, stars, checkout, wallet, orders, referral, settings, help
│   │   │       ├── payments.py      # pre_checkout_query, successful_payment, refunded_payment
│   │   │       ├── admin/           # panel, stats, orders, users, finance, pricing, payments_cfg,
│   │   │       │                    # broadcast, promo, referral_cfg, channels, settings, admins, commands
│   │   │       └── errors.py
│   │   └── workers/
│   │       ├── runner.py            # barcha joblarni ishga tushiradi, supervisor
│   │       └── jobs/                # ton_watcher, fulfillment, expirer, rates, provider_prices,
│   │                                # stats, broadcast, hot_wallet, stars_balance, reports, health
│   └── tests/
│       ├── conftest.py  factories.py
│       ├── unit/                    # pricing, security, state machine, money...
│       └── integration/             # API, servislar + haqiqiy PostgreSQL
│
├── webapp/
│   ├── package.json  pnpm-lock.yaml  next.config.ts  tsconfig.json  .env.example
│   ├── public/                      # tonconnect-manifest.json, icons/, lottie/
│   └── src/
│       ├── app/                     # sahifalar (12.3-bo'lim)
│       ├── components/
│       │   ├── ui/                  # shadcn: button, card, badge, sheet, tabs, input, switch, dialog, skeleton, toast
│       │   ├── layout/              # AppShell, BottomNav, AdminNav, PageHeader
│       │   ├── shop/                # PlanCard, StarsPackageGrid, RecipientPicker, PaymentMethodPicker,
│       │   │                        # PriceTag, OrderStatusTimeline, CheckoutCountdown
│       │   ├── wallet/              # BalanceCard, TxList, TopUpForm
│       │   └── admin/               # KpiCard, PeriodSwitcher, RevenueChart, OrdersChart, UsersChart,
│       │                            # MethodsDonut, DataTable, ConfirmDialog, FilterBar
│       ├── lib/                     # api.ts, tma.ts, ton.ts, format.ts, i18n.ts, query-client.ts
│       ├── hooks/                   # useMe, useCatalog, useOrder, useMainButton, useBackButton, useHaptic, useIsAdmin
│       ├── stores/                  # checkout.ts (Zustand)
│       ├── messages/                # uz.json, ru.json, en.json
│       └── styles/                  # globals.css, tokens.css
│
└── deploy/
    ├── nginx/premium.conf
    ├── systemd/                     # premium-api, premium-worker, premium-web, premium-backup (.service/.timer)
    └── scripts/                     # bootstrap_server.sh, deploy.sh, backup.sh, restore.sh
```

### 6.3 Backend modullari — vazifalari

| Modul | Vazifa | Asosiy metodlar |
|-------|--------|-----------------|
| `UserService` | Foydalanuvchi yaratish/yangilash, til, ban, qidiruv | `upsert_from_telegram`, `set_language`, `ban`, `unban`, `search` |
| `SettingsService` | Typed sozlamalar (DB + Redis kesh, o'zgarganda keshni tozalash) | `get`, `set`, `get_all`, `invalidate` |
| `RateService` | TON/USD, USD/UZS kurslari, zaxira manbalar | `ton_usd`, `usd_uzs`, `refresh` |
| `PricingService` | 3.3–3.5 formulalari | `quote_premium`, `quote_stars`, `quote_topup`, `apply_promo` |
| `CatalogService` | Tariflar + paketlar + narxlar (barcha valyutalarda) | `get_catalog` |
| `OrderService` | Buyurtma yaratish, holat o'tishlari (state machine) | `create`, `cancel`, `mark_paid`, `start_processing`, `complete`, `fail`, `mark_review`, `refund` |
| `PaymentService` | To'lov yaratish va tasdiqlash (strategy: TON / Stars / Balance) | `create_for_order`, `create_topup`, `confirm_ton`, `confirm_stars`, `expire_stale` |
| `BalanceService` | Ichki balans ledger (row lock bilan) | `credit`, `debit`, `history` |
| `FulfillmentService` | Provider tanlash, yetkazish, qayta urinish, refund | `process_next`, `retry`, `select_provider` |
| `HotWalletService` | Hot wallet balansi, yechish, avto-sweep, ledger | `balance`, `withdraw_to_admin`, `auto_sweep` |
| `ReferralService` | Referrer biriktirish, bonus hisoblash/qaytarish | `attach`, `reward_for_order`, `revoke_for_order`, `stats` |
| `PromoService` | Promokod tekshirish, qo'llash | `validate`, `redeem` |
| `AnalyticsService` | Statistika, davrlar, solishtirish | `dashboard`, `timeseries`, `top_buyers`, `recompute_day` |
| `ExportService` | Excel hisobotlar | `export_period` |
| `BroadcastService` | Ommaviy xabar yaratish, yuborish, progress | `create`, `start`, `pause`, `cancel`, `send_batch` |
| `NotificationService` | Foydalanuvchi va admin(log kanal)ga xabarlar | `notify_user`, `notify_admins`, `alert` |
| `AdminService` | Adminlar, rollar | `add_admin`, `remove_admin`, `role_of` |
| `AuditService` | Admin amallarini yozish | `log` |

### 6.4 Konfiguratsiya (`backend/.env`)

```dotenv
# ── Umumiy ─────────────────────────────────────────
APP_ENV=production                 # development | production
APP_SECRET_KEY=                    # openssl rand -hex 32 (biz generatsiya qilamiz)
ENCRYPTION_KEY=                    # Fernet kalit (biz generatsiya qilamiz)
TIMEZONE=Asia/Tashkent
PUBLIC_BASE_URL=https://premium.example.uz
WEBAPP_URL=https://premium.example.uz

# ── Telegram ───────────────────────────────────────
BOT_TOKEN=                         # @BotFather
BOT_USERNAME=                      # masalan PremiumMarketUzBot
OWNER_TELEGRAM_ID=                 # sizning raqamli ID'ingiz
WEBHOOK_SECRET=                    # openssl rand -hex 32
LOG_CHAT_ID=                       # admin log kanali/guruhi ID (-100...)
BOT_MODE=webhook                   # webhook | polling (dev)

# ── Ma'lumotlar bazasi / Redis ─────────────────────
DATABASE_URL=postgresql+asyncpg://premium:PAROL@127.0.0.1:5432/premium
REDIS_URL=redis://:PAROL@127.0.0.1:6379/0

# ── TON ────────────────────────────────────────────
TON_NETWORK=mainnet                # mainnet | testnet
TONAPI_KEY=                        # tonconsole.com
TONCENTER_API_KEY=                 # zaxira (@tonapibot)
HOT_WALLET_VERSION=v5r1            # W5
HOT_WALLET_MNEMONIC_FILE=/etc/premium/hot_wallet.enc   # shifrlangan seed fayli (chatga emas!)
ADMIN_TON_ADDRESS=                 # sizning Telegram Wallet TON manzilingiz
ADMIN_TON_MEMO=                    # kerak bo'lsa (custodial hamyon uchun)

# ── Fragment ───────────────────────────────────────
FRAGMENT_MODE=direct               # direct | api
FRAGMENT_API_KEY=                  # faqat api rejimida
# Fragment cookie'lari .env da emas — admin panel orqali shifrlangan holda bazaga yoziladi

# ── Ixtiyoriy ──────────────────────────────────────
SENTRY_DSN=
```

`webapp/.env`:

```dotenv
NEXT_PUBLIC_API_BASE=/api
NEXT_PUBLIC_BOT_USERNAME=PremiumMarketUzBot
NEXT_PUBLIC_TONCONNECT_MANIFEST=https://premium.example.uz/tonconnect-manifest.json
```

### 6.5 Xatoliklar va loglash

- **Xato ierarxiyasi:** `AppError(code, message_key, http_status)` → `NotFound`, `Forbidden`, `ValidationFailed`,
  `InsufficientBalance`, `PriceChanged`, `PaymentExpired`, `RecipientNotFound`, `ProviderUnavailable`,
  `ProviderUncertain`, `RateLimited`, `Maintenance`.
- **API javob formati (xato):**

  ```json
  { "error": { "code": "INSUFFICIENT_BALANCE", "message": "Balansingizda mablag' yetarli emas", "details": { "need_usd": "2.40" } } }
  ```

- Bot handlerlarida xato bo'lsa foydalanuvchiga do'stona xabar ("⚠️ Xatolik yuz berdi, qayta urinib ko'ring") va
  `LOG_CHAT_ID` ga texnik tafsilot (stack trace qisqartmasi, user_id, update turi) yuboriladi.
- **Loglar:** JSON formatda stdout → journald (`journalctl -u premium-api -f`). Har bir so'rovda `request_id`,
  har bir buyurtmada `order_id` kontekstga qo'shiladi. Seed, cookie, token kabi maxfiy qiymatlar loglarda
  avtomatik `***` bilan yashiriladi (structlog processor).

### 6.6 Tranzaksiyalar, qulflar va idempotentlik (pul xavfsizligi)

| Muammo | Yechim |
|--------|--------|
| Bitta to'lov ikki marta hisoblanishi | `payments.ton_tx_hash` va `payments.tg_charge_id` ustunlarida `UNIQUE` |
| Bitta buyurtma ikki marta yetkazilishi | Holat o'tishi shartli: `UPDATE orders SET status='processing' WHERE id=:id AND status='paid'`; worker `FOR UPDATE SKIP LOCKED`; providerga `idempotency_key = order.public_id` |
| Noaniq natija (TON yuborildi, javob yo'q) | Avtomatik qayta urinish **yo'q** → `needs_review`; avval provider/blokcheyndan holat tekshiriladi |
| Balans manfiy bo'lib qolishi | `SELECT ... FOR UPDATE` + `CHECK (balance_usd >= 0)` |
| Foydalanuvchi tugmani 2 marta bosishi | `Idempotency-Key` sarlavhasi (Mini App) / Redis lock (bot, 5 soniya) |
| Narx o'zgarib ketishi | Narx invoice'da muzlatiladi; `pre_checkout_query` da summa qayta tekshiriladi |
| Bir nechta worker bir xil ishni qilishi | PostgreSQL advisory lock (`ton_watcher`, `broadcast`) |
| Ledger va balans mos kelmasligi | Har kuni reconciliation job: `SUM(balance_transactions) == users.balance_usd`, farq bo'lsa alert |

Fulfillment uchun navbatdagi buyurtmani olish:

```sql
UPDATE orders
SET status = 'processing', attempts = attempts + 1, locked_at = now()
WHERE id = (
    SELECT id FROM orders
    WHERE status = 'paid' AND (next_attempt_at IS NULL OR next_attempt_at <= now())
    ORDER BY paid_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *;
```

---

## 7. Jarayon arxitekturasi (process architecture)

### 7.1 Production jarayonlari

```mermaid
flowchart TB
    subgraph systemd["systemd (Docker o'rniga)"]
        direction TB
        N["nginx.service<br/>:80 → :443 redirect<br/>:443 TLS"]
        A["premium-api.service<br/>uvicorn app.main:app<br/>--workers 2 · 127.0.0.1:8000"]
        W["premium-worker.service<br/>python -m app.workers.runner"]
        F["premium-web.service<br/>node .next/standalone/server.js<br/>127.0.0.1:3000"]
        P["postgresql.service"]
        R["redis-server.service"]
        T["premium-backup.timer<br/>har kuni 03:30"]
    end
    N --> A
    N --> F
    A --> P
    A --> R
    W --> P
    W --> R
    T --> P
```

| Jarayon | Nima qiladi | Restart siyosati | Resurs (taxminan) |
|---------|-------------|------------------|-------------------|
| `nginx` | TLS, `/` → web, `/api` va `/tg/webhook` → api, gzip, xavfsizlik sarlavhalari | OS standart | 20 MB |
| `premium-api` | REST API (Mini App), Telegram webhook (aiogram dispatcher), `pre_checkout_query` ga 10 soniya ichida javob | `Restart=always`, `RestartSec=3` | 2 × 150 MB |
| `premium-worker` | Fon vazifalari (7.3), bitta nusxa | `Restart=always`, `RestartSec=5` | 150 MB |
| `premium-web` | Next.js Mini App (SSR shell + client) | `Restart=always` | 120 MB |
| `postgresql` | Ma'lumotlar bazasi, faqat localhost | OS | 300 MB+ |
| `redis-server` | FSM, kesh, rate-limit, heartbeat; faqat localhost, parol bilan | OS | 30 MB |
| `premium-backup.timer` | `pg_dump` → shifrlangan arxiv → 14 kun saqlash + owner'ga Telegram orqali yuborish | timer | — |

**Nega bot alohida jarayon emas?** Bot webhook orqali `premium-api` ichida ishlaydi — servislar, DB pool va
konfiguratsiya umumiy, alohida port/TLS kerak emas. Development'da esa `python -m app.bot.polling` bilan
polling rejimida ishlatiladi (domen/HTTPS kerak emas).

### 7.2 Ishga tushish tartibi (lifespan)

1. `premium-api` start → config yuklanadi va validatsiya qilinadi (yetishmayotgan kalit bo'lsa — aniq xato bilan to'xtaydi).
2. DB pool + Redis ulanadi, `alembic` versiyasi tekshiriladi (migratsiya qilinmagan bo'lsa start to'xtaydi).
3. aiogram `Bot` va `Dispatcher` yaratiladi, routerlar va middlewarelar ulanadi.
4. Webhook **deploy skripti** orqali bir marta o'rnatiladi (`python -m app.cli bot set-webhook`), har worker
   start'da emas.
5. `premium-worker` start → har bir job alohida `asyncio.Task` sifatida, supervisor bilan (job yiqilsa
   backoff bilan qayta ko'tariladi, 3 marta ketma-ket yiqilsa adminga alert).

### 7.3 Worker joblari

| Job | Interval | Vazifa | Qulf |
|-----|----------|--------|------|
| `ton_watcher` | 5 s | Hot wallet'ning yangi kiruvchi tranzaksiyalarini `after_lt` kursor bilan oladi, comment + summa bo'yicha `pending` to'lovlarga moslaydi, tasdiqlaydi; mos kelmaganlarni `unmatched` deb saqlab adminga xabar beradi | advisory lock |
| `fulfillment` | 2 s (navbat bo'sh bo'lsa 5 s) | `paid` buyurtmalarni `SKIP LOCKED` bilan oladi, providerni tanlaydi, yetkazadi, natijani yozadi, xabar yuboradi | row lock |
| `fulfillment_recovery` | 1 daq | 10 daqiqadan ortiq `processing` da qolgan buyurtmalarni topadi → provider/blokcheyn holatini tekshiradi → `completed` yoki `needs_review` | row lock |
| `expirer` | 1 daq | Muddati o'tgan `pending` to'lovlar va `awaiting_payment` buyurtmalarni `expired` qiladi, bot xabarini yangilaydi | — |
| `rates` | 1 daq (CBU — kuniga 1) | TON/USD, USD/UZS kurslarini yangilaydi (Redis + `exchange_rates`) | — |
| `provider_prices` | 10 daq | Fragment'dan premium va stars tannarxini oladi; katalog keshini yangilaydi | — |
| `stars_balance` | 10 daq | `getMyStarBalance` → admin dashboard uchun | — |
| `hot_wallet` | 2 daq | Balansni tekshiradi; past bo'lsa alert; avto-sweep yoqilgan bo'lsa ortiqchasini admin wallet'ga yuboradi | advisory lock |
| `stats` | 5 daq | Bugungi va kechagi `daily_stats` qatorlarini qayta hisoblaydi (idempotent upsert) | advisory lock |
| `broadcast` | doimiy | `running` broadcastlarni ~25 xabar/s tezlikda yuboradi, `retry_after` ni hurmat qiladi, bloklaganlarni belgilaydi | advisory lock |
| `reports` | cron | Har kuni 23:55 — kunlik hisobot; dushanba 09:00 — haftalik; oyning 1-kuni — oylik (owner'ga) | — |
| `reconciliation` | har kuni 04:00 | Ledger ↔ balans, hot wallet ledger ↔ blokcheyn balansi solishtiriladi | — |
| `fragment_health` | 30 daq | Fragment sessiyasi tirikligini tekshiradi; cookie eskirgan bo'lsa alert | — |
| `heartbeat` | 30 s | Redis'ga `worker:heartbeat` yozadi (API `/health` buni tekshiradi) | — |

### 7.4 Ketma-ketlik diagrammalari (asosiy oqimlar)

#### 7.4.1 Mini App autentifikatsiyasi

```mermaid
sequenceDiagram
    autonumber
    actor U as Foydalanuvchi
    participant TG as Telegram ilova
    participant MA as Mini App
    participant API as FastAPI
    participant DB as PostgreSQL

    U->>TG: Menu tugmasi yoki "Ilovani ochish"
    TG->>MA: WebView ochadi + initData (imzolangan)
    MA->>API: GET /api/v1/me  [Authorization: tma initDataRaw]
    API->>API: HMAC-SHA256 tekshiruvi (bot token asosida)
    API->>API: auth_date 24 soatdan eski emasligini tekshirish
    API->>DB: foydalanuvchini upsert + last_seen + kunlik faollik
    API-->>MA: user, balans, til, rol (is_admin)
    MA->>U: Bosh sahifa (admin bo'lsa "Admin panel" tugmasi ham)
```

#### 7.4.2 Premium — TON bilan (Mini App, TON Connect)

```mermaid
sequenceDiagram
    autonumber
    actor U as Foydalanuvchi
    participant MA as Mini App
    participant API as FastAPI
    participant DB as PostgreSQL
    participant WL as TON hamyon
    participant TA as TonAPI
    participant WK as Worker
    participant FR as Fragment
    participant BOT as Bot

    U->>MA: 12 oy, @do'stim, TON
    MA->>API: POST /api/v1/recipients/resolve (@do'stim)
    API->>FR: qabul qiluvchini qidirish
    FR-->>API: topildi, ism, premium olishi mumkin
    API-->>MA: preview (ism, avatar)
    U->>MA: "4.39 TON to'lash"
    MA->>API: POST /api/v1/orders [Idempotency-Key]
    API->>API: narx hisoblash (server), promokod
    API->>DB: order awaiting_payment + payment pending (comment PM-7F3K9Q, 20 daq)
    API-->>MA: manzil, nanoton summa, comment, expires_at
    MA->>WL: TON Connect sendTransaction (payload = comment)
    U->>WL: Tasdiqlash
    WL-->>MA: BOC (yuborildi)
    MA->>API: POST /payments/{id}/ton/submitted (boc)
    loop har 5 soniyada
        WK->>TA: hot wallet yangi tranzaksiyalari (after_lt)
    end
    TA-->>WK: kiruvchi tx: 4.39 TON, comment PM-7F3K9Q
    WK->>DB: payment confirmed (tx_hash UNIQUE), order paid
    WK->>BOT: "✅ To'lov qabul qilindi"
    WK->>DB: order processing (SKIP LOCKED)
    WK->>FR: Premium 12 oy → @do'stim (idempotency = order id)
    FR-->>WK: muvaffaqiyat, tx hash
    WK->>DB: order completed, cost_usd, profit_usd, ledgerlar
    WK->>BOT: foydalanuvchiga "🎉 Tayyor", log kanalga xabar
    MA->>API: GET /api/v1/orders/{id} (har 3 soniyada)
    API-->>MA: completed
    MA->>U: 🎉 Muvaffaqiyat animatsiyasi + haptic
```

#### 7.4.3 Premium — Stars bilan (bot ichida)

```mermaid
sequenceDiagram
    autonumber
    actor U as Foydalanuvchi
    participant BOT as Bot (FastAPI ichida)
    participant DB as PostgreSQL
    participant TGP as Telegram Payments
    participant WK as Worker

    U->>BOT: Premium → O'zimga → 3 oy → ⭐ Stars
    BOT->>DB: order awaiting_payment + payment pending (1100 XTR)
    BOT->>U: sendInvoice (currency XTR, 1100 ⭐, payload = payment id)
    U->>TGP: "⭐ 1100 to'lash"
    TGP->>BOT: pre_checkout_query
    BOT->>DB: to'lov pending va summa mosligini tekshirish
    BOT-->>TGP: answerPreCheckoutQuery ok (10 s ichida)
    TGP->>BOT: successful_payment (telegram_payment_charge_id)
    BOT->>DB: payment confirmed (charge_id UNIQUE), order paid, stars ledger +1100
    BOT->>U: "✅ To'lov qabul qilindi, faollashtirilmoqda..."
    WK->>DB: order processing
    WK->>TGP: giftPremiumSubscription(user_id, 3, 1000)
    TGP-->>WK: True
    WK->>DB: order completed, stars ledger −1000, foyda 100 ⭐
    WK->>U: "🎉 Premium 3 oyga faollashtirildi!"
```

#### 7.4.4 Balansdan xarid

```mermaid
sequenceDiagram
    autonumber
    actor U as Foydalanuvchi
    participant API as API / Bot
    participant DB as PostgreSQL
    participant WK as Worker

    U->>API: Stars 500 → @username → 💼 Balansdan
    API->>DB: BEGIN
    API->>DB: SELECT balance FROM users WHERE id=? FOR UPDATE
    alt balans yetarli
        API->>DB: balans −narx, balance_transactions (purchase)
        API->>DB: order paid, payment confirmed (method balance)
        API->>DB: COMMIT
        API-->>U: "✅ To'landi, yuborilmoqda..."
        WK->>DB: yetkazish (7.4.2 dagi kabi)
    else yetarli emas
        API->>DB: ROLLBACK
        API-->>U: "Balans yetarli emas (yana 2.40 $ kerak)" + [To'ldirish]
    end
```

#### 7.4.5 Yetkazish xatosi va pulni qaytarish

```mermaid
sequenceDiagram
    autonumber
    participant WK as Worker
    participant PR as Provider (Fragment)
    participant DB as PostgreSQL
    participant U as Foydalanuvchi
    participant AD as Admin (log kanal)

    WK->>PR: deliver(order)
    alt vaqtinchalik xato (5xx, timeout pul yuborilishidan oldin)
        PR-->>WK: xato
        WK->>DB: status paid, next_attempt_at = hozir + 30s/2m/10m
        Note over WK,DB: maksimal 3 urinish, zaxira provider sinab ko'riladi
    else doimiy xato (username yo'q, qabul qila olmaydi)
        PR-->>WK: RecipientInvalid
        WK->>DB: order failed
        WK->>DB: refund (Stars → refundStarPayment, TON/balans → ichki balans)
        WK->>U: "❌ Bajarilmadi, pul qaytarildi" + sabab
        WK->>AD: alert
    else noaniq (TON yuborildi, javob kelmadi)
        PR-->>WK: timeout
        WK->>DB: order needs_review (avtomatik qaytarish YO'Q)
        WK->>AD: "⚠️ Tekshirish kerak" [Bajarildi] [Qayta] [Qaytarish]
        WK->>U: "⏳ Buyurtmangiz tekshirilmoqda"
    end
```

#### 7.4.6 Balansni TON bilan to'ldirish

```mermaid
sequenceDiagram
    autonumber
    actor U as Foydalanuvchi
    participant API as API / Bot
    participant DB as PostgreSQL
    participant WK as Worker (ton_watcher)

    U->>API: Hamyon → To'ldirish → TON → 10 $
    API->>DB: payment pending (purpose topup, 3.34 TON, comment TP-K2M9QX, 20 daq)
    API-->>U: manzil + summa + izoh / TON Connect
    U->>U: hamyondan TON yuboradi
    WK->>DB: moslik topildi → payment confirmed
    WK->>DB: balans +10 $ (balance_transactions topup, kurs muzlatilgan)
    WK->>U: "💼 Balansingiz 10 $ ga to'ldirildi"
```

#### 7.4.7 Admin pul yechishi (Telegram Wallet'ga)

```mermaid
sequenceDiagram
    autonumber
    actor A as Owner
    participant BOT as Bot / Mini App
    participant HW as HotWalletService
    participant TON as TON tarmog'i
    participant DB as PostgreSQL

    A->>BOT: 💰 Moliya → 💸 Pul yechish
    BOT->>HW: mavjud summa = balans − rezerv
    BOT-->>A: "Maksimal 95.4 TON. Qancha yechasiz?"
    A->>BOT: 50
    BOT-->>A: "50 TON → UQ...x9F (ADMIN_TON_ADDRESS). Tasdiqlaysizmi?" [✅ Tasdiqlash] [✖️ Bekor]
    A->>BOT: ✅ Tasdiqlash
    BOT->>HW: withdraw_to_admin(50, actor=owner)
    HW->>HW: rol = owner? kunlik limit? manzil faqat .env dan
    HW->>TON: transfer 50 TON (+ memo bo'lsa)
    TON-->>HW: tx hash
    HW->>DB: hot_wallet_transactions (withdrawal) + audit_logs
    BOT-->>A: "✅ Yuborildi" + tonviewer havolasi
```

#### 7.4.8 Ommaviy xabar (broadcast)

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant BOT as Bot / Mini App
    participant DB as PostgreSQL
    participant WK as Worker (broadcast)
    participant TG as Telegram

    A->>BOT: 📣 Xabar yuborish → kontent → tugmalar → segment
    BOT-->>A: Oldindan ko'rish + "~12 430 kishiga yuboriladi"
    A->>BOT: 🚀 Yuborish (yoki rejalashtirish)
    BOT->>DB: broadcast running, cursor = 0
    loop har bir partiya (25 ta)
        WK->>DB: keyingi foydalanuvchilar (id > cursor)
        WK->>TG: copyMessage / sendMessage
        alt 403 bot bloklangan
            WK->>DB: user is_bot_blocked = true
        else 429 retry_after
            WK->>WK: kutish
        end
        WK->>DB: sent, failed, cursor yangilanadi
    end
    WK->>A: "✅ Yakunlandi: 12 101 yuborildi, 329 bloklagan"
```

### 7.5 Holat mashinalari (state machines)

#### 7.5.1 Buyurtma (`orders.status`)

```mermaid
stateDiagram-v2
    [*] --> awaiting_payment: buyurtma yaratildi
    awaiting_payment --> paid: to'lov tasdiqlandi
    awaiting_payment --> expired: muddat o'tdi
    awaiting_payment --> cancelled: foydalanuvchi bekor qildi
    paid --> processing: worker oldi
    processing --> completed: provider muvaffaqiyatli
    processing --> paid: vaqtinchalik xato, qayta urinish
    processing --> failed: doimiy xato yoki urinishlar tugadi
    processing --> needs_review: natija noaniq
    needs_review --> completed: admin tasdiqladi
    needs_review --> paid: admin qayta urinish
    needs_review --> refunded: admin qaytardi
    failed --> paid: admin qayta urinish
    failed --> refunded: pul qaytarildi
    failed --> completed: admin qo'lda bajardi
    completed --> [*]
    refunded --> [*]
    expired --> [*]
    cancelled --> [*]
```

Ruxsat etilgan o'tishlar kodda `ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]]` sifatida saqlanadi va
har bir o'tish `UPDATE ... WHERE status = :old` bilan atomik bajariladi + `order_events` jadvaliga yoziladi.

#### 7.5.2 To'lov (`payments.status`)

```mermaid
stateDiagram-v2
    [*] --> pending: invoice yaratildi
    pending --> confirmed: pul keldi (summa yetarli)
    pending --> expired: muddat o'tdi
    pending --> failed: kam to'lov yoki xato
    expired --> confirmed: kech kelgan to'lov (is_late, balansga)
    confirmed --> refunded: qaytarildi
    confirmed --> [*]
    refunded --> [*]
    failed --> [*]
    expired --> [*]
```

---

## 8. Class diagrammalar

### 8.1 Domen modellari (ORM)

```mermaid
classDiagram
    direction LR

    class User {
        +int id
        +str username
        +str first_name
        +str last_name
        +str language
        +Decimal balance_usd
        +int referrer_id
        +bool is_banned
        +bool is_bot_blocked
        +bool tg_is_premium
        +datetime created_at
        +datetime last_seen_at
    }
    class Admin {
        +int user_id
        +AdminRole role
        +int added_by
        +datetime created_at
    }
    class PremiumPlan {
        +int id
        +int months
        +bool is_enabled
        +bool provider_supported
        +Decimal cost_ton
        +Decimal markup_percent
        +Decimal fixed_markup_usd
        +Decimal fixed_price_usd
        +int price_stars
        +Decimal reference_price_usd
        +str badge
        +int sort_order
    }
    class StarPackage {
        +int id
        +int amount
        +bool is_enabled
        +bool is_popular
        +int sort_order
    }
    class Order {
        +int id
        +str public_id
        +ProductType product_type
        +int plan_months
        +int stars_amount
        +RecipientType recipient_type
        +str recipient_username
        +int recipient_user_id
        +OrderStatus status
        +Decimal price_usd
        +Decimal discount_usd
        +Decimal cost_usd
        +Decimal profit_usd
        +ProviderCode provider
        +int attempts
        +datetime next_attempt_at
        +str error_code
        +can_transition(to) bool
    }
    class OrderEvent {
        +int id
        +int order_id
        +OrderStatus from_status
        +OrderStatus to_status
        +str actor
        +dict data
    }
    class Payment {
        +int id
        +str public_id
        +PaymentPurpose purpose
        +PaymentMethod method
        +PaymentStatus status
        +Decimal amount
        +str currency
        +Decimal amount_usd
        +Decimal rate_used
        +str ton_comment
        +str ton_tx_hash
        +str tg_charge_id
        +bool is_late
        +datetime expires_at
    }
    class BalanceTransaction {
        +int id
        +int user_id
        +Decimal amount_usd
        +Decimal balance_after
        +BalanceTxType type
        +str ref_type
        +int ref_id
    }
    class HotWalletTransaction {
        +int id
        +Direction direction
        +HotWalletTxKind kind
        +Decimal amount_ton
        +Decimal amount_usd
        +str tx_hash
        +int order_id
    }
    class StarsTransaction {
        +int id
        +Direction direction
        +StarsTxKind kind
        +int amount
        +int order_id
    }
    class PromoCode {
        +int id
        +str code
        +PromoType type
        +Decimal value
        +int max_uses
        +int used_count
        +int per_user_limit
        +datetime valid_to
        +is_valid_for(user, order) bool
    }
    class PromoRedemption {
        +int id
        +int promo_id
        +int user_id
        +int order_id
        +Decimal discount_usd
    }
    class ReferralReward {
        +int id
        +int referrer_id
        +int referred_id
        +int order_id
        +Decimal amount_usd
        +RewardStatus status
    }
    class Expense {
        +int id
        +ExpenseCategory category
        +Decimal amount_usd
        +str note
        +date spent_on
    }
    class Broadcast {
        +int id
        +dict content
        +dict segment
        +BroadcastStatus status
        +int total
        +int sent
        +int failed
        +int cursor_user_id
    }
    class Channel {
        +int id
        +int chat_id
        +str title
        +str invite_link
        +bool is_active
    }
    class Setting {
        +str key
        +dict value
        +bool is_secret
    }
    class AuditLog {
        +int id
        +int actor_id
        +str action
        +str entity
        +str entity_id
        +dict before
        +dict after
    }
    class DailyStats {
        +date day
        +int new_users
        +int active_users
        +int orders_completed
        +Decimal revenue_usd
        +Decimal cost_usd
        +Decimal profit_usd
    }
    class ExchangeRate {
        +str pair
        +Decimal rate
        +str source
        +datetime fetched_at
    }

    User "1" --> "*" Order : buyurtma beradi
    User "1" --> "*" Payment : to'laydi
    User "1" --> "*" BalanceTransaction : ledger
    User "0..1" --> "*" User : taklif qilgan
    Admin "1" --> "1" User : rol
    Order "1" --> "*" Payment : to'lovlar
    Order "1" --> "*" OrderEvent : tarix
    Order "1" --> "0..1" PromoRedemption : chegirma
    PromoCode "1" --> "*" PromoRedemption
    Order "1" --> "0..1" ReferralReward : bonus
    Order "1" --> "*" HotWalletTransaction : tannarx TON
    Order "1" --> "*" StarsTransaction : tannarx Stars
    PremiumPlan "1" ..> "*" Order : asosida
    StarPackage "1" ..> "*" Order : asosida
    User "1" --> "*" AuditLog : admin amallari
```

### 8.2 Servislar, strategiyalar va providerlar

```mermaid
classDiagram
    direction TB

    class OrderService {
        -OrderRepository orders
        -PricingService pricing
        -PromoService promo
        +create(user, CreateOrderRequest) Order
        +cancel(order_id, user) Order
        +mark_paid(order, payment) Order
        +start_processing(order) Order
        +complete(order, DeliveryResult) Order
        +fail(order, error) Order
        +mark_review(order, reason) Order
    }
    class PricingService {
        -RateService rates
        -SettingsService settings
        +quote_premium(plan, method) Quote
        +quote_stars(amount, method) Quote
        +quote_topup(amount_usd, method) Quote
        +apply_promo(quote, code, user) Quote
    }
    class Quote {
        +Decimal price_usd
        +Decimal price_ton
        +int price_xtr
        +int price_uzs
        +Decimal cost_usd
        +Decimal discount_usd
        +datetime valid_until
    }
    class RateService {
        -List~RateSource~ sources
        +ton_usd() Decimal
        +usd_uzs() Decimal
        +refresh() None
    }
    class RateSource {
        <<interface>>
        +fetch(pair) Decimal
    }
    class PaymentService {
        -dict handlers
        +create_for_order(order, method) PaymentInstructions
        +create_topup(user, amount, method) PaymentInstructions
        +confirm(payment, evidence) Payment
        +expire_stale() int
    }
    class PaymentMethodHandler {
        <<abstract>>
        +PaymentMethod method
        +create(payment) PaymentInstructions
        +confirm(payment, evidence) Payment
        +refund(payment) None
    }
    class TonPaymentHandler {
        -TonChainClient chain
        +generate_comment() str
        +match_incoming(IncomingTx) Payment
    }
    class StarsPaymentHandler {
        -Bot bot
        +send_invoice(payment) None
        +create_invoice_link(payment) str
        +validate_pre_checkout(query) bool
    }
    class BalancePaymentHandler {
        -BalanceService balance
    }
    class FulfillmentService {
        -List~FulfillmentProvider~ providers
        -OrderService orders
        +process_next() bool
        +select_provider(order) FulfillmentProvider
        +retry(order_id, actor) None
        +refund(order_id, actor) None
    }
    class FulfillmentProvider {
        <<interface>>
        +ProviderCode code
        +supports(order) bool
        +is_available() bool
        +get_prices() ProviderPrices
        +resolve_recipient(username) RecipientInfo
        +deliver(order) DeliveryResult
        +check_status(order) DeliveryStatus
    }
    class FragmentDirectProvider {
        -FragmentSession session
        -TonWallet wallet
    }
    class FragmentApiProvider {
        -str api_key
        -TonWallet wallet
    }
    class BotStarsProvider {
        -Bot bot
        +star_balance() int
    }
    class MockProvider {
        +bool fail_mode
    }
    class BalanceService {
        +credit(user_id, amount, type, ref) BalanceTransaction
        +debit(user_id, amount, type, ref) BalanceTransaction
        +history(user_id, page) List~BalanceTransaction~
    }
    class HotWalletService {
        -TonWallet wallet
        -TonChainClient chain
        +balance() Decimal
        +withdraw_to_admin(amount, actor) str
        +auto_sweep() str
    }
    class TonChainClient {
        <<interface>>
        +get_incoming(address, after_lt) List~IncomingTx~
        +get_balance(address) Decimal
        +send(to, amount, comment) str
        +get_tx(hash) TxInfo
    }
    class TonApiClient
    class ToncenterClient
    class AnalyticsService {
        +dashboard(period) Dashboard
        +timeseries(metric, granularity, from, to) Series
        +top_buyers(period, limit) List
        +recompute_day(day) None
    }
    class BroadcastService {
        +create(admin, content, segment) Broadcast
        +start(id) None
        +pause(id) None
        +send_batch(broadcast) int
    }
    class NotificationService {
        +notify_user(user_id, key, data) None
        +notify_admins(event, data) None
        +alert(level, text) None
    }
    class ReferralService {
        +attach(user, ref_code) None
        +reward_for_order(order) None
        +revoke_for_order(order) None
    }
    class PromoService {
        +validate(code, user, product) PromoCode
        +redeem(promo, order) PromoRedemption
    }
    class SettingsService {
        +get(key) Any
        +set(key, value, actor) None
    }
    class AuditService {
        +log(actor, action, entity, before, after) None
    }

    OrderService --> PricingService
    OrderService --> PromoService
    PricingService --> RateService
    PricingService --> SettingsService
    PricingService ..> Quote : yaratadi
    RateService --> RateSource
    PaymentService --> PaymentMethodHandler
    PaymentMethodHandler <|-- TonPaymentHandler
    PaymentMethodHandler <|-- StarsPaymentHandler
    PaymentMethodHandler <|-- BalancePaymentHandler
    BalancePaymentHandler --> BalanceService
    TonPaymentHandler --> TonChainClient
    FulfillmentService --> FulfillmentProvider
    FulfillmentService --> OrderService
    FulfillmentService --> BalanceService
    FulfillmentService --> NotificationService
    FulfillmentService --> ReferralService
    FulfillmentProvider <|.. FragmentDirectProvider
    FulfillmentProvider <|.. FragmentApiProvider
    FulfillmentProvider <|.. BotStarsProvider
    FulfillmentProvider <|.. MockProvider
    HotWalletService --> TonChainClient
    TonChainClient <|.. TonApiClient
    TonChainClient <|.. ToncenterClient
    HotWalletService --> AuditService
    BroadcastService --> NotificationService
```

### 8.3 Ishlatilgan dizayn patternlar

| Pattern | Qayerda | Nima uchun |
|---------|---------|------------|
| Strategy | `PaymentMethodHandler`, `FulfillmentProvider`, `RateSource` | Yangi to'lov/yetkazish usulini mavjud kodni buzmasdan qo'shish |
| Repository | `repositories/*` | SQL'ni biznes mantiqdan ajratish, test qilish oson |
| State machine | `Order`, `Payment`, `Broadcast` | Noto'g'ri holat o'tishlarini imkonsiz qilish |
| Unit of Work | Har bir so'rov/update = bitta DB tranzaksiya | Pul operatsiyalarining atomikligi |
| Chain of Responsibility | aiogram middlewarelar | Throttle → user → i18n → ban → maintenance → obuna |
| Outbox (yengil) | `order_events` + worker xabarlari | Xabar yuborish DB tranzaksiyasidan keyin, yo'qolmasdan |
| Dependency Injection | FastAPI `Depends`, aiogram `workflow_data` | Servislarni handlerlarga uzatish, testda almashtirish |

---

## 9. Ma'lumotlar bazasi (PostgreSQL)

### 9.1 Umumiy qoidalar

- Barcha vaqtlar `timestamptz` (UTC'da saqlanadi, Asia/Tashkent'da ko'rsatiladi).
- Pul: USD → `NUMERIC(18,6)`, TON → `NUMERIC(20,9)` (nano aniqlik), Stars → `INTEGER`, so'm → `BIGINT`.
- Har bir jadvalda `created_at` (default `now()`), o'zgaradiganlarida `updated_at` (trigger yoki ORM `onupdate`).
- Foydalanuvchi ID = Telegram ID (`BIGINT`), boshqa jadvallar `BIGSERIAL` / `BIGINT GENERATED ALWAYS AS IDENTITY`.
- Tashqi ko'rinadigan identifikatorlar: `public_id` (masalan `PR-8F3K2Q`, `ST-…`, `TP-…`) — ichki ID'ni oshkor qilmaslik uchun.
- Enumlar PostgreSQL `ENUM` turi sifatida (Alembic orqali boshqariladi).

### 9.2 ER diagramma

```mermaid
erDiagram
    USERS ||--o{ ORDERS : "buyurtma"
    USERS ||--o{ PAYMENTS : "to'lov"
    USERS ||--o{ BALANCE_TRANSACTIONS : "ledger"
    USERS ||--o{ USERS : "referrer"
    USERS ||--o| ADMINS : "rol"
    USERS ||--o{ USER_DAILY_ACTIVITY : "faollik"
    USERS ||--o{ REFERRAL_REWARDS : "bonus"
    ORDERS ||--o{ PAYMENTS : "to'lovlar"
    ORDERS ||--o{ ORDER_EVENTS : "tarix"
    ORDERS ||--o| PROMO_REDEMPTIONS : "chegirma"
    ORDERS ||--o{ HOT_WALLET_TRANSACTIONS : "TON harakati"
    ORDERS ||--o{ STARS_TRANSACTIONS : "Stars harakati"
    ORDERS ||--o| REFERRAL_REWARDS : "bonus"
    PROMO_CODES ||--o{ PROMO_REDEMPTIONS : "ishlatilgan"
    PREMIUM_PLANS ||--o{ ORDERS : "tarif"
    USERS ||--o{ BROADCASTS : "yaratgan"
    USERS ||--o{ AUDIT_LOGS : "amal"
    USERS ||--o{ EXPENSES : "kiritgan"

    USERS {
        bigint id PK
        varchar username
        varchar first_name
        varchar last_name
        varchar language
        numeric balance_usd
        bigint referrer_id FK
        boolean is_banned
        boolean is_bot_blocked
        boolean tg_is_premium
        varchar source
        timestamptz created_at
        timestamptz last_seen_at
    }
    ADMINS {
        bigint user_id PK
        admin_role role
        bigint added_by FK
        timestamptz created_at
    }
    PREMIUM_PLANS {
        int id PK
        int months
        boolean is_enabled
        boolean provider_supported
        numeric cost_ton
        numeric markup_percent
        numeric fixed_markup_usd
        numeric fixed_price_usd
        int price_stars
        numeric reference_price_usd
        varchar badge
        int sort_order
    }
    STAR_PACKAGES {
        int id PK
        int amount
        boolean is_enabled
        boolean is_popular
        int sort_order
    }
    ORDERS {
        bigint id PK
        varchar public_id
        bigint user_id FK
        product_type product_type
        int plan_id FK
        int plan_months
        int stars_amount
        recipient_type recipient_type
        varchar recipient_username
        bigint recipient_user_id
        varchar recipient_name
        order_status status
        numeric price_usd
        numeric discount_usd
        numeric cost_usd
        numeric profit_usd
        provider_code provider
        varchar provider_ref
        int attempts
        timestamptz next_attempt_at
        varchar error_code
        jsonb meta
        timestamptz paid_at
        timestamptz completed_at
    }
    ORDER_EVENTS {
        bigint id PK
        bigint order_id FK
        order_status from_status
        order_status to_status
        varchar actor
        jsonb data
        timestamptz created_at
    }
    PAYMENTS {
        bigint id PK
        varchar public_id
        bigint user_id FK
        bigint order_id FK
        payment_purpose purpose
        payment_method method
        payment_status status
        numeric amount
        varchar currency
        numeric amount_usd
        numeric rate_used
        varchar ton_comment
        varchar ton_tx_hash
        varchar ton_sender
        varchar tg_charge_id
        boolean is_late
        timestamptz expires_at
        timestamptz confirmed_at
    }
    BALANCE_TRANSACTIONS {
        bigint id PK
        bigint user_id FK
        numeric amount_usd
        numeric balance_after
        balance_tx_type type
        varchar ref_type
        bigint ref_id
        varchar comment
        bigint created_by
    }
    HOT_WALLET_TRANSACTIONS {
        bigint id PK
        direction direction
        hot_wallet_tx_kind kind
        numeric amount_ton
        numeric fee_ton
        numeric amount_usd
        varchar tx_hash
        varchar counterparty
        bigint order_id FK
        bigint payment_id FK
    }
    STARS_TRANSACTIONS {
        bigint id PK
        direction direction
        stars_tx_kind kind
        int amount
        bigint order_id FK
        bigint payment_id FK
    }
    PROMO_CODES {
        int id PK
        varchar code
        promo_type type
        numeric value
        product_scope applies_to
        numeric min_order_usd
        int max_uses
        int used_count
        int per_user_limit
        timestamptz valid_from
        timestamptz valid_to
        boolean is_active
    }
    PROMO_REDEMPTIONS {
        bigint id PK
        int promo_id FK
        bigint user_id FK
        bigint order_id FK
        numeric discount_usd
    }
    REFERRAL_REWARDS {
        bigint id PK
        bigint referrer_id FK
        bigint referred_id FK
        bigint order_id FK
        numeric amount_usd
        reward_status status
    }
    EXPENSES {
        bigint id PK
        expense_category category
        numeric amount_usd
        varchar note
        date spent_on
        bigint created_by FK
    }
    BROADCASTS {
        bigint id PK
        bigint created_by FK
        jsonb content
        jsonb segment
        broadcast_status status
        timestamptz scheduled_at
        int total
        int sent
        int failed
        bigint cursor_user_id
    }
    CHANNELS {
        int id PK
        bigint chat_id
        varchar title
        varchar invite_link
        boolean is_active
    }
    SETTINGS {
        varchar key PK
        jsonb value
        boolean is_secret
        bigint updated_by
        timestamptz updated_at
    }
    AUDIT_LOGS {
        bigint id PK
        bigint actor_id FK
        varchar action
        varchar entity
        varchar entity_id
        jsonb before
        jsonb after
        varchar source
    }
    EXCHANGE_RATES {
        bigint id PK
        varchar pair
        numeric rate
        varchar source
        timestamptz fetched_at
    }
    USER_DAILY_ACTIVITY {
        date day PK
        bigint user_id PK
    }
    DAILY_STATS {
        date day PK
        int new_users
        int active_users
        int orders_completed
        numeric revenue_usd
        numeric cost_usd
        numeric profit_usd
    }
    UNMATCHED_TON_TXS {
        bigint id PK
        varchar tx_hash
        numeric amount_ton
        varchar comment
        varchar sender
        varchar resolution
    }
```

### 9.3 Enum turlari

| Enum | Qiymatlar |
|------|-----------|
| `product_type` | `premium`, `stars` |
| `recipient_type` | `self`, `other` |
| `order_status` | `awaiting_payment`, `paid`, `processing`, `completed`, `failed`, `needs_review`, `refunded`, `expired`, `cancelled` |
| `payment_purpose` | `order`, `topup` |
| `payment_method` | `ton`, `usdt_ton` (keyin), `stars`, `balance` |
| `payment_status` | `pending`, `confirmed`, `expired`, `failed`, `refunded` |
| `provider_code` | `fragment_direct`, `fragment_api`, `bot_stars`, `manual`, `mock` |
| `balance_tx_type` | `topup`, `purchase`, `refund`, `referral_bonus`, `referral_revoke`, `admin_credit`, `admin_debit`, `late_payment`, `overpayment`, `underpayment` |
| `direction` | `in`, `out` |
| `hot_wallet_tx_kind` | `user_payment`, `fulfillment`, `withdrawal`, `sweep`, `network_fee`, `manual_deposit`, `refund_out`, `other` |
| `stars_tx_kind` | `payment_in`, `premium_gift`, `refund`, `withdrawal_manual`, `telegram_refund` |
| `admin_role` | `owner`, `admin`, `support` |
| `promo_type` | `percent`, `fixed_usd` |
| `product_scope` | `all`, `premium`, `stars` |
| `reward_status` | `credited`, `revoked` |
| `expense_category` | `server`, `domain`, `fragment_fee`, `network_fee`, `advertising`, `salary`, `other` |
| `broadcast_status` | `draft`, `scheduled`, `running`, `paused`, `completed`, `cancelled`, `failed` |

### 9.4 Jadvallar — ustunlar, cheklovlar, indekslar

#### `users`

| Ustun | Tur | Cheklov / default | Izoh |
|-------|-----|-------------------|------|
| `id` | `BIGINT` | PK | Telegram user ID |
| `username` | `VARCHAR(32)` | NULL | `@` siz, kichik harfda indekslanadi |
| `first_name`, `last_name` | `VARCHAR(128)` | | |
| `language` | `VARCHAR(5)` | `'uz'` | `uz` / `ru` / `en` |
| `balance_usd` | `NUMERIC(18,6)` | `0`, `CHECK (balance_usd >= 0)` | ichki balans |
| `referrer_id` | `BIGINT` | FK `users.id`, NULL, `CHECK (referrer_id <> id)` | kim taklif qilgan |
| `is_banned` | `BOOLEAN` | `false` | |
| `ban_reason` | `VARCHAR(255)` | NULL | |
| `is_bot_blocked` | `BOOLEAN` | `false` | botni bloklaganmi (broadcast'da aniqlanadi) |
| `tg_is_premium` | `BOOLEAN` | `false` | Telegram'dan keladi |
| `source` | `VARCHAR(64)` | NULL | `/start` parametri (reklama manbasi) |
| `total_spent_usd` | `NUMERIC(18,6)` | `0` | denormalizatsiya (tez statistika) |
| `orders_count` | `INTEGER` | `0` | |
| `created_at`, `last_seen_at` | `TIMESTAMPTZ` | `now()` | |

Indekslar: `ix_users_username_lower (lower(username))`, `ix_users_created_at`, `ix_users_referrer_id`,
`ix_users_last_seen_at`.

#### `admins`

| Ustun | Tur | Cheklov | Izoh |
|-------|-----|---------|------|
| `user_id` | `BIGINT` | PK, FK `users.id` | |
| `role` | `admin_role` | NOT NULL | `owner` faqat `.env` dagi ID'ga beriladi |
| `added_by` | `BIGINT` | FK | |
| `created_at` | `TIMESTAMPTZ` | | |

#### `premium_plans`

| Ustun | Tur | Default | Izoh |
|-------|-----|---------|------|
| `id` | `SERIAL` | PK | |
| `months` | `SMALLINT` | UNIQUE, `CHECK (months IN (1,3,6,12))` | |
| `is_enabled` | `BOOLEAN` | `true` (1 oy — `false`) | admin yoqadi/o'chiradi |
| `provider_supported` | `BOOLEAN` | `true` (1 oy — `false`) | provider qo'llaydimi |
| `cost_ton` | `NUMERIC(20,9)` | NULL | Fragment'dan oxirgi narx |
| `cost_updated_at` | `TIMESTAMPTZ` | NULL | |
| `markup_percent` | `NUMERIC(6,2)` | `8.00` | |
| `fixed_markup_usd` | `NUMERIC(18,6)` | `0` | |
| `fixed_price_usd` | `NUMERIC(18,6)` | NULL | qo'yilsa formula o'rniga |
| `price_stars` | `INTEGER` | 3→1100, 6→1650, 12→2750 | Stars narxi |
| `reference_price_usd` | `NUMERIC(18,6)` | NULL | "X% arzon" belgisi uchun |
| `badge` | `VARCHAR(32)` | NULL | masalan `🔥 Eng foydali` |
| `sort_order` | `SMALLINT` | | |

#### `star_packages`

`id SERIAL PK`, `amount INTEGER UNIQUE CHECK (amount >= 50)`, `is_enabled BOOLEAN`, `is_popular BOOLEAN`,
`sort_order SMALLINT`. Seed: 50, 100, 250, 500 (🔥), 1000, 2500, 5000, 10000.

#### `orders`

| Ustun | Tur | Cheklov | Izoh |
|-------|-----|---------|------|
| `id` | `BIGINT IDENTITY` | PK | |
| `public_id` | `VARCHAR(16)` | UNIQUE | `PR-8F3K2Q` / `ST-…` |
| `user_id` | `BIGINT` | FK, NOT NULL | xaridor |
| `product_type` | `product_type` | NOT NULL | |
| `plan_id` | `INTEGER` | FK, NULL | premium uchun |
| `plan_months` | `SMALLINT` | NULL | snapshot |
| `stars_amount` | `INTEGER` | NULL, `CHECK (stars_amount >= 50)` | stars uchun |
| `recipient_type` | `recipient_type` | NOT NULL | |
| `recipient_username` | `VARCHAR(32)` | NULL | |
| `recipient_user_id` | `BIGINT` | NULL | |
| `recipient_name` | `VARCHAR(128)` | NULL | Fragment'dan olingan ism |
| `status` | `order_status` | NOT NULL | |
| `payment_method` | `payment_method` | NOT NULL | |
| `price_usd` | `NUMERIC(18,6)` | NOT NULL | chegirmadan keyingi narx |
| `discount_usd` | `NUMERIC(18,6)` | `0` | |
| `price_amount` / `price_currency` | `NUMERIC(30,9)` / `VARCHAR(8)` | | to'langan valyutada (TON/XTR/USD) |
| `cost_usd` | `NUMERIC(18,6)` | NULL | haqiqiy tannarx (yetkazishdan keyin) |
| `cost_amount` / `cost_currency` | `NUMERIC(30,9)` / `VARCHAR(8)` | | TON yoki XTR |
| `profit_usd` | `NUMERIC(18,6)` | NULL | `price_usd − cost_usd` |
| `provider` | `provider_code` | NULL | |
| `provider_ref` | `VARCHAR(128)` | NULL | Fragment tx hash / boshqa ref |
| `idempotency_key` | `VARCHAR(64)` | UNIQUE (`user_id`, `idempotency_key`) | |
| `attempts` | `SMALLINT` | `0` | |
| `next_attempt_at` | `TIMESTAMPTZ` | NULL | |
| `locked_at` | `TIMESTAMPTZ` | NULL | `processing` boshlangan vaqt |
| `error_code`, `error_message` | `VARCHAR` | NULL | |
| `bot_message_id` | `BIGINT` | NULL | botdagi holat xabarini tahrirlash uchun |
| `meta` | `JSONB` | `{}` | |
| `created_at`, `paid_at`, `completed_at`, `updated_at` | `TIMESTAMPTZ` | | |

Indekslar: `(user_id, created_at DESC)`, `(status, next_attempt_at) WHERE status IN ('paid','processing','needs_review')`,
`(completed_at) WHERE status = 'completed'`, `(created_at)`.

#### `order_events`

`id`, `order_id FK`, `from_status`, `to_status`, `actor VARCHAR(32)` (`system`, `worker`, `admin:<id>`, `user`),
`data JSONB`, `created_at`. Indeks: `(order_id, created_at)`.

#### `payments`

| Ustun | Tur | Cheklov | Izoh |
|-------|-----|---------|------|
| `id` | `BIGINT IDENTITY` | PK | |
| `public_id` | `VARCHAR(16)` | UNIQUE | |
| `user_id` | `BIGINT` | FK | |
| `order_id` | `BIGINT` | FK, NULL | `topup` da NULL |
| `purpose` | `payment_purpose` | | |
| `method` | `payment_method` | | |
| `status` | `payment_status` | | |
| `amount` | `NUMERIC(30,9)` | `> 0` | kutilgan summa |
| `received_amount` | `NUMERIC(30,9)` | NULL | haqiqatda kelgan |
| `currency` | `VARCHAR(8)` | | `TON` / `XTR` / `USD` |
| `amount_usd` | `NUMERIC(18,6)` | | |
| `rate_used` | `NUMERIC(20,9)` | | invoice paytidagi kurs |
| `ton_comment` | `VARCHAR(32)` | UNIQUE (NULL emas bo'lsa) | `PM-7F3K9Q` |
| `ton_tx_hash` | `VARCHAR(64)` | UNIQUE | |
| `ton_sender` | `VARCHAR(68)` | | |
| `tg_charge_id` | `VARCHAR(128)` | UNIQUE | Stars `telegram_payment_charge_id` |
| `is_late` | `BOOLEAN` | `false` | |
| `expires_at`, `confirmed_at`, `created_at` | `TIMESTAMPTZ` | | |
| `raw` | `JSONB` | | xom tranzaksiya / update |

Indekslar: `(status, expires_at) WHERE status = 'pending'`, `(user_id, created_at DESC)`, `(confirmed_at)`.

#### `balance_transactions` (ichki balans ledger — faqat INSERT, UPDATE/DELETE yo'q)

`id`, `user_id FK`, `amount_usd NUMERIC(18,6)` (musbat — kirim, manfiy — chiqim), `balance_after NUMERIC(18,6)`,
`type balance_tx_type`, `ref_type VARCHAR(32)` (`order` / `payment` / `admin`), `ref_id BIGINT`,
`comment VARCHAR(255)`, `created_by BIGINT NULL`, `created_at`. Indeks: `(user_id, created_at DESC)`.

#### `hot_wallet_transactions` (hot wallet ledger)

`id`, `direction`, `kind`, `amount_ton NUMERIC(20,9)`, `fee_ton NUMERIC(20,9)`, `amount_usd`, `rate_used`,
`tx_hash VARCHAR(64) UNIQUE`, `counterparty VARCHAR(68)`, `order_id FK NULL`, `payment_id FK NULL`,
`created_by NULL`, `created_at`.

#### `stars_transactions` (bot Stars ledger)

`id`, `direction`, `kind`, `amount INTEGER`, `order_id FK NULL`, `payment_id FK NULL`, `tg_charge_id NULL`, `created_at`.

#### `unmatched_ton_txs`

Hech bir to'lovga mos kelmagan kiruvchi TON o'tkazmalari (izoh noto'g'ri/yo'q). Admin ularni panelda ko'radi va
qo'lda foydalanuvchiga biriktiradi (balansga) yoki "e'tiborsiz" deb belgilaydi. Ustunlar: `tx_hash UNIQUE`,
`amount_ton`, `comment`, `sender`, `resolution` (`pending` / `credited:<user_id>` / `ignored`), `resolved_by`, `created_at`.

#### `promo_codes`, `promo_redemptions`

`promo_codes.code` — `UNIQUE (upper(code))`. `promo_redemptions` — `UNIQUE (promo_id, order_id)`; foydalanuvchi
limiti `COUNT(*) WHERE promo_id AND user_id` bilan tekshiriladi (`SELECT ... FOR UPDATE` promo qatorida).

#### `referral_rewards`

`UNIQUE (order_id)` — bitta buyurtma uchun bitta bonus.

#### `expenses`

Qo'lda kiritiladigan xarajatlar (server, domen, reklama...). `amount_usd`, `category`, `note`, `spent_on DATE`, `created_by`.

#### `broadcasts`

`content JSONB` = `{ "type": "text|photo|video|copy", "text": "...", "media_file_id": "...", "buttons": [[{"text": "...", "url": "..."}]], "from_chat_id": ..., "message_id": ... }`;
`segment JSONB` = `{ "language": ["uz"], "has_orders": true, "registered_after": "2026-09-01", "only_active_days": 30 }`.

#### `channels`

Majburiy obuna kanallari: `chat_id UNIQUE`, `title`, `invite_link`, `is_active`, `sort_order`.

#### `settings`

Kalit-qiymat (JSONB). `is_secret = true` bo'lgan qiymatlar Fernet bilan shifrlanadi va API'da `***` bo'lib qaytadi.
Standart kalitlar:

| Kalit | Standart | Izoh |
|-------|----------|------|
| `payments.ton.enabled` | `true` | |
| `payments.stars.enabled` | `true` | |
| `payments.balance.enabled` | `true` | |
| `payments.topup.stars.enabled` | `true` | Stars bilan balans to'ldirish |
| `payments.invoice_ttl_minutes` | `20` | |
| `pricing.network_fee_ton` | `0.05` | |
| `pricing.min_margin_percent` | `2` | |
| `pricing.round_step_usd` | `0.05` | |
| `pricing.stars.markup_percent` | `7` | |
| `pricing.stars.max_amount` | `100000` | |
| `pricing.star_usd_rate` | `0.013` | Stars → USD (hisobot va 3.5-band uchun) |
| `pricing.topup.min_usd` / `max_usd` | `1` / `5000` | |
| `fulfillment.premium.priority` | `["fragment_direct","fragment_api","bot_stars"]` | |
| `fulfillment.stars_paid_strategy` | `"bot_stars"` | 3.5-band |
| `fulfillment.max_attempts` | `3` | |
| `fulfillment.auto_refund` | `true` | |
| `fragment.mode` | `"direct"` | |
| `fragment.cookies` | — (secret) | admin panel orqali |
| `hot_wallet.reserve_ton` | `30` | |
| `hot_wallet.low_balance_alert_ton` | `15` | |
| `hot_wallet.sweep_enabled` | `false` | |
| `hot_wallet.sweep_threshold_ton` | `100` | |
| `hot_wallet.daily_withdraw_limit_ton` | `1000` | |
| `referral.enabled` / `referral.percent` | `true` / `2` | |
| `bot.maintenance` | `false` | |
| `bot.support_username` | `""` | |
| `bot.welcome_text` | `{uz, ru, en}` | |
| `bot.mandatory_subscription` | `false` | |
| `notify.log_chat_id` | `.env` dan | |
| `notify.events` | `{order_paid: true, order_completed: true, order_failed: true, new_user: false}` | |
| `ton_watcher.last_lt` | `0` | kursor |

#### `audit_logs`

Har bir admin amali: `actor_id`, `action` (`price.update`, `user.ban`, `balance.adjust`, `wallet.withdraw`,
`order.refund`, `settings.update`, `admin.add`...), `entity`, `entity_id`, `before`, `after`, `source` (`bot` / `webapp` / `cli`).

#### `exchange_rates`, `user_daily_activity`, `daily_stats`

- `exchange_rates`: kurs tarixi (`pair` = `TON_USD`, `USD_UZS`), indeks `(pair, fetched_at DESC)`.
- `user_daily_activity`: `PK (day, user_id)` — foydalanuvchining kundagi birinchi harakatida
  `INSERT ... ON CONFLICT DO NOTHING` (DAU/WAU/MAU uchun).
- `daily_stats`: 13.3-bo'limga qarang.

### 9.5 Migratsiyalar va seed

1. `0001_initial` — barcha enumlar, jadvallar, indekslar, cheklovlar.
2. `0002_seed_reference` — `premium_plans` (1/3/6/12), `star_packages`, standart `settings`.
3. Har bir keyingi o'zgarish — alohida migratsiya; `downgrade()` majburiy yoziladi.
4. `python -m app.cli admin create-owner` — `OWNER_TELEGRAM_ID` ni `admins` ga `owner` sifatida qo'shadi (idempotent).

---

## 10. Backend API (barcha endpointlar)

### 10.1 Umumiy qoidalar

- Bazaviy yo'l: `/api/v1`. Format: JSON. Pul qiymatlari **string** sifatida (`"13.150000"`) — aniqlik yo'qolmasligi uchun.
- **Autentifikatsiya:** har bir so'rovda `Authorization: tma <initDataRaw>`; server HMAC'ni tekshiradi
  (stateless, sessiya/JWT shart emas). `auth_date` 24 soatdan eski bo'lsa → `401 INIT_DATA_EXPIRED` → Mini App
  foydalanuvchiga "Ilovani qayta oching" deydi.
- **Pagination:** `?limit=20&cursor=<opaque>` → `{ "items": [...], "next_cursor": "..." }`.
- **Idempotentlik:** pul bilan bog'liq POST'larda `Idempotency-Key: <uuid>` majburiy.
- **Rate limit:** foydalanuvchi bo'yicha 60 so'rov/daqiqa, buyurtma yaratish 10/daqiqa → `429 RATE_LIMITED`.
- **OpenAPI:** `/api/docs` faqat `APP_ENV=development` da ochiq.

`initData` tekshiruvi (Telegram rasmiy algoritmi):

```python
def validate_init_data(init_data: str, bot_token: str, max_age: int = 86_400) -> dict[str, str]:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InvalidInitData()
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise InvalidInitData()
    if time.time() - int(pairs["auth_date"]) > max_age:
        raise ExpiredInitData()
    return pairs
```

### 10.2 Foydalanuvchi API

| Metod | Yo'l | Tavsif | Javob (qisqa) |
|-------|------|--------|---------------|
| GET | `/me` | Profil, balans, til, rol, referal havolasi | `{id, name, username, language, balance_usd, balance_uzs, is_admin, role, ref_link}` |
| PATCH | `/me` | Tilni o'zgartirish | `{language}` |
| GET | `/catalog` | Tariflar + paketlar + barcha valyutalarda narxlar + yoqilgan to'lov usullari | `{plans[], star_packages[], stars_unit_price_usd, methods[], rates{}}` |
| POST | `/catalog/stars-quote` | O'z miqdori uchun narx (`{amount}`) | `Quote` |
| POST | `/recipients/resolve` | `{username, product}` → Fragment orqali tekshiruv | `{found, name, photo_url, can_receive, reason}` |
| POST | `/promo/validate` | `{code, product_type, plan_id?, stars_amount?}` | `{valid, discount_usd, final_price}` |
| POST | `/orders` | Buyurtma yaratish (pastda) | `{order, payment_instructions}` |
| GET | `/orders` | Mening buyurtmalarim (pagination, `status` filtri) | `Page<Order>` |
| GET | `/orders/{public_id}` | Bitta buyurtma + holat tarixi | `Order + events[]` |
| POST | `/orders/{public_id}/cancel` | Faqat `awaiting_payment` holatida | `Order` |
| POST | `/payments/{public_id}/ton/submitted` | TON Connect'dan BOC (tezroq aniqlash uchun, majburiy emas) | `{ok}` |
| POST | `/payments/{public_id}/stars-link` | Stars invoice havolasi (`openInvoice` uchun) | `{invoice_link}` |
| GET | `/payments/{public_id}` | To'lov holati | `Payment` |
| GET | `/wallet` | Balans + so'nggi harakatlar | `{balance_usd, balance_uzs, balance_ton_equiv}` |
| GET | `/wallet/transactions` | Ledger (pagination) | `Page<BalanceTx>` |
| POST | `/wallet/topup` | `{amount_usd, method: ton\|stars}` | `{payment, payment_instructions}` |
| GET | `/referral` | Havola, taklif qilinganlar soni, jami bonus, so'nggi bonuslar | `{link, invited, earned_usd, items[]}` |

**`POST /orders` so'rovi:**

```json
{
  "product_type": "premium",
  "plan_id": 3,
  "stars_amount": null,
  "recipient": { "type": "other", "username": "dostim" },
  "payment_method": "ton",
  "promo_code": "KUZ5"
}
```

**Javob (TON):**

```json
{
  "order": { "public_id": "PR-8F3K2Q", "status": "awaiting_payment", "price_usd": "31.500000", "price_uzs": 403000 },
  "payment_instructions": {
    "payment_id": "PM-7F3K9Q",
    "method": "ton",
    "address": "UQB...hot",
    "amount": "10.500000000",
    "amount_nano": "10500000000",
    "comment": "PM-7F3K9Q",
    "expires_at": "2026-10-01T10:20:00Z",
    "tonkeeper_link": "https://app.tonkeeper.com/transfer/UQB...?amount=10500000000&text=PM-7F3K9Q"
  }
}
```

Stars uchun `payment_instructions = { "method": "stars", "amount": 2750, "invoice_link": "https://t.me/$..." }`,
balans uchun — buyurtma darhol `paid` holatida qaytadi.

### 10.3 Admin API (`/api/v1/admin/*`, `require_role(...)`)

| Metod | Yo'l | Rol | Tavsif |
|-------|------|-----|--------|
| GET | `/admin/dashboard?period=today\|week\|month\|year` | admin+ | KPI'lar + oldingi davr bilan solishtirish + balanslar + alertlar |
| GET | `/admin/stats/timeseries?metric=&granularity=hour\|day\|week\|month&from=&to=` | admin+ | Grafik ma'lumotlari |
| GET | `/admin/stats/breakdown?by=product\|method\|language\|provider&from=&to=` | admin+ | Taqsimotlar (donut/bar) |
| GET | `/admin/stats/top-buyers?from=&to=&limit=` | admin+ | Top xaridorlar |
| GET | `/admin/stats/export.xlsx?from=&to=` | admin+ | Excel |
| GET | `/admin/orders?status=&product=&method=&q=&from=&to=` | support+ | Ro'yxat |
| GET | `/admin/orders/{public_id}` | support+ | Tafsilot + events + to'lovlar + provider javobi |
| POST | `/admin/orders/{public_id}/retry` | support+ | Qayta urinish |
| POST | `/admin/orders/{public_id}/refund` | admin+ | `{to: balance\|stars}` |
| POST | `/admin/orders/{public_id}/mark-completed` | admin+ | `{provider_ref, note}` |
| GET | `/admin/users?q=&banned=&has_orders=&sort=` | support+ | Ro'yxat/qidiruv |
| GET | `/admin/users/{id}` | support+ | Profil, statistikasi, buyurtmalari, ledger |
| POST | `/admin/users/{id}/ban` · `/unban` | admin+ | `{reason}` |
| POST | `/admin/users/{id}/balance` | admin+ | `{amount_usd (±), comment}` (owner bo'lmasa limit: ±50 $) |
| POST | `/admin/users/{id}/message` | support+ | `{text}` → bot orqali yuboriladi |
| GET/PUT | `/admin/pricing/plans` | admin+ | Tariflar sozlamalari + jonli tannarx ko'rinishi |
| GET/PUT | `/admin/pricing/star-packages` | admin+ | Paketlar |
| GET/PUT | `/admin/pricing/settings` | admin+ | Stars ustamasi, yaxlitlash, min foyda... |
| POST | `/admin/pricing/refresh` | admin+ | Fragment narxlarini hozir yangilash |
| GET | `/admin/finance/overview` | admin+ | Hot wallet, Stars balansi, rezerv, foydalanuvchi balanslari jami (majburiyat) |
| GET | `/admin/finance/hot-wallet/transactions` | admin+ | Hot wallet ledger |
| GET | `/admin/finance/stars/transactions` | admin+ | Stars ledger |
| POST | `/admin/finance/withdraw` | **owner** | `{amount_ton}` → faqat `ADMIN_TON_ADDRESS` ga |
| GET/PUT | `/admin/finance/sweep` | **owner** | Avto-sweep sozlamalari |
| GET | `/admin/finance/unmatched` | admin+ | Mos kelmagan TON o'tkazmalari |
| POST | `/admin/finance/unmatched/{id}/resolve` | admin+ | `{user_id}` yoki `{ignore: true}` |
| GET/POST/DELETE | `/admin/expenses` | admin+ | Xarajatlar |
| GET/POST | `/admin/broadcasts` | admin+ | Ro'yxat / yaratish |
| POST | `/admin/broadcasts/{id}/preview` | admin+ | O'ziga test yuborish |
| POST | `/admin/broadcasts/{id}/start` · `/pause` · `/cancel` | admin+ | Boshqarish |
| GET | `/admin/broadcasts/{id}` | admin+ | Progress |
| GET/POST/PATCH/DELETE | `/admin/promo-codes` | admin+ | Promokodlar |
| GET/PUT | `/admin/settings` | admin+ | Umumiy sozlamalar (secret'lar `***`) |
| PUT | `/admin/settings/fragment-cookies` | **owner** | Fragment cookie yangilash (shifrlanadi) |
| GET/PUT | `/admin/payment-methods` | admin+ | To'lov usullarini yoqish/o'chirish |
| GET/POST/DELETE | `/admin/channels` | admin+ | Majburiy obuna |
| GET/POST/DELETE | `/admin/admins` | **owner** | Adminlar va rollar |
| GET | `/admin/audit-logs?actor=&action=&from=&to=` | admin+ | Audit |
| GET | `/admin/health` | admin+ | DB, Redis, worker heartbeat, TonAPI, Fragment, bot webhook holati |

### 10.4 Webhook va xizmat endpointlari

| Metod | Yo'l | Tavsif |
|-------|------|--------|
| POST | `/tg/webhook` | Telegram update'lari. `X-Telegram-Bot-Api-Secret-Token` == `WEBHOOK_SECRET` bo'lmasa `401`. `allowed_updates`: `message`, `callback_query`, `pre_checkout_query`, `my_chat_member`, `chat_member` (majburiy obuna uchun ixtiyoriy) |
| GET | `/api/health` | Ochiq: `{status: ok}` (UptimeRobot uchun) |

### 10.5 Xato kodlari

| HTTP | Kod | Qachon |
|------|-----|--------|
| 400 | `VALIDATION_ERROR` | Noto'g'ri ma'lumot |
| 401 | `INIT_DATA_INVALID` / `INIT_DATA_EXPIRED` | Autentifikatsiya |
| 403 | `FORBIDDEN` / `USER_BANNED` | Ruxsat yo'q |
| 404 | `NOT_FOUND` | |
| 409 | `INVALID_STATE` / `PRICE_CHANGED` / `DUPLICATE` | Holat mos emas, narx o'zgardi |
| 422 | `RECIPIENT_NOT_FOUND` / `RECIPIENT_CANNOT_RECEIVE` / `INSUFFICIENT_BALANCE` / `PROMO_INVALID` / `METHOD_DISABLED` / `PLAN_UNAVAILABLE` | Biznes qoidalar |
| 429 | `RATE_LIMITED` | |
| 503 | `MAINTENANCE` / `PROVIDER_UNAVAILABLE` | |

---

## 11. Telegram bot: buyruqlar, ekranlar, tugmalar va ranglar

### 11.1 UX tamoyillari (BotFather uslubi)

1. **Bitta xabar — bitta ekran.** Tugma bosilganda yangi xabar yuborilmaydi, mavjud xabar **tahrirlanadi**
   (`editMessageText` / `editMessageReplyMarkup`) — xuddi BotFather'dagidek. Chat toza qoladi.
2. **Har ekranda yo'l ko'rsatkichi** (breadcrumb) sarlavhada: `💎 Premium › Kimga › Muddat › To'lov`.
3. **« Orqaga** har doim oxirgi qatorda, chap tomonda; **✖️ Bekor qilish** — o'ng tomonda (qizil).
4. **Bitta ekranda bitta asosiy harakat** (yashil tugma). Ikkinchi darajali harakatlar — standart rangda.
5. **Xavfli amal = tasdiqlash ekrani** (pul yechish, refund, ban, o'chirish).
6. **Tezkor javob:** har bir `callback_query` ga 1 soniya ichida `answerCallbackQuery` (kerak bo'lsa toast matni bilan).
7. **Narxlar har doim 2 valyutada:** asosiy ($ / TON / ⭐) + taxminiy so'm.
8. **Matnlar qisqa**, emoji bilan bo'limlarga ajratilgan, HTML formatlash (`<b>`, `<code>` — nusxalash uchun).
9. Foydalanuvchi matn yozib qo'ysa (FSM'da bo'lmasa) → "Menyudan foydalaning 👇" + bosh menyu.
10. `/start` har doim bosh menyuni **yangi xabar** sifatida yuboradi (yo'qolib qolgan foydalanuvchi uchun).

### 11.2 Tugma ranglari tizimi

| Belgi | `style` | Rang | Qachon ishlatiladi | Misollar |
|-------|---------|------|--------------------|----------|
| 🟩 | `success` | Yashil | **Pul bilan bog'liq asosiy harakat / tasdiqlash** | "💎 Premium sotib olish", "✅ To'lash", "➕ Balansni to'ldirish", "✅ Saqlash", "🚀 Yuborish" |
| 🟦 | `primary` | Ko'k | **Ilovani ochish, tavsiya etilgan variant, muhim navigatsiya** | "🚀 Ilovani ochish", "🔥 12 oy", "🔄 To'lovni tekshirish", "🛠 Admin panel", tanlangan davr |
| 🟥 | `danger` | Qizil | **Bekor qilish, qaytarib bo'lmaydigan / xavfli amal** | "✖️ Bekor qilish", "⛔️ Bloklash", "↩️ Pulni qaytarish", "🗑 O'chirish", "➖ Balans ayirish" |
| ⬜ | — | Standart | Ikkinchi darajali harakatlar, navigatsiya | "« Orqaga", "📦 Buyurtmalarim", "📋 Nusxalash", "🆘 Yordam" |

**Yoqish/o'chirish (toggle) tugmalari:** holat yoqilgan → `✅ … ` + 🟩; o'chirilgan → `⛔️ …` + ⬜.

Kodda rangli tugma yaratish uchun yagona yordamchi:

```python
Style = Literal["primary", "success", "danger"]

def btn(text: str, *, cb: CallbackData | str | None = None, url: str | None = None,
        web_app: str | None = None, copy: str | None = None, pay: bool = False,
        style: Style | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=cb.pack() if isinstance(cb, CallbackData) else cb,
        url=url,
        web_app=WebAppInfo(url=web_app) if web_app else None,
        copy_text=CopyTextButton(text=copy) if copy else None,
        pay=pay or None,
        style=style,
    )
```

### 11.3 BotFather sozlamalari (bir martalik)

| Sozlama | Qiymat |
|---------|--------|
| `/newbot` | Nom: "Premium Market" (taklif), username: `PremiumMarketUzBot` (bo'sh bo'lsa) |
| `/setdescription` | "💎 Telegram Premium va ⭐ Stars — eng arzon narxda. 1–3 daqiqada faollashadi." (uz/ru/en — API orqali ham o'rnatiladi) |
| `/setabouttext` | "Premium va Stars eng arzon narxda · TON · Stars · 24/7" |
| `/setuserpic` | Logo (premium gradient + yulduz) |
| `/setjoingroups` | **Disable** (bot faqat shaxsiy chatda) |
| `/setprivacy` | Enable (standart) |
| Bot Settings → Configure Mini App | Enable; Main App URL = `https://<domen>/` |
| `/newapp` | Short name `app` → `https://t.me/<bot>/app` (deep link uchun) |
| Menu Button | API orqali: `setChatMenuButton(type=web_app, text="🚀 Ilova", url=WEBAPP_URL)` |
| Payments | Stars uchun provider kerak emas (`currency="XTR"`) |
| Commands | API orqali `setMyCommands` (11.4, har til va scope uchun) |

### 11.4 Buyruqlar

**Foydalanuvchi buyruqlari** (`BotCommandScopeDefault`, uz/ru/en tarjimalari bilan):

| Buyruq | Tavsif (uz) | Harakat |
|--------|-------------|---------|
| `/start` | Botni ishga tushirish | Til (birinchi marta) → bosh menyu; parametrlar: 11.5 |
| `/premium` | 💎 Premium sotib olish | Premium oqimi (U3) |
| `/stars` | ⭐ Stars sotib olish | Stars oqimi (U9) |
| `/wallet` | 💼 Hamyon va balans | U11 |
| `/orders` | 📦 Buyurtmalarim | U14 |
| `/referral` | 👥 Do'stlarni taklif qilish | U15 |
| `/app` | 🚀 Mini ilovani ochish | Web App tugmali xabar |
| `/lang` | 🌐 Tilni o'zgartirish | U1 |
| `/help` | 🆘 Yordam | U17 |
| `/cancel` | ✖️ Joriy amalni bekor qilish | FSM tozalanadi → bosh menyu |

**Admin buyruqlari** (`BotCommandScopeChat(chat_id=<admin>)` — faqat adminlarda ko'rinadi, foydalanuvchi buyruqlari ham qo'shiladi):

| Buyruq | Rol | Tavsif |
|--------|-----|--------|
| `/admin` | support+ | 🛠 Admin panel (A1) |
| `/stats [today\|week\|month\|year]` | admin+ | 📊 Tezkor statistika |
| `/order <PR-XXXXXX>` | support+ | 🧾 Buyurtmani ochish |
| `/find <id\|@username>` | support+ | 🔍 Foydalanuvchini topish |
| `/addbalance <id> <usd> [izoh]` | admin+ | ➕ Balans qo'shish (tasdiqlash bilan) |
| `/subbalance <id> <usd> [izoh]` | admin+ | ➖ Balans ayirish (tasdiqlash bilan) |
| `/ban <id> [sabab]` · `/unban <id>` | admin+ | ⛔️ Bloklash / ✅ blokdan chiqarish |
| `/broadcast` | admin+ | 📣 Xabar yuborish ustasi |
| `/prices` | admin+ | 🏷 Narxlar |
| `/finance` | admin+ | 💰 Moliya |
| `/withdraw <ton>` | **owner** | 💸 Telegram Wallet'ga yechish (tasdiqlash bilan) |
| `/maintenance on\|off` | admin+ | 🛠 Texnik ishlar rejimi |
| `/health` | admin+ | 🩺 Tizim holati |

### 11.5 Deep linklar

| Havola | Natija |
|--------|--------|
| `t.me/<bot>?start=ref_123456` | Referrer biriktiriladi (faqat yangi foydalanuvchi uchun) |
| `t.me/<bot>?start=src_instagram` | Reklama manbasi `users.source` ga yoziladi (statistikada ko'rinadi) |
| `t.me/<bot>?start=premium` / `stars` / `wallet` | To'g'ridan-to'g'ri bo'limga |
| `t.me/<bot>?start=order_PR-8F3K2Q` | Buyurtma kartasi |
| `t.me/<bot>/app?startapp=premium` | Mini App → `/premium` |
| `t.me/<bot>/app?startapp=admin` | Mini App → `/admin` (faqat admin) |
| `t.me/<bot>/app?startapp=ref_123456` | Mini App orqali referal |

### 11.6 Foydalanuvchi ekranlari

> Belgilar: 🟩 success · 🟦 primary · 🟥 danger · ⬜ standart. "cb" = callback tugma, "web_app" = Mini App ochadi,
> "copy" = nusxalash tugmasi, "url" = havola.

#### U1. Til tanlash (birinchi `/start`)

```text
🌐 Tilni tanlang · Выберите язык · Choose language
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `🇺🇿 O'zbekcha` 🟦 (Telegram tili uz bo'lsa) · `🇷🇺 Русский` ⬜ · `🇬🇧 English` ⬜ |

#### U2. Bosh menyu

```text
Assalomu alaykum, Jasur! 👋

💎 Telegram Premium va ⭐ Stars — eng arzon narxda.

⚡️ 1–3 daqiqada faollashadi
🔒 Rasmiy Telegram sovg'a tizimi orqali
💳 TON, Stars yoki balans bilan to'lov

💼 Balansingiz: 12.50 $ (≈ 160 000 so'm)
```

| Qator | Tugma | Rang | Harakat |
|-------|-------|------|---------|
| 1 | 🚀 Ilovani ochish | 🟦 | web_app `/` |
| 2 | 💎 Premium sotib olish | 🟩 | cb `m:premium` |
| 3 | ⭐ Stars sotib olish | 🟩 | cb `m:stars` |
| 4 | 💼 Hamyon · 12.50 $ ⬜ · 📦 Buyurtmalarim ⬜ | ⬜ | cb `m:wallet`, `m:orders` |
| 5 | 👥 Do'stlarni taklif qilish ⬜ · ⚙️ Sozlamalar ⬜ | ⬜ | cb `m:ref`, `m:settings` |
| 6 | 🆘 Yordam | ⬜ | cb `m:help` |
| 7 | 🛠 Admin panel *(faqat adminlarga)* | 🟦 | cb `a:panel` |

Chat pastidagi **Menu tugmasi**: `🚀 Ilova` (Mini App).

#### U3. Premium — kimga?

```text
💎 Premium › Kimga

Premium kimga kerak?
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `🙋 O'zimga (@jasur)` 🟦 · `🎁 Boshqa odamga` ⬜ |
| 2 | `« Orqaga` ⬜ |

Username'i yo'q foydalanuvchi "O'zimga" ni bossa: faqat ⭐ Stars to'lov usuli taklif qilinadi (B usul, `user_id` orqali)
yoki "Username o'rnatish: Sozlamalar → Username" yo'riqnomasi ko'rsatiladi.

#### U4. Qabul qiluvchini kiritish (FSM: `PremiumFlow.recipient`)

```text
💎 Premium › Kimga › Username

🎁 Qabul qiluvchining username'ini yuboring
Masalan: @durov yoki durov

Yoki pastdagi "👤 Kontaktdan tanlash" tugmasini bosing.
```

Inline: `✖️ Bekor qilish` 🟥.
Reply klaviatura (vaqtincha): `👤 Kontaktdan tanlash` 🟦 — `KeyboardButtonRequestUsers(request_username=True, request_name=True)`
(Telegram foydalanuvchiga o'z kontaktlaridan tanlash oynasini ochadi va bot `user_id` + `username` oladi).

Tekshiruvdan keyin:

```text
✅ Topildi: Ali Valiyev (@ali_v)

Shu foydalanuvchiga Premium sovg'a qilinsinmi?
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `✅ Ha, davom etish` 🟩 |
| 2 | `✏️ Boshqa username` ⬜ · `✖️ Bekor qilish` 🟥 |

Xatolar: "❌ @xyz topilmadi", "❌ Bu foydalanuvchi hozir Premium sovg'a qabul qila olmaydi", "❌ Username noto'g'ri
(5–32 belgi, a–z, 0–9, _)".

#### U5. Muddat tanlash

```text
💎 Premium › Muddat
👤 Qabul qiluvchi: @ali_v

▫️ 3 oy  — 13.15 $  (≈ 168 000 so'm)
▫️ 6 oy  — 17.45 $  (≈ 223 000 so'm) · −27%
▫️ 12 oy — 31.50 $  (≈ 403 000 so'm) · 🔥 eng foydali

💡 Telegram ichidagi narxdan 25% gacha arzon
```

| Qator | Tugma | Rang |
|-------|-------|------|
| 1 | 3 oy · 13.15 $ | ⬜ |
| 2 | 6 oy · 17.45 $ | ⬜ |
| 3 | 🔥 12 oy · 31.50 $ | 🟦 |
| 4 | 1 oy · tez kunda *(agar ko'rsatish tanlansa; bosilsa toast: "Telegram 1 oylik sovg'ani hali qo'llamaydi")* | ⬜ |
| 5 | « Orqaga ⬜ · ✖️ Bekor qilish 🟥 | |

#### U6. To'lov usuli (buyurtma xulosasi)

```text
🧾 Buyurtma
━━━━━━━━━━━━━━━━
💎 Telegram Premium · 12 oy
👤 Kimga: @ali_v (Ali Valiyev)
💵 Narx: 31.50 $ ≈ 403 000 so'm
━━━━━━━━━━━━━━━━
To'lov usulini tanlang:
```

| Qator | Tugma | Rang | Izoh |
|-------|-------|------|------|
| 1 | 💎 TON · 10.50 TON | ⬜ | yoqilgan bo'lsa |
| 2 | ⭐ Stars · 2 750 ⭐ | ⬜ | yoqilgan bo'lsa |
| 3 | 💼 Balansdan · 31.50 $ | ⬜ | yetmasa: "💼 Balans (yetarli emas)" → toast + to'ldirish taklifi |
| 4 | 🎟 Promokod kiritish | ⬜ | FSM `PromoFlow.code` |
| 5 | « Orqaga ⬜ · ✖️ Bekor qilish 🟥 | | |

#### U7a. TON to'lov ekrani

```text
💎 TON orqali to'lov
━━━━━━━━━━━━━━━━
Summa:   10.50 TON
Manzil:  UQB2...full_address
Izoh:    PM-7F3K9Q   ← MAJBURIY
⏳ 14:20 gacha to'lang (20 daqiqa)
━━━━━━━━━━━━━━━━
❗️ Izohni (comment) yozmasangiz to'lov avtomatik aniqlanmaydi.
💡 Eng oson yo'l — "Hamyon orqali to'lash" tugmasi.
```

| Qator | Tugma | Rang | Harakat |
|-------|-------|------|---------|
| 1 | 💎 Hamyon orqali to'lash | 🟩 | web_app `/checkout/PR-8F3K2Q` (TON Connect: Telegram Wallet, Tonkeeper…) |
| 2 | 📋 Manzil · 📋 Izoh · 📋 Summa | ⬜ | copy (har biri alohida) |
| 3 | Tonkeeper'da ochish | ⬜ | url `https://app.tonkeeper.com/transfer/...` |
| 4 | 🔄 To'lovni tekshirish | 🟦 | cb → `ton_watcher` ni darhol ishga tushiradi |
| 5 | ✖️ Buyurtmani bekor qilish | 🟥 | cb → tasdiqlash |

> Inline tugmalarda `ton://` havolasi ishlamaydi (faqat `https://` va `tg://`), shuning uchun asosiy yo'l — Mini App'dagi
> TON Connect, zaxira — Tonkeeper universal havolasi va qo'lda nusxalash.

#### U7b. Stars to'lov

`sendInvoice`: sarlavha "Telegram Premium · 12 oy", tavsif "Qabul qiluvchi: @ali_v", `currency="XTR"`, narx 2750.

| Qator | Tugma | Rang |
|-------|-------|------|
| 1 | ⭐ 2 750 to'lash (`pay=True`, birinchi tugma bo'lishi shart) | 🟩 |
| 2 | ✖️ Bekor qilish | 🟥 |

#### U7c. Balansdan to'lash

```text
💼 Balansdan to'lov
Narx: 31.50 $
Balans: 45.00 $ → to'lovdan keyin 13.50 $
```

| Qator | Tugma |
|-------|-------|
| 1 | `✅ To'lash · 31.50 $` 🟩 |
| 2 | `« Orqaga` ⬜ · `✖️ Bekor qilish` 🟥 |

#### U8. Buyurtma holati (bitta xabar, holat o'zgarganda tahrirlanadi)

```text
🧾 Buyurtma PR-8F3K2Q
💎 Premium 12 oy → @ali_v

✅ To'lov qabul qilindi
⏳ Premium faollashtirilmoqda...
```

Muvaffaqiyat:

```text
🎉 Tayyor! @ali_v ga Telegram Premium 12 oyga faollashtirildi.

🧾 Buyurtma: PR-8F3K2Q
💵 To'landi: 10.50 TON
🕐 Vaqt: 1 daq 42 s

Do'stlaringizni taklif qiling va har xariddan 2% bonus oling 👇
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `💎 Yana sotib olish` 🟩 · `👥 Taklif qilish` ⬜ |
| 2 | `🏠 Bosh menyu` ⬜ |

Xato:

```text
❌ Buyurtma bajarilmadi
Sabab: qabul qiluvchi Premium qabul qila olmaydi
↩️ 31.50 $ balansingizga qaytarildi.
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `🔄 Qayta urinish` 🟦 · `🆘 Yordam` ⬜ |

#### U9–U10. Stars sotib olish

U9 — "Kimga?" (U3 bilan bir xil). U10 — paket:

```text
⭐ Stars › Paket
👤 Kimga: @jasur

Paketni tanlang (1 ⭐ ≈ 0.016 $):
```

| Qator | Tugmalar (2 ustunli grid) |
|-------|---------------------------|
| 1 | `⭐ 50 · 0.81 $` ⬜ · `⭐ 100 · 1.61 $` ⬜ |
| 2 | `⭐ 250 · 4.02 $` ⬜ · `🔥 ⭐ 500 · 8.03 $` 🟦 |
| 3 | `⭐ 1 000 · 16.05 $` ⬜ · `⭐ 2 500 · 40.13 $` ⬜ |
| 4 | `⭐ 5 000 · 80.25 $` ⬜ · `⭐ 10 000 · 160.50 $` ⬜ |
| 5 | `✏️ O'z miqdorim` ⬜ (FSM `StarsFlow.amount`, 50 dan katta butun son) |
| 6 | `« Orqaga` ⬜ · `✖️ Bekor qilish` 🟥 |

Keyin U6 (faqat TON va Balans usullari) → U7a/U7c → U8.

#### U11. Hamyon

```text
💼 Hamyon
━━━━━━━━━━━━━━━━
Balans: 12.50 $
≈ 160 000 so'm · ≈ 4.17 TON
━━━━━━━━━━━━━━━━
Balans bilan xarid — bir bosishda to'lov ⚡️
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `➕ Balansni to'ldirish` 🟩 |
| 2 | `📜 Tarix` ⬜ · `🚀 Ilovada ochish` 🟦 (web_app `/wallet`) |
| 3 | `« Orqaga` ⬜ |

#### U12. Balansni to'ldirish

1-qadam — usul: `💎 TON` ⬜ · `⭐ Stars` ⬜ (yoqilgan bo'lsa); `« Orqaga`.
2-qadam — summa: `5 $` · `10 $` · `25 $` · `50 $` · `100 $` (⬜, 3+2 grid) · `✏️ Boshqa summa` ⬜ · `« Orqaga`.
3-qadam — TON bo'lsa U7a ko'rinishi (izoh `TP-…`), Stars bo'lsa invoice (`10 $ ≈ 770 ⭐`).

#### U13. Balans tarixi

```text
📜 Balans tarixi (1/3)

+10.00 $ · To'ldirish (TON) · 01.10 14:22
−31.50 $ · Premium 12 oy · 30.09 18:05
+0.63 $ · Referal bonus · 29.09 11:40
```

Tugmalar: `◀️` ⬜ · `1/3` ⬜ · `▶️` ⬜ / `« Orqaga` ⬜.

#### U14. Buyurtmalarim

Ro'yxat (har biri tugma): `✅ PR-8F3K2Q · 💎 12 oy · @ali_v` / `⏳ ST-2K9D1A · ⭐ 500 · o'zimga` / `❌ …`;
sahifalash; `« Orqaga`. Tafsilot ekranida: to'liq ma'lumot + holat tarixi + `🔁 Takrorlash` 🟩 · `🆘 Muammo bormi?` ⬜.

Holat belgilari: ⏳ to'lov kutilmoqda · 💳 to'landi · ⚙️ bajarilmoqda · ✅ bajarildi · ❌ xato · 🔍 tekshirilmoqda ·
↩️ qaytarildi · ⌛️ muddati o'tdi · 🚫 bekor qilindi.

#### U15. Referal

```text
👥 Do'stlarni taklif qiling

Har bir do'stingizning xaridlaridan 2% bonus balansingizga tushadi.

🔗 Havolangiz:
https://t.me/PremiumMarketUzBot?start=ref_123456

👤 Taklif qilinganlar: 14
💰 Jami bonus: 3.42 $
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `📤 Do'stlarga ulashish` 🟩 (url `https://t.me/share/url?url=…&text=…`) |
| 2 | `📋 Havolani nusxalash` ⬜ (copy) |
| 3 | `« Orqaga` ⬜ |

#### U16. Sozlamalar

`🌐 Til: O'zbekcha` ⬜ → U1 · `🔔 Aksiya xabarlari: ✅` ⬜ (broadcast'dan chiqish) · `« Orqaga`.

#### U17. Yordam

```text
🆘 Yordam

❓ Ko'p so'raladigan savollar
• Premium qancha vaqtda faollashadi? — Odatda 1–3 daqiqa.
• Username'im yo'q, nima qilaman? — Telegram → Sozlamalar → Username.
• To'ladim, lekin "kutilmoqda" turibdi? — "🔄 To'lovni tekshirish" ni bosing; izoh yozilmagan bo'lsa supportga yozing.
• 1 oylik Premium bormi? — Telegram hozircha faqat 3, 6, 12 oylik sovg'aga ruxsat beradi.
• Pulim qaytadimi? — Buyurtma bajarilmasa, pul avtomatik balansingizga qaytariladi.
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `💬 Support bilan bog'lanish` 🟦 (url `t.me/<support>`) |
| 2 | `📄 Foydalanish shartlari` ⬜ (web_app `/terms`) |
| 3 | `« Orqaga` ⬜ |

#### U18–U20. Tizim ekranlari

- **Majburiy obuna:** "📢 Botdan foydalanish uchun kanalga obuna bo'ling" → `➕ <Kanal nomi>` 🟦 (url) har kanal uchun ·
  `✅ Obuna bo'ldim` 🟩 (tekshiradi).
- **Texnik ishlar:** "🛠 Botda texnik ishlar olib borilmoqda. Tez orada qaytamiz!" (adminlar uchun ishlamaydi).
- **Ban:** "⛔️ Sizning hisobingiz bloklangan. Savollar bo'lsa: @support".

### 11.7 Admin ekranlari (bot ichida)

#### A1. Admin panel

```text
🛠 Admin panel

📊 Bugun (01.10.2026)
💵 Kirim: 1 240.50 $ · Chiqim: 1 102.30 $
📈 Foyda: 138.20 $ (▲ 12%)
📦 Buyurtmalar: 37 (✅ 35 · ⏳ 1 · ❌ 1)
👥 Yangi: +52 · Faol: 418

💎 Hot wallet: 125.40 TON (rezerv 30)
⭐ Stars balans: 8 450
⚠️ Tekshirish kerak: 1 ta buyurtma
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `🚀 Admin Mini App` 🟦 (web_app `/admin`) |
| 2 | `📊 Statistika` ⬜ · `📦 Buyurtmalar (⚠️1)` ⬜ |
| 3 | `👥 Foydalanuvchilar` ⬜ · `💰 Moliya` ⬜ |
| 4 | `🏷 Narxlar` ⬜ · `💳 To'lov usullari` ⬜ |
| 5 | `📣 Xabar yuborish` ⬜ · `🎟 Promokodlar` ⬜ |
| 6 | `🤝 Referal` ⬜ · `📢 Majburiy obuna` ⬜ |
| 7 | `⚙️ Sozlamalar` ⬜ · `👮 Adminlar` ⬜ *(owner)* |
| 8 | `🔄 Yangilash` ⬜ · `« Bosh menyu` ⬜ |

Rolga qarab ko'rinmaydigan tugmalar umuman chiqmaydi (support faqat Buyurtmalar va Foydalanuvchilarni ko'radi).

#### A2. Statistika

| Qator | Tugmalar |
|-------|----------|
| 1 | `Bugun` · `Kecha` · `Hafta` · `Oy` · `Yil` (tanlangani 🟦, qolgani ⬜) |
| 2 | `📅 Ixtiyoriy davr` ⬜ · `⚖️ Oldingi davr bilan` ⬜ |

```text
📊 Statistika · Shu oy (01.10 – 31.10)
━━━━━━━━━━━━━━━━
💵 MOLIYA
Tushum (cash-in):   12 430.00 $  ▲ 18%
Sotuv:              11 980.00 $
Tannarx:            10 870.00 $
Yalpi foyda:         1 110.00 $  ▲ 22%
Xarajatlar:            120.00 $
Sof foyda:             990.00 $
━━━━━━━━━━━━━━━━
📦 BUYURTMALAR: 812 (✅ 798 · ❌ 9 · ↩️ 5)
💎 Premium: 3 oy 210 · 6 oy 95 · 12 oy 180
⭐ Stars: 327 ta · 412 500 ⭐
💳 To'lov: TON 61% · Stars 24% · Balans 15%
O'rtacha chek: 14.75 $ · O'rtacha yetkazish: 1m 38s
━━━━━━━━━━━━━━━━
👥 FOYDALANUVCHILAR
Jami: 24 310 · Yangi: 3 140 (▲ 9%)
Faol (MAU): 9 870 · Xarid qilgan: 702
Konversiya: 22.4% · Botni bloklagan: 1 205
```

| Qator | Tugmalar |
|-------|----------|
| 3 | `📈 Grafiklar` 🟦 (web_app `/admin/stats?period=month`) |
| 4 | `📥 Excel yuklab olish` ⬜ · `🏆 Top xaridorlar` ⬜ |
| 5 | `« Orqaga` ⬜ |

#### A3. Buyurtmalar

Filtrlar: `⏳ Kutilmoqda` · `⚙️ Jarayonda` · `🔍 Tekshirish (1)` · `❌ Xato` · `✅ Bajarilgan` · `🔎 Qidirish` (public_id / username).
Ro'yxat 10 tadan, har biri tugma: `🔍 PR-8F3K2Q · 💎12 · @ali_v · 31.50$`.

Buyurtma kartasi:

```text
🧾 PR-8F3K2Q · 🔍 needs_review
👤 Xaridor: Jasur (@jasur · 123456789)
💎 Premium 12 oy → @ali_v
💵 31.50 $ · 10.50 TON · to'landi 14:02
🔧 Provider: fragment_direct · urinish 1/3
❗️ Xato: javob kelmadi (tx yuborilgan)
📜 awaiting_payment → paid → processing → needs_review
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `✅ Bajarildi deb belgilash` 🟩 · `🔄 Qayta urinish` 🟦 |
| 2 | `↩️ Pulni qaytarish` 🟥 |
| 3 | `👤 Xaridor` ⬜ · `🔗 Tonviewer` ⬜ (url) |
| 4 | `« Orqaga` ⬜ |

Har bir amal → tasdiqlash: "↩️ 31.50 $ @jasur balansiga qaytarilsinmi?" `✅ Ha, qaytarish` 🟥 · `Yo'q` ⬜.

#### A4. Foydalanuvchilar

"🔍 ID, @username yoki ism yuboring" + `🆕 Yangilar` · `💰 Top xaridorlar` · `⛔️ Bloklanganlar` · `« Orqaga`.

```text
👤 Jasur Aliyev (@jasur)
🆔 123456789 · 🇺🇿 uz · TG Premium: yo'q
📅 Ro'yxat: 12.08.2026 · Oxirgi faollik: bugun 14:05
💼 Balans: 12.50 $
📦 Buyurtmalar: 7 · Jami xarid: 98.40 $
👥 Taklif qilganlari: 3 · Uni taklif qilgan: @ali
Manba: src_instagram · Holat: ✅ Faol
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `➕ Balans qo'shish` 🟩 · `➖ Balans ayirish` 🟥 |
| 2 | `✉️ Xabar yozish` 🟦 · `📦 Buyurtmalari` ⬜ |
| 3 | `⛔️ Bloklash` 🟥 *(yoki `✅ Blokdan chiqarish` 🟩)* |
| 4 | `📜 Balans tarixi` ⬜ · `« Orqaga` ⬜ |

#### A5. Moliya

```text
💰 Moliya
━━━━━━━━━━━━━━━━
💎 Hot wallet: 125.40 TON (≈ 376.20 $)
   Rezerv: 30 TON · Yechish mumkin: 95.40 TON
⭐ Bot Stars: 8 450 ⭐ (≈ 109.85 $)
   21 kundan oshgani: ≈ 5 100 ⭐
💼 Foydalanuvchi balanslari (majburiyat): 1 240.00 $
━━━━━━━━━━━━━━━━
🏦 Admin hamyon: UQ...x9F
🔁 Avto-o'tkazish: o'chiq
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `💸 Telegram Wallet'ga yechish` 🟩 *(owner)* |
| 2 | `🔁 Avto-o'tkazish` ⬜ · `🧾 Xarajatlar` ⬜ |
| 3 | `📜 Hot wallet tarixi` ⬜ · `❓ Mos kelmagan to'lovlar (2)` ⬜ |
| 4 | `⭐ Stars'ni qanday yechish?` ⬜ (yo'riqnoma: BotFather → Bot → Balance → Withdraw → Fragment) |
| 5 | `« Orqaga` ⬜ |

Yechish oqimi: 7.4.7. Xarajat qo'shish: summa → kategoriya (tugmalar) → izoh → `✅ Saqlash` 🟩.

#### A6. Narxlar

```text
🏷 Narxlar (1 TON = 3.00 $ · 1 $ = 12 800 so'm)
━━━━━━━━━━━━━━━━
💎 3 oy   ✅ tannarx 12.15 $ → 13.15 $ (+8%) · 1 100 ⭐
💎 6 oy   ✅ tannarx 16.14 $ → 17.45 $ (+8%) · 1 650 ⭐
💎 12 oy  ✅ tannarx 29.13 $ → 31.50 $ (+8%) · 2 750 ⭐
💎 1 oy   ⛔️ provider qo'llamaydi
⭐ Stars: 1 ⭐ = 0.0150 $ → 0.01605 $ (+7%)
🔄 Yangilangan: 2 daqiqa oldin
```

| Qator | Tugmalar |
|-------|----------|
| 1 | `💎 3 oy` · `💎 6 oy` · `💎 12 oy` · `💎 1 oy` (⬜) |
| 2 | `⭐ Stars ustamasi` ⬜ · `📦 Stars paketlari` ⬜ |
| 3 | `⚙️ Umumiy (yaxlitlash, min foyda, fee)` ⬜ |
| 4 | `🔄 Fragment narxini yangilash` 🟦 |
| 5 | `« Orqaga` ⬜ |

Tarif tahrirlash ekrani: `✏️ Ustama %` · `✏️ Qat'iy narx` · `✏️ Stars narxi` · `✏️ Belgi` · `✏️ Telegram narxi (solishtirish)` ·
`⛔️ O'chirish` 🟥 / `✅ Yoqish` 🟩 · `« Orqaga`. Har bir o'zgartirishdan oldin oldindan ko'rish:
"Yangi narx: 13.40 $ (foyda 1.25 $, 10.3%). Saqlaymizmi?" `✅ Saqlash` 🟩 · `✖️ Bekor` 🟥.

#### A7. To'lov usullari

```text
💳 To'lov usullari
💎 TON — ✅ yoqilgan
⭐ Stars — ✅ yoqilgan
💼 Balans — ✅ yoqilgan
➕ Stars bilan balans to'ldirish — ✅
💵 USDT (TON) — 🔜 keyingi versiya
⏱ Invoice muddati: 20 daqiqa
```

Toggle tugmalar: `✅ TON` 🟩 / `⛔️ TON` ⬜ va h.k. · `⏱ Muddatni o'zgartirish` ⬜ · `« Orqaga`.

#### A8. Xabar yuborish ustasi

| Qadam | Ekran | Tugmalar |
|-------|-------|----------|
| 1 | "📣 Xabarni yuboring (matn, rasm, video, GIF — formatlash saqlanadi)" | `✖️ Bekor` 🟥 |
| 2 | "🔘 Tugma qo'shasizmi? Format: `Matn - https://havola` (har qatorda bitta)" | `➕ Tugma qo'shish` ⬜ · `⏭ Tugmasiz` ⬜ |
| 3 | "👥 Kimga?" | `👥 Hammaga` 🟦 · `🇺🇿 uz` · `🇷🇺 ru` · `🇬🇧 en` · `💰 Xaridorlar` · `😴 30 kun nofaol` · `🆕 7 kunlik yangilar` |
| 4 | Oldindan ko'rish (xabarning o'zi) + "Qabul qiluvchilar: ~12 430" | `🧪 O'zimga test` ⬜ · `⏰ Rejalashtirish` ⬜ · `🚀 Yuborish` 🟩 · `✖️ Bekor` 🟥 |
| 5 | Progress (har 5 s yangilanadi): "📣 4 120 / 12 430 (33%) · ❌ 102 · ⏱ ~5 daq" | `⏸ To'xtatish` ⬜ · `⏹ Bekor qilish` 🟥 |

#### A9–A13. Qolgan bo'limlar

| Bo'lim | Ekran va tugmalar |
|--------|-------------------|
| 🎟 Promokodlar | Ro'yxat (kod · qiymat · ishlatilgan/limit · holat) · `➕ Yangi promokod` 🟩 → usta: kod → tur (`%` / `$`) → qiymat → umumiy limit → foydalanuvchi limiti → muddat → mahsulot → tasdiqlash · kartada `⛔️ O'chirish` 🟥 |
| 🤝 Referal | `✅ Yoqilgan` toggle · `✏️ Foiz: 2%` ⬜ · `🏆 Top referallar` ⬜ · `« Orqaga` |
| 📢 Majburiy obuna | Kanallar ro'yxati · `➕ Kanal qo'shish` 🟩 (bot kanalga admin bo'lishi kerak; kanal postini forward qilish yoki @username yuborish) · `🗑` 🟥 har kanal yonida · umumiy toggle |
| ⚙️ Sozlamalar | `✏️ Xush kelibsiz matni (uz/ru/en)` · `🆘 Support username` · `🛠 Texnik ishlar: ⛔️` · `🔐 Fragment` · `🔔 Bildirishnomalar` · `🌐 Standart til` · `🩺 Tizim holati` |
| 🔐 Fragment | Rejim (`direct` / `api`) · oxirgi tekshiruv · `🔑 Cookie yangilash` 🟩 *(owner; yuborilgan xabar o'qilgach darhol o'chiriladi, qiymat shifrlanadi)* · `🧪 Ulanishni tekshirish` 🟦 |
| 👮 Adminlar *(owner)* | Ro'yxat (ism · rol) · `➕ Admin qo'shish` 🟩 (ID yuborish yoki `👤 Tanlash` — request_users) → rol tanlash · `🗑 Olib tashlash` 🟥 |
| 🩺 Tizim holati | `DB ✅ · Redis ✅ · Worker ✅ (3 s oldin) · TonAPI ✅ · Fragment ✅ · Webhook ✅ (navbat 0)` · `🔄 Yangilash` |

### 11.8 Callback data sxemasi (aiogram `CallbackData`, ≤ 64 bayt)

```python
class MenuCb(CallbackData, prefix="m"):      action: str                                # m:premium, m:wallet
class PremiumCb(CallbackData, prefix="pr"):  step: str; value: str | None = None         # pr:plan:12
class StarsCb(CallbackData, prefix="st"):    step: str; value: str | None = None         # st:pkg:500
class PayCb(CallbackData, prefix="pay"):     action: str; pid: str                       # pay:check:PM-7F3K9Q
class OrderCb(CallbackData, prefix="o"):     action: str; oid: str | None = None; page: int = 0
class WalletCb(CallbackData, prefix="w"):    action: str; value: str | None = None; page: int = 0
class AdmCb(CallbackData, prefix="a"):       sec: str; act: str = "open"; id: str | None = None; page: int = 0
class ConfirmCb(CallbackData, prefix="cf"):  token: str; yes: bool                       # token → Redis'dagi kutilayotgan amal
```

Xavfsizlik: admin callback'larida rol **har safar** qayta tekshiriladi; xavfli amallar `ConfirmCb` tokeni orqali
(amalning o'zi Redis'da 5 daqiqa saqlanadi, callback'dan o'qilmaydi).

### 11.9 FSM holatlari

| Guruh | Holatlar |
|-------|----------|
| `PremiumFlow` | `recipient_username` |
| `StarsFlow` | `recipient_username`, `custom_amount` |
| `PromoFlow` | `code` |
| `TopUpFlow` | `custom_amount` |
| `AdminUserSearch` | `query` |
| `AdminBalance` | `amount`, `comment` |
| `AdminMessageUser` | `text` |
| `AdminPlanEdit` | `markup`, `fixed_price`, `stars_price`, `badge`, `reference_price` |
| `AdminStarsPricing` | `markup`, `packages` |
| `AdminBroadcast` | `content`, `buttons`, `schedule` |
| `AdminWithdraw` | `amount` |
| `AdminExpense` | `amount`, `category`, `note` |
| `AdminPromo` | `code`, `type`, `value`, `max_uses`, `per_user`, `valid_to`, `scope` |
| `AdminChannel` | `channel` |
| `AdminSettings` | `welcome_text`, `support_username`, `fragment_cookies` |
| `AdminAdmins` | `user` |
| `AdminStatsRange` | `from_date`, `to_date` |

FSM holati Redis'da (`RedisStorage`), 30 daqiqa harakatsizlikdan keyin tozalanadi.

### 11.10 Middleware zanjiri

| # | Middleware | Vazifa |
|---|------------|--------|
| 1 | `ThrottlingMiddleware` | Redis: foydalanuvchiga 1 update / 0.5 s; spam → "⏳ Sekinroq" toast |
| 2 | `DbSessionMiddleware` | Har update uchun `AsyncSession` (tranzaksiya oxirida commit/rollback) |
| 3 | `UserMiddleware` | Foydalanuvchini upsert (ism, username, `tg_is_premium`), `last_seen_at`, `user_daily_activity` |
| 4 | `I18nMiddleware` | Foydalanuvchi tili → gettext |
| 5 | `BanMiddleware` | Ban bo'lsa U20 va to'xtatish |
| 6 | `MaintenanceMiddleware` | Texnik ishlar → U19 (admin o'tadi; `pre_checkout_query` ga "texnik ishlar" xatosi) |
| 7 | `SubscriptionMiddleware` | Majburiy obuna yoqilgan bo'lsa `getChatMember` (Redis keshi 5 daq) → U18 |
| 8 | `AdminFilter` (router darajasida) | Admin routerlar faqat rol bo'lsa ishlaydi |

`pre_checkout_query` va `successful_payment` uchun 5–7-middleware'lar **o'tkazib yuboriladi** (to'lov hech qachon bloklanmasligi kerak).

### 11.11 Bildirishnomalar

**Foydalanuvchiga:**

| Hodisa | Xabar |
|--------|-------|
| To'lov tasdiqlandi | "✅ To'lov qabul qilindi, faollashtirilmoqda..." (U8 xabari tahrirlanadi) |
| Buyurtma bajarildi | "🎉 Tayyor! …" |
| Buyurtma xato / qaytarildi | "❌ … ↩️ … qaytarildi" |
| Tekshiruvga tushdi | "🔍 Buyurtmangiz tekshirilmoqda, 30 daqiqa ichida javob beramiz" |
| Kech / kam / ortiqcha to'lov | "💼 X $ balansingizga yozildi" + tushuntirish |
| Balans to'ldirildi | "💼 Balansingiz X $ ga to'ldirildi" |
| Referal bonus | "🎁 Do'stingiz xarid qildi — sizga +0.63 $ bonus!" |
| Qabul qiluvchiga (agar botda bo'lsa) | "🎁 @jasur sizga Telegram Premium 12 oy sovg'a qildi!" |
| Admin xabari | Admin yozgan matn |

**Admin log kanaliga (`LOG_CHAT_ID`):**

| Hodisa | Daraja | Xabar namunasi |
|--------|--------|----------------|
| Yangi buyurtma bajarildi | ℹ️ | "✅ PR-8F3K2Q · 💎12 · @ali_v · 31.50$ · foyda 2.37$ · TON" |
| Buyurtma xato / needs_review | ⚠️ | tugmalar bilan: `✅ Bajarildi` · `🔄 Qayta` · `↩️ Qaytarish` |
| Hot wallet kam | 🔴 | "Hot wallet: 12.3 TON (chegara 15). To'ldiring: UQ…" |
| Fragment cookie eskirdi | 🔴 | "Fragment sessiyasi tugadi — ⚙️ Sozlamalar → 🔐 Fragment" |
| Mos kelmagan TON to'lov | ⚠️ | "❓ 5 TON keldi, izoh: `salom` — Moliya → Mos kelmaganlar" |
| Telegram Stars refund | ⚠️ | "⭐ Telegram 1100 ⭐ to'lovni qaytardi (PM-…)" |
| Worker / job yiqildi | 🔴 | job nomi + xato |
| Pul yechildi | ℹ️ | "💸 50 TON → UQ…x9F · tx" |
| Kunlik hisobot (23:55) | 📊 | A2 formatidagi qisqa hisobot |
| Yangi foydalanuvchi | ℹ️ | ixtiyoriy (standart o'chiq) |

### 11.12 Ko'p tillilik

- Bot: gettext (`locales/{uz,ru,en}/LC_MESSAGES/messages.po`), aiogram `I18nMiddleware`. Standart — `uz`.
- Birinchi `/start` da Telegram `language_code` asosida taklif qilinadi, foydalanuvchi tanlaydi; Mini App bilan bir xil
  (`users.language`).
- Raqam formati: `12 430.50 $`, `168 000 so'm`, `10.50 TON`, `2 750 ⭐`; sana: `01.10.2026 14:22` (Asia/Tashkent).

---

## 12. Mini App (Next.js): UI/UX dizayn va arxitektura

### 12.1 Dizayn tamoyillari

1. **Telegram'ning o'zidek his qilinsin:** Telegram mavzu ranglari (`themeParams`) ishlatiladi → light/dark avtomatik,
   har bir foydalanuvchida o'z Telegram mavzusiga mos.
2. **Asosiy harakat — Telegram MainButton** (ekran pastidagi katta native tugma): "💎 10.50 TON to'lash". Ikkinchi
   darajali — `SecondaryButton`. Orqaga — Telegram `BackButton` (yuqori chapda, native).
3. **Bir qo'l bilan ishlatish:** muhim elementlar ekranning pastki 2/3 qismida, tugmalar ≥ 44 px balandlik.
4. **3 bosishda xarid:** Muddat → To'lov usuli → To'lash (qabul qiluvchi standart "o'zimga").
5. **Haptic feedback:** tanlashda `impactOccurred('light')`, muvaffaqiyatda `notificationOccurred('success')`,
   xatoda `notificationOccurred('error')`.
6. **Skeleton loading** (spinner emas), bo'sh holatlar uchun illyustratsiya + harakat tugmasi, xatolar uchun toast.
7. **Narx doim ko'rinadi:** asosiy valyuta yirik, so'mdagi taxminiy narx kichik kulrang.
8. To'lov jarayonida `enableClosingConfirmation()` (tasodifan yopib qo'ymaslik), formalarda `disableVerticalSwipes()`.

### 12.2 Dizayn tizimi (design tokens)

**Ranglar:**

| Token | Light | Dark | Ishlatilishi |
|-------|-------|------|--------------|
| `--bg` | `var(--tg-theme-bg-color, #FFFFFF)` | `var(--tg-theme-bg-color, #17212B)` | Sahifa foni |
| `--bg-secondary` | `var(--tg-theme-secondary-bg-color, #F1F2F6)` | `var(--tg-theme-secondary-bg-color, #232E3C)` | Kartalar orasidagi fon |
| `--surface` | `var(--tg-theme-section-bg-color, #FFFFFF)` | `var(--tg-theme-section-bg-color, #1E2C3A)` | Kartalar |
| `--text` | `var(--tg-theme-text-color, #000000)` | `var(--tg-theme-text-color, #F5F5F5)` | Asosiy matn |
| `--hint` | `var(--tg-theme-hint-color, #8E8E93)` | `var(--tg-theme-hint-color, #708499)` | Ikkinchi darajali matn |
| `--link` | `var(--tg-theme-link-color, #2481CC)` | `var(--tg-theme-link-color, #6AB3F3)` | Havolalar |
| `--accent` | `var(--tg-theme-button-color, #2481CC)` | `var(--tg-theme-button-color, #5288C1)` | Standart tugmalar |
| `--premium-gradient` | `linear-gradient(135deg, #6B93FF 0%, #976FFF 50%, #E46ACE 100%)` | xuddi shu | Premium kartalari, hero |
| `--stars-gradient` | `linear-gradient(135deg, #FFD54A 0%, #FFB300 50%, #FF8A00 100%)` | xuddi shu | Stars kartalari |
| `--ton` | `#0098EA` | `#2AABEE` | TON belgilari, TON tugmalari |
| `--success` | `#31B545` | `#3FC35A` | To'lash tugmasi, muvaffaqiyat, kirim grafigi |
| `--danger` | `#E5484D` | `#FF6369` | Bekor qilish, xato, chiqim grafigi |
| `--warning` | `#F5A524` | `#FFB224` | Ogohlantirish, "kutilmoqda" |
| `--profit` | `#8B5CF6` | `#A78BFA` | Foyda grafigi |

**Tugmalar (botdagi ranglar bilan bir xil mantiq):**

| Turi | Ko'rinish | Qayerda |
|------|-----------|---------|
| Asosiy (to'lash) | Telegram MainButton, fon `--success`, oq matn, to'liq kenglik | Checkout, to'ldirish |
| Brend (Premium) | `--premium-gradient` fon, oq matn, radius 14 px | Bosh sahifadagi Premium kartasi CTA |
| Brend (Stars) | `--stars-gradient`, qora matn | Stars CTA |
| Ikkinchi darajali | `--bg-secondary` fon, `--text` matn | "Tarix", "Batafsil" |
| Xavfli | shaffof fon, `--danger` matn/chegara | "Bekor qilish", "O'chirish" |
| Tanlov kartasi (tarif, paket, usul) | `--surface`, 1 px chegara; tanlanganda 2 px `--accent` chegara + ✓ belgi | Premium/Stars/to'lov usuli |

**Tipografiya:** tizim shrifti (`-apple-system, "SF Pro Text", Roboto, "Segoe UI", sans-serif`) — Telegram bilan bir xil.
Sarlavha 22/28 semibold · bo'lim sarlavhasi 17/22 semibold · asosiy 15/20 · kichik 13/18 · narx 28/34 bold (tabular-nums).

**O'lchamlar:** spacing 4 · 8 · 12 · 16 · 20 · 24 · 32; radius: karta 16, tugma 12, chip 999; soya minimal
(`0 1px 2px rgba(0,0,0,.06)`); sahifa chetidan 16 px.

**Ikonalar:** lucide-react (chiziqli, 20/24 px) + emoji mahsulot belgilari uchun; Premium va Stars uchun Lottie animatsiyalar.

### 12.3 Navigatsiya xaritasi

```mermaid
flowchart TD
    ROOT["/ Bosh sahifa"]
    ROOT --> PR["/premium"]
    ROOT --> ST["/stars"]
    ROOT --> WA["/wallet"]
    ROOT --> PF["/profile"]
    ROOT --> OR["/orders"]
    PR --> CO["/checkout/[id]"]
    ST --> CO
    WA --> TU["/wallet/topup"]
    TU --> CO
    OR --> OD["/orders/[id]"]
    PF --> RF["/referral"]
    PF --> HP["/help"]
    PF --> AD["/admin (faqat admin)"]
    AD --> AD1["/admin/stats"]
    AD --> AD2["/admin/orders → /admin/orders/[id]"]
    AD --> AD3["/admin/users → /admin/users/[id]"]
    AD --> AD4["/admin/pricing"]
    AD --> AD5["/admin/finance"]
    AD --> AD6["/admin/broadcasts → /new, /[id]"]
    AD --> AD7["/admin/promo"]
    AD --> AD8["/admin/settings"]
    AD --> AD9["/admin/admins"]
    AD --> AD10["/admin/audit"]
```

**Pastki navigatsiya (foydalanuvchi):** `🏠 Asosiy` · `💎 Premium` · `⭐ Stars` · `💼 Hamyon` · `👤 Profil`
(faol bo'lim `--accent` rangda, checkout sahifasida yashiriladi).

**Admin navigatsiyasi:** `📊 Dashboard` · `📦 Buyurtmalar` · `👥 Users` · `💰 Moliya` · `☰ Ko'proq` (Narxlar, Xabarlar,
Promokodlar, Sozlamalar, Adminlar, Audit). Yuqorida "← Foydalanuvchi rejimi" havolasi.

### 12.4 Foydalanuvchi sahifalari (wireframe)

#### `/` — Bosh sahifa

```text
┌─────────────────────────────────────┐
│ (●) Salom, Jasur 👋          🇺🇿 ▾ │
│ ┌─────────────────────────────────┐ │
│ │ 💼 Balans                       │ │
│ │ 12.50 $                         │ │
│ │ ≈ 160 000 so'm      [ + To'ldirish ]│
│ └─────────────────────────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │ 💎 PREMIUM    │ │ ⭐ STARS      │ │  ← gradient kartalar,
│ │ 3 · 6 · 12 oy │ │ 50 tadan      │ │    Lottie animatsiya
│ │ 13.15 $ dan   │ │ 0.81 $ dan    │ │
│ │ −25% gacha    │ │               │ │
│ └───────────────┘ └───────────────┘ │
│  ⚡ 1–3 daqiqa   🔒 Rasmiy   💬 24/7 │
│                                     │
│ So'nggi buyurtmalar      Barchasi › │
│ ┌─────────────────────────────────┐ │
│ │ 💎 12 oy → @ali_v   ✅ Bajarildi │ │
│ │ ⭐ 500 → o'zimga    ⚙️ Jarayonda │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 👥 Do'stlarni taklif qiling     │ │
│ │ har xariddan 2% bonus        ›  │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 🏠 Asosiy  💎  ⭐  💼 Hamyon  👤 Profil │
└─────────────────────────────────────┘
```

#### `/premium` — Premium sotib olish

```text
┌─────────────────────────────────────┐
│ ‹ (BackButton)     Telegram Premium │
│ ┌─────────────────────────────────┐ │
│ │   [Lottie: premium yulduz]      │ │  ← --premium-gradient hero
│ │   Telegram Premium              │ │
│ │   Telegram'dan 25% gacha arzon  │ │
│ └─────────────────────────────────┘ │
│ 1  Kimga?                           │
│ [ 🙋 O'zimga ][ 🎁 Do'stimga ]       │  ← segmented control
│ ┌ @ username ─────────────────────┐ │  (Do'stimga tanlansa)
│ │ @ali_v                    ✓     │ │
│ └─────────────────────────────────┘ │
│  (●) Ali Valiyev · Premium olishi mumkin ✅ │ ← preview kartasi
│                                     │
│ 2  Muddat                           │
│ ┌─────────────────────────────────┐ │
│ │ 3 oy                   13.15 $  │ │
│ │ 4.39 TON · 1 100 ⭐ · 168 000 so'm│
│ ├─────────────────────────────────┤ │
│ │ 6 oy        −27%       17.45 $  │ │
│ ├═════════════════════════════════┤ │
│ ║ 12 oy  🔥 Eng foydali  31.50 $ ✓║ │  ← tanlangan: 2px accent chegara
│ ├─────────────────────────────────┤ │
│ │ 1 oy · tez kunda       (kulrang)│ │
│ └─────────────────────────────────┘ │
│ 3  To'lov usuli                     │
│ (●) 💎 TON            10.50 TON     │
│ ( ) ⭐ Stars          2 750 ⭐      │
│ ( ) 💼 Balans  12.50 $ · yetarli emas [To'ldirish] │
│ 🎟 Promokodingiz bormi?          ›  │
│ ─────────────────────────────────── │
│ Jami: 31.50 $  ≈ 403 000 so'm       │
├─────────────────────────────────────┤
│ [ MainButton:  💎 10.50 TON to'lash ]│  ← yashil, native
└─────────────────────────────────────┘
```

Holatlar: username kiritilganda 500 ms debounce bilan `/recipients/resolve`; xato bo'lsa input qizil chegara + matn;
MainButton faqat hamma tanlov to'g'ri bo'lganda faol (`isEnabled`), so'rov vaqtida `showLoader()`.

#### `/stars` — Stars sotib olish

```text
┌─────────────────────────────────────┐
│ ‹                      Telegram Stars│
│ [Lottie: oltin yulduzlar]           │  ← --stars-gradient hero
│ 1  Kimga?  [ O'zimga ][ Do'stimga ] │
│ 2  Miqdor                           │
│ ┌────────┐┌────────┐┌────────┐      │
│ │ ⭐ 50  ││ ⭐ 100 ││ ⭐ 250 │      │  ← 3 ustunli grid
│ │ 0.81 $ ││ 1.61 $ ││ 4.02 $ │      │
│ └────────┘└────────┘└────────┘      │
│ ┌────────┐┌────────┐┌────────┐      │
│ │🔥⭐ 500││ ⭐ 1000││ ⭐ 2500│      │
│ └────────┘└────────┘└────────┘      │
│ ✏️ O'z miqdorim: [ 750 ] ⭐ = 12.04 $│  ← input + slider (50…max)
│ 3  To'lov: (●) 💎 TON  ( ) 💼 Balans│
├─────────────────────────────────────┤
│ [ MainButton:  ⭐ 750 — 4.02 TON to'lash ]│
└─────────────────────────────────────┘
```

#### `/checkout/[id]` — To'lov va holat

```text
┌─────────────────────────────────────┐
│ ‹                   Buyurtma PR-8F3K2Q│
│ 💎 Premium 12 oy → @ali_v           │
│ ┌─────────────────────────────────┐ │
│ │      10.50 TON                  │ │
│ │      ≈ 31.50 $                  │ │
│ │  ⏳ 18:42 qoldi                  │ │  ← countdown
│ └─────────────────────────────────┘ │
│ [ 🔗 Hamyonni ulash (TON Connect) ] │  ← ulanmagan bo'lsa
│ Ulangan: UQ…a1B2 (Tonkeeper)  o'zgartirish │
│                                     │
│ Holat:                              │
│ ● To'lov kutilmoqda                 │  ← timeline (OrderStatusTimeline)
│ ○ To'lov qabul qilindi              │
│ ○ Premium faollashtirilmoqda        │
│ ○ Tayyor 🎉                         │
│                                     │
│ ▸ Qo'lda to'lash (manzil, izoh) 📋  │  ← yig'iladigan bo'lim
├─────────────────────────────────────┤
│ [ MainButton: 💎 Hamyonda tasdiqlash ]│
│ [ SecondaryButton: Bekor qilish ]    │
└─────────────────────────────────────┘
```

Muvaffaqiyatda: konfetti + Lottie + haptic `success` + "🎉 Tayyor!" + `💎 Yana sotib olish` / `🏠 Bosh sahifa`.
Holat yangilanishi — har 3 soniyada polling (TanStack Query `refetchInterval`), yakuniy holatda to'xtaydi.
Stars usulida sahifa `openInvoice(link)` chaqiradi; callback `paid` bo'lsa timeline davom etadi, `cancelled` bo'lsa qaytadi.

#### `/wallet`, `/wallet/topup`

```text
┌─────────────────────────────────────┐
│ ┌─────────────────────────────────┐ │
│ │ 💼 Balans              (gradient)│ │
│ │ 12.50 $                         │ │
│ │ ≈ 160 000 so'm · ≈ 4.17 TON     │ │
│ │ [ ➕ To'ldirish ]  [ 📜 Tarix ]   │ │
│ └─────────────────────────────────┘ │
│ TON hamyon: UQ…a1B2 ✓   [Uzish]     │
│ Bugun                               │
│  ↓ +10.00 $  To'ldirish (TON) 14:22 │  ← yashil
│ Kecha                               │
│  ↑ −31.50 $  Premium 12 oy   18:05  │  ← qizil
│  ↓ +0.63 $   Referal bonus   11:40  │
└─────────────────────────────────────┘
```

To'ldirish: usul tanlash (TON / Stars) → summa chiplari (5, 10, 25, 50, 100 $) + o'z summasi → MainButton
"➕ 10 $ — 3.34 TON to'lash" → `/checkout/[id]`.

#### `/orders`, `/orders/[id]`, `/profile`, `/referral`, `/help`

- **Buyurtmalar:** filtr chiplari (Hammasi · Jarayonda · Bajarilgan · Xato), karta: mahsulot ikonkasi, qabul qiluvchi,
  narx, holat badge'i (rangli), sana. Tafsilot: timeline + to'lov ma'lumoti + `🔁 Takrorlash` + `🆘 Yordam`.
- **Profil:** avatar, ism, ID; til tanlash; `👥 Referal` · `🆘 Yordam` · `📄 Shartlar`; adminlarga `🛠 Admin panel` (🟦 brend tugma).
- **Referal:** havola + `📤 Ulashish` (`shareURL`) + `📋 Nusxalash`; statistikalar (taklif qilinganlar, bonus);
  bonuslar ro'yxati.
- **Yordam:** FAQ akkordeon + `💬 Supportga yozish` (`openTelegramLink`).

### 12.5 Admin sahifalari (wireframe)

#### `/admin` — Dashboard

```text
┌─────────────────────────────────────┐
│ Admin · Dashboard      [Kun|Hafta|Oy|Yil|📅]│ ← PeriodSwitcher
│ ┌───────────────┐ ┌───────────────┐ │
│ │ Kirim         │ │ Chiqim        │ │
│ │ 1 240 $  ▲12% │ │ 1 102 $  ▲8%  │ │  ← KpiCard (o'sish yashil/qizil)
│ └───────────────┘ └───────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │ Foyda         │ │ Buyurtmalar   │ │
│ │ 138 $  ▲21%   │ │ 37 ✅35 ❌1   │ │
│ └───────────────┘ └───────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │ Yangi userlar │ │ Faol (DAU)    │ │
│ │ +52   ▲9%     │ │ 418           │ │
│ └───────────────┘ └───────────────┘ │
│ Kirim / Chiqim / Foyda              │
│ [Area chart: yashil kirim, qizil chiqim, binafsha foyda chizig'i] │
│ Buyurtmalar mahsulot bo'yicha       │
│ [Stacked bar: 3oy · 6oy · 12oy · Stars] │
│ To'lov usullari    Foydalanuvchilar │
│ [Donut TON/Stars/Balans] [Line: o'sish] │
│ ┌─────────────────────────────────┐ │
│ │ 💎 Hot wallet 125.40 TON [Yechish]│ │
│ │ ⭐ Stars 8 450                   │ │
│ │ 💼 User balanslari 1 240 $       │ │
│ └─────────────────────────────────┘ │
│ ⚠️ 1 ta buyurtma tekshirish kutmoqda › │
├─────────────────────────────────────┤
│ 📊 Dashboard 📦 Buyurtma 👥 Users 💰 Moliya ☰ │
└─────────────────────────────────────┘
```

#### Qolgan admin sahifalari

| Sahifa | Tarkib | Asosiy harakatlar |
|--------|--------|-------------------|
| `/admin/stats` | Davr tanlash (kun/hafta/oy/yil/ixtiyoriy), granularity (soat/kun/hafta/oy), metrika tanlash, "oldingi davr bilan" ustma-ust chizig'i; jadvallar: mahsulot, usul, til, manba (`src_*`), provider; top xaridorlar, top referallar | 📥 Excel |
| `/admin/orders` | Filtrlar (holat, mahsulot, usul, sana, qidiruv), virtual ro'yxat | Kartaga o'tish |
| `/admin/orders/[id]` | To'liq ma'lumot, timeline (`order_events`), to'lovlar, provider javobi (JSON), xaridor | ✅ Bajarildi · 🔄 Qayta urinish · ↩️ Qaytarish (ConfirmDialog) |
| `/admin/users` | Qidiruv, saralash (yangi / ko'p xarid / balans), filtr (ban, xaridor) | Kartaga o'tish |
| `/admin/users/[id]` | Profil, statistikasi, buyurtmalari, ledger, referallari | ➕/➖ Balans · ✉️ Xabar · ⛔️ Ban |
| `/admin/pricing` | Tariflar jadvali (tannarx → narx → foyda jonli hisob), Stars ustamasi, paketlar (drag-n-drop tartib), umumiy sozlamalar | 💾 Saqlash · 🔄 Fragment narxini yangilash |
| `/admin/finance` | Hot wallet balansi va ledgeri, Stars balansi va ledgeri, majburiyatlar, mos kelmagan to'lovlar, xarajatlar | 💸 Yechish (owner) · 🔁 Avto-o'tkazish · ➕ Xarajat |
| `/admin/broadcasts` | Ro'yxat (holat, progress), yangi xabar muharriri (matn + media + tugmalar + segment + jadval), jonli oldindan ko'rish (Telegram xabari ko'rinishida) | 🧪 Test · 🚀 Yuborish · ⏸ · ⏹ |
| `/admin/promo` | Jadval + yaratish formasi | ➕ · ⛔️ |
| `/admin/settings` | Tablar: Umumiy · To'lov usullari · Matnlar (uz/ru/en) · Majburiy obuna · Fragment · Bildirishnomalar · Texnik ishlar · Tizim holati | 💾 Saqlash |
| `/admin/admins` | Adminlar va rollar (owner) | ➕ · 🗑 |
| `/admin/audit` | Kim, qachon, nima o'zgartirdi (before/after diff) | Filtr |

### 12.6 Frontend arxitekturasi

```text
src/app/layout.tsx
 └─ <Providers>
     ├─ TMA SDK init (init(), miniApp.mount(), themeParams.bindCssVars(), viewport.expand())
     ├─ <TonConnectUIProvider manifestUrl twaReturnUrl="https://t.me/<bot>/app">
     ├─ <QueryClientProvider>
     ├─ <NextIntlClientProvider locale={user.language}>
     └─ <AppRoot> (telegram-ui, platform = ios | base)
```

| Qism | Yechim |
|------|--------|
| Rendering | Sahifalar `"use client"` (initData faqat klientda); `output: "standalone"`; statik qismlar (ikonalar, Lottie) `public/` dan, Nginx kesh |
| API klient | `lib/api.ts` — `fetch` wrapper: `Authorization: tma ${initDataRaw}`, `Idempotency-Key`, JSON xatolarni `ApiError(code)` ga o'girish, 401 → "Ilovani qayta oching" ekrani |
| Server holati | TanStack Query: kalitlar `['me']`, `['catalog']`, `['order', id]`, `['orders', filters]`, `['admin','dashboard',period]`…; `staleTime` katalog uchun 30 s |
| Klient holati | Zustand `checkoutStore` (tanlangan tarif, qabul qiluvchi, usul, promokod) |
| Formalar | react-hook-form + zod (username regex `^[a-zA-Z][a-zA-Z0-9_]{3,31}$`, summalar) |
| Marshrutlash | `startapp` parametri → `useEffect` da kerakli sahifaga `router.replace` |
| Admin himoya | `/admin/layout.tsx` — `useMe()`; rol yo'q bo'lsa `/` ga; backend baribir har so'rovda tekshiradi |
| Telegram tugmalari | `useMainButton({text, color, onClick, enabled, loading})`, `useBackButton(onBack)` hooklari — sahifadan chiqishda tozalanadi |
| i18n | next-intl, `messages/{uz,ru,en}.json`, foydalanuvchi tili `me.language` dan; raqam/valyuta `Intl.NumberFormat` |
| Dev muhit | `mockTelegramEnv` (brauzerda initData va theme simulyatsiyasi), backend `APP_ENV=development` da test bot token bilan imzolangan initData |
| Sifat | ESLint, Prettier, `tsc --noEmit`, Vitest + Testing Library, Playwright (e2e, mock TMA) |

### 12.7 TON Connect integratsiyasi

`public/tonconnect-manifest.json`:

```json
{ "url": "https://premium.example.uz", "name": "Premium Market", "iconUrl": "https://premium.example.uz/icons/icon-180.png" }
```

Tranzaksiya yuborish (comment payload bilan):

```ts
import { beginCell } from "@ton/core";

export async function payWithTonConnect(tonConnectUI: TonConnectUI, p: TonPaymentInstructions) {
  const payload = beginCell().storeUint(0, 32).storeStringTail(p.comment).endCell().toBoc().toString("base64");
  const result = await tonConnectUI.sendTransaction({
    validUntil: Math.floor(Date.now() / 1000) + 600,
    messages: [{ address: p.address, amount: p.amount_nano, payload }],
  });
  await api.post(`/payments/${p.payment_id}/ton/submitted`, { boc: result.boc });
}
```

- Hamyon ulanmagan bo'lsa MainButton "🔗 Hamyonni ulash" → `tonConnectUI.openModal()` (Telegram Wallet, Tonkeeper,
  MyTonWallet va boshqalar ro'yxati).
- Foydalanuvchi rad etsa → toast "To'lov bekor qilindi", buyurtma `awaiting_payment` da qoladi (qayta urinish mumkin).
- Backend BOC'ga ishonmaydi — to'lov faqat blokcheynda tasdiqlangandan keyin (`ton_watcher`) qabul qilinadi; BOC faqat
  tezroq qidirish uchun ishora.

### 12.8 Stars to'lovi (Mini App)

```ts
const { invoice_link } = await api.post(`/payments/${paymentId}/stars-link`);
invoice.open(invoice_link, "url").then((status) => {   // "paid" | "cancelled" | "failed" | "pending"
  if (status === "paid") haptic.notificationOccurred("success");
});
```

Yakuniy tasdiq baribir botdagi `successful_payment` orqali keladi (klient holati faqat UI uchun).

---

## 13. Analitika va statistika

### 13.1 Metrikalar va formulalar

**💵 Moliya:**

| Metrika | Formula | Izoh |
|---------|---------|------|
| **Tushum (cash-in)** | `Σ payments.amount_usd` (`status = confirmed`, `method ≠ balance`) | Tashqaridan kelgan barcha pul (buyurtma + to'ldirish). Stars `star_usd_rate` bo'yicha |
| **Sotuv (revenue)** | `Σ orders.price_usd` (`status = completed`, `completed_at` davrda) | Barcha usullar, balans ham |
| **Tannarx (COGS)** | `Σ orders.cost_usd` (completed) | Fragment TON + tarmoq fee yoki sarflangan Stars |
| **Yalpi foyda** | Sotuv − Tannarx | |
| **Xarajatlar** | `Σ expenses.amount_usd` + `Σ referral_rewards` (credited) | Server, reklama… + referal bonuslari |
| **Qaytarishlar** | `Σ refund` summalari | Ma'lumot uchun |
| **Sof foyda** | Yalpi foyda − Xarajatlar | |
| **Chiqim (cash-out)** | Fragment'ga to'lovlar + tarmoq fee + Stars sarfi + xarajatlar | "Kirim va chiqim" grafigi uchun |
| **Admin'ga yechilgan** | `Σ hot_wallet_transactions` (`withdrawal`, `sweep`) | Xarajat emas — o'tkazma, alohida ko'rsatiladi |
| **Majburiyat** | `Σ users.balance_usd` | Foydalanuvchilarga tegishli pul |
| **O'rtacha chek (AOV)** | Sotuv / bajarilgan buyurtmalar soni | |
| **Marja %** | Yalpi foyda / Sotuv | |

**📦 Buyurtmalar:** jami, holat bo'yicha, mahsulot bo'yicha (3/6/12 oy, Stars), sotilgan Stars soni, to'lov usuli
bo'yicha, provider bo'yicha, muvaffaqiyat darajasi (`completed / (completed + failed + refunded)`), o'rtacha yetkazish
vaqti (`completed_at − paid_at`, median va p95), muddati o'tgan invoice'lar ulushi.

**👥 Foydalanuvchilar:** jami, yangi (davrda ro'yxatdan o'tgan), faol — DAU / WAU / MAU (`user_daily_activity`),
xarid qilganlar (paying users), birinchi xarid qilganlar, konversiya (`yangi xaridorlar / yangi foydalanuvchilar`),
ARPU / ARPPU, botni bloklaganlar, til bo'yicha, manba (`src_*`) bo'yicha, referal orqali kelganlar, qaytib keluvchilar
(retention: 1, 7, 30-kun — kogorta jadvali, ixtiyoriy).

**🏆 Reytinglar:** top 10 xaridorlar (summa), top 10 referallar, eng ko'p sotilgan tarif.

### 13.2 Davrlar

| Davr | Chegaralar (Asia/Tashkent) | Grafik granularity | Solishtirish |
|------|----------------------------|--------------------|--------------|
| Bugun | 00:00 – hozir | soatlik | kecha shu vaqtgacha |
| Kecha | kecha 00:00 – 24:00 | soatlik | o'tgan haftaning shu kuni |
| Hafta | dushanba 00:00 – hozir (ISO hafta) | kunlik | o'tgan hafta |
| Oy | 1-sana 00:00 – hozir | kunlik | o'tgan oy |
| Yil | 1-yanvar – hozir | oylik | o'tgan yil |
| Ixtiyoriy | `from` – `to` | ≤ 2 kun: soatlik, ≤ 90 kun: kunlik, aks holda haftalik/oylik | teng uzunlikdagi oldingi davr |

O'zgarish foizi: `(joriy − oldingi) / oldingi × 100`, oldingi = 0 bo'lsa "yangi" belgisi.

### 13.3 Agregatsiya mexanizmi

- **Xom ma'lumotlar** (`orders`, `payments`, `users`, `user_daily_activity`, `expenses`, ledgerlar) — haqiqat manbai.
- **`daily_stats`** — kunlik agregat jadval (bir kun = bir qator), `stats` job har 5 daqiqada **bugun va kecha**
  qatorlarini xom ma'lumotdan qayta hisoblaydi (idempotent `INSERT ... ON CONFLICT (day) DO UPDATE`). Eski kunlar
  o'zgarmaydi (kerak bo'lsa `python -m app.cli stats recompute --from --to`).
- Hafta / oy / yil — `daily_stats` dan `date_trunc` bilan yig'iladi (tez, millionlab buyurtmada ham).
- Soatlik grafik (bugun/kecha) — to'g'ridan-to'g'ri xom jadvaldan (indeks bilan tez).
- Dashboard javobi Redis'da 60 soniya keshlanadi.

`daily_stats` ustunlari:

```text
day (PK, Asia/Tashkent sanasi)
new_users, active_users, total_users_eod, blocked_users_eod, paying_users, first_time_buyers
orders_created, orders_completed, orders_failed, orders_refunded, orders_expired
premium_3m, premium_6m, premium_12m, stars_orders, stars_sold
cash_in_usd, cash_in_ton, cash_in_xtr, topups_usd
revenue_usd, cost_usd, gross_profit_usd, expenses_usd, referral_usd, refunds_usd, net_profit_usd
revenue_by_method JSONB   -- {"ton": .., "stars": .., "balance": ..}
revenue_by_source JSONB   -- {"src_instagram": .., "ref": .., "organic": ..}
avg_delivery_seconds, p95_delivery_seconds
updated_at
```

### 13.4 SQL namunalar

```sql
-- Kunlik sotuv va foyda (Toshkent vaqti bo'yicha)
SELECT (completed_at AT TIME ZONE 'Asia/Tashkent')::date AS day,
       count(*)                    AS orders,
       sum(price_usd)              AS revenue_usd,
       sum(cost_usd)               AS cost_usd,
       sum(price_usd - cost_usd)   AS gross_profit_usd
FROM orders
WHERE status = 'completed'
  AND completed_at >= :from_utc AND completed_at < :to_utc
GROUP BY 1
ORDER BY 1;

-- Oylik hisobot daily_stats'dan
SELECT date_trunc('month', day)::date AS month,
       sum(revenue_usd) AS revenue, sum(cost_usd) AS cost,
       sum(net_profit_usd) AS net_profit, sum(new_users) AS new_users
FROM daily_stats
WHERE day BETWEEN :from AND :to
GROUP BY 1 ORDER BY 1;

-- MAU (oxirgi 30 kun)
SELECT count(DISTINCT user_id) FROM user_daily_activity
WHERE day > (now() AT TIME ZONE 'Asia/Tashkent')::date - 30;

-- Top 10 xaridor
SELECT u.id, u.username, count(o.id) AS orders, sum(o.price_usd) AS spent
FROM orders o JOIN users u ON u.id = o.user_id
WHERE o.status = 'completed' AND o.completed_at >= :from_utc AND o.completed_at < :to_utc
GROUP BY u.id ORDER BY spent DESC LIMIT 10;
```

### 13.5 Grafiklar (Mini App, Recharts)

| Grafik | Turi | Ranglar |
|--------|------|---------|
| Kirim / Chiqim / Foyda | Area (kirim, chiqim) + Line (foyda) | `--success`, `--danger`, `--profit` |
| Buyurtmalar mahsulot bo'yicha | Stacked bar | 3 oy `#6B93FF`, 6 oy `#976FFF`, 12 oy `#E46ACE`, Stars `#FFB300` |
| To'lov usullari | Donut | TON `--ton`, Stars `#FFB300`, Balans `#8E8E93` |
| Foydalanuvchilar o'sishi | Line (jami) + Bar (yangi) | `--accent`, `--warning` |
| DAU/WAU/MAU | Line | 3 xil to'yinganlik `--accent` |
| Yetkazish vaqti | Line (median, p95) | `--success`, `--warning` |
| Joriy vs oldingi davr | Ikki chiziq (oldingisi punktir) | — |

Tooltip'da aniq qiymat + so'mdagi ekvivalent; bo'sh davr uchun "Ma'lumot yo'q" holati.

### 13.6 Eksport va hisobotlar

- **Excel (`.xlsx`):** varaqlar — Umumiy (KPI), Kunlik (`daily_stats`), Buyurtmalar, To'lovlar, Xarajatlar,
  Hot wallet harakati. Botda `📥 Excel` → fayl sifatida yuboriladi; Mini App'da yuklab olish
  (`downloadFile` / havola).
- **Avtomatik hisobotlar** (owner va log kanalga): kunlik 23:55, haftalik dushanba 09:00, oylik 1-sana 09:00.

---

## 14. Xavfsizlik

### 14.1 Ilova darajasi

| # | Tahdid | Himoya |
|---|--------|--------|
| 1 | Soxta foydalanuvchi (Mini App) | Har so'rovda `initData` HMAC tekshiruvi, `auth_date` ≤ 24 soat, `hmac.compare_digest` |
| 2 | Soxta Telegram webhook | `X-Telegram-Bot-Api-Secret-Token` tekshiruvi; webhook yo'li faqat Nginx orqali |
| 3 | Narxni o'zgartirib yuborish | Narx faqat serverda hisoblanadi; klientdan faqat ID'lar keladi; `pre_checkout_query` da summa qayta tekshiriladi |
| 4 | Ikki marta to'lov/yetkazish | 6.6-bo'limdagi UNIQUE, shartli UPDATE, SKIP LOCKED, idempotency kalitlari |
| 5 | Admin huquqini oshirish | Rol faqat bazadan (`admins`), har so'rov/callback'da tekshiriladi; `owner` faqat `.env` dagi ID |
| 6 | Admin akkaunti o'g'irlanishi | Pul faqat `.env` dagi `ADMIN_TON_ADDRESS` ga; kunlik yechish limiti; har yechish log kanalga; owner'dan boshqasi yecha olmaydi |
| 7 | SQL injection | Faqat SQLAlchemy parametrli so'rovlar |
| 8 | XSS (Mini App, broadcast) | React avtomatik escape; bot HTML matnlarida foydalanuvchi qiymatlari `html.escape` |
| 9 | Spam / DoS | Redis throttling (bot), rate limit (API), Nginx `limit_req` |
| 10 | Maxfiy ma'lumot sizishi | Loglarda maskalash; secret sozlamalar Fernet bilan shifrlangan; API'da `***` |
| 11 | Callback soxtalashtirish | Xavfli amallar `ConfirmCb` token orqali (amal Redis'da), rol qayta tekshiriladi |
| 12 | Referal/promokod suiiste'moli | O'zini taklif qilish taqiqi, bonus faqat `completed` buyurtmadan, promo limitlari row lock bilan |
| 13 | Kam/noto'g'ri TON to'lov | Summa va izoh qat'iy tekshiriladi; mos kelmaganlar alohida jadvalda, avtomatik hech kimga yozilmaydi |
| 14 | Clickjacking | CSP `frame-ancestors 'self' https://web.telegram.org https://*.telegram.org` |
| 15 | Zaif kutubxonalar | `pip-audit`, `pnpm audit` CI'da; Dependabot |

### 14.2 Hot wallet va kalitlar

- Hot wallet seed **serverda** `python -m app.cli wallet generate` bilan yaratiladi, `ENCRYPTION_KEY` bilan shifrlanib
  `/etc/premium/hot_wallet.enc` ga yoziladi (`chmod 600`, egasi `premium` foydalanuvchisi). Seed hech qachon chatga,
  git'ga, loglarga tushmaydi. Owner'ga **bir marta** ekranga chiqariladi — qog'ozga yozib, xavfsiz joyda saqlash uchun.
- Hot wallet'da faqat rezerv + aylanma mablag'; avto-sweep yoqilsa ortiqchasi avtomatik owner'ga.
- Kutilmagan chiquvchi tranzaksiya (bizning ledgerimizda yo'q) aniqlansa → 🔴 alert va barcha chiqimlar avtomatik
  to'xtatiladi (`hot_wallet.frozen = true`), owner qo'lda ochadi.
- Fragment cookie'lari bazada shifrlangan; admin kiritgan xabar botdan darhol o'chiriladi.

### 14.3 RBAC huquqlar matritsasi

| Amal | owner | admin | support |
|------|:-----:|:-----:|:-------:|
| Dashboard, statistika, eksport | ✅ | ✅ | ❌ |
| Buyurtmalarni ko'rish | ✅ | ✅ | ✅ |
| Qayta urinish | ✅ | ✅ | ✅ |
| Qo'lda bajarildi / refund | ✅ | ✅ | ❌ |
| Foydalanuvchilarni ko'rish, xabar yozish | ✅ | ✅ | ✅ |
| Ban / unban | ✅ | ✅ | ❌ |
| Balansni o'zgartirish | ✅ (cheksiz) | ✅ (±50 $ gacha) | ❌ |
| Narxlar, to'lov usullari, promokod, referal | ✅ | ✅ | ❌ |
| Broadcast | ✅ | ✅ | ❌ |
| Sozlamalar, majburiy obuna, texnik ishlar | ✅ | ✅ | ❌ |
| Fragment cookie'lari | ✅ | ❌ | ❌ |
| Hot wallet'dan yechish, avto-sweep | ✅ | ❌ | ❌ |
| Adminlarni boshqarish | ✅ | ❌ | ❌ |
| Audit log | ✅ | ✅ | ❌ |

### 14.4 Server darajasi

- SSH faqat kalit bilan, `PasswordAuthentication no`, `PermitRootLogin no`; `fail2ban`.
- `ufw`: faqat 22, 80, 443 ochiq. PostgreSQL va Redis faqat `127.0.0.1`, Redis `requirepass`.
- Har servis alohida `premium` tizim foydalanuvchisi ostida; systemd hardening: `NoNewPrivileges=yes`,
  `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`, `ReadWritePaths=` faqat kerakli papkalar.
- `unattended-upgrades` (xavfsizlik yangilanishlari avtomatik).
- Backuplar shifrlangan (`age`), 14 kun saqlanadi, haftada bir tiklash sinovi (`restore.sh` test bazaga).

---

## 15. Kerakli secret kalitlar va ularni olish yo'li

> ⚠️ **Muhim:** quyidagi "❌ Chatga yubormang" belgisi bor kalitlarni hech qachon chatga, GitHub'ga yoki
> boshqa joyga yubormang — ularni o'zingiz to'g'ridan-to'g'ri serverdagi `.env` faylga yoki admin panelga kiritasiz.
> Development (ishlab chiqish) uchun **alohida test bot** yaratishingizni tavsiya qilaman — uning tokenini
> menga berishingiz mumkin; production bot tokeni faqat serverda turadi.

| # | Kalit | Nima uchun | Qayerdan olinadi | Qaysi bosqichda kerak | Chatga yuborish |
|---|-------|-----------|------------------|-----------------------|-----------------|
| 1 | `BOT_TOKEN` (test bot) | Ishlab chiqish va sinov | @BotFather → `/newbot` | Bosqich 4 | ⚠️ Faqat **test** bot tokeni |
| 2 | `BOT_TOKEN` (asosiy bot) | Production | @BotFather → `/newbot` | Bosqich 16 | ❌ Serverga o'zingiz |
| 3 | `OWNER_TELEGRAM_ID` | Sizni owner sifatida tanish | @userinfobot ga `/start` yozing | Bosqich 2 | ✅ Mumkin (maxfiy emas) |
| 4 | Domen nomi | Mini App (HTTPS majburiy), webhook | Domen registratori (masalan `premium.uz` yoki subdomen) | Bosqich 12/16 | ✅ Mumkin |
| 5 | VPS (Ubuntu 24.04, 2 vCPU, 4 GB RAM, 40 GB SSD) | Server | Har qanday hosting (Hetzner, DigitalOcean, mahalliy) | Bosqich 16 | ❌ SSH kalit/parolni yubormang |
| 6 | `TONAPI_KEY` | TON to'lovlarni kuzatish, kurslar | tonconsole.com → ro'yxatdan o'tish → API key | Bosqich 7 | ⚠️ Test uchun mumkin, keyin almashtiring |
| 7 | `TONCENTER_API_KEY` | Zaxira TON API | Telegram'da @tonapibot | Bosqich 7 | ⚠️ Test uchun mumkin |
| 8 | Hot wallet seed | Bot hamyoni | **Biz serverda generatsiya qilamiz** (`app.cli wallet generate`) | Bosqich 7 | ❌ HECH QACHON |
| 9 | `ADMIN_TON_ADDRESS` | Foydani sizga yechish | Telegram Wallet → TON → Qabul qilish (manzilni nusxalash) yoki Tonkeeper | Bosqich 7 | ✅ Mumkin (ochiq manzil) |
| 10 | Fragment akkaunt | Premium/Stars sotib olish | fragment.com → Telegram bilan kirish → TON hamyon ulash → (kerak bo'lsa) KYC | Bosqich 8 | — |
| 11 | Fragment cookie'lari (`stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token`) | `fragment_direct` rejimi | Brauzerda fragment.com → DevTools → Application → Cookies | Bosqich 8 | ❌ Admin panel orqali kiritasiz |
| 12 | `FRAGMENT_API_KEY` | `fragment_api` rejimi (agar tanlansa) | Tanlangan servis saytidan | Bosqich 8 | ❌ Serverga o'zingiz |
| 13 | `LOG_CHAT_ID` | Admin bildirishnomalari | Yopiq kanal/guruh yarating → botni admin qiling → ID'ni bot o'zi aniqlab beradi (`/admin` → Sozlamalar) | Bosqich 4 | ✅ Mumkin |
| 14 | Support username | Yordam tugmasi | Sizning yoki support akkaunt | Bosqich 4 | ✅ Mumkin |
| 15 | `APP_SECRET_KEY`, `ENCRYPTION_KEY`, `WEBHOOK_SECRET`, DB va Redis parollari | Ichki xavfsizlik | **Biz generatsiya qilamiz** (`openssl rand -hex 32`, Fernet) | Bosqich 1/16 | — sizdan kerak emas |
| 16 | `SENTRY_DSN` | Xatolarni kuzatish (ixtiyoriy) | sentry.io | Bosqich 16 | ⚠️ |

**Hozir (tasdiqlashdan keyin darhol) menga kerak bo'ladiganlar:** faqat **3** (`OWNER_TELEGRAM_ID`), **1** (test bot tokeni)
va 21-bo'limdagi savollarga javoblar. Qolganlari tegishli bosqichda so'raladi.

---

## 16. Deploy (Dockersiz)

### 16.1 Server talablari

| Resurs | Minimal | Tavsiya |
|--------|---------|---------|
| OS | Ubuntu 24.04 LTS | Ubuntu 24.04 LTS |
| CPU | 2 vCPU | 2–4 vCPU |
| RAM | 2 GB | 4 GB |
| Disk | 30 GB SSD | 40+ GB NVMe |
| Tarmoq | Statik IPv4 | + IPv6 |
| Domen | A yozuv → server IP | `premium.example.uz` |

### 16.2 Serverni tayyorlash (`deploy/scripts/bootstrap_server.sh` ichida avtomatlashtiriladi)

```bash
# 1. Tizim
sudo apt update && sudo apt -y upgrade
sudo apt -y install git curl build-essential ufw fail2ban unattended-upgrades nginx certbot python3-certbot-nginx age
sudo adduser --system --group --home /opt/premium premium
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw --force enable

# 2. PostgreSQL 18 (rasmiy PGDG repozitoriysi)
sudo apt -y install postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
sudo apt -y install postgresql-18
sudo -u postgres psql -c "CREATE ROLE premium LOGIN PASSWORD '<generatsiya>';"
sudo -u postgres psql -c "CREATE DATABASE premium OWNER premium;"

# 3. Redis
sudo apt -y install redis-server
sudo sed -i 's/^# requirepass .*/requirepass <generatsiya>/' /etc/redis/redis.conf
sudo systemctl restart redis-server

# 4. Python (uv) va Node.js 24 LTS + pnpm
curl -LsSf https://astral.sh/uv/install.sh | sudo -u premium sh
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash - && sudo apt -y install nodejs
sudo corepack enable

# 5. Kod
sudo -u premium git clone https://github.com/<owner>/online-sale-telegram.git /opt/premium/app
sudo mkdir -p /etc/premium && sudo chown premium:premium /etc/premium && sudo chmod 700 /etc/premium
# /etc/premium/backend.env va /etc/premium/webapp.env — qo'lda to'ldiriladi (chmod 600)

# 6. SSL
sudo certbot --nginx -d premium.example.uz --redirect -m <email> --agree-tos -n
```

### 16.3 systemd unit fayllari

`/etc/systemd/system/premium-api.service`:

```ini
[Unit]
Description=Premium Market API + Telegram webhook
After=network-online.target postgresql.service redis-server.service
Wants=network-online.target

[Service]
User=premium
Group=premium
WorkingDirectory=/opt/premium/app/backend
EnvironmentFile=/etc/premium/backend.env
ExecStart=/opt/premium/app/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=3
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/opt/premium/app/backend /var/lib/premium

[Install]
WantedBy=multi-user.target
```

`premium-worker.service` — xuddi shunday, `ExecStart=/opt/premium/app/backend/.venv/bin/python -m app.workers.runner`,
`RestartSec=5`.

`premium-web.service`:

```ini
[Unit]
Description=Premium Market Mini App (Next.js)
After=network-online.target

[Service]
User=premium
Group=premium
WorkingDirectory=/opt/premium/app/webapp/.next/standalone
EnvironmentFile=/etc/premium/webapp.env
Environment=NODE_ENV=production PORT=3000 HOSTNAME=127.0.0.1
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=3
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
```

`premium-backup.service` + `premium-backup.timer` (`OnCalendar=*-*-* 03:30:00`, `Persistent=true`) →
`deploy/scripts/backup.sh`: `pg_dump -Fc` → `age` bilan shifrlash → `/var/backups/premium/` → 14 kundan eskisini
o'chirish → owner'ga bot orqali yuborish (fayl < 50 MB bo'lsa).

### 16.4 Nginx

`/etc/nginx/sites-available/premium.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;

server {
    listen 443 ssl http2;            # Ubuntu 24.04 dagi nginx 1.24 sintaksisi
    server_name premium.example.uz;

    ssl_certificate     /etc/letsencrypt/live/premium.example.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/premium.example.uz/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Content-Security-Policy "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org" always;

    client_max_body_size 20m;
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    location /tg/webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /api/ {
        limit_req zone=api burst=40 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 30s;
    }

    location /_next/static/ {
        alias /opt/premium/app/webapp/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

server {
    listen 80;
    server_name premium.example.uz;
    return 301 https://$host$request_uri;
}
```

### 16.5 Yangilash skripti (`deploy/scripts/deploy.sh`)

```bash
set -euo pipefail
cd /opt/premium/app
git fetch origin main && git reset --hard origin/main

# Backend
cd backend
uv sync --frozen --no-dev
uv run alembic upgrade head
uv run python -m app.cli bot set-webhook        # webhook + setMyCommands + menu button
cd ..

# Frontend
cd webapp
pnpm install --frozen-lockfile
pnpm build
cp -r public .next/standalone/ && cp -r .next/static .next/standalone/.next/
cd ..

sudo systemctl restart premium-api premium-worker premium-web
curl -fsS https://premium.example.uz/api/health
```

> Migratsiyalar har doim **orqaga mos** yoziladi (avval ustun qo'shiladi, keyingi relizda eskisi olib tashlanadi), shuning
> uchun qayta ishga tushirish paytida xizmat uzilishi soniyalar bilan o'lchanadi.

### 16.6 Monitoring va loglar

| Vosita | Nima |
|--------|------|
| `journalctl -u premium-api -f` | Jonli loglar (JSON) |
| `/api/health` + UptimeRobot (bepul) | Tashqi tekshiruv, 5 daqiqada bir, tushsa sizga Telegram/email |
| `/admin/health`, botda `/health` | DB, Redis, worker heartbeat, TonAPI, Fragment, webhook navbati |
| Log kanal (`LOG_CHAT_ID`) | Barcha muhim hodisalar va xatolar (11.11) |
| Sentry (ixtiyoriy) | Stack trace'lar |
| `pg_stat_statements` | Sekin SQL so'rovlarni aniqlash |

---

## 17. Testlash strategiyasi

| Daraja | Vosita | Nima testlanadi | Maqsad |
|--------|--------|-----------------|--------|
| Unit | pytest | Narx formulalari (jadvalli testlar), yaxlitlash, `initData` tekshiruvi (haqiqiy test vektori), state machine o'tishlari, comment generatsiya, callback data, Decimal yordamchilari | Servislar qamrovi ≥ 85% |
| Integratsion | pytest + haqiqiy PostgreSQL (lokal/CI runner'da o'rnatilgan, Docker'siz) | Buyurtma → to'lov → yetkazish to'liq sikli (Mock provider), balans ledger mosligi, parallel so'rovlarda ikki marta yechilmasligi, promo limitlari | Barcha pul oqimlari |
| Provider | respx (HTTP mock) + yozib olingan javoblar | TonAPI parsing, Fragment javoblari, xato holatlari (timeout, 5xx, noaniq) | |
| Bot | aiogram `Dispatcher.feed_update` + soxta Bot sessiyasi | Handlerlar, FSM o'tishlari, klaviaturalar (rang va tartib), middleware'lar | Asosiy ekranlar |
| API | httpx `AsyncClient` | Har bir endpoint: auth, rollar, validatsiya, xato kodlari | Admin endpointlarda rol testlari 100% |
| Frontend unit | Vitest + Testing Library | Komponentlar (PlanCard, PriceTag, formalar), formatlash | |
| E2E | Playwright (mock Telegram muhiti) | Premium xarid oqimi, admin narx o'zgartirish | Asosiy 5 ta senariy |
| Yuklama | Locust | 100 RPS katalog/me, 20 buyurtma/s | p95 < 300 ms |
| Real sinov | Testnet + mainnet kichik summalar | TON to'lov (0.1 TON), Stars (1 ⭐ test tarif), Fragment 3 oy + 50 ⭐ | Bosqich 7–8 |
| Qo'lda QA | Checklist | iOS, Android, Desktop, Web Telegram; light/dark; uz/ru/en | Har relizdan oldin |

CI (GitHub Actions, Docker ishlatilmaydi): `ruff check`, `ruff format --check`, `mypy`, `pytest` (runner'dagi
PostgreSQL `sudo systemctl start postgresql` bilan), `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`,
`pip-audit`, `pnpm audit`.

---

## 18. Bosqichma-bosqich ish rejasi

> Har bir bosqich: **vazifalar → natija → DoD (tayyor deyish mezoni)**. Bosqich oxirida sizga ko'rsatiladi
> (demo/screenshot), commit va push qilinadi. "Hajm" — nisbiy ish hajmi (kunlarda, taxminiy); asosiy vaqt
> real to'lovlarni sinash va sizning fikringizni olishga ketadi.

### 🏁 Bosqichlar xaritasi

```mermaid
flowchart LR
    B0["0 Tayyorgarlik"] --> B1["1 Skelet"] --> B2["2 DB"] --> B3["3 Yadro"] --> B4["4 Bot asos"]
    B4 --> B5["5 Narxlash"] --> B6["6 Stars to'lov"] --> B7["7 TON + hot wallet"] --> B8["8 Yetkazish"]
    B8 --> B9["9 Balans, referal, promo"]
    B9 --> M1{{"M1: MVP bot"}}
    M1 --> B10["10 Bot admin panel"] --> B11["11 Analitika"]
    B11 --> M2{{"M2: To'liq bot"}}
    M2 --> B12["12 Mini App user"] --> B13["13 Mini App admin"]
    B13 --> M3{{"M3: Mini App"}}
    M3 --> B14["14 Broadcast, obuna"] --> B15["15 Xavfsizlik, test"] --> B16["16 Deploy"] --> B17["17 Ishga tushirish"]
    B17 --> M4{{"M4: Production"}}
```

### Bosqich 0 — Tayyorgarlik (siz + men) · hajm: 1

- [ ] Ushbu rejani tasdiqlash va 21-bo'lim savollariga javob berish
- [ ] @BotFather'da **test bot** yaratish (va keyinroq asosiy bot)
- [ ] `OWNER_TELEGRAM_ID` ni aniqlash (@userinfobot)
- [ ] Log kanal (yopiq) yaratish
- [ ] Telegram Wallet'dagi TON manzilingizni tayyorlash
- [ ] fragment.com'da akkaunt (Telegram bilan kirish, TON hamyon ulash), KYC holatini tekshirish
- [ ] tonconsole.com'da TonAPI kalit olish
- [ ] Domen va VPS (16-bosqichgacha kerak emas, lekin oldindan tayyorlash yaxshi)

**DoD:** savollarga javob berilgan; test bot tokeni va owner ID bor.

### Bosqich 1 — Repo skeleti va asboblar · hajm: 1

- [ ] Monorepo tuzilmasi (6.2), `.gitignore`, `.editorconfig`, `README.md`
- [ ] `backend/`: `uv init`, `pyproject.toml` (barcha bog'liqliklar), ruff + mypy (strict) + pytest sozlamalari
- [ ] `app/main.py` (app factory, lifespan), `GET /api/health`
- [ ] `core/config.py` — barcha `.env` o'zgaruvchilari typed, `.env.example`
- [ ] `core/logging.py` — structlog JSON, maxfiy qiymatlarni maskalash
- [ ] `webapp/`: Next.js 16 (TS, App Router, `src/`, Tailwind 4), shadcn/ui init, ESLint + Prettier, `output: "standalone"`
- [ ] `Makefile`: `dev-api`, `dev-bot`, `dev-worker`, `dev-web`, `lint`, `test`, `migrate`, `seed`
- [ ] GitHub Actions CI (17-bo'lim)

**DoD:** `make lint test` yashil; `curl localhost:8000/api/health` → `{"status":"ok"}`; `pnpm dev` ochiladi; CI yashil.

### Bosqich 2 — Ma'lumotlar bazasi · hajm: 2

- [ ] `core/db.py` (async engine, session), `core/enums.py`, `core/money.py`
- [ ] Barcha ORM modellar (9-bo'lim) + indekslar + CHECK cheklovlar
- [ ] Alembic: `0001_initial`, `0002_seed_reference`
- [ ] Repository'lar (users, orders, payments, ledgerlar, settings…)
- [ ] CLI: `db seed`, `admin create-owner`
- [ ] Testlar: cheklovlar (`balance >= 0`, UNIQUE'lar), seed idempotentligi, upgrade/downgrade

**DoD:** toza bazada `alembic upgrade head` va `downgrade base` xatosiz; seed 2 marta ishlasa ham dublikat yo'q.

### Bosqich 3 — Backend yadrosi · hajm: 2

- [ ] `core/errors.py` + FastAPI exception handlerlar (10.5 formatida)
- [ ] `core/security.py`: `initData` tekshiruvi, Fernet shifrlash; testlar (haqiqiy imzo, eskirgan, buzilgan)
- [ ] `api/deps.py`: `get_session`, `current_user`, `require_role`
- [ ] `UserService`, `GET/PATCH /me`
- [ ] `SettingsService` (DB + Redis kesh + invalidatsiya), typed kalitlar
- [ ] `RateService` + providerlar (TonAPI rates, CoinGecko zaxira, CBU.uz)
- [ ] `AuditService`, Redis rate-limiter

**DoD:** `/me` haqiqiy initData bilan ishlaydi; kurslar Redis'da; testlar ≥ 90% (security, settings, rates).

### Bosqich 4 — Bot poydevori · hajm: 3

- [ ] `bot/setup.py`: Bot (HTML parse mode), Dispatcher, RedisStorage, routerlar
- [ ] `POST /tg/webhook` (secret tekshiruvi) + dev uchun polling rejimi
- [ ] Middleware zanjiri (11.10) to'liq
- [ ] i18n: `uz`, `ru`, `en` `.po` fayllari, `babel` ekstrakt/kompilyatsiya buyruqlari
- [ ] `keyboards/builder.py` — rangli tugma yordamchisi (`style`), `CallbackData` fabrikalari
- [ ] `/start` (ref_, src_, deep link parametrlari), U1 til, U2 bosh menyu, U16 sozlamalar, U17 yordam, `/cancel`
- [ ] `commands.py`: `setMyCommands` (default + admin scope, 3 til), `setChatMenuButton`, bot tavsiflari
- [ ] Xatolar handleri → foydalanuvchiga do'stona xabar + log kanalga tafsilot
- [ ] Ban, texnik ishlar, majburiy obuna ekranlari (U18–U20)

**DoD:** test botda `/start` → til → bosh menyu **rangli tugmalar** bilan; admin'da "🛠 Admin panel" ko'rinadi, oddiy
foydalanuvchida ko'rinmaydi; referal havolasi referrer'ni biriktiradi.

### Bosqich 5 — Katalog va narxlash · hajm: 2

- [ ] `PricingService` (3.3–3.5 formulalari, min foyda, yaxlitlash, promo)
- [ ] Table-driven testlar (kamida 30 holat: turli kurslar, qat'iy narx, chegirma, zararga tushish)
- [ ] `FulfillmentProvider.get_prices()` interfeysi + Mock; `provider_prices` job (Fragment ulangach haqiqiy)
- [ ] `CatalogService`, `GET /catalog`, `POST /catalog/stars-quote`
- [ ] `POST /recipients/resolve` (Mock → keyin Fragment), username validatsiyasi
- [ ] Bot: U3, U4 (kontaktdan tanlash bilan), U5, U9, U10, U6 (to'lov usullari hozircha ko'rinadi)
- [ ] `POST /promo/validate`, botda promokod kiritish

**DoD:** botda va API'da narxlar formula bo'yicha to'g'ri; admin narx sozlamasini bazada o'zgartirsa ≤ 1 s ichida aks etadi.

### Bosqich 6 — Buyurtmalar va Stars to'lovi · hajm: 3

- [ ] `OrderService` + state machine (`ALLOWED_TRANSITIONS`, shartli UPDATE, `order_events`)
- [ ] `PaymentService` + `StarsPaymentHandler`: `sendInvoice`, `createInvoiceLink`, `pre_checkout_query` tekshiruvi,
  `successful_payment`, `refundStarPayment`, `refunded_payment` update
- [ ] `stars_transactions` ledger
- [ ] `POST /orders`, `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/cancel`, `POST /payments/{id}/stars-link`
- [ ] `expirer` job; bot U7b, U8, U14
- [ ] Testlar: ikki marta `successful_payment` → bitta to'lov; muddati o'tgan buyurtmaga to'lov

**DoD:** test botda Stars bilan to'lov (dev'da 1 ⭐ test narx) → buyurtma `paid` → Mock provider → `completed`;
foydalanuvchi U8 xabarini oladi.

### Bosqich 7 — TON to'lovlari va hot wallet · hajm: 3

- [ ] `TonChainClient` (TonAPI asosiy, Toncenter zaxira), testnet/mainnet sozlamasi
- [ ] CLI: `wallet generate` (W5, shifrlangan fayl), `wallet info`, `wallet balance`
- [ ] `TonPaymentHandler`: comment generatsiya (`PM-` / `TP-` + 6 belgi, chalkashtirmaydigan alifbo), nanoton summa, muddat
- [ ] `ton_watcher` job: `after_lt` kursor, advisory lock, moslashtirish, kam/ortiqcha/kech to'lov qoidalari,
  `unmatched_ton_txs`
- [ ] `HotWalletService`: balans, `withdraw_to_admin` (faqat `ADMIN_TON_ADDRESS`, limitlar, audit), `auto_sweep`, `frozen` rejim
- [ ] `hot_wallet_transactions` ledger, `hot_wallet` job (past balans alerti)
- [ ] Bot U7a (copy tugmalari, Tonkeeper havolasi, "To'lovni tekshirish"), U12 TON bilan to'ldirish
- [ ] Testlar: yozib olingan TonAPI javoblari bilan barcha moslashtirish holatlari

**DoD:** testnet'da to'liq sikl; mainnet'da 0.1 TON bilan haqiqiy to'lov avtomatik aniqlanadi; 1 TON sizning Telegram
Wallet'ingizga muvaffaqiyatli yechiladi.

### Bosqich 8 — Yetkazish (fulfillment) · hajm: 4

- [ ] `FulfillmentProvider` interfeysi yakuniy, `MockProvider` (muvaffaqiyat / xato / noaniq rejimlari)
- [ ] `BotStarsProvider`: `giftPremiumSubscription`, `getMyStarBalance`, Stars ledger
- [ ] Fragment: `fragment-api-lib` va `pyfragment` ni kichik summa bilan sinash → tanlash; `FragmentDirectProvider`
  va `FragmentApiProvider` (qabul qiluvchini qidirish, narxlar, premium, stars, holatni tekshirish)
- [ ] Provider tanlash strategiyasi (sozlamadagi ustuvorlik, mavjudlik, balans yetarliligi, 2.3-band qoidasi)
- [ ] `fulfillment` job (SKIP LOCKED, backoff 30 s / 2 daq / 10 daq), `fulfillment_recovery` job, `needs_review`
- [ ] Avtomatik refund (3.8), referal bonusni hisoblash/qaytarish ilgagi
- [ ] Bildirishnomalar (foydalanuvchi, qabul qiluvchi, log kanal tugmalar bilan)
- [ ] `fragment_health` job, cookie eskirish alerti
- [ ] Testlar: ikki marta yetkazmaslik (parallel workerlar), noaniq holat, zaxira providerga o'tish

**DoD:** mainnet'da haqiqiy **3 oylik Premium** (sizning test akkauntingizga) va **50 ⭐** muvaffaqiyatli yetkazildi;
Stars bilan to'langan premium `giftPremiumSubscription` orqali bajarildi; xato senariylarida pul to'g'ri qaytdi.

### Bosqich 9 — Ichki balans, referal, promokod · hajm: 2

- [ ] `BalanceService` (row lock, ledger, `balance_after`)
- [ ] `BalancePaymentHandler`, U7c
- [ ] To'ldirish: TON va Stars (`POST /wallet/topup`), U11, U12, U13, `GET /wallet`, `/wallet/transactions`
- [ ] `ReferralService` + U15 + `GET /referral`
- [ ] `PromoService` (limitlar, muddat, scope, row lock)
- [ ] `reconciliation` job

**DoD:** reconciliation testi: 1000 ta tasodifiy operatsiyadan keyin `Σ ledger == balance`; parallel xaridlarda
balans manfiyga tushmaydi.

### 🎯 M1 — MVP bot tayyor

Foydalanuvchi botda Premium (3/6/12) va Stars'ni TON, Stars yoki balans bilan sotib oladi; hammasi avtomatik.

### Bosqich 10 — Bot admin panel · hajm: 5

- [ ] `IsAdmin`/`HasRole` filtrlari, admin router, `ConfirmCb` mexanizmi
- [ ] A1 panel, A3 buyurtmalar (filtr, karta, retry/refund/mark-completed), A4 foydalanuvchilar (qidiruv, karta, balans, ban, xabar)
- [ ] A5 moliya (yechish oqimi, avto-sweep, xarajatlar, mos kelmagan to'lovlar), A6 narxlar, A7 to'lov usullari
- [ ] A9 promokodlar, A10 referal, A11 majburiy obuna, A12 sozlamalar (matnlar, support, texnik ishlar, Fragment cookie), A13 adminlar
- [ ] Tezkor buyruqlar (11.4 admin jadvali), `/health`
- [ ] Hamma admin amallari `audit_logs` ga

**DoD:** Mini App'siz faqat bot orqali butun biznesni boshqarish mumkin; support roli faqat ruxsat etilgan bo'limlarni ko'radi.

### Bosqich 11 — Analitika · hajm: 3

- [ ] `user_daily_activity` yozish (middleware), `daily_stats` + `stats` job + `recompute` CLI
- [ ] `AnalyticsService`: dashboard, davrlar, solishtirish, breakdown, top'lar
- [ ] Admin API: `/admin/dashboard`, `/admin/stats/*`, Excel eksport (`ExportService`)
- [ ] Bot A2 statistika ekrani, `/stats`, `📥 Excel`
- [ ] `reports` job (kunlik/haftalik/oylik hisobotlar)
- [ ] Testlar: sintetik ma'lumotlar bilan qo'lda hisoblangan qiymatlar mosligi, timezone chegaralari (23:59 / 00:01)

**DoD:** test ma'lumotlarida barcha metrikalar qo'lda hisoblangan bilan 100% mos; dashboard < 200 ms.

### 🎯 M2 — To'liq bot (user + admin + analitika)

### Bosqich 12 — Mini App: foydalanuvchi qismi · hajm: 6

- [ ] Providers (TMA SDK, TON Connect, Query, i18n, AppRoot), design tokens (12.2), `AppShell`, `BottomNav`
- [ ] `lib/api.ts`, `useMe`, `useMainButton`, `useBackButton`, `useHaptic`, `startapp` marshrutlash
- [ ] Sahifalar: `/`, `/premium`, `/stars`, `/checkout/[id]`, `/wallet`, `/wallet/topup`, `/orders`, `/orders/[id]`,
  `/profile`, `/referral`, `/help`, `/terms`
- [ ] TON Connect to'lov (12.7), Stars `openInvoice` (12.8), muvaffaqiyat animatsiyasi
- [ ] Skeletonlar, bo'sh holatlar, xato holatlari, 401 ekrani
- [ ] BotFather: Main Mini App URL, `/newapp` short name (dev uchun vaqtinchalik HTTPS tunnel, masalan Cloudflare Tunnel)
- [ ] Vitest + Playwright asosiy senariylar

**DoD:** iOS, Android, Desktop va Web Telegram'da light/dark mavzularda to'liq xarid oqimi ishlaydi; Lighthouse
Performance ≥ 90 (mobil).

### Bosqich 13 — Mini App: admin qismi · hajm: 6

- [ ] `/admin/layout.tsx` (rol himoyasi, admin navigatsiya)
- [ ] Dashboard (KPI, 4 grafik, balanslar, alertlar), `/admin/stats`
- [ ] Buyurtmalar, foydalanuvchilar (ro'yxat + karta + amallar), narxlar, moliya, xarajatlar
- [ ] Broadcast muharriri (oldindan ko'rish bilan), promokodlar, sozlamalar (tablar), adminlar, audit
- [ ] `ConfirmDialog` barcha xavfli amallarda

**DoD:** bot admin panelidagi har bir amal Mini App'da ham bor va bir xil natija beradi.

### 🎯 M3 — Mini App tayyor

### Bosqich 14 — Broadcast, majburiy obuna, bildirishnomalar · hajm: 2

- [ ] `BroadcastService` + `broadcast` job (25 xabar/s, `retry_after`, 403 → `is_bot_blocked`, pauza/davom, cursor)
- [ ] Segmentlar, rejalashtirish, o'ziga test, progress xabari (A8)
- [ ] Majburiy obuna tekshiruvi (kesh bilan), kanal qo'shish oqimi
- [ ] Barcha bildirishnoma shablonlari 3 tilda (11.11)

**DoD:** 1000 ta test qabul qiluvchiga yuborish xatosiz; bloklaganlar to'g'ri belgilanadi; pauza/davom ishlaydi.

### Bosqich 15 — Xavfsizlik va to'liq test · hajm: 3

- [ ] 14-bo'lim checklistini to'liq tekshirish
- [ ] `pip-audit`, `pnpm audit`, maxfiy qiymatlar skaneri
- [ ] Qamrov: servislar ≥ 85%, admin endpointlar rol testlari 100%
- [ ] Locust yuklama testi, xaos testlar (TonAPI / Fragment / Redis o'chiq bo'lganda tizim xatti-harakati)
- [ ] Qo'lda QA checklist (barcha ekranlar × 3 til × 4 platforma)

**DoD:** checklist 100% ✅; kritik/yuqori darajali xatolar yo'q.

### Bosqich 16 — Deploy (Dockersiz) · hajm: 2

- [ ] `bootstrap_server.sh`, systemd unitlar, Nginx, Certbot, ufw, fail2ban
- [ ] `/etc/premium/*.env` (siz kiritasiz), hot wallet generatsiyasi serverda, owner seed'ni yozib oladi
- [ ] `deploy.sh`, webhook, menu button, BotFather Mini App URL
- [ ] Backup timer + tiklash sinovi, UptimeRobot, log kanal
- [ ] Production asosiy bot tokeni bilan ishga tushirish (yopiq rejim: faqat adminlar uchun `bot.maintenance`)

**DoD:** `https://<domen>` ishlaydi; server qayta yuklanganda hamma servis avtomatik ko'tariladi; backup'dan tiklash sinovdan o'tgan.

### Bosqich 17 — Ishga tushirish · hajm: 1 + 1 hafta kuzatuv

- [ ] Yopiq sinov: siz + 5–10 ishonchli foydalanuvchi, kichik summalar
- [ ] Narxlarni yakuniy sozlash, matnlarni tekshirish
- [ ] Ommaviy ishga tushirish (`maintenance` o'chiriladi), birinchi broadcast/reklama (`src_*` havolalar bilan)
- [ ] 1 hafta kunlik kuzatuv: xatolar, yetkazish vaqti, konversiya; tezkor tuzatishlar

**DoD:** 7 kun davomida muvaffaqiyat darajasi ≥ 98%, o'rtacha yetkazish < 3 daqiqa, hal qilinmagan `needs_review` yo'q.

### 🎯 M4 — Production

---

## 19. Xavflar va ularni kamaytirish

| # | Xavf | Ehtimol | Ta'sir | Kamaytirish |
|---|------|---------|--------|-------------|
| 1 | Fragment ichki API'sini o'zgartiradi / cookie eskiradi | O'rta | Yuqori | Adapter, 2 rejim (direct + api), `fragment_health` alerti, zaxira `bot_stars` provider, buyurtmalar navbatda kutadi (yo'qolmaydi) |
| 2 | TON kursi keskin o'zgaradi | O'rta | O'rta | 20 daqiqalik muzlatish, kurs har daqiqada, `min_margin_percent` bufer |
| 3 | Hot wallet buzilishi | Past | Juda yuqori | Minimal balans + sweep, yechish faqat `.env` manziliga, server hardening, kutilmagan chiqimda avto-muzlatish |
| 4 | Ikki marta yetkazish (pul yo'qotish) | Past | Yuqori | Idempotentlik, SKIP LOCKED, noaniq holatda avtomatik qayta urinish yo'q |
| 5 | Foydalanuvchi izohsiz TON yuboradi | Yuqori | Past | Mini App TON Connect (izoh avtomatik), `unmatched_ton_txs` + admin qo'lda biriktiradi |
| 6 | Telegram limitlari (broadcast 429) | O'rta | Past | 25 xabar/s, `retry_after` |
| 7 | Stars yechish 21 kun kechikishi (cash-flow) | Yuqori | O'rta | `bot_stars` strategiyasi (Stars Stars'ga sarflanadi), statistikada "yechilishi mumkin" ko'rsatkichi |
| 8 | Qabul qiluvchi username'ni o'zgartiradi | Past | O'rta | Buyurtma paytida va yetkazishdan oldin qayta tekshiruv |
| 9 | Telegram `refunded_payment` (Stars qaytarildi) | Past | O'rta | Update qayta ishlanadi, alert, foydalanuvchi balansi tekshiriladi |
| 10 | Huquqiy/soliq talablari (kripto to'lovlar) | — | Yuqori | O'zbekistondagi kripto-aktivlar va onlayn savdo qoidalari bo'yicha mutaxassis bilan maslahatlashish tavsiya etiladi; foydalanish shartlari sahifasi |
| 11 | Server ishdan chiqishi | Past | Yuqori | Kunlik backup, tiklash yo'riqnomasi, UptimeRobot alerti; hot wallet seed qog'ozda owner'da |

---

## 20. Kelajakdagi imkoniyatlar (v2+)

- 💳 **UZS to'lovlar:** Click, Payme, Uzum (karta orqali) — `PaymentMethodHandler` sifatida qo'shiladi.
- 💵 **USDT (TON jetton)** to'lovi va balans to'ldirish.
- 🤖 **@CryptoBot (Crypto Pay API)** — qo'shimcha kripto to'lov usuli.
- 🎁 **Telegram Gifts** (sovg'alar) va NFT gift'lar sotish.
- 🔢 Fragment username va anonim raqamlar savdosi.
- 🏪 Reseller (diler) API — boshqa botlar sizdan ulgurji narxda olishi.
- 🏅 Sodiqlik darajalari (ko'p xarid qilganlarga avtomatik chegirma).
- 📲 Inline rejim (`@bot` orqali chatda referal ulashish).
- 🌍 Qo'shimcha tillar (qozoq, qirg'iz, tojik).

---

## 21. ❓ Tasdiqlash uchun savollar (siz javob berasiz)

Iltimos, har biriga javob yozing (masalan: "1-B, 2-C, 3-A, ..."). Qavs ichidagi **tavsiya** — agar farqi yo'q bo'lsa,
shuni tanlashingiz mumkin.

| # | Savol | Variantlar | Tavsiya |
|---|-------|-----------|---------|
| 1 | **1 oylik Premium** (Telegram sovg'a qilishga ruxsat bermaydi) | **A)** umuman ko'rsatilmasin · **B)** "1 oy — tez kunda" deb kulrang ko'rsatilsin | **B** |
| 2 | **Fragment rejimi** | **A)** o'z Fragment akkauntingiz (cookie + KYC, komissiyasiz — eng arzon) · **B)** uchinchi tomon API (oson, ~bir necha % komissiya) · **C)** ikkalasi: A asosiy, B zaxira | **C** |
| 3 | **Stars bilan to'langan Premium** qanday yetkazilsin | **A)** bot Stars balansidan (`giftPremiumSubscription`, Stars narxi 1100/1650/2750 ⭐) · **B)** hot wallet TON'i bilan Fragment orqali (Stars arzonroq, lekin TON darhol sarflanadi) | **A** |
| 4 | **Ichki balans valyutasi** | **A)** USD · **B)** so'm · **C)** TON | **A** (barqaror, so'mda ham ko'rsatiladi) |
| 5 | **Tillar** | **A)** uz + ru + en · **B)** faqat uz · **C)** uz + ru | **A** |
| 6 | **Foydani Telegram Wallet'ga o'tkazish** | **A)** faqat qo'lda (tugma bilan) · **B)** avtomatik: hot wallet X TON dan oshsa ortiqchasi o'tadi (X = ?) | Boshida **A**, ishonch hosil qilgach **B** |
| 7 | **Boshlang'ich ustamalar** | Premium 8%, Stars 7%, referal 2%, min foyda 2% — o'zgartirasizmi? | Shunday qoldirish |
| 8 | **Majburiy obuna** (kanalga a'zo bo'lmasa bot ishlamaydi) | **A)** kerak (kanal: ?) · **B)** kerak emas | **B** (konversiyaga zarar) |
| 9 | **Bot nomi, username va brend** | Masalan "Premium Market" / `@PremiumMarketUzBot` — o'z variantingiz? | — |
| 10 | **UZS karta to'lovlari** (Click/Payme) | **A)** v1 da kerak · **B)** v2 da · **C)** kerak emas | **B** |
| 11 | **Foydalanuvchi balansini pulga yechish** | **A)** mumkin emas (faqat xarid uchun) · **B)** admin orqali qo'lda | **A** |
| 12 | **Server va domen** | Hozir bormi? Qaysi hosting? | — |
| 13 | **Rollar** | owner / admin / support — yetarlimi? | Ha |
| 14 | **Yangi foydalanuvchi bildirishnomasi** log kanalga | **A)** har biri · **B)** faqat kunlik hisobotda | **B** |

---

> ✅ **Keyingi qadam:** rejani ko'rib chiqing, o'zgartirish kerak bo'lgan joylarni yozing va 21-bo'lim savollariga
> javob bering. Tasdiqlaganingizdan so'ng **Bosqich 1** dan boshlayman va har bir bosqich oxirida natijani ko'rsatib boraman.
