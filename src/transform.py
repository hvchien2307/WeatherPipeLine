import json
import pandas as pd


from pathlib import Path
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



