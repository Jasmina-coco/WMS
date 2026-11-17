#!/usr/bin/env bash
# Serverdagi deploy agenti (CD ning "pull" usuli).
#
# GitHub Actions faqat Docker image yig'ib, GHCR ga :latest tegi bilan yuklaydi.
# Bu skript har daqiqada (systemd timer) GHCR ni tekshiradi va yangi versiya
# chiqqan bo'lsa: migratsiya -> rolling update. Shu tufayli GitHub'da AWS kaliti
# ham, SSH kaliti ham saqlanmaydi, serverning 22-porti esa umuman yopiq.
#
#   omborhub-deploy.sh           — yangi versiya bo'lsa deploy qiladi
#   omborhub-deploy.sh --force   — versiya o'zgarmagan bo'lsa ham qayta deploy

set -euo pipefail

PREFIX=ghcr.io/jasmina-coco
DIR=/opt/omborhub
STATE=$DIR/deployed-web

# Oldingi deploy hali tugamagan bo'lsa, ikkinchisini boshlamaymiz
exec 9>/var/lock/omborhub-deploy.lock
flock -n 9 || exit 0

digest() {
    docker pull -q "$PREFIX/$1:latest" >/dev/null
    docker image inspect --format '{{index .RepoDigests 0}}' "$PREFIX/$1:latest"
}

WEB=$(digest wms-web)
if [ "${1:-}" != "--force" ] && [ "$(cat "$STATE" 2>/dev/null)" = "$WEB" ]; then
    exit 0
fi

echo "Yangi versiya: $WEB"
NGINX=$(digest wms-nginx)
SCALER=$(digest wms-autoscaler)

# Stack fayli va nginx konfiguratsiyasi web image ichida keladi —
# shunda kod va infratuzilma sozlamalari doim bir xil versiyada bo'ladi
CID=$(docker create "$WEB")
docker cp "$CID:/app/deploy/docker-stack.yml" "$DIR/docker-stack.yml"
docker cp "$CID:/app/deploy/nginx/prod.conf" "$DIR/prod.conf"
docker rm "$CID" >/dev/null

echo "Migratsiya..."
docker run --rm --env-file "$DIR/.env" "$WEB" python manage.py migrate --noinput

echo "Rolling update..."
cd "$DIR"
WEB_IMAGE=$WEB NGINX_IMAGE=$NGINX SCALER_IMAGE=$SCALER CONF_VERSION=${WEB: -12} \
    docker stack deploy -c docker-stack.yml --prune --detach=false wms

echo "$WEB" > "$STATE"

# Eski, endi ishlatilmaydigan image'lar diskni to'ldirib qo'ymasin
docker image prune -af --filter "until=72h" >/dev/null || true
docker config ls -q --filter name=nginx_conf_ | xargs -r docker config rm >/dev/null 2>&1 || true
echo "Tayyor."
