from django.http import JsonResponse
from django.db import connection

def db_version(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
    return JsonResponse({'version': version})

