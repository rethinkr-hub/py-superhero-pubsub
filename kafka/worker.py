from lib.pubsub.kafka import Kafka_Subscriber
from lib.worker import sub_routine

import asyncio

async def main():
    subscriber = Kafka_Subscriber()
    subscriber.callback_func = sub_routine
    await subscriber.connect()
    await subscriber.run()

if __name__ == '__main__':
    asyncio.run(main())
    