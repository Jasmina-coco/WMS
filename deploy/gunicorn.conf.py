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

# Nginx ulanishlarni qayta ishlatadi (keepalive). Gunicorn ulanishni Nginx'dan
# uzoqroq ushlab turishi kerak, aks holda Nginx yopilgan ulanishga so'rov yuborib,
# foydalanuvchi 502 xato oladi.
keepalive = 75

# Xotira asta-sekin oqib ketmasligi uchun worker vaqti-vaqti bilan yangilanadi.
# Juda tez-tez bo'lmasin: har yangilanish ochiq ulanishlarni uzadi.
max_requests = 5000
max_requests_jitter = 500

accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(M)sms'
