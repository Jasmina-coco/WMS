# AWS infratuzilmasi

Sayt: **https://vangogh.uz** · Region: **Sidney (`ap-southeast-2`)**

AWS akkaunti tashkilot siyosati (Service Control Policy) bilan faqat Sidney regioniga
cheklangan, shuning uchun hamma resurslar shu yerda. Faqat Free Tier / kredit doirasidagi
xizmatlar ishlatilgan.

> Parol, access key va boshqa maxfiy ma'lumotlar GitHub'da, hisobotda va skrinshotlarda
> bo'lmasligi kerak. Skrinshotda ko'rinib qolsa, qora rang bilan yashiring.

## Resurslar

| Xizmat | Resurs | Sozlama |
|---|---|---|
| EC2 | `wms-web` (`i-00b0566de3a0b03a7`) | t3.micro, Ubuntu 24.04, 1 GB swap, Docker Swarm |
| Elastic IP | `15.134.247.142` | EC2 ga biriktirilgan |
| RDS | `wms-db` | PostgreSQL 18, db.t4g.micro, 20 GB, Public access = **No** |
| Secrets Manager | `rds!db-…` | RDS master paroli, RDS o'zi har 7 kunda almashtiradi |
| S3 | `wms-vangogh-files-132074799573` | Private, Block Public Access, SSE-S3 |
| IAM | `wms-ec2-role` | EC2 instance profile (pastda) |
| Security Groups | `wms-web-sg`, `wms-db-sg` | pastda |
| CloudWatch | dashboard `WMS`, 3 alarm, log group `/wms/app` | pastda |
| SNS | `wms-alerts` | alarm xabarlari emailga |
| Budgets | `My Zero-Spend Budget` | har qanday xarajatda ogohlantirish |
| DNS | eskiz.uz | `vangogh.uz` A → Elastic IP, `www` CNAME, `wms` A |

## Tarmoq (Security Groups)

**`wms-web-sg`** (EC2):

| Port | Manba | Vazifasi |
|---|---|---|
| 80 | 0.0.0.0/0 | HTTPS ga yo'naltirish va Let's Encrypt tekshiruvi |
| 443 | 0.0.0.0/0 | Sayt |

**22 (SSH) yopiq.** Serverga AWS Systems Manager (Session Manager / Run Command) orqali
kiriladi: kalit kerak emas, port ochish kerak emas, har bir buyruq CloudTrail'da qayd etiladi.

**`wms-db-sg`** (RDS):

| Port | Manba | Vazifasi |
|---|---|---|
| 5432 | `wms-web-sg` | Faqat bizning EC2 bazaga ulana oladi |

## IAM — `wms-ec2-role`

Eng kam ruxsat tamoyili bo'yicha:

- [iam-ec2-policy.json](iam-ec2-policy.json) — faqat bitta S3 bucket va faqat RDS secret'ini o'qish
- `CloudWatchAgentServerPolicy` — metrika va loglarni yuborish
- `AmazonSSMManagedInstanceCore` — Systems Manager orqali boshqarish

Serverda va kodda access key yo'q: boto3 va Docker vaqtinchalik kalitlarni role'dan oladi.

## Baza paroli

Parol hech qayerga yozilmagan. Ilova `DB_SECRET_ARN` bo'yicha Secrets Manager'dan oladi
(`apps/core/db/base.py`), 10 daqiqa keshlaydi. RDS parolni almashtirsa, ulanish rad etiladi —
ilova yangi parolni olib, qayta ulanadi.

## Deploy (CD)

```
git push main → GitHub Actions: lint → test → 3 ta image → GHCR (:latest)
                                                              │
EC2: systemd timer har daqiqada → omborhub-deploy.sh ─────────┘
     yangi image bo'lsa: migratsiya → docker stack deploy (rolling update)
GitHub Actions: verify → https://vangogh.uz/health/ da yangi commit SHA chiqquncha kutadi
```

Nega shunday: tashkilot siyosati GitHub OIDC orqali AWS ga kirishni taqiqlaydi. Pull usulida
GitHub'da hech qanday AWS yoki SSH kaliti saqlanmaydi, serverga kiruvchi port ham kerak emas.

Serverdagi fayllar:

| Fayl | Vazifasi |
|---|---|
| `/opt/omborhub/.env` | sozlamalar (`chmod 600`, `SECRET_KEY` serverda generatsiya qilingan) |
| `/opt/omborhub/omborhub-deploy.sh` | deploy agenti |
| `/etc/systemd/system/omborhub-deploy.timer` | har daqiqada ishga tushiradi |
| `/etc/cron.d/omborhub-certbot` | HTTPS sertifikatini yangilash |
| `/opt/omborhub/src` | repo nusxasi (faqat server-setup uchun) |

## Serverga kirish

AWS konsol → **EC2 → Instances → wms-web → Connect → Session Manager → Connect**.

Yoki terminaldan:

```bash
aws ssm start-session --target i-00b0566de3a0b03a7 --region ap-southeast-2
```

Foydali buyruqlar:

```bash
sudo docker service ls                         # replikalar soni
sudo docker service logs -f wms_autoscaler     # autoscaler qarorlari
sudo journalctl -u omborhub-deploy -n 50       # oxirgi deploylar
sudo /opt/omborhub/omborhub-deploy.sh --force  # qo'lda qayta deploy
```

## Load balancing va autoscalingni namoyish qilish

O'z kompyuteringizda:

```bash
python deploy/loadtest.py https://vangogh.uz/ --seconds 240 --workers 40
```

Shu paytda CloudWatch → Dashboards → **WMS** da CPU ko'tariladi, "Autoscaler qarorlari"
jadvalida `SCALE: 2 -> 3` chiqadi. Test oxirida jadvalda so'rovlar bir nechta konteyner IP siga
taqsimlangani ko'rinadi. Yuklama tushgach, ~3 daqiqada replikalar 2 taga qaytadi.

## Himoya uchun skrinshotlar

1. EC2 instance → Details (type, AMI, IAM role, security group)
2. RDS → Connectivity & security (Public access = No)
3. Brauzerda `https://vangogh.uz/health/` → `"database": true`
4. S3 bucket ichidagi `companies/…` fayllari va tizimdagi tovar rasmi
5. Security Groups → Inbound rules (ikkalasi)
6. IAM → `wms-ec2-role` → Permissions
7. CloudWatch → Dashboard `WMS` va alarm'lar
8. GitHub Actions → muvaffaqiyatli run (`verify` bosqichi bilan)

## Himoyadan keyin resurslarni o'chirish

O'qituvchi ruxsat bergandan keyin: EC2 (Terminate) → RDS (Delete, snapshotsiz) → S3 (Empty +
Delete) → Elastic IP (Release) → Secrets Manager secret → CloudWatch alarm, dashboard va log
group → SNS topic → IAM role.
