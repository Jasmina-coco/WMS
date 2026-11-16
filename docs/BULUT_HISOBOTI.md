# "Bulutli texnologiyalar" fanidan loyiha hisoboti

**Talaba:** Ismoilova Jasmina · **Guruh:** ATT 01-24 · **O'qituvchi:** Uzoqov L.

## 1. Loyiha nomi va turi

**OmborHub** — omborlarni boshqarish tizimi (**WMS**), ko'p kompaniyali SaaS.

Manzil: <https://vangogh.uz>

## 2. Loyihaning vazifasi

Kompaniyalarga omborlar, yacheykalar, tovar qoldiqlari, kirim, terish va jo'natish, ko'chirish,
inventarizatsiya va hisobotlarni bitta tizimda yuritish imkonini beradi. Har bir kompaniyaning
ma'lumotlari boshqalaridan ajratilgan. Landing sahifa orqali yangi mijozlar ariza qoldiradi.

## 3. Dasturlash tili va framework

| Qatlam | Texnologiya |
|---|---|
| Backend | Python 3.12, Django 5.2 |
| Frontend | HTML, CSS, JavaScript (frameworksiz) |
| Ma'lumotlar bazasi | PostgreSQL 16 |
| Ilova serveri | Gunicorn |
| Load balancer | Nginx |
| Konteynerlar | Docker, Docker Swarm |
| CI/CD | GitHub Actions |

## 4. Bulut provayderi va xizmatlar

Provayder: **Amazon Web Services**, region **eu-central-1 (Frankfurt)**. Faqat Free Tier
doirasidagi xizmatlar ishlatilgan.

| Xizmat | Vazifasi |
|---|---|
| Amazon EC2 (t3.micro) | Ilova serveri: Nginx, Django konteynerlari, autoscaler |
| Elastic IP | O'zgarmas public IP, domen shu IP ga yo'naltirilgan |
| Amazon RDS (PostgreSQL) | Boshqariladigan ma'lumotlar bazasi |
| Amazon S3 | Mahsulot rasmlari va ombor hujjatlari (nakladnoy, skan) |
| IAM | EC2 role (minimal ruxsatlar), GitHub uchun OIDC role |
| Security Groups | Tarmoq darajasidagi himoya |
| CloudWatch | Metrikalar, loglar, alarmlar, dashboard |
| AWS Budgets | Xarajat nazorati |

## 5. Bulut arxitekturasi

![Arxitektura](arxitektura.svg)

```
Foydalanuvchi → Internet → vangogh.uz (DNS) → Elastic IP → EC2
EC2: Nginx (HTTPS, load balancer) → Django/Gunicorn replikalari (2–4 ta, Docker Swarm)
Django → Amazon RDS (PostgreSQL, 5432-port faqat EC2 dan)
Django → Amazon S3 (IAM role orqali, presigned URL bilan ochiladi)
EC2 / konteynerlar → CloudWatch (metrikalar, loglar, alarmlar)
GitHub Actions → GHCR → EC2 (avtomatik deploy)
```

## 6. Qismlar tavsifi

### 6.1. Compute — EC2

