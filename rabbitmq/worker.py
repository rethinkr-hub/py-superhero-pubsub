from lib.pubsub.rabbit import Rabbit_Subscriber
from lib.worker import sub_routine

import asyncio

async def main():
    subscriber = Rabbit_Subscriber()
    subscriber.callback_func = sub_routine
    await subscriber.connect()
    await subscriber.run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()