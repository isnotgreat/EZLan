import logging
from logging import getLogger, StreamHandler, Formatter, INFO
from datetime import datetime

class Logger:
    def __init__(self, name):
        self.logger = getLogger(name)
        self.logger.setLevel(INFO)
        
        if not self.logger.handlers:
            handler = StreamHandler()
            formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message):
        self.logger.info(message)
        
    def error(self, message):
        self.logger.error(message)
        
    def warning(self, message):
        self.logger.warning(message)
        
    def debug(self, message):
        self.logger.debug(message)
