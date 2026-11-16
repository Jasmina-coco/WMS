# Texnik topshiriq: WMS (omborlarni boshqarish tizimi) — SaaS

Versiya: 0.2 · Sana: 16.11.2026 · Topshirish muddati: **8-dekabr 2026**

Loyiha bir vaqtda ikki talabni qoplaydi:
- "Web tizimlar, web dasturlash, axborot tizimlari yechimlari va loyihalash" — funksionallik, frontend/backend, biznes mantiq;
- "Bulutli texnologiyalar" (o'qituvchi: Uzoqov L.) — AWS deploy, RDS, S3, xavfsizlik, monitoring (14-bo'lim).

---

## 1. Maqsad

Ko'p kompaniyalar uchun bitta umumiy WMS platformasi (SaaS). Har bir kompaniya o'z omborlari, tovarlari va xodimlari bilan ishlaydi. Kompaniyalarning ma'lumotlari bir-biridan to'liq ajratilgan bo'ladi.

Tizim ikki qismdan iborat:

1. **Landing page** — WMS haqida ma'lumot, imkoniyatlar, aloqa va ariza qoldirish formasi.
2. **WMS ilovasi** — kompaniyalar ishlaydigan ichki tizim, hamda platforma admini uchun boshqaruv paneli.

## 2. Texnologiyalar (qat'iy)

| Qatlam | Texnologiya |
|---|---|
| Backend | Python 3.12, Django 5.x |
| Ma'lumotlar bazasi | PostgreSQL 16 (production'da Amazon RDS) |
| Fayllar | Amazon S3 (mahsulot rasmlari, ombor hujjatlari) |
| Bulut | AWS: EC2, RDS, S3, IAM, Security Groups, CloudWatch — faqat Free Tier |
| Frontend | Django templates, toza HTML, CSS, vanilla JS (framework yo'q, Bootstrap/Tailwind yo'q) |
| Ilova serveri | Gunicorn |
| Load balancer / statika | Nginx |
| Konteyner va scaling | Docker, Docker Swarm |
| CI/CD | GitHub Actions, GitHub Container Registry |
| Kod sifati | flake8, black, Django test runner |

