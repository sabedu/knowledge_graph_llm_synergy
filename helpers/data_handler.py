import json
from logging import getLogger

logger = getLogger(__name__)

class DataHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        logger.info('Loading data from {}'.format(self.file_path))
        with open(self.file_path, 'r') as file:
            return json.load(file)