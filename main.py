# This is a sample Python script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import logging
from pathlib import Path
logger = logging.getLogger(__name__)
from src import extract
from src import transform
from src import load

def main():
    from config.logging_config import setup_logging
    setup_logging()
    path = extract.execute_extract_pipeline()
    data = transform.execute_transform_pipeline(path)
    load. execute_load_pipeline(data)
    return

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
