#!/usr/bin/env bash
# EC2 (Ubuntu 24.04) serverni bir marta tayyorlash.
# Loyiha papkasidan: sudo bash deploy/server-setup.sh
# (Serverga SSH emas, AWS Systems Manager orqali kiriladi.)
set -euo pipefail

echo "== 1. Swap: t3.micro da 1 GB RAM, xotira yetmay qolmasligi uchun 1 GB swap =="
if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

echo "== 2. Docker =="
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh

echo "== 3. Docker Swarm (bitta tugunli) =="
docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active || docker swarm init

echo "== 4. Papkalar va certbot =="
mkdir -p /opt/omborhub /var/www/certbot
command -v certbot >/dev/null || { apt-get update -y && apt-get install -y certbot; }

echo "== 5. Deploy agenti (har daqiqada yangi versiyani tekshiradi) =="
install -m 755 deploy/agent/omborhub-deploy.sh /opt/omborhub/omborhub-deploy.sh
install -m 644 deploy/agent/omborhub-deploy.service /etc/systemd/system/
install -m 644 deploy/agent/omborhub-deploy.timer /etc/systemd/system/
systemctl daemon-reload

echo "== 6. Sertifikatni avtomatik yangilash =="
cat > /etc/cron.d/omborhub-certbot <<'CRON'
0 3 * * * root certbot renew --webroot -w /var/www/certbot --quiet --deploy-hook "docker service update --force wms_nginx"
CRON

echo "Tayyor. /opt/omborhub/.env ni yarating, so'ng: systemctl enable --now omborhub-deploy.timer"
