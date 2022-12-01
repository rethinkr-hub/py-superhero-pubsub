# Code taken from Pika GitHub examples
# https://github.com/pika/pika/blob/main/examples/long_running_publisher.py
# https://github.com/pika/pika/blob/main/examples/asynchronous_consumer_example.py

from functools import wraps
from this import d

import aiokafka
import asyncio
import logging
import random
import kafka
import json
import sys
import os

from numpy import partition

# Environment Variables
KAFKA_HOST=os.getenv('KAFKA_HOST', 'localhost')
KAFKA_PORT=int(os.getenv('KAFKA_PORT', 9092))
KAFKA_PARTITIONS=int(os.getenv('KAFKA_PARTITIONS', 2))
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'lib.server.lobby')

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
KAFKA_URL = '%s:%d' % (KAFKA_HOST, KAFKA_PORT)

class Kafka_Publisher(object):

    async def connect(self):
        def _partitioner(key, all_partitions, available_partitions):
            return random.choice(all_partitions)

        try:
            # Get cluster layout and initial topic/partition leadership information
            logging.info('Connecting to Kafka')
            self.connection = aiokafka.AIOKafkaProducer(bootstrap_servers=KAFKA_URL, partitioner=_partitioner)
            await self.connection.start()
        except kafka.errors.KafkaConnectionError:
            await asyncio.sleep(1)
            await self.connect()
    
    async def publish(self, message, queue):
        # Sending the message
        logging.info('Publishing message to %s' % queue)
        await self.connection.send_and_wait(queue, json.dumps(message).encode('utf8'))

class Kafka_Subscriber(object):

    @property
    def callback_func(self):
        return
    
    @callback_func.setter
    def callback_func(self, func):
        self._callback_func = func

    async def connect(self):
        try:
            # Get cluster layout and join group `superhero_sim`
            logging.info('Connecting to Kafka')
            self.connection = aiokafka.AIOKafkaConsumer(
                WORKER_CHANNEL, 
                bootstrap_servers=KAFKA_URL,
                group_id='superhero_sim')
        
            await self.connection.start()
        except kafka.errors.KafkaConnectionError:
            await asyncio.sleep(1)
            await self.connect()

    async def run(self):
        # Consume messages
        async for msg in self.connection:
            self._callback_func(json.loads(msg.value.decode('utf8')))