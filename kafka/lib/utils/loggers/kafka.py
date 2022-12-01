from lib.utils.loggers.default import base_handler
from lib.utils.loggers import log_level
from lib.pubsub.kafka import Kafka_Publisher

import datetime
import asyncio
import logging
import os

# Environment Variables
LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO')

# Setup
publisher = Kafka_Publisher()
asyncio.create_task(publisher.connect())

class Kafka_Handler(logging.StreamHandler):
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

logger = logging.getLogger('kafka')
logger.setLevel(log_level('DEBUG'))

kafka_handler = Kafka_Handler()
kafka_handler.setLevel(log_level(LOG_LEVEL))

kafka_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
kafka_handler.setFormatter(kafka_formatter)

logger.addHandler(base_handler)
logger.addHandler(kafka_handler)
logger.propagate = False