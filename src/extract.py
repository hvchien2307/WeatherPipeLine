from dotenv import load_dotenv
import os
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
import json

load_dotenv()
Hanoi_OpenWeather_ID = 1581130


def get_current_weather_data_from_open_weather_map(city_id=Hanoi_OpenWeather_ID):
    """ Returns current weather data by city id (Ha Noi by default)
    """
    base_url = "https://openweathermap.org"
    api_key = os.getenv("OPEN_WEATHER_API_KEY")

    query_params = {
        "id": city_id,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=query_params, timeout=5)
        response.raise_for_status()
        return  response.json()

    except HTTPError as http_err:
        http_response = http_err.response
        if http_response is not None and http_response.status_code == 401:
            print("[ERROR] Authentical Error: Check if your API key is valid or activated")
        elif http_response is not None and http_response.status_code == 404:
            print(f"[ERROR] ID Not Found: The city ID '{city_id}' could not be found")
        else:
            print(f"[ERROR] HTTP Error Occurred: {http_err}")

    except Timeout:
        print(f"[ERROR] Timeout Error: The OpenWeather servers took too long to respond")

    except ConnectionError:
        print(f"[ERROR] Connection Error: Please check your Internet Connection")

    except RequestException as err:
        print(f"[ERROR] An unexpected error occurred: {err}")

    return None


def write_weather_data_in_json_file(json_data: dict | None) -> str | None:
    """ Saving the extracted weather data into a json-file
        File Name is automatically names as Unix Timestamp of data(dt)
    """

    if not json_data or 'dt' not in json_data:
        print("[WARNING] No valid data to write this file")
        return None
    cache_dir = "data"
    os.makedirs(cache_dir, exist_ok=True)

    file_name = f"data{json_data['dt']}.json"
    file_path = os.path.join(cache_dir, file_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f,ensure_ascii=False, indent=4)
        print(f"[SUCCESS] Weather data extracted and cached to: {file_path}")
        return file_path

    except IOError as io_err:
        print(f"[ERROR] Could not write file to disk: {io_err}")
        return None


# Operational Function "
def execute_extract_pipeline():
    print("Executing Extract Pipeline Step ...........................")
    raw_data = get_current_weather_data_from_open_weather_map()
    if raw_data is not None:
        cached_file = write_weather_data_in_json_file(raw_data)
        return cached_file
    return None

if __name__ == "__main__":
    execute_extract_pipeline()