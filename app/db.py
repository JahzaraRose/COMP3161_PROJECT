import mysql.connector
import os
from dotenv import load_dotenv
from urllib.parse import unquote, urlparse
 
load_dotenv()


def _db_config():
    database_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "user": unquote(parsed.username) if parsed.username else None,
            "password": unquote(parsed.password) if parsed.password else None,
            "database": parsed.path.lstrip("/")
        }

    return {
        "host": os.getenv("DB_HOST") or os.getenv("MYSQLHOST"),
        "port": int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or 3306),
        "user": os.getenv("DB_USER") or os.getenv("MYSQLUSER"),
        "password": os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD"),
        "database": os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE")
    }


def get_db():
    conn = mysql.connector.connect(**_db_config())
    return conn
