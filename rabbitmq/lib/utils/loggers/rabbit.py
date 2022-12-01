from lib.utils.loggers.default import base_handler
from lib.utils.loggers import log_level
from lib.pubsub.rabbit import Rabbit_Publisher

import datetime
import asyncio
import logging
import os

# Environment Variables
LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO')

# Setup
publisher = Rabbit_Publisher()
asyncio.create_task(publisher.connect())

class Rabbit_Handler(logging.StreamHandler):
    """SQL Stream Handler

    Stream log messages to SQL Database.
    """
        
    def emit(self, record):
        """Record Emit

        Format log record and commit to Database.

        Args:
            record: logging record
        """
        if hasattr(record, 'queue') and hasattr(record, 'task'):
            ts = datetime.datetime.fromtimestamp(record.created)
            asyncio.create_task(
                publisher.publish({
                    'level': record.levelname,
                    'timestamp': ts.isoformat(),
                    'name': record.name,
                    'log_message': record.msg,
                    'task': record.task
                }, record.queue))
        elif hasattr(record, 'queue'):
            ts = datetime.datetime.fromtimestamp(record.created)
            asyncio.create_task(
                publisher.publish({
                    'level': record.levelname,
                    'timestamp': ts.isoformat(),
                    'name': record.name,
                    'log_message': record.msg
                }, record.queue))

logger = logging.getLogger('rabbit')
logger.setLevel(log_level('DEBUG'))

rabbit_handler = Rabbit_Handler()
rabbit_handler.setLevel(log_level(LOG_LEVEL))

rabbit_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rabbit_handler.setFormatter(rabbit_formatter)

logger.addHandler(base_handler)
logger.addHandler(rabbit_handler)
logger.propagate = False