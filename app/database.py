import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

REQUIRED_SETTINGS = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")


def get_db_connection():
    # An empty password is allowed (local development), a missing
    # variable is not.
    missing = [name for name in REQUIRED_SETTINGS if os.getenv(name) is None]
    if missing:
        raise RuntimeError(
            "Missing database settings in .env: " + ", ".join(missing)
        )

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4"
    )


@contextmanager
def db_cursor(dictionary=True):
    """Yield (connection, cursor); always closes, rolls back on error.

    Usage:
        with db_cursor() as (connection, cursor):
            cursor.execute(...)
            connection.commit()

    A `return` inside the block is fine: the connection is closed and
    anything not committed is discarded.
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=dictionary)

    try:
        yield connection, cursor

    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass  # the original error matters more
        raise

    finally:
        cursor.close()
        connection.close()