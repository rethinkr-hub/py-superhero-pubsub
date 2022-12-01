from lib.pubsub.redis import Redis_Subscriber
from lib.worker.parser import HOSTNAME
from lib.worker import sub_routine

import random
import os

# Envionrment Variabels
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'lib.server.lobby')

subscriber = Redis_Subscriber()
subscriber.callback_function = sub_routine

if __name__ == '__main__':
    while True:
        try:
            subscriber.run(channel='%s.%s' % (WORKER_CHANNEL, HOSTNAME))
        except KeyboardInterrupt:
            subscriber.stop()
