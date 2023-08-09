from lib.pubsub.redis import Redis_Subscriber
from lib.worker import R_CONN

import importlib
import logging
import random
import json
import sys
import os

# Envionrment Variabels
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'lib.server.lobby')
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

# Setup
logger_module = importlib.import_module('lib.utils.loggers.%s' % LOGGER_MODULE)

QUEUE='worker.%s' % __name__
logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

def narrowcast(msg):
    workers = R_CONN.pubsub_channels('%s.*' % WORKER_CHANNEL)
    if len(workers) > 0:
        channel = workers[random.randint(0, len(workers)-1)].decode('utf8')
        logger.info('Narrowcasting to channel: %s' % channel)
        R_CONN.publish(channel, json.dumps(msg))

if __name__ == '__main__':
    redis_client = Redis_Subscriber()
    redis_client.callback_function = narrowcast
    redis_client.run()