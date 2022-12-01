from lib.pubsub.kafka import Kafka_Publisher
from lib.pubsub.redis import Redis_Subscriber
from lib.worker import R_CONN
from lib.utils import loggers

import importlib
import asyncio
import logging
import json
import os

# Envionrment Variabels
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

async def main():
    # Setup
    logger_module = importlib.import_module('lib.utils.loggers', LOGGER_MODULE)

    QUEUE='worker.%s' % __name__
    logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))
    
    async def fanout(msg):
        logger.info('Fanning out message from Redis to Kafka')
        if isinstance(msg, bytes):
            msg = json.loads(msg.decode('utf8'))
        elif isinstance(msg, str):
            msg = json.loads(msg)

        await kafka_client.publish(msg, queue=msg['name'])
    
    logger.info('Establishing Fanout Publisher for Kafka')
    kafka_client = Kafka_Publisher()
    await kafka_client.connect()

    logger.info('Establishing Fanout Subscriber for Redis')
    redis_client = Redis_Subscriber()
    redis_client.callback_function = fanout
    await redis_client.run()

if __name__ == '__main__':
    asyncio.run(main())