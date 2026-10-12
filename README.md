# Weather Pipeline

An basic ETL that pulls current weather data for Hanoi from OpenWeather API,
cleans it with pandas, and loads it into a MySQL database.

## Architecture
OpenWeather API -> Extract (raw JSON) -> Transform (pandas) -> Load(MySQL)

-- **Extract**-- calls the API with retry and backoff, saves the raw response to 'data/raw_data/' .
--**Transform**-- flattens the JSON to DataFrame, then handles null, types, duplicates, outliers, and test inconsistencies
--**Load**-- upserts the city, then inserts the reading, in one transaction

## Tech stack
Python 3.x, requests, pandas, mysql-connector-python, python-dotenv, MySQL 8 

## Project structure
    config/             logging and database configuration 
    src/                extract.py, transform.py, load.py
    data/raw-data/      cached raw API response (gitignored)
    logs/               application logs (gitignored)  
    main.py             pipeline entry point

## Setup
1. Clone the repo and create a virtual environment
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
2. Create a MySQL database named "OpenWeather"
3. Create a '.venv' file in the project root 
4. Create the tables (see Data model)

## Configuration
Create '.venv' with:
    OPEN_WEATHER_API_KEY=your_key_here
    MYSQL_HOST=localhost
    MYSQL_USER=your_user
    MYSQL_PASSWORD=your_password
    MYSQL_DATABASE=OpenWeather

## Usage
    python main.py

## Data model
- 'cities': one row per city (dimension)
- 'weather_readings': one row per city per timestamp (fact), unique on '(city_id, recorded_at)'
