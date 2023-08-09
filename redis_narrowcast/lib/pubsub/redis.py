from lib.worker import R_CONN

import json
import os

# Envionrment Variabels
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'lib.server.lobby')
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))

class Redis_Subscriber:

    @property
    def callback_function(self):
        return
    
    @callback_function.setter
    def callback_function(self, callback_function):
        self._callback_function = callback_function
    
    def run(self, channel=WORKER_CHANNEL):
        sub = R_CONN.pubsub()
        sub.subscribe(channel)
        for msg in sub.listen():
            if isinstance(msg['data'], bytes):
                msg = json.loads(msg['data'].decode('utf8'))
                self._callback_function(msg)
    
    def stop(self):
        return