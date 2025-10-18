from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS donations_donation CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS donations_donationtype CASCADE;")
    cursor.execute("DELETE FROM django_migrations WHERE app='donations';")
print("Tablas y migraciones de donations eliminadas.") 