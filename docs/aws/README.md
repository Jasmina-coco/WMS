# AWS ga joylashtirish (faqat Free Tier)

Region: **Frankfurt (`eu-central-1`)**. Konsolning yuqori o'ng burchagida regionni tanlab oling va
hamma resurslarni shu regionda yarating.

Quyidagi qadamlarni tartib bilan bajaring. Har bir qadam oxirida himoya uchun skrinshot oling
(📸 belgisi bilan ko'rsatilgan).

> **Muhim.** Parol, access key va boshqa maxfiy ma'lumotlarni hech qachon GitHub'ga, hisobotga
> yoki skrinshotga qo'ymang. Skrinshotlarda ular ko'rinib qolsa, qora rang bilan yashiring.

---

## 0. Eski loyihani o'chirish (Sidney)

Regionni **Asia Pacific (Sydney)** ga o'tkazing va quyidagilarni o'chiring:

1. **EC2 → Instances** → instance → *Instance state → Terminate*
2. **RDS → Databases** → baza → *Actions → Delete*. "Create final snapshot" belgisini olib tashlang.
3. **S3** → bucket → *Empty*, keyin *Delete*
4. **EC2 → Elastic IPs** → *Release*. Bo'shatilmagan IP ishlatilmasa ham pul oladi.

## 1. Xarajat nazorati (Budgets)

**Billing → Budgets → Create budget → Zero spend budget** (yoki $1 lik oylik budget). Email —
o'zingizniki. Tasodifan pullik xizmat yoqilib qolsa, darhol xat keladi.

## 2. S3 bucket

**S3 → Create bucket**

| Sozlama | Qiymat |
|---|---|
| Nomi | `vangogh-wms-files` (dunyo bo'yicha noyob bo'lishi kerak) |
| Region | eu-central-1 |
| Block all public access | ✅ yoqilgan (fayllar faqat imzolangan havola orqali ochiladi) |
| Default encryption | SSE-S3 |

📸 Bucket sozlamalari (Permissions → Block public access).

## 3. IAM

### 3.1. EC2 uchun role

1. **IAM → Policies → Create policy → JSON**. [iam-ec2-policy.json](iam-ec2-policy.json) dagi
   matnni qo'ying, `BUCKET_NOMI` va `AKKAUNT_ID` ni almashtiring. Nomi: `wms-ec2-policy`.
2. **IAM → Roles → Create role → AWS service → EC2**. Ikkita policy biriktiring:
   - `wms-ec2-policy` (S3 va loglar — faqat bizning bucket va log group)
   - `CloudWatchAgentServerPolicy` (AWS tayyor policy — RAM/disk metrikalari)
3. Role nomi: `wms-ec2-role`.

Nega role, access key emas: role'ning vaqtinchalik kalitlari serverning o'zida avtomatik
yangilanib turadi va hech qayerga yozilmaydi. Kalit sizib chiqish xavfi yo'q.

📸 Role'ning *Permissions* bo'limi.

### 3.2. Admin foydalanuvchi

Kundalik ishni root akkaunt bilan qilmang. **IAM → Users** da o'zingizga user yarating va
**MFA** ni yoqing (root uchun ham).

## 4. Security Groups

**EC2 → Security Groups → Create**

**`wms-web-sg`** (EC2 uchun):

| Turi | Port | Manba | Nima uchun |
|---|---|---|---|
| HTTP | 80 | 0.0.0.0/0 | HTTPS ga yo'naltirish va sertifikat tekshiruvi |
| HTTPS | 443 | 0.0.0.0/0 | Sayt |
| SSH | 22 | *Mening IP* | Serverni boshqarish (faqat sizning IP) |

**`wms-db-sg`** (RDS uchun):

| Turi | Port | Manba | Nima uchun |
|---|---|---|---|
| PostgreSQL | 5432 | `wms-web-sg` | Faqat bizning EC2 bazaga ulana oladi |

Baza Internetga umuman ochiq emas. Manba sifatida IP emas, boshqa security group ko'rsatilgan.

📸 Ikkala SG ning *Inbound rules* bo'limi.

## 5. RDS (PostgreSQL)

**RDS → Create database → Standard create**

| Sozlama | Qiymat |
|---|---|
| Engine | PostgreSQL 16 |
| Templates | **Free tier** |
| DB instance identifier | `wms-db` |
| Master username | `wms_admin` |
| Master password | kuchli parol (faqat serverdagi `.env` ga yoziladi) |
| Instance | db.t4g.micro yoki db.t3.micro |
| Storage | 20 GB gp2, *Storage autoscaling* — o'chiq |
| Public access | **No** |
| VPC security group | `wms-db-sg` |
| Initial database name | `wms` |
| Backup retention | 1 kun |
| Performance Insights, Enhanced monitoring | o'chiq (pullik bo'lishi mumkin) |

