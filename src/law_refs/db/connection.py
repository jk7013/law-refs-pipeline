from contextlib import contextmanager
import psycopg2

from .config import DbConfig


@contextmanager
def get_connection(config: DbConfig):
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

