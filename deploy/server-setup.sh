#!/usr/bin/env bash
# EC2 (Ubuntu 24.04) serverni bir marta tayyorlash.
# Ishlatish:  sudo bash server-setup.sh
set -euo pipefail

echo "== 1. Swap (t3.micro da 1 GB RAM, xotira yetmay qolmasligi uchun 2 GB swap) =="
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

echo "== 2. Docker =="
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
usermod -aG docker ubuntu

echo "== 3. Docker Swarm (bitta tugunli) =="
docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active || docker swarm init

echo "== 4. Loyiha papkalari =="
mkdir -p /opt/wms /var/www/certbot
chown ubuntu:ubuntu /opt/wms

echo "== 5. certbot (HTTPS sertifikat) =="
apt-get update -y
apt-get install -y certbot

echo "== 6. CloudWatch Agent (RAM va disk metrikalari uchun) =="
if [ ! -f /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl ]; then
  curl -fsSLo /tmp/cwagent.deb \
    https://amazoncloudwatch-agent.s3.amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
  dpkg -i /tmp/cwagent.deb
fi

echo "Tayyor. Keyingi qadam: docs/aws/README.md dagi 7-bo'lim."