📸 Baza *Connectivity & security* sahifasi (Endpoint, Public access = No).

## 6. EC2

**EC2 → Launch instance**

| Sozlama | Qiymat |
|---|---|
| Nomi | `wms-server` |
| AMI | Ubuntu Server 24.04 LTS |
| Instance type | **t3.micro** (Free tier eligible) |
| Key pair | yangi `wms-key` (.pem faylni xavfsiz saqlang) |
| Security group | `wms-web-sg` |
| Storage | 30 GB gp3 |
| Advanced → IAM instance profile | `wms-ec2-role` |

Keyin **Elastic IPs → Allocate → Associate** — shu instance'ga. IP o'zgarmas bo'ladi.

📸 Instance *Details* sahifasi (type, AMI, IAM role, security group).

## 7. Domen (eskiz.uz)

my.eskiz.uz → Domen → `vangogh.uz` → **DNS yozuvlar**:

| Turi | Nomi | Qiymat |
|---|---|---|
| A | @ | Elastic IP |
| A | www | Elastic IP |

DNS yangilanishi 5 daqiqadan bir necha soatgacha davom etadi. Tekshirish: `ping vangogh.uz`.

## 8. Serverni tayyorlash

```bash
ssh -i wms-key.pem ubuntu@<ELASTIC_IP>
```

O'z kompyuteringizdan kerakli fayllarni serverga yuboring (loyiha papkasida turib):

```bash
scp -i wms-key.pem deploy/server-setup.sh deploy/cloudwatch-agent.json ubuntu@<ELASTIC_IP>:~
```

Serverda:

```bash
sudo bash ~/server-setup.sh
```

So'ng `.env` faylini yarating:

```bash
nano /opt/wms/.env
```

```ini
DEBUG=False
SECRET_KEY=<uzun tasodifiy qator: python3 -c "import secrets; print(secrets.token_urlsafe(50))">
ALLOWED_HOSTS=vangogh.uz,www.vangogh.uz,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://vangogh.uz,https://www.vangogh.uz
SECURE_COOKIES=True

DB_HOST=<RDS endpoint>
DB_PORT=5432
DB_NAME=wms
DB_USER=wms_admin
DB_PASSWORD=<RDS paroli>
DB_SSLMODE=require

USE_S3=True
AWS_S3_BUCKET=vangogh-wms-files
AWS_REGION=eu-central-1

SITE_NAME=OmborHub
CONTACT_PHONE=+998 88 803 30 24
CONTACT_EMAIL=jasminaismoilova279@gmail.com
```

```bash
chmod 600 /opt/wms/.env
```

HTTPS sertifikat (80-port bo'sh paytda, ya'ni birinchi deploydan oldin):

```bash
sudo certbot certonly --standalone -d vangogh.uz -d www.vangogh.uz \
  -m jasminaismoilova279@gmail.com --agree-tos -n
```

Sertifikat 90 kunda yangilanadi. Avtomatik yangilash uchun:

```bash
echo '0 3 * * * root certbot renew --webroot -w /var/www/certbot --quiet --deploy-hook "docker service update --force wms_nginx"' | sudo tee /etc/cron.d/certbot-renew
```

CloudWatch Agent:

```bash
sudo cp ~/cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/config.json
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json -s
```

## 9. GitHub Actions (CD)

