from lib.pubsub.rabbit import Rabbit_Publisher
from lib.pubsub.redis import Redis_Subscriber
from lib.worker import R_CONN

import importlib
import asyncio
import logging
import json
import os

# Envionrment Variabels
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

async def main():
    logger_module = importlib.import_module('lib.utils.loggers', LOGGER_MODULE)

    # Setup
    QUEUE='worker.%s' % __name__
    logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

    async def fanout(msg):
        logger.info('Narrowcasting from Redis to RabbitMQ')
        if isinstance(msg, bytes):
            msg = json.loads(msg.decode('utf8'))
        elif isinstance(msg, str):
            msg = json.loads(msg)
            
        await rabbit_client.publish(msg, queue=msg['name'])
    
    logger.info('Establishing Publisher for RabbitMQ')
    rabbit_client = Rabbit_Publisher()
    await rabbit_client.connect()

    logger.info('Establishing Subscriber for Redis')
    redis_client = Redis_Subscriber()
    redis_client.callback_function = fanout
    await redis_client.run()

if __name__ == '__main__':
    asyncio.run(main())