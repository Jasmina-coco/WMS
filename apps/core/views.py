from django.db import connection
from django.http import JsonResponse


def health(request):
    """
    Load balancer va Docker healthcheck shu manzilni tekshiradi.
    Baza javob bermasa 503 qaytadi va nosoz konteyner qayta ishga tushiriladi.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "error", "database": db_ok}, status=status)