- Ubuntu 24.04, t3.micro (2 vCPU, 1 GB RAM), 30 GB gp3 disk, 2 GB swap.
- Docker Swarm (bitta tugun) uchta servisni boshqaradi:
  - `nginx` — HTTPS (Let's Encrypt), statik fayllar, so'rovlarni replikalarga taqsimlash
    (`least_conn`);
  - `web` — Django + Gunicorn, 2 tadan 4 tagacha replika, har biri 0.5 CPU / 220 MB bilan
    cheklangan;
  - `autoscaler` — har 30 soniyada CPU ni o'lchab, replikalar sonini o'zgartiradi.
- **Load balancing:** Nginx `tasks.web` DNS yozuvi orqali barcha replikalarni topadi va
  so'rovlarni eng kam band replikaga yuboradi. Javobdagi `X-Served-By` sarlavhasi qaysi replika
  javob berganini ko'rsatadi.
- **Autoscaling:** o'rtacha CPU 70% dan oshsa, replika qo'shiladi, 25% dan tushsa — kamaytiriladi
  (min 2, max 4). Har bir qaror CloudWatch Logs ga yoziladi.
- **Rolling update:** yangi versiya avval ishga tushadi va healthcheck'dan o'tadi, keyin eskisi
  o'chadi. Xato bo'lsa, avtomatik oldingi versiyaga qaytadi.

📸 *[EC2 instance sahifasi]* · 📸 *[`docker service ls`]*

### 6.2. Database — RDS

- PostgreSQL 16, db.t4g.micro, 20 GB, Single-AZ, avtomatik backup (1 kun).
- **Public access: No** — baza Internetdan ko'rinmaydi, faqat `wms-db-sg` orqali EC2 dan.
- Ulanish SSL bilan (`sslmode=require`). Parol faqat serverdagi `.env` faylida (`chmod 600`).
- `/health/` sahifasi bazaga ulanishni tekshiradi: `{"status": "ok", "database": true}`.

📸 *[RDS Connectivity sahifasi]* · 📸 *[/health/ javobi]*

### 6.3. Storage — S3

- Bucket: `vangogh-wms-files`, Block Public Access yoqilgan, SSE-S3 shifrlash.
- Saqlanadi: mahsulot rasmlari (`companies/<id>/products/`) va hujjatlarga biriktirilgan fayllar
  (`companies/<id>/documents/`).
- Django uchun S3 storage `boto3` orqali yozilgan (`apps/core/storage.py`). Fayl 1 soatlik
  imzolangan havola (presigned URL) bilan ochiladi. Havola faqat foydalanuvchining shu hujjatga
  ruxsati tekshirilgandan keyin beriladi.

📸 *[Bucket ichidagi fayllar]* · 📸 *[Tizimda tovar rasmi]*

### 6.4. Security

| Port | Kimga ochiq | Vazifasi |
|---|---|---|
| 22 (SSH) | Faqat administrator IP si; deploy vaqtida bir necha daqiqaga GitHub runner IP si | Serverni boshqarish |
| 80 (HTTP) | Hamma | HTTPS ga yo'naltirish, sertifikat tekshiruvi |
| 443 (HTTPS) | Hamma | Sayt |
| 5432 (PostgreSQL) | Faqat `wms-web-sg` | EC2 → RDS |

IAM (eng kam ruxsat tamoyili):

- `wms-ec2-role`: faqat bitta bucketning `companies/*` papkasiga o'qish/yozish/o'chirish va
  `/wms/*` log guruhlariga yozish. Access key yo'q — vaqtinchalik kalitlarni EC2 o'zi oladi.
- `wms-github-deploy`: faqat `wms-web-sg` ga SSH qoidasini qo'shish/olib tashlash. GitHub AWS ga
  OIDC orqali kalitsiz kiradi va faqat `production` environment uchun.
- Root akkaunt va admin user da MFA yoqilgan.

Ilova darajasida: HTTPS va HSTS, CSRF himoyasi, xavfsiz cookie, parollar hash qilingan, kompaniya
ma'lumotlari ajratilgan (testlar bilan tekshirilgan), ariza formasida honeypot va IP bo'yicha limit,
konteynerlar root bo'lmagan foydalanuvchi nomidan ishlaydi.

📸 *[Security Group inbound rules]* · 📸 *[IAM role policy]*

### 6.5. Monitoring — CloudWatch

- Metrikalar: EC2 CPU va status check (standart), RAM, swap va disk (CloudWatch Agent), RDS CPU,
  ulanishlar soni va bo'sh joy.
- Loglar: barcha konteyner loglari `awslogs` driver orqali `/wms/app` log guruhiga.
- Alarmlar (email): EC2 CPU > 80%, status check xatosi, RDS bo'sh joy < 2 GB.
- Dashboard: `WMS` — asosiy grafiklar bitta sahifada.

📸 *[CloudWatch dashboard]* · 📸 *[Autoscaler logi: SCALE 2 -> 3]*

## 7. CI/CD

GitHub Actions (`.github/workflows/ci-cd.yml`):

1. **lint** — `black`, `flake8`
2. **test** — PostgreSQL bilan Django testlari, migratsiyalar tekshiruvi
3. **build** — 3 ta Docker image (web, nginx, autoscaler) → GitHub Container Registry
4. **deploy** — SSH ni vaqtincha ochish → migratsiya → `docker stack deploy` (rolling update) →
   `/health/` tekshiruvi → SSH ni yopish

📸 *[GitHub Actions muvaffaqiyatli run]*

## 8. Xarajatlar

Kreditli Free plan ($133 kredit). Taxminiy oylik sarf: EC2 ≈ $7.5, public IPv4 ≈ $3.6,
RDS ≈ $14, S3 va CloudWatch ≈ $0–1. Pullik xizmatlar (Application Load Balancer, NAT Gateway,
Multi-AZ) ataylab ishlatilmagan. Budget ogohlantirishi sozlangan.

## 9. Xulosa

Web-ilova AWS bulutiga joylashtirildi va domen orqali HTTPS bilan ishlaydi. Ma'lumotlar bazasi
boshqariladigan RDS xizmatida, fayllar S3 da saqlanadi. Tarmoq Security Group'lar bilan, kirish
huquqlari IAM role'lar bilan minimal darajada cheklangan. Holat CloudWatch orqali kuzatiladi.
Load balancing va autoscaling bepul server ichida Nginx va Docker Swarm yordamida amalga oshirildi.
Har bir o'zgarish GitHub Actions orqali avtomatik tekshirilib, sayt to'xtamasdan serverga
yetkaziladi.
