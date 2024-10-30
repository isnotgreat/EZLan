import logging
import asyncio
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create a queue for logging
        self.log_queue = Queue()
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Use QueueHandler for thread-safe logging
        queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)
        
        # Start a listener thread
        listener = QueueListener(self.log_queue, handler)
        listener.start()
    
    def info(self, message):
        self.logger.info(message)
        
    def error(self, message):
        self.logger.error(message)
        
    def warning(self, message):
        self.logger.warning(message)
        
    def debug(self, message):
        self.logger.debug(message)
