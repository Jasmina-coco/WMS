"""
Autoscaling va load balancingni namoyish qilish uchun yuklama testi.

    python deploy/loadtest.py https://vangogh.uz/ --seconds 300 --workers 40

Skript ko'p oqimda so'rov yuboradi va oxirida qaysi konteyner nechta
so'rovga javob berganini (X-Served-By sarlavhasi) ko'rsatadi.
Shu vaqtda serverda `docker service ls` bilan replikalar oshganini kuzating.
"""

import argparse
import collections
import threading
import time
import urllib.request


def worker(url, deadline, stats, lock):
    while time.time() < deadline:
        started = time.time()
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                response.read()
                served_by = response.headers.get("X-Served-By", "?")
                status = response.status
        except Exception:
            served_by, status = "xato", 0
        with lock:
            stats["servers"][served_by] += 1
            stats["statuses"][status] += 1
            stats["times"].append(time.time() - started)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--workers", type=int, default=30)
    args = parser.parse_args()

    stats = {"servers": collections.Counter(), "statuses": collections.Counter(), "times": []}
    lock = threading.Lock()
    deadline = time.time() + args.seconds
    threads = [
        threading.Thread(target=worker, args=(args.url, deadline, stats, lock), daemon=True)
        for _ in range(args.workers)
    ]
    print(f"{args.workers} oqim, {args.seconds} soniya: {args.url}")
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    times = sorted(stats["times"]) or [0]
    total = len(stats["times"])
    print(f"\nJami so'rovlar: {total} ({total / args.seconds:.1f} so'rov/s)")
    print(
        f"O'rtacha javob: {sum(times) / len(times) * 1000:.0f} ms, "
        f"95%: {times[int(len(times) * 0.95) - 1] * 1000:.0f} ms"
    )
    print("Status kodlari:", dict(stats["statuses"]))
    print("\nQaysi konteyner javob berdi:")
    for server, count in stats["servers"].most_common():
        print(f"  {server:<22} {count}")


if __name__ == "__main__":
    main()
