"""
Docker Swarm uchun oddiy autoscaler.

Swarm o'zi yuklamaga qarab konteyner qo'shmaydi — faqat berilgan sonni
ushlab turadi. Shuning uchun bu skript har 30 soniyada web konteynerlarining
CPU yuklamasini o'lchaydi va replikalar sonini o'zgartiradi:

    o'rtacha CPU > 70%  (ketma-ket 2 marta)  ->  +1 replika
    o'rtacha CPU < 25%  (ketma-ket 5 marta)  ->  -1 replika

Docker bilan /var/run/docker.sock orqali gaplashamiz (Docker Engine API).
Faqat Pythonning standart kutubxonasi ishlatilgan — qo'shimcha paket yo'q.
"""

import http.client
import json
import logging
import os
import socket
import time
from urllib.parse import quote

SERVICE = os.environ.get("SERVICE_NAME", "wms_web")
MIN_REPLICAS = int(os.environ.get("MIN_REPLICAS", "2"))
MAX_REPLICAS = int(os.environ.get("MAX_REPLICAS", "4"))
SCALE_UP_AT = float(os.environ.get("SCALE_UP_CPU", "70"))
SCALE_DOWN_AT = float(os.environ.get("SCALE_DOWN_CPU", "25"))
INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))
COOLDOWN = int(os.environ.get("COOLDOWN", "120"))
UP_CHECKS = 2
DOWN_CHECKS = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s autoscaler: %(message)s")
log = logging.getLogger()


class DockerSocketConnection(http.client.HTTPConnection):
    """HTTP so'rovni TCP emas, Docker'ning unix socket'i orqali yuboradi."""

    def __init__(self, path="/var/run/docker.sock"):
        super().__init__("localhost")
        self.socket_path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


def docker(method, path, body=None):
    conn = DockerSocketConnection()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    if response.status >= 400:
        raise RuntimeError(f"Docker API {method} {path}: {response.status} {data[:200]!r}")
    return json.loads(data) if data else None


def get_service():
    return docker("GET", f"/services/{SERVICE}")


def cpu_limit(service):
    """Bitta konteynerga ajratilgan CPU (masalan 0.5). Limit yo'q bo'lsa — 1 yadro."""
    resources = service["Spec"]["TaskTemplate"].get("Resources", {})
    nano = resources.get("Limits", {}).get("NanoCPUs")
    return nano / 1e9 if nano else 1.0


def running_containers():
    filters = quote(json.dumps({"label": [f"com.docker.swarm.service.name={SERVICE}"]}))
    return docker("GET", f"/containers/json?filters={filters}")


def container_cpu_percent(container_id):
    """
    `docker stats` dagi CPU% ni hisoblash formulasi: konteyner sarflagan CPU
    vaqtining o'zgarishini butun tizim CPU vaqtining o'zgarishiga bo'lamiz.
    Natija — bitta yadroga nisbatan foiz (100% = bitta yadro to'liq band).
    """
    stats = docker("GET", f"/containers/{container_id}/stats?stream=false")
    cpu, pre = stats["cpu_stats"], stats["precpu_stats"]
    cpu_delta = cpu["cpu_usage"]["total_usage"] - pre["cpu_usage"]["total_usage"]
    system_delta = cpu.get("system_cpu_usage", 0) - pre.get("system_cpu_usage", 0)
    cores = cpu.get("online_cpus") or 1
    if system_delta <= 0 or cpu_delta < 0:
        return 0.0
    return cpu_delta / system_delta * cores * 100


def average_load(service):
    """Konteynerlarning o'rtacha yuklamasi, ularga ajratilgan limitga nisbatan (0–100%)."""
    containers = running_containers()
    if not containers:
        return None
    limit = cpu_limit(service)
    loads = [container_cpu_percent(c["Id"]) / limit for c in containers]
    return sum(loads) / len(loads)


def set_replicas(service, replicas):
    spec = service["Spec"]
    spec["Mode"]["Replicated"]["Replicas"] = replicas
    version = service["Version"]["Index"]
    docker("POST", f"/services/{service['ID']}/update?version={version}", spec)


def main():
    log.info(
        "ishga tushdi: servis=%s, replikalar %s..%s, chegaralar %.0f%%/%.0f%%",
        SERVICE,
        MIN_REPLICAS,
        MAX_REPLICAS,
        SCALE_DOWN_AT,
        SCALE_UP_AT,
    )
    high_streak = low_streak = 0
    last_change = 0.0

    while True:
        try:
            service = get_service()
            replicas = service["Spec"]["Mode"]["Replicated"]["Replicas"]
            load = average_load(service)

            if load is None:
                log.info("konteynerlar topilmadi, kutamiz")
            else:
                high_streak = high_streak + 1 if load > SCALE_UP_AT else 0
                low_streak = low_streak + 1 if load < SCALE_DOWN_AT else 0
                cooling = time.time() - last_change < COOLDOWN
                log.info("replikalar=%s, o'rtacha CPU=%.1f%%", replicas, load)

                target = replicas
                if replicas < MIN_REPLICAS:
                    target = MIN_REPLICAS
                elif not cooling and high_streak >= UP_CHECKS and replicas < MAX_REPLICAS:
                    target = replicas + 1
                elif not cooling and low_streak >= DOWN_CHECKS and replicas > MIN_REPLICAS:
                    target = replicas - 1

                if target != replicas:
                    set_replicas(service, target)
                    last_change = time.time()
                    high_streak = low_streak = 0
                    log.info("SCALE: %s -> %s replika", replicas, target)
        except Exception as error:  # noqa: BLE001 — skript to'xtab qolmasligi kerak
            log.error("xato: %s", error)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
