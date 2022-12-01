# Code taken from Pika GitHub examples
# https://github.com/pika/pika/blob/main/examples/long_running_publisher.py
# https://github.com/pika/pika/blob/main/examples/asynchronous_consumer_example.py

from functools import wraps

import asyncio
import logging
import aiormq
import json
import sys
import os

# Environment Variables
RABBIT_USER=os.getenv('RABBIT_USER', 'guest')
RABBIT_PASS=os.getenv('RABBIT_PASS', 'guest')
AMQP_HOST=os.getenv('AMQP_HOST', 'localhost')
AMQP_PORT=int(os.getenv('AMQP_PORT', 5672))
AMQP_EXCHANGE=os.getenv('AMQP_EXCHANGE', 'superhero')
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'lib.server.lobby')

# Setup
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
AMQP_URL = 'amqp://%s:%s@%s:%d' % (RABBIT_USER, RABBIT_PASS, AMQP_HOST, AMQP_PORT)

class Rabbit_Publisher(object):
    channel = None

    async def connect(self):
        try:
            # Perform connection
            logging.info('Connecting to RabbitMQ')
            self.connection = await aiormq.connect(AMQP_URL)
            # Creating a channel
            self.channel = await self.connection.channel()
        except ConnectionError:
            await asyncio.sleep(1)
            await self.connect()
    
    async def publish(self, message, queue):
        # Sending the message
        logging.info('Publishing message to task_%s' % queue)
        if self.channel:
            await self.channel.basic_publish(
                bytes(json.dumps(message), 'utf8'), 
                routing_key='task_%s' % queue
            )

class Rabbit_Subscriber(object):

    @property
    def callback_func(self):
        return
    
    @callback_func.setter
    def callback_func(self, func):
        self._callback_func = func

    async def connect(self):
        try:
            # Perform connection
            logging.info('Connecting to RabbitMQ')
            self.connection = await aiormq.connect(AMQP_URL)

            # Creating a channel
            self.channel = await self.connection.channel()
            await self.channel.basic_qos(prefetch_count=1)

            # Declaring queue
            self.declare_ok = await self.channel.queue_declare('task_%s' % WORKER_CHANNEL, durable=True)
        except ConnectionError:
            await asyncio.sleep(1)
            await self.connect()

    async def run(self):

        def callback(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                message = args[0]
                self._callback_func(message)
                
                return f(*args, **kwargs)


            return wrapper
        
        @callback
        async def ack(message):
            await message.channel.basic_ack(
                message.delivery.delivery_tag
            )

        # Start listening to the queue
        await self.channel.basic_consume(self.declare_ok.queue, ack)