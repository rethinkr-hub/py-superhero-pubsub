# Super Hero Combat Simulator - Pub/Sub - Kafka

Here is a demonstration of a Kafka Pub/Sub system handling the [Super Hero Combat Simulator](https://github.com/jg-ghub/py-superhero) streaming data. Again, we utilize a hook in the Logging Transport to stream log data to the Kafka broker, so the tasks can be distributed to the scalable workers for processsing.

# Overview

## Worker

The worker service listens to the Kafka Channel `lib.server.lobby`, whereby messages are streamed during the life-cycle of the game. The worker is specifically listening for logs which carry the following message: `Cleaning Game Records`. This message signifies that the game has completed, and will provide the following payload.

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
| WORKER_CHANNEL | CLEAN     | [str] Redis/Kafka Pub/Sub Channel                             |
| CLEAN_ROUTINE  | False     | [bool] Flag to run Redis Clean                                |
| LOGGER_MODULE  | Default   | [str] Logging Module Name                                     |
| LOG_LEVEL      | INFO      | [str] Logging Message Level Filter                            |

# Performance

Kafka's performance can be measured with the Kafka UI application. Kafka UI is spun up along side Kafka in the provided docker-compose, and can be accessed with this link [localhost:15672](http://localhost:15672).

We can monitor the `lib.server.lobby` topic throughput in the Topic section of the Kafka UI application, or by following this [link]() after login. Kafka UI can provide us great detail about the number of messages sitting in a Topic, what those message's content looks like and how many subscribers are consuming messages within that topic. However, it doesn't provide any useful charts for monitoring Topic throughput, nor what messages were actually executed succesfully.

A significant benefit to Kafka is its native batch processing capabilities. This demonstration uses an agnostic worker to sink Redis logs into Parquet files, but really isn't necessary with Kafka's streaming buffer technology. The logs are published to Kafka Topics, but a never actually removed from the Topic (unlike Message Queue Platforms). Instead, the logs are given an expiry period before they're discarded or archived in Cold storage. 

This enables the logs in Kafka Topics to be processable through batch or stream style processing. The agnostic worker is purely for demonstrating the ability to extend the same processing across different Pub/Sub and Message Queue architectures. Batch exectuion would the prefered ingestion methodology for this style of data processing.

# How to Use

## Local Development

To test/debug these services, each service can be started locally by executing the script in bash. A Redis service must be running, and can easily be started separate from the other docker services. The following commands will have the server application running locally

```bash

export $(cat .env) && \
docker-compose -f compose/docker-compose.kafka.yml up -d redis build_db zookeeper kafka kafka-ui && \
python3 server.py && \
python3 worker.py

```

Once the server is up and running, we can deploy as many clients as we'd like with the following - repeat as necessary to meet required participants. Note: make sure that Kafka is not only up, but accepting publications as well. The HeartBeat for Kafka uptime isn't a proper signal that it's ready to receive Topic publications.

```bash

python3 client.py

```

The Redis DB often requires a fresh slate for testing purposes. While we can't wipe anything specific in the Redis DB, we do have the option to flush the entire DB, and rebuild the Super Hero Collection, with the following command.

```bash

export REDIS_DB=0
redis-cli -h localhost -n ${REDIS_DB} -e FLUSHDB
docker-compose -f compose/docker-compose.kafka.yml up -d build_db

```

## Production

Spinning up a production appliaction with docker-compose is faily simple, requiring 2 setps. The first step is to spin up the Kafka services and allow it time to be in a ready position to receive Topic publications.

```bash

docker-compose --env-file .env -f compose/docker-compose.kafka.yml build && \
docker-compose --env-file .env -f compose/docker-compose.kafka.yml up -d zookeeper kafka kafka-ui

```

Normally, once Kafka-UI is up and can be navigated to via webpage, then we can spin the rest of the application up following the commands below - replacing `${PLAYERS}` with the required participants.

```bash

export PLAYERS=10
docker-compose --env-file .env -f compose/docker-compose.kafka.yml up --scale player=${PLAYERS}

```

We can scale the workers with the following

```bash

export PLAYERS=10
export WORKERS=4
docker-compose --env-file .env -f compose/docker-compose.kafka.yml up --scale worker=${WORKERS} --scale player=${PLAYERS}

```

## TODO

* Scalability to Brokers