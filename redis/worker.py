from lib.worker import sub_routine
from lib.pubsub.redis import Redis_Subscriber

subscriber = Redis_Subscriber()
subscriber.callback_function = sub_routine

if __name__ == '__main__':
    while True:
        try:
            subscriber.run()
        except KeyboardInterrupt:
            subscriber.stop()
