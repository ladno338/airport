import os
import time
import psycopg2

from django.core.management import BaseCommand
from django.db.utils import OperationalError


class Command(BaseCommand):
    MAX_RETRIES = 20
    RETRY_INTERVAL = 1

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_conn = None
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                conn = psycopg2.connect(
                    dbname=os.environ["POSTGRES_DB"],
                    user=os.environ["POSTGRES_USER"],
                    password=os.environ["POSTGRES_PASSWORD"],
                    host=os.environ["POSTGRES_HOST"],
                )
                conn.close()
                db_conn = True
                break
            except OperationalError as e:
                self.stdout.write(f"Database unavailable: {str(e)}")
                self.stdout.write("Retrying...")
                time.sleep(self.RETRY_INTERVAL)
                retries += 1

        if db_conn:
            self.stdout.write(self.style.SUCCESS("Database is available!"))
        else:
            self.stdout.write(
                self.style.ERROR("Failed to connect to the database after max retries")
            )
