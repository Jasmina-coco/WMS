# OmborHub — omborlarni boshqarish tizimi (WMS)

Ko'p kompaniyalar uchun SaaS WMS: har bir kompaniya o'z omborlari, tovarlari va xodimlari bilan
ishlaydi, ma'lumotlar bir-biridan ajratilgan. Landing sahifadan ariza qoldiriladi, platforma
admini qo'ng'iroq qilib, kompaniya akkauntini ochadi.

**Texnologiyalar:** Python 3.12, Django 5.2, PostgreSQL 16, HTML/CSS/JS (frameworksiz),
Gunicorn, Nginx, Docker Swarm, GitHub Actions, AWS (EC2, RDS, S3, IAM, CloudWatch).

## Imkoniyatlar

- **Landing**: tizim haqida ma'lumot, ariza formasi (spamdan himoyalangan)
- **Platforma paneli** (`/panel/`): arizalar va statuslari, kompaniyalarni yaratish va bloklash
- **Omborlar va joylar**: ombor → zona → yacheyka (`A-01-03`)
- **Tovarlar**: SKU, kategoriya, shtrix-kod, minimal qoldiq, rasm (S3)
- **Kirim, chiqim (terish → jo'natish), ko'chirish**: hujjatlar, terish varag'i, fayl biriktirish
- **Inventarizatsiya**: sanoq, farqlar va qoldiqni tuzatish
- **Qoldiq va harakatlar jurnali**: har bir o'zgarish kim, qachon, qaysi hujjat bilan
- **Hisobotlar**: qoldiq, aylanma, kam qolgan tovarlar, xodimlar faolligi; CSV va PDF (print)
- **Rollar**: menejer o'z rollarini yaratadi, xodimlarga ruxsat va omborlarni biriktiradi
- **Tillar**: o'zbek va rus

## Lokal ishga tushirish

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # DB sozlamalarini to'g'rilang
createdb wms
python manage.py migrate
python manage.py compilemessages --locale ru
python manage.py seed_demo    # demo ma'lumotlar
python manage.py createsuperuser
python manage.py runserver
```

Demo loginlar: `demo_manager` / `demo_omborchi`, parol `demo12345`.

### Docker bilan (load balancing bilan)

```bash
docker compose up --build --scale web=3
```

Sayt: <http://localhost:8080>. Har bir javobning `X-Served-By` sarlavhasida qaysi konteyner
javob bergani ko'rinadi.

## Testlar va kod sifati

```bash
python manage.py test
black --check .
flake8
```

## Loyiha tuzilishi

```
apps/
  core/        umumiy: kompaniya bo'yicha filtr, ruxsatlar, S3 storage, healthcheck
  accounts/    kompaniya, foydalanuvchi, rollar
  landing/     landing sahifa va arizalar
  panel/       platforma admini paneli
  warehouses/  omborlar va joylar
  catalog/     tovarlar va kategoriyalar
  inventory/   qoldiq va harakatlar jurnali (qoldiqni o'zgartirishning yagona joyi)
  operations/  kirim, chiqim, ko'chirish, inventarizatsiya
  reports/     dashboard va hisobotlar
deploy/        Nginx, Gunicorn, Swarm stack, autoscaler, server sozlash
docs/          texnik topshiriq, AWS qo'llanma, bulut hisoboti
```

## Deploy

`main` branchga push → GitHub Actions: lint → testlar → Docker image'lar (GHCR) → EC2 ga rolling
update. Batafsil: [docs/aws/README.md](docs/aws/README.md).
