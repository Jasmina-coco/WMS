# Ikki bosqichli build:
#   web   — Django + Gunicorn
#   nginx — Nginx + yig'ilgan statik fayllar (CSS, JS)

FROM python:3.12-slim AS web

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# gettext — tarjima fayllarini (.po -> .mo) kompilyatsiya qilish uchun
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval faqat requirements — kod o'zgarganda kutubxonalar qayta o'rnatilmaydi (kesh)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && SECRET_KEY=build-only python manage.py compilemessages --locale ru

# Konteyner root huquqida ishlamasligi kerak
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

EXPOSE 8000

# Docker shu tekshiruv orqali nosoz konteynerni aniqlaydi va almashtiradi
HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=4)"

CMD ["gunicorn", "config.wsgi:application", "-c", "deploy/gunicorn.conf.py"]


FROM nginx:1.28-alpine AS nginx

COPY --from=web /app/staticfiles /usr/share/nginx/static
# Lokal konfiguratsiya. Serverda (Swarm) uning o'rniga prod.conf ulanadi
COPY deploy/nginx/local.conf /etc/nginx/conf.d/default.conf
