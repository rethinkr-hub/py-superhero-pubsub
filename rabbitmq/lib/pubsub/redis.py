from lib.worker import R_CONN

import logging
import asyncio
import json
import sys
import os

# Envionrment Variabels
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'lib.server.lobby')
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def redis_publisher(message):
    R_CONN.publish(WORKER_CHANNEL, json.dumps(message))

class Redis_Subscriber:

    @property
    def callback_function(self):
        return
    
    @callback_function.setter
    def callback_function(self, callback_function):
        self._callback_function = callback_function
    
    async def run(self):
        logging.info('Middleware Activated')
        sub = R_CONN.pubsub()
        sub.subscribe(WORKER_CHANNEL)
        for msg in sub.listen():
            if isinstance(msg['data'], bytes):
                msg = json.loads(msg['data'].decode('utf8'))
                await self._callback_function(msg)