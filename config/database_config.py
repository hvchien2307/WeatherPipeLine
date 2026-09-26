import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv
import logging
from typing import Optional

from mysql.connector.abstracts import MySQLConnectionAbstract

load_dotenv()
logger = logging.getLogger(__name__)
connection: Optional[MySQLConnectionAbstract]

#Declare env variables
MYSQL_USER=os.getenv("MYSQL_USER")
MYSQL_HOST=os.getenv("MYSQL_HOST")
MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE=os.getenv("MYSQL_DATABASE")

DB_CONFIG = {
    'user': MYSQL_USER,
    'password': MYSQL_PASSWORD,
    'host': MYSQL_USER,
    'database': MYSQL_DATABASE,
    'raise_on_warnings': True
}


def is_validate_env() -> bool | None:
    env_params = {
        "MYSQL_USER": MYSQL_USER,
        "MYSQL_HOST": MYSQL_HOST,
        "MYSQL_PASSWORD": MYSQL_PASSWORD,
        "MYSQL_DATABASE": MYSQL_DATABASE
    }
    missing = [key for key, val in env_params.items() if val is None]
    if missing:
        logger.error("Missing requires env vars for database '%s' connection: %s", MYSQL_DATABASE, ", ".join(missing))
        return None
    return True


def db_connect() -> mysql.connector.MySQLConnection | None:
    if is_validate_env() is None:
        return None

    try:
        db_connection = mysql.connector.connect(** DB_CONFIG)
        logger.info("Database connection established to '%s'", MYSQL_DATABASE)
        return db_connection

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Access Denied: check your MYSQL username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("Database '%s' does not exist", MYSQL_DATABASE)
        else:
            logger.error("MySQL connection error: %s", err)
        return None


def db_disconnect(db_connection , cursor = None) -> None:
    if cursor is not None:
        try:
            cursor.close()
        except mysql.connector.Error as err:
            logger.warning("Error closing cursor: %s", err)

    if db_connection and db_connection.is_connected():
        db_connection.close()
        logger.info("Database '%s' connection closed", MYSQL_DATABASE)


class DBConnection:
    """Context manager wrapper around db_connect/db_disconnect.

        USAGE:
            with DBConnection() as conn:
                if conn is None:
                    return
                cursor = conn.cursor()
                ............

    """

    def __enter__(self) -> mysql.connector.MySQLConnection | None:
        self.conn = db_connect()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        db_disconnect(self.conn)