### 9.1. GitHub uchun AWS role (kalitsiz kirish)

1. **IAM → Identity providers → Add provider → OpenID Connect**
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
2. **IAM → Roles → Create role → Web identity** → shu provider. Trust policy'ni
   [iam-github-trust.json](iam-github-trust.json) bilan almashtiring.
3. Ruxsat: [iam-github-policy.json](iam-github-policy.json) (`WEB_SG_ID` — `wms-web-sg` ning ID si).
   Role nomi: `wms-github-deploy`.

Bu role faqat bitta ish qila oladi: `wms-web-sg` ga SSH qoidasini qo'shish va olib tashlash.
Deploy paytida GitHub serveriga 22-port bir necha daqiqaga ochiladi, keyin yopiladi.

### 9.2. Deploy kaliti

Serverda deploy uchun alohida SSH kalit yarating:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy      # shu matn GitHub secret'ga qo'yiladi, keyin faylni o'chiring
rm ~/.ssh/github_deploy
```

### 9.3. GitHub sozlamalari

Repo → **Settings → Environments → New environment** → `production`.

Repo → **Settings → Secrets and variables → Actions**:

| Turi | Nomi | Qiymat |
|---|---|---|
| Secret | `SSH_HOST` | `vangogh.uz` |
| Secret | `SSH_USER` | `ubuntu` |
| Secret | `SSH_KEY` | 9.2 dagi yopiq kalit matni |
| Secret | `AWS_DEPLOY_ROLE_ARN` | `wms-github-deploy` role ARN |
| Variable | `AWS_REGION` | `eu-central-1` |
| Variable | `SECURITY_GROUP_ID` | `wms-web-sg` ID |
| Variable | `DEPLOY_ENABLED` | `true` |

GHCR dagi image'lar private bo'lsa, server ularni deploy vaqtidagi vaqtinchalik token bilan
yuklab oladi — qo'shimcha sozlash kerak emas.

Endi `main` ga har bir push → testlar → image → serverga avtomatik deploy.

### 9.4. Birinchi ishga tushirish

Birinchi deploy'dan keyin serverda platforma admini yarating:

```bash
docker exec -it $(docker ps -q -f name=wms_web | head -1) python manage.py createsuperuser
```

Namoyish ma'lumotlari kerak bo'lsa:

```bash
docker exec -it $(docker ps -q -f name=wms_web | head -1) python manage.py seed_demo
```

## 10. CloudWatch

1. **CloudWatch → Alarms → Create alarm** (3 tagacha, hammasi bepul):
   - `EC2 CPUUtilization > 80%` 5 daqiqa davomida
   - `EC2 StatusCheckFailed >= 1`
   - `RDS FreeStorageSpace < 2 GB`

   Xabar: SNS topic → email.
2. **CloudWatch → Dashboards → Create**: EC2 CPU, `WMS/mem_used_percent`, RDS CPU va
   `DatabaseConnections` grafiklari.
3. **CloudWatch → Log groups → `/wms/app`** — Nginx, Django va autoscaler loglari.

📸 Dashboard va autoscaler logi (`SCALE: 2 -> 3`).

## 11. Load balancing va autoscalingni namoyish qilish

Serverda:

```bash
docker service ls                     # wms_web 2/2
docker service logs -f wms_autoscaler
```

O'z kompyuteringizda:

```bash
python deploy/loadtest.py https://vangogh.uz/ --seconds 300 --workers 40
```

Bir-ikki daqiqada autoscaler logida `SCALE: 2 -> 3` chiqadi, `docker service ls` da `wms_web 3/3`
ko'rinadi. Test oxirida jadvalda so'rovlar bir nechta konteyner (IP) ga taqsimlangani ko'rinadi.
Yuklama tushgach, ~3 daqiqada replikalar yana 2 taga qaytadi.

## 12. Himoyadan keyin resurslarni o'chirish

O'qituvchi ruxsat bergandan keyin: EC2 (Terminate) → RDS (Delete, snapshotsiz) → S3 (Empty +
Delete) → Elastic IP (Release) → CloudWatch alarm va log group → IAM role va OIDC provider.
