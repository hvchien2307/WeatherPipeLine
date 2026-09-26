import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv


load_dotenv()

mysql_host = os.getenv("MYSQL_HOST")
mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_database = os.getenv("MYSQL_DATABASE")

config = {
    'user': mysql_user,
    'password': mysql_password,
    'host': mysql_host,
    'database': mysql_database,
    'raise_on_warnings': True
}


def db_connect():
    try:
        db_connection = mysql.connector.connect(** config)
        print("Database connection established")
        return db_connection
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return None


def db_disconnect(db_connection, cursor = None):
    if cursor:
        try:
            cursor.close()
        except mysql.connector.Error:
            pass

    if db_connection and db_connection.is_connected():
        db_connection.close()
        print("Database connection closed")

