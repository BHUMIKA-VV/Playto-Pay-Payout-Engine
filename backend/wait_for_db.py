import os
import time
import sys

import psycopg2
from psycopg2 import OperationalError


def wait_for_db(host: str, port: int, dbname: str, user: str, password: str, retries: int = 30, delay: int = 2) -> None:
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
            )
            conn.close()
            print(f"Postgres is available after {attempt} attempt(s)")
            return
        except OperationalError as error:
            print(f"Postgres unavailable, waiting ({attempt}/{retries})... {error}")
            time.sleep(delay)
    print("Postgres did not become available in time", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    wait_for_db(
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "playto"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    )
