# Gunicorn sozlamalari.
# t3.micro serverda xotira kam (1 GB), shuning uchun har bir konteynerda
# 2 ta worker va har birida 2 ta thread — bir vaqtda 4 ta so'rov.
# Ko'proq yuklama bo'lsa, worker sonini emas, konteynerlar sonini oshiramiz
# (buni autoscaler qiladi).

bind = "0.0.0.0:8000"
workers = 2
threads = 2
timeout = 30
graceful_timeout = 20

# Xotira asta-sekin oqib ketmasligi uchun worker har ~1000 so'rovdan keyin yangilanadi
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(M)sms'
