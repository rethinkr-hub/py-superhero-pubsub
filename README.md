# Super Hero Combat Simulator - Pub/Sub

This repo is an evaulation of Pub/Sub and Message Queue service suitability for the [Super Hero Combat Simulator](https://github.com/jg-ghub/py-superhero). We evaluate how efficient the service can synergize with the logs we're streaming from the Simulator.

**Motivation:** provide replicatable demonstrations for some popular Open Source Pub/Sub services with an similar pattern style plugin, so we can interchange services with simplicity.

**Objective:** Choose a service which best suits the DataOps goals for this simulator. We use an identical ETL job to output streaming logs to Parquet files for later ingestion to Data Warehouses. The output to Parquet files isn't the most efficient choice for ingestion, but does provide an equivalent test for evaluating the different services herein.

# Pattern

Choosing a design for interopability with the evaluation trials helped to achieve a milestone pattern for logging transports worthy of a mention. In particular, we've been able to achieve a modular container design which builds on the `superhero_server` service and allows us to simply introduce another logging transport and import via the Environment Variable `LOGGER_MODULE`. Now we can minimize the amount of repetitive work by only building on the evaluation components, and hooking them into the logging transport pattern.

Dockerfiles only need to source the upstream `python/datasim/superhero` image, and then inject the Logging Transport Hooks, Pub/Sub service, and Output Model.

```docker

FROM python/datasim/superhero

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./lib/utils/loggers/kafka.py ./lib/utils/loggers
COPY ./lib/pubsub/kafka.py ./lib/pubsub
COPY ./lib/pubsub/redis.py ./lib/pubsub
COPY ./lib/model ./lib/model
COPY ./lib/worker ./lib/worker
COPY ./worker_fanout.py .
COPY ./worker.py .

```

The `python/datasim/superhero` build will then configure the logger based on which `LOGGER_MODULE` is provided at start-up. The configuration will setup some prerequisits to publish messages to the evaluated Pub/Sub service, and push the messages on the emit hook in the Logging Transport.

**Logging Configuration**

```python

# Enivornment Variables
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

# Setup
QUEUE=__name__
logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))


```

**Logging Transport**

```python

from lib.pubsub.redis import redis_publisher

import logging

class Redis_Handler(logging.StreamHandler):
    """Redis Pub/Sub Stream Handler

    Publish log messages to Redis Pub/Sub.
    """
        
    def emit(self, record):
        """Record Emit

        Format log record and publish to Pub/Sub.

        Args:
            record: logging record
        """
        if hasattr(record, 'queue') and hasattr(record, 'task'):
            ts = datetime.datetime.fromtimestamp(record.created)
            redis_publisher(record.queue, {
                'level': record.levelname,
                'timestamp': ts.isoformat(),
                'name': record.name,
                'log_message': record.msg,
                'task': record.task
            })
        elif hasattr(record, 'queue'):
            ts = datetime.datetime.fromtimestamp(record.created)
            redis_publisher(record.queue, {
                'level': record.levelname,
                'timestamp': ts.isoformat(),
                'name': record.name,
                'log_message': record.msg
            })

logger = logging.getLogger('redis')

redis_handler = Redis_Handler()
redis_handler.setLevel(log_level(LOG_LEVEL))

logger.addHandler(redis_handler)

```


# Overview

## Redis

Redis Pub/Sub offers a very simplistic and easy to use messaging framework out-of-the-box. It's already acting as our DB Key Store on the application side, so making use of it's Pub/Sub feature is a no brainer. Running this application on a local environment, using a small amount of Player Services, with Redis' built-in Pub/Sub works wonders - it handles the payload effectively. However, Redis Pub/Sub suffers from scalability issues when we try to add more workers attempting to create some efficiency.

Redis' simplicity effectively breaks the out-of-the-box solution for our application's needs. The Redis Pub/Sub mechanism is a Broadcast message to all Subscribers listening to our channel `redis.lib.server.lobby`, which means that all workers receive the same message. This doesn't help provide us more efficieny when we scale our workers - instead it causes duplication.

In this example, the ETL jobs were run once on each worker serverice. This solution isn't viable for our needs. Instead, we would like to have our workers take tasks from a queue whereby they run unique operations simultaneously, but never the identical task. We've validated some other popular services within the repo for you to explore.

## Redis - Fanout

The Fanout service is a middleware subscriber we dedicate to receiving all messages in the `redis.lib.server.lobby` channel, and then randomly publishing back to a worker's unique channel - following the pattern `redis.lib.server.lobby-*`. Middleware is a common technique used to insert logic between the Publisher and Subscriber.

Here we've come one step closer to building a sustainable Pub/Sub service which processes independent tasks scaled over multiple workers. The Fanout service was a quick way to spread out tasks amongst the workers, so that nothing was being processed more than once. This example doesn't actually replicate a message queue system, but instead fans out a broadcast message to a narrower focus group.

In terms of sustainability, this approach still doesn't meet other service's levels of fail-over supoport and resiliency in message delivery/acknowledgment. This is where other popular solutions will be used, instead of trying to recreate the wheel with Redis.

## RabbitMQ

RabbitMQ's performance can be measured, and visualized, with the RabbitMQ Management UI. When spinning up RabbitMQ with Docker, the Management UI can be accessed by visiting [localhost:15672](http://localhost:15672). The default credentials are
 * User: guest
 * Pass: guest

We can monitor the `task_lib.server.lobby` queue throughput in the Queue section of the Management tool, or by following this [link](http://localhost:15672/#/queues/%2F/task_lib.server.lobby) after login. On this run we have 100% acknoweldgment of messages consumed succesfully with no issues consuming the velocity of message publications/sec. This can be infered by the Consumer Ack (Green) *Message Rate* overlapping the Publish (Yellow) in ths image below.

A significant benefit to RabbitMQ is its smart broker technology. With other brokers, a Published message is immediately sent out to a consumer once received by the broker. If no consumer is available to receive the Published message, then the message has lost its opportunity for consumer processing. However, with RabbitMQ the Published message is persisted in the Queue until fetched by the consumer. The Published message can be consumed at a future time, and will only be removed from the queue once a consumer has acknowledged the completion of message processing.

## Kafka

Kafka's performance can be measured with the Kafka UI application. Kafka UI is spun up along side Kafka in the provided docker-compose, and can be accessed with this link [localhost:15672](http://localhost:15672).

We can monitor the `lib.server.lobby` topic throughput in the Topic section of the Kafka UI application, or by following this [link]() after login. Kafka UI can provide us great detail about the number of messages sitting in a Topic, what those message's content looks like and how many subscribers are consuming messages within that topic. However, it doesn't provide any useful charts for monitoring Topic throughput, nor what messages were actually executed succesfully.

A significant benefit to Kafka is its native batch processing capabilities. This demonstration uses an agnostic worker to sink Redis logs into Parquet files, but really isn't necessary with Kafka's streaming buffer technology. The logs are published to Kafka Topics, but a never actually removed from the Topic (unlike Message Queue Platforms). Instead, the logs are given an expiry period before they're discarded or archived in Cold storage. 

This enables the logs in Kafka Topics to be processable through batch or stream style processing. The agnostic worker is purely for demonstrating the ability to extend the same processing across different Pub/Sub and Message Queue architectures. Batch exectuion would the prefered ingestion methodology for this style of data processing.

# Supporting Documents

A great document on the two favorited services (RabbitMQ & Kafka) can be found here [Apache Kafka Vs RabbitMQ: Main Differences You Should Know](https://www.simplilearn.com/kafka-vs-rabbitmq-article#:~:text=Deciding%20Between%20Kafka%20and%20RabbitMQ&text=While%20Kafka%20is%20best%20suited,for%20both%20Kafka%20and%20RabbitMQ.). This is a very well thought out comparison of the two tools, and those most prevalent realization to this evaluation was the descript on broker "smartness"

The document mentions that RabbitMQ is considered a Smart Broker for dumb consumers, and Kafka is a dumb broker for smart consumers. These evaluations prove how simple it is to start up using Rabbit MQ, and how much the Broker handles the queue for message cosumption. Where I don't see the same simplicity in Kafka, I do see better suitability for the later ingestion of data given:
 * batch processing capability
 * message retention

 This allows for more efficient ingestion procedures to be built into the workers which is the goal of this evaluation.