import json
import os

import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException

from pathlib import Path
from dotenv import load_dotenv

import logging
import time

# Declare global variables
load_dotenv()
HANOI_OPEN_WEATHER_ID = 1581130
API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Path to the saving point of raw data
CACHE_DIR = Path("data")/"raw_data"

#Path to save the log
LOG_FILE = Path("logs")/"app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Declare number of attempt
MAX_RETRIES = 3
RETRY_BACKOFF_SECOND = 2


# Config Log
logger = logging.getLogger(__name__)

if not API_KEY:
    logger.critical("OPEN_WEATHER_API_KEY not found in environment - aborting")
    raise SystemExit(1)


# Function call api request
def get_current_weather_data_from_open_weather_map(city_id: int = HANOI_OPEN_WEATHER_ID) -> dict|None:
    """ Returns current weather data by city id (Ha Noi by default)
    """
    query_params = {
        "id": city_id,
        "appid": API_KEY,
        "units": "metric"
    }

    for attempt in range(1, MAX_RETRIES+1):
        try:
            response = requests.get(url=BASE_URL, params=query_params, timeout=5)
            response.raise_for_status()
            return response.json()

        except HTTPError as http_err:
            status = http_err.response.status_code if http_err.response is not None else None
            if status == 401:
                logger.error("Authentication error: check if your API key is valid or activated")
                return None  #Retry won't help
            elif status == 404:
                logger.error("City ID '%s' could not be found", city_id)
                return None  #Retry won't help
            else:
                logger.error("HTTP error occurred: %s", http_err)

        except Timeout:
            logger.warning("Attempt %d/%d: request timed out", attempt, MAX_RETRIES)

        except ConnectionError:
            logger.warning("Attempt %d/%d: connection error", attempt, MAX_RETRIES)

        except RequestException as err:
            logger.error("Unexpected request error, %s", err)
            return None

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SECOND*attempt)

    logger.error("All %d attempts failed", MAX_RETRIES)
    return None


def write_weather_data_in_json_file(json_data: dict | None) -> Path | None:
    """ Saving the extracted weather data into a json-file
        File Name is automatically names as Unix Timestamp of data(dt)
    """
    if not json_data or "dt" not in json_data:
        logger.warning("No valid data to write to file")
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)  #Ensure directory exist
    file_path = CACHE_DIR / f"data_{json_data['dt']}.json"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            logger.info("Weather cached into %s", file_path)
            return file_path

    except IOError as ioe_err:
        logger.error("Could not write data file to the disk: %s", ioe_err)
        return None


def execute_extract_pipeline() -> Path | None:
    logger.info("Executing extract pipeline step ....")
    raw_data = get_current_weather_data_from_open_weather_map()
    if raw_data:
        return write_weather_data_in_json_file(raw_data)
    return None



if __name__ == "__main__":
    from config.logging_config import setup_logging
    setup_logging()
    execute_extract_pipeline()