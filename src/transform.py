import json
from pathlib import Path
import pandas as pd
import logging


logger = logging.getLogger(__name__)

def convert_json_to_dict(filepath) -> dict | None:
    """Convert JSON file to Python Dict
    """

    try:
        with open(filepath, 'r', encoding="utf-8") as json_file:
            dict_data = json.load(json_file)
        return dict_data

    except OSError as ose:
        logger.error("Can not read JSON file '%s': %s", filepath, ose)
        return None

    except json.JSONDecodeError as decode_err:
        logger.error("JSON DATA inside '%s' is invalid (corrupted): %s", filepath, decode_err)
        return None


def load_json_file_to_dataframe(file_path) -> pd.DataFrame | None:
    """ Convert Python Dict to DataFrame
    """

    dict_data = convert_json_to_dict(file_path)
    if dict_data is None:
        return None

    try:
        df_data = pd.json_normalize(
            data = dict_data,
            record_path=["weather"],
            meta=[
                ["coord", "lon"],
                ["coord", "lat"],
                "base",
                ["main", "temp"],
                ["main", "feels_like"],
                ["main", "temp_min"],
                ["main", "temp_max"],
                ["main", "humidity"],
                ["main", "pressure"],
                ["main", "sea_level"],
                ["main", "grnd_level"],
                "visibility",
                ["wind", "speed"],
                ["wind", "deg"],
                ["wind", "gust"],
                ["clouds", "all"],
                "dt",
                ["sys", "country"],
                ["sys", "sunrise"],
                ["sys", "sunset"],
                "timezone",
                "id",
                "name"
            ],
            meta_prefix=None,
            record_prefix="weather_",
            errors="ignore"
        )

        logger.info("Data '%s' converted to DataFrame. Ready to transform", file_path)
        return df_data

    except Exception as err:
        logger.error("Error flattening data '%s' to DataFrame: %s", file_path, err)
        return None


# ----------------------- Main stage (TRANSFORM) ---------------------------
RENAME_MAP = {
    "id": "city_id",
    "name": "city_name",
    "coord.lat": "lat",
    "coord.lon": "lon",
    "sys.country": "country",
    "timezone": "timezone_offset",

    "main.temp": "temp",
    "main.feels_like": "feels_like",
    "main.temp_min": "temp_min",
    "main.temp_max": "temp_max",
    "main.pressure": "pressure",
    "main.humidity": "humidity",
    "main.sea_level": "sea_level",
    "main.grnd_level": "grnd_level",

    "wind.speed": "wind_speed",
    "wind.deg": "wind_deg",
    "wind.gust": "wind_gust",

    "clouds.all": "cloud_pct",

    "sys.sunset": "sunset",
    "sys.sunrise": "sunrise",

    "weather_id": "weather_id",
    "weather_main": "weather_main",
    "weather_description": "weather_description",
    "weather_icon": "weather_icon",
}

def rename_columns(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns=RENAME_MAP)
    return df


REQUIRED_COLS = [
        "city_id", "temp", "pressure", "humidity", "wind_speed",
        "cloud_pct", "weather_id", "weather_main", "weather_description",
        "dt"
    ]
def handler_null(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.dropna(subset=REQUIRED_COLS)
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d row(s) with missing required fields", dropped)

    return df


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    #Date-time types:
    df["recorded_at"] = pd.to_datetime(df["dt"], unit="s", utc=True)
    df["sunrise"] = pd.to_datetime(df["sunrise"], unit="s", utc=True)
    df["sunset"] = pd.to_datetime(df["sunset"], unit="s", utc=True)

    #Float types
    float_cols = ["temp", "feels_like", "temp_min", "temp_max",
                  "wind_speed", "wind_gust"]

    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    #Int types:
    int_cols = ["pressure", "humidity", "sea_level", "grnd_level",
                "wind_deg", "visibility", "cloud_pct", "city_id", "weather_id"]
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    return df


def handler_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(subset=["city_id", "recorded_at"], keep="first")
    after = len(df)
    dropped = before - after
    if dropped:
        logger.warning("Drop %d duplicate row(s)", dropped)
    return df


KNOWN_WEATHER_MAIN = {
    "Clear", "Clouds", "Rain", "Drizzle", "Thunderstorm",
    "Snow", "Mist", "Smoke", "Haze", "Dust", "Fog",
    "Sand", "Ash"
    , "Squall", "Tornado"
}

REQUIRED_NUMERIC = {"temp", "pressure", "humidity", "wind_speed", "cloud_pct"}
def handler_outlier(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    out_of_range = {
        "humidity": ~df["humidity"].between(0, 100),
        "cloud_pct": ~df["cloud_pct"].between(0, 100),
        "wind_deg":  ~df["wind_deg"].between(0, 360),
        "pressure": ~df["pressure"].between(870, 1085),
        "wind_speed": ~df["wind_speed"].between(0, 150),
        "wind_gust": ~df["wind_gust"].between(0, 150),
        "temp": ~df["temp"].between(-50, 60),
    }

    for col, mask in out_of_range.items():
        mask = mask & df[col].notna()
        count = mask.sum()
        if not count:
            continue

        if col in REQUIRED_NUMERIC:
            logger.warning("Dropped %d row(s): '%s' out of range", count, col)
            df = df[~mask]
        else:
            logger.warning("%d row(s) has '%s' out of range, nulled", count, col)
            df.loc[mask, col] = pd.NA

    return df



def clean_text(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Trim whitespace
    text_cols = ["city_name", "country", "weather_main", "weather_description", "weather_icon"]
    for col in text_cols:
        df[col] = df[col].str.strip()

    cases_rule = {
        "country": "upper",
        "weather_main": "title",
        "weather_description": "lower",
    }

    for col, method in cases_rule.items():
        df[col] = getattr(df[col].str, method)()


    unexpected = df.loc[~df["weather_main"].isin(KNOWN_WEATHER_MAIN), "weather_main"]
    if not unexpected.empty:
        logger.warning("Unexpected weather_main value %s", unexpected.unique().tolist())

    # Bad country code check
    bad_country_code = df.loc[~df["country"].str.match(r"^[A-Z]{2}$", na=False), "country"]
    if not bad_country_code.empty:
        logger.warning("Unexpected country code %s", bad_country_code.unique().tolist())

    return df


FINAL_COLUMNS = [
    "city_id", "city_name", "country", "lat", "lon", "timezone_offset",
    "temp", "feels_like", "temp_min", "temp_max", "pressure", "humidity",
    "sea_level", "grnd_level",
    "wind_speed", "wind_deg", "wind_gust",
    "cloud_pct",
    "visibility",
    "weather_id", "weather_main", "weather_description", "weather_icon",
    "recorded_at", "sunrise", "sunset",
]
def final_select_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[FINAL_COLUMNS]
    return df


def execute_transform_pipeline(file_path: Path) -> pd.DataFrame | None:
    logger.info("Executing transform step _____")
    df = load_json_file_to_dataframe(file_path)
    if df is None:
        return None
    df = rename_columns(df)
    df = handler_null(df)
    df = convert_types(df)
    df = handler_duplicates(df)
    df = handler_outlier(df)
    df = clean_text(df)
    df = final_select_column(df)

    return df
