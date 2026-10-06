from config.database_config import DBConnection
import mysql.connector
import pandas as pd
from pathlib import Path

import logging
logger = logging.getLogger(__name__)


UPSERT_INTO_CITIES = """
    INSERT INTO cities (city_id, city_name, country, lat, lon, timezone_offset)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            city_name = VALUES(city_name),
            country = VALUES(country),
            lat = VALUES(lat),
            lon = VALUES(lon),
            timezone_offset = VALUES(timezone_offset)
"""

INSERT_INTO_WEATHER_READING = """
    INSERT IGNORE INTO weather_reading (city_id, temp, feels_like, temp_min, temp_max, pressure, humidity,
    sea_level, grnd_level,
    wind_speed, wind_deg, wind_gust,
    cloud_pct, visibility,
    weather_id, weather_main, weather_description, weather_icon,
    recorded_at, sunrise, sunset)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s)
    """


def _clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value


def upsert_cities(conn, row: dict) -> None:
    """ Insert cities if new, update if it is already exist"""
    cursor = conn.cursor()
    try:
        params = (
            _clean_value(row["city_id"]),
            _clean_value(row["city_name"]),
            _clean_value(row["country"]),
            _clean_value(row["lat"]),
            _clean_value(row["lon"]),
            _clean_value(row["timezone_offset"]),
        )

        cursor.execute(UPSERT_INTO_CITIES, params)
    finally:
        cursor.close()


def insert_reading(conn, row: dict) -> bool:
    """ Insert one weather reading.
    Returns True if a new row was inserted, False if it was skipped (duplicate)"""
    cursor = conn.cursor()
    try:
        params = (
            _clean_value(row["city_id"]),
            _clean_value(row["temp"]),
            _clean_value(row["feels_like"]),
            _clean_value(row["temp_min"]),
            _clean_value(row["temp_max"]),
            _clean_value(row["pressure"]),
            _clean_value(row["humidity"]),
            _clean_value(row["sea_level"]),
            _clean_value(row["grnd_level"]),
            _clean_value(row["wind_speed"]),
            _clean_value(row["wind_deg"]),
            _clean_value(row["wind_gust"]),
            _clean_value(row["cloud_pct"]),
            _clean_value(row["visibility"]),
            _clean_value(row["weather_id"]),
            _clean_value(row["weather_main"]),
            _clean_value(row["weather_description"]),
            _clean_value(row["weather_icon"]),
            _clean_value(row["recorded_at"]),
            _clean_value(row["sunrise"]),
            _clean_value(row["sunset"])
        )
        cursor.execute(INSERT_INTO_WEATHER_READING, params)
        return cursor.rowcount > 0
    finally:
        cursor.close()

def  execute_load_pipeline(df: pd.DataFrame) -> int:

    if df is None or df.empty:
        logger.warning("No data to load")
        return 0

    inserted = 0
    with DBConnection() as conn:
        if conn is None:
            logger.error("No database connection, aborting load")
            return 0

        try:
            for city_id in df["city_id"].unique():
                city_row = df.loc[df["city_id"] == city_id].iloc[0]
                upsert_cities(conn, city_row.to_dict())

            for _, row in df.iterrows():
                if insert_reading(conn, row.to_dict()):
                    inserted += 1

            conn.commit()
            logger.info("Loaded %d new reading(s) outs of %d row(s)", inserted, len(df))

        except mysql.connector.Error as err:
            conn.rollback()
            logger.error("Load failed, rolled back: %s", err)
            return 0

    return inserted

if __name__ == "__main__":
    from config.logging_config import setup_logging
    from src.transform import execute_transform_pipeline

    setup_logging()
    test_file = Path("data/raw_data/data_1790423088.json")
    df_test = execute_transform_pipeline(test_file)
    if df_test is not None:
        execute_load_pipeline(df_test)
