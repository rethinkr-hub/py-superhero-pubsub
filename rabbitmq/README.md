# Super Hero Combat Simulator - Pub/Sub - RabbitMQ

Here is a demonstration of a RabbitMQ Message Queueing system handling the [Super Hero Combat Simulator](https://github.com/jg-ghub/py-superhero) streaming data. Again, we utilize a hook in the Logging Transport to stream log data to the RabbitMQ broker, so the tasks can be distributed to the scalable workers for processsing.

# Overview

## Worker

The worker service listens to the Redis Channel `task_lib.server.lobby`, whereby messages are streamed during the life-cycle of the game. The worker is specifically listening for logs which carry the following message: `Cleaning Game Records`. This message signifies that the game has completed, and will provide the following payload.

```json

{
    "game_token": {{ %game_token% }},
    "user_token": {{ %user_token% }}
}

```

The worker can now use this payload to pull that game's session logs, and proceed to Extact-Transfer-Load these 2 sets of data for post-hoc analysis

### GAME META

The Game Meta data consists of which player's superheros participated in a specific game - which in this example is considered the dimension table. This table is stored in a gzip compressed parquet file with the following schema

| Field        | Type   |
|--------------|--------|
| game_token   | uft16  |
| user_token   | uft16  |
| superhero_id | uint16 |

### GAME PODIUM

The Game Podium data consists of the following in battle metrics - which is this example is considered the fact table.

| Field           | Type    |
|-----------------|---------|
| game_token      | uft16   |
| user_token      | uft16   |
| rank            | uint8   |
| rounds          | uint8   |
| damage_received | unint64 |
| damage_sent     | unint64 |

## Environment Variables

| Variable Name  | Default   | Description                                                   |
|----------------|-----------|---------------------------------------------------------------|
| REDIS_HOST     | localhost | [str] Redis Host Address                                      |
| REDIS_PORT     | 6379      | [int] Redis Host Port                                         |
| REDIS_DB       | 0         | [int] Redis Databse                                           |
| REDIS_EXPIRY   | 30        | [int] Redis Key Expiry in seconds                             |
| WORKER_CHANNEL | CLEAN     | [str] Redis/ RabbitMQ Pub/Sub Channel                         |
| CLEAN_ROUTINE  | False     | [bool] Flag to run Redis Clean                                |
| LOGGER_MODULE  | Default   | [str] Logging Module Name                                     |
| LOG_LEVEL      | INFO      | [str] Logging Message Level Filter                            |

# Performance

RabbitMQ's performance can be measured, and visualized, with the RabbitMQ Management UI. When spinning up RabbitMQ with Docker, the Management UI can be accessed by visiting [localhost:15672](http://localhost:15672). The default credentials are
 * User: guest
 * Pass: guest

We can monitor the `task_lib.server.lobby` queue throughput in the Queue section of the Management tool, or by following this [link](http://localhost:15672/#/queues/%2F/task_lib.server.lobby) after login. On this run we have 100% acknoweldgment of messages consumed succesfully with no issues consuming the velocity of message publications/sec. This can be infered by the Consumer Ack (Green) *Message Rate* overlapping the Publish (Yellow) in ths image below.

A significant benefit to RabbitMQ is its smart broker technology. With other brokers, a Published message is immediately sent out to a consumer once received by the broker. If no consumer is available to receive the Published message, then the message has lost its opportunity for consumer processing. However, with RabbitMQ the Published message is persisted in the Queue until fetched by the consumer. The Published message can be consumed at a future time, and will only be removed from the queue once a consumer has acknowledged the completion of message processing.

# How to Use

## Local Development

To test/debug these services, each service can be started locally by executing the script in bash. A Redis service must be running, and can easily be started separate from the other docker services. The following commands will have the server application running locally

```bash

export $(cat .env) && \
docker-compose up -d redis build_db rabbit && \
python3 server.py && \
python3 worker.py

```

Once the server is up and running, we can deploy as many clients as we'd like with the following - repeat as necessary to meet required participants.

```bash

python3 client.py

```

The Redis DB often requires a fresh slate for testing purposes. While we can't wipe anything specific in the Redis DB, we do have the option to flush the entire DB, and rebuild the Super Hero Collection, with the following command.

```bash

export REDIS_DB=0
redis-cli -h localhost -n ${REDIS_DB} -e FLUSHDB
docker-compose up -d build_db

```

## Production

Spinning up a production application with docker-compose is simple. Follow the commands below, replacing `${PLAYERS}` with the required participants.

```bash

export PLAYERS=10
docker-compose --env-file .env -f compose/docker-compose.rabbitmq.yml build && \
docker-compose --env-file .env -f compose/docker-compose.rabbitmq.yml up --scale player=${PLAYERS}

```

We can scale the workers with the following

```bash

export PLAYERS=10
export WORKERS=4
docker-compose --env-file .env -f compose/docker-compose.rabbitmq.yml build && \
docker-compose --env-file .env -f compose/docker-compose.rabbitmq.yml up --scale worker=${WORKERS} --scale player=${PLAYERS}

```

## TODO

* Scalability to Brokers