Python kutubxonalari minimal: `Django`, `psycopg`, `gunicorn`, `boto3` (S3 bilan ishlash uchun rasmiy AWS kutubxonasi; usiz S3 integratsiyasini qilib bo'lmaydi). Dev uchun `flake8`, `black`. Boshqa kutubxona faqat kelishilgan holda qo'shiladi.

Hisobot eksporti: CSV (Pythonning standart `csv` moduli) va PDF (brauzerdan print uchun alohida CSS).

## 3. Foydalanuvchilar va rollar

### 3.1. Platforma admini (loyiha egasi)
- Landingdan kelgan arizalarni ko'radi va boshqaradi.
- Kompaniyalarni **qo'lda** yaratadi, faollashtiradi yoki bloklaydi.
- Har bir kompaniya uchun birinchi menejer akkauntini yaratadi.

### 3.2. Kompaniya menejeri
- Kompaniya ichidagi hamma narsani boshqaradi.
- **O'z rollarini yaratadi** (masalan: "Omborchi", "Kontroller") va har bir rolga ruxsatlarni belgilaydi.
- Xodim akkauntlarini yaratadi, ularga rol beradi va qaysi omborlarga kira olishini tanlaydi.

### 3.3. Kompaniya xodimlari
- Faqat o'z roliga berilgan ruxsatlar doirasida va faqat ruxsat berilgan omborlarda ishlaydi.

### 3.4. Ruxsatlar ro'yxati (rol yaratishda tanlanadi)

| Modul | Ruxsatlar |
|---|---|
| Omborlar va lokatsiyalar | ko'rish, tahrirlash |
| Tovarlar | ko'rish, tahrirlash |
| Qoldiqlar | ko'rish |
| Kirim | ko'rish, yaratish, tasdiqlash, bekor qilish |
| Chiqim (terish / jo'natish) | ko'rish, yaratish, tasdiqlash, bekor qilish |
| Ko'chirish | ko'rish, yaratish, tasdiqlash |
| Inventarizatsiya | ko'rish, o'tkazish, yakunlash |
| Hisobotlar | ko'rish, eksport |
| Xodimlar va rollar | boshqarish |

## 4. Landing page

### 4.1. Bo'limlar
1. Hero — qisqa taklif va "Ariza qoldirish" tugmasi
2. Qanday muammolarni hal qiladi
3. Imkoniyatlar (modullar bo'yicha)
4. Qanday ishlaydi (3–4 qadam: ariza → qo'ng'iroq → akkaunt → ishlash)
5. Kimlar uchun (chakana savdo, distribyutorlar, ishlab chiqarish omborlari)
6. Ko'p beriladigan savollar (FAQ)
7. Aloqa (telefon, email)
8. Ariza formasi

### 4.2. Ariza formasi
Maydonlar: ism, kompaniya nomi, telefon (majburiy), email (ixtiyoriy), omborlar soni, izoh.

Himoya: CSRF, honeypot (botlar uchun yashirin maydon), bitta IP dan cheklangan miqdordagi ariza (DB orqali hisoblanadi).

### 4.3. Arizalarni qayta ishlash
- Arizalar platforma admini panelida ro'yxat ko'rinishida chiqadi.
- Statuslar: **Yangi → Bog'lanildi → Rozi bo'ldi / Rad etildi**.
- Har bir arizaga izoh yozish mumkin (qo'ng'iroq natijasi).
- Filtr: status, sana. Yangi arizalar soni panelda ko'rinib turadi.
- Email/Telegram xabarnomasi yo'q — admin panelga kirib ko'radi.

## 5. WMS modullari

### 5.1. Asosiy ombor
- **Omborlar**: nomi, manzili, faol/faol emas.
- **Lokatsiyalar**: ombor → zona → yacheyka (masalan `A-01-03`). Har bir lokatsiyaning kodi ombor ichida noyob.
- **Tovarlar**: SKU (kompaniya ichida noyob), nomi, kategoriya, o'lchov birligi, shtrix-kod (hozircha **qo'lda kiritiladi**, skaner keyingi bosqichda), minimal qoldiq, **rasm (S3 da saqlanadi)**.
- **Ombor hujjatlari**: kirim/chiqim hujjatlariga fayl biriktirish (nakladnoy, skan, PDF) — **S3 da saqlanadi**. Fayllar yopiq bucketda turadi, faqat vaqtinchalik imzolangan havola (presigned URL) orqali ochiladi; boshqa kompaniya faylini ko'rib bo'lmaydi.
- **Kategoriyalar** va **o'lchov birliklari**.

### 5.2. Qoldiqlar
- Qoldiq = tovar + lokatsiya + miqdor.
- Qoldiq faqat hujjat tasdiqlanganda o'zgaradi. Har bir o'zgarish **harakatlar jurnaliga** (`StockMovement`) yoziladi va jurnal o'chirilmaydi.
- Manfiy qoldiqqa yo'l qo'yilmaydi.
- Bir vaqtda ikki xodim bir tovarni chiqarsa ham qoldiq buzilmasligi uchun tranzaksiya ichida qator bloklanadi (`select_for_update`).

### 5.3. Kirim (qabul qilish)
- Hujjat: yetkazib beruvchi, ombor, sana, qatorlar (tovar, miqdor, lokatsiya).
- Statuslar: **Qoralama → Tasdiqlangan → Bekor qilingan**.
- Tasdiqlanganda qoldiq oshadi.

### 5.4. Chiqim (terish va jo'natish)
- Hujjat: mijoz/manzil, ombor, qatorlar.
- Statuslar: **Qoralama → Terilmoqda → Jo'natildi → Bekor qilingan**.
- Terish varag'i: qaysi tovarni qaysi yacheykadan olish kerakligi (print qilinadigan).
- Jo'natilganda qoldiq kamayadi.

### 5.5. Ko'chirish
- Yacheykadan yacheykaga yoki ombordan omborga.
- Tasdiqlanganda bir joydan kamayib, boshqa joyga qo'shiladi (bitta tranzaksiyada).

### 5.6. Inventarizatsiya
- Ombor yoki zona bo'yicha sanoq ochiladi; tizimdagi qoldiq qayd etiladi.
- Xodim haqiqiy miqdorni kiritadi, farqlar ko'rsatiladi.
- Yakunlanganda farqlar tuzatish harakati sifatida jurnalga yoziladi.

### 5.7. Hisobotlar va dashboard
- Dashboard: umumiy qoldiq, bugungi kirim/chiqim, kam qolgan tovarlar, ochiq hujjatlar.
- Hisobotlar: qoldiq (ombor/lokatsiya bo'yicha), harakatlar tarixi, tovar aylanmasi (davr bo'yicha), kam qolgan tovarlar, xodimlar faolligi.
- Eksport: CSV va print/PDF.

### 5.8. Audit
Kim, qachon, qaysi hujjatni yaratdi, tasdiqladi yoki bekor qildi — hammasi saqlanadi.

## 6. Multi-tenant (kompaniyalarni ajratish)

- Bitta PostgreSQL bazasi, har bir biznes jadvalida `company_id`.
- Middleware so'rov qaysi kompaniyaga tegishli ekanini aniqlaydi (`request.company`).
- Hamma so'rovlar kompaniya bo'yicha filtrlangan maxsus manager orqali o'tadi. Boshqa kompaniyaning ID si URL ga qo'lda yozilsa ham 404 qaytadi.
- Bu ajratish alohida testlar bilan tekshiriladi.
- Bloklangan kompaniya xodimlari tizimga kira olmaydi.

## 7. Til

O'zbek (asosiy) va rus tillari — Django i18n, sahifada til almashtirish tugmasi. Landing ham, tizim ham ikki tilda.

## 8. Infratuzilma

### 8.1. Arxitektura

```
 Foydalanuvchi → Internet → domen (eskiz.uz DNS) → Elastic IP
                                                      │
 ┌─────────────────── AWS EC2 (free tier) ────────────▼───────────┐
 │                    ┌───────────┐                               │
 │                    │   Nginx   │  load balancer + statika + HTTPS
 │                    └─────┬─────┘                               │
 │          ┌───────────────┼───────────────┐                     │
 │      ┌───▼───┐       ┌───▼───┐       ┌───▼───┐                 │
 │      │ web 1 │       │ web 2 │       │ web N │  Django+Gunicorn │
 │      └───┬───┘       └───┬───┘       └───┬───┘  (Swarm replika) │
 │          └───────────────┼───────────────┘                     │
 │   autoscaler (Python) ── web replikalari sonini boshqaradi     │
 │   CloudWatch Agent ───── metrikalar va loglarni yuboradi       │
 └──────────────┬──────────────────────┬──────────────────────────┘
                │ 5432 (faqat EC2 dan) │ IAM role orqali
         ┌──────▼──────┐        ┌──────▼──────┐      ┌────────────┐
         │ Amazon RDS  │        │  Amazon S3  │      │ CloudWatch │
         │ PostgreSQL  │        │ rasmlar,    │      │ metrika,   │
         │ (yopiq)     │        │ hujjatlar   │      │ alarm, log │
         └─────────────┘        └─────────────┘      └────────────┘
```

Nima uchun bitta EC2 ichida: AWS Application Load Balancer va ikkinchi EC2 server Free Tier dan chiqib, pul to'lashga olib kelishi mumkin. PDF talabi bo'yicha keraksiz xarajat qilinmaydi. Shuning uchun load balancing va autoscaling bitta bepul server ichida Nginx va Docker Swarm bilan qilinadi.

### 8.2. Load balancing
- Nginx so'rovlarni barcha `web` replikalariga taqsimlaydi (Swarm ichki DNS orqali).
- Ilova stateless: sessiyalar PostgreSQL da saqlanadi, shuning uchun so'rov istalgan replikaga borishi mumkin.
- `/health/` endpoint — bazaga ulanishni tekshiradi; Docker healthcheck shu orqali ishlaydi va nosoz replika qayta ishga tushiriladi.

### 8.3. Autoscaling
Docker Swarm o'zi avtomatik scaling qilmaydi, shuning uchun alohida kichik **Python autoscaler servisi** yoziladi:
- Har 30 soniyada `web` konteynerlarining o'rtacha CPU yuklamasini o'lchaydi.
- CPU > 70% bo'lsa replikalar sonini oshiradi, < 30% bo'lsa kamaytiradi.
- Chegaralar: min 2, max 6 replika (sozlamalardan o'zgartiriladi).
- Oshirish/kamaytirish orasida kutish vaqti (cooldown), har bir qaror logga yoziladi.
- Yuklama testi bilan namoyish qilinadi (Python skripti bilan ko'p so'rov yuborish).

### 8.4. CI/CD (GitHub Actions)

**CI** — har bir push va pull request da:
1. `black --check` va `flake8`
2. PostgreSQL servisi bilan Django testlari
3. Migratsiyalar tekshiruvi (`makemigrations --check`)

**CD** — `main` branchga push bo'lganda (CI o'tsa):
1. Docker image yig'iladi va GitHub Container Registry ga yuklanadi (commit SHA tegi bilan)
2. SSH orqali serverga ulanib `docker stack deploy` qilinadi
3. Migratsiyalar qo'llanadi
4. Rolling update: replikalar birma-bir yangilanadi, sayt to'xtamaydi; muammo bo'lsa avtomatik oldingi versiyaga qaytadi

Deploy EC2 ga SSH orqali bo'ladi. GitHub Secrets: `SSH_HOST`, `SSH_USER`, `SSH_KEY`. AWS kalitlari GitHub ga qo'yilmaydi — EC2 S3 ga IAM role orqali kiradi.

### 8.5. Muhitlar
- **Lokal**: `docker compose up` — Postgres, web, Nginx. S3 o'rniga lokal papka ishlatiladi (`USE_S3=False`).
- **Production**: EC2 dagi Docker Swarm stack + RDS + S3.
- Barcha maxfiy ma'lumotlar (`SECRET_KEY`, DB paroli) faqat serverdagi `.env` faylda yoki environment o'zgaruvchilarida. Repoda faqat `.env.example` bo'ladi.

## 9. Kod talablari

- Clean code: kichik funksiyalar, aniq nomlar, biznes logika view larda emas, alohida `services.py` da.
- Har bir Django app o'z vazifasiga ega (`landing`, `accounts`, `companies`, `warehouses`, `catalog`, `inventory`, `operations`, `reports`, `panel`).
- Izohlar o'zbek tilida, oddiy va tushunarli: kod **nima uchun** shunday yozilgani tushuntiriladi, himoya paytida izohlab berish oson bo'lsin.
- Kod odatiy dasturchi uslubida, keraksiz murakkabliksiz.
- Commitlar kichik va mazmunli, `Jasmina-coco` nomidan; commit xabarlarida va kodda AI vositalari haqida hech qanday belgi bo'lmaydi.

## 10. Testlar

- Qoldiq hisoblash: kirim, chiqim, ko'chirish, inventarizatsiya.
- Manfiy qoldiqqa yo'l qo'yilmasligi.
- Ruxsatlar: rolsiz xodim himoyalangan sahifaga kira olmaydi.
- Kompaniyalar ajratilishi: A kompaniya B ning ma'lumotini ko'ra olmaydi.
- Landing ariza formasi va spam himoyasi.

## 11. Bosqichlar

| # | Bosqich | Natija |
|---|---|---|
| 1 | Loyiha skeleti | Django loyiha, Docker, Postgres, CI (lint + test) |
| 2 | Landing + arizalar | Landing sahifa, forma, admin panelda arizalar |
| 3 | Kompaniyalar, foydalanuvchilar, rollar | Multi-tenant, login, menejer rollari |
| 4 | Asosiy ombor | Omborlar, lokatsiyalar, tovarlar |
| 5 | Qoldiq va operatsiyalar | Kirim, chiqim, ko'chirish, inventarizatsiya |
| 6 | Hisobotlar va dashboard | Hisobotlar, eksport |
| 7 | Tarjima | Rus tili |
| 8 | Infratuzilma | Nginx LB, Swarm stack, autoscaler, CD |
| 9 | AWS | EC2, RDS, S3, IAM, Security Groups, CloudWatch, domen + HTTPS |
| 10 | Yakuniy | Testlar, README, bulut bo'yicha texnik hisobot, skrinshotlar, himoyaga tayyorlanish |

Muddat 8-dekabr bo'lgani uchun 1–9-bosqichlar taxminan 1-dekabrgacha tugashi kerak. Qolgan hafta hisobot va himoyaga tayyorlanishga qoladi.

## 12. Keyingi bosqichlarga qoldirilganlar
- Shtrix-kod skaneri (USB va kamera)
- Online to'lov va tariflar
- Arizalar uchun email/Telegram xabarnomalari
- Mobil ilova

## 13. Aniqlangan ma'lumotlar va ochiq savollar

Aniqlangan:
- **Domen**: `vangogh.uz` (eskiz.uz, 15.10.2027 gacha). DNS: `vangogh.uz` va `www` uchun A-yozuv EC2 ning Elastic IP siga yo'naltiriladi.
- **Telefon (landing)**: +998 88 803 30 24
- **AWS akkaunt**: kreditli Free plan — 16.11.2026 holatida $133.34 kredit qolgan, 15.04.2027 gacha (152 kun). Har bir ishlatilgan xizmat kreditdan yechiladi, shuning uchun xarajat nazorati muhim.

- **Email (landing)**: jasminaismoilova279@gmail.com
- **Telegram va manzil**: landingda ko'rsatilmaydi.
- **Mahsulot nomi**: vaqtincha `OmborHub`. `SITE_NAME` sozlamasidan bitta joyda almashtiriladi.
- **AWS region**: Frankfurt (`eu-central-1`). Sidney'dagi eski loyiha o'chiriladi.

## 14. Bulutli texnologiyalar talablari (AWS, faqat Free Tier)

### 14.1. Xizmatlar va bepul chegaralar

| Xizmat | Nima uchun | Sozlama (Free Tier ichida) |
|---|---|---|
| **EC2** | Ilova serveri | 1 ta `t3.micro` (yoki `t2.micro`), Ubuntu 24.04, 30 GB gp3 disk, Elastic IP |
| **RDS** | Boshqariladigan PostgreSQL | `db.t4g.micro`/`db.t3.micro`, Single-AZ, 20 GB, Public access = **No**, avtomatik backup 1 kun |
| **S3** | Mahsulot rasmlari va ombor hujjatlari | 1 ta private bucket, Block Public Access yoqilgan, 5 GB dan kam |
| **IAM** | Minimal ruxsatlar | EC2 uchun role: faqat shu bucketga `GetObject/PutObject/DeleteObject` + CloudWatch Agent; root akkaunt ishlatilmaydi, admin user da MFA |
| **Security Groups** | Tarmoq himoyasi | `web-sg`: 80, 443 — hamma uchun; 22 — faqat sizning IP. `db-sg`: 5432 — faqat `web-sg` dan |
| **CloudWatch** | Monitoring | EC2 CPU, status check; Agent orqali RAM/disk va Nginx/Django loglari; 2–3 alarm (CPU > 80%, status check failed, RDS bo'sh joy kam) |
| **Budgets** | Xarajat nazorati | $1 lik budget va email ogohlantirish — tasodifiy to'lov bo'lsa darrov bilish uchun |

Ishlatilmaydi (pullik bo'lgani uchun): Application Load Balancer, NAT Gateway, ikkinchi EC2, Multi-AZ RDS, Route 53 (DNS eskiz.uz da qoladi).

Taxminiy xarajat (kreditdan): EC2 t3.micro ≈ $7.5, public IPv4 ≈ $3.6, RDS db.t4g.micro + 20 GB ≈ $14, S3 va CloudWatch ≈ $0–1. Jami **oyiga ≈ $25–27**. $133 kredit himoyagacha bemalol yetadi.

### 14.2. Portlar va ularning vazifasi (himoyada tushuntirish uchun)
- **22 (SSH)** — serverga ulanib boshqarish va CI/CD deploy. Faqat sizning IP manzilingiz va GitHub Actions deploy vaqti uchun.
- **80 (HTTP)** — HTTPS ga yo'naltirish va Let's Encrypt sertifikatini tekshirish.
- **443 (HTTPS)** — sayt uchun asosiy shifrlangan port.
- **5432 (PostgreSQL)** — Internetga yopiq, faqat EC2 dan RDS ga ulanish uchun.

### 14.3. Topshiriladigan materiallar (PDF 4-bo'lim) — loyihada qayerda
1. Ishlaydigan manzil — domen (HTTPS)
2. Arxitektura sxemasi — `docs/` dagi rasm + 8.1 dagi sxema
3. EC2 konfiguratsiyasi — `docs/aws/` qo'llanmasi va skrinshot
4. RDS ulanishi — `/health/` sahifasi DB holatini ko'rsatadi + RDS konsol skrinshoti
5. S3 — tovar rasmi yuklash namoyishi + bucket skrinshoti
6. Security Group va IAM — qoidalar skrinshoti va JSON policy (`docs/aws/iam-policy.json`, kalitlarsiz)
7. Monitoring — CloudWatch dashboard skrinshoti
8. Texnik hisobot — `docs/BULUT_HISOBOTI.md` (PDF 5-bo'lim tuzilmasi bo'yicha)
9. Himoya — har bir xizmat bo'yicha qisqa tushuntirish matni hisobotda

### 14.4. AWS qo'llanmasi
`docs/aws/` da AWS konsolda bajariladigan qadamlar ketma-ket yoziladi (bucket, IAM role, SG, RDS, EC2, CloudWatch Agent, Budget, DNS). Ularni siz o'z akkauntingizda bajarasiz. Kalit va parollar hech qayerga yozilmaydi.

### 14.5. Himoyadan keyin
O'qituvchi ko'rsatmasi bilan resurslarni o'chirish tartibi qo'llanmada yoziladi: EC2, RDS (oxirgi snapshotsiz), S3 bucket, Elastic IP.
