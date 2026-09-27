# This is a sample Python script.
from config.logging_config import setup_logging
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from config.logging_config import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)
from src import extract

def main():
    setup_logging()
    extract.execute_extract_pipeline()
    return

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
