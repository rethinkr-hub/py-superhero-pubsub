# Super Hero Combat Simulator - Pub/Sub - Redis

This is a working example of a Redis Pub/Sub in action, whereby it is streaming data from the [Super Hero Combat Simulator](https://github.com/jg-ghub/py-superhero) for distributed task processing. In this demonstration, a Redis Publisher has been hooked into the Redis Logger Module Transport to stream log data to the Redis Pub/Sub. We now have a plugin to stream raw log data to a streaming buffer for future processing, which is now where the Subscriber workers come into play. The ETL workers process and sink data locally into Parquet files for later analysis. The Subscriber worker is also responsible for cleaning stale data in the Redis DB, so the backend can continue to run efficiently.

# Overview

## Worker

The worker service listens to the Redis Channel `redis.lib.server.lobby`, whereby messages are streamed during the life-cycle of the game. The worker is specifically listening for logs which carry the following message: `Cleaning Game Records`. This message signifies that the game has completed, and will provide the following payload.

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
| rounds          | uint16  |
| damage_received | unint64 |
| damage_sent     | unint64 |

## Environment Variables

| Variable Name  | Default   | Description                                                   |
|----------------|-----------|---------------------------------------------------------------|
| REDIS_HOST     | localhost | [str] Redis Host Address                                      |
| REDIS_PORT     | 6379      | [int] Redis Host Port                                         |
| REDIS_DB       | 0         | [int] Redis Databse                                           |
| REDIS_EXPIRY   | 30        | [int] Redis Key Expiry in seconds                             |
| WORKER_CHANNEL | CLEAN     | [str] Redis Pub/Sub Channel                                   |
| CLEAN_ROUTINE  | False     | [bool] Flag to run Redis Clean                                |
| LOGGER_MODULE  | Default   | [str] Logging Module Name                                     |
| LOG_LEVEL      | INFO      | [str] Logging Message Level Filter                            |

# Performance

This is less about benchmark and more around suitability. Redis Pub/Sub offers a very simplistic and easy to use messaging framework out-of-the-box. It's already acting as our DB Key Store on the application side, so making use of it's Pub/Sub feature is a no brainer. Running this application on a local environment, using a small amount of Player Services, with Redis' built-in Pub/Sub works wonders - it handles the payload effectively. However, Redis Pub/Sub suffers from scalability issues when we try to add more workers attempting to create some efficiency.

Redis' simplicity effectively breaks the out-of-the-box solution for our application's needs. The Redis Pub/Sub mechanism is a Broadcast message to all Subscribers listening to our channel `redis.lib.server.lobby`, which means that all workers receive the same message. This doesn't help provide us more efficieny when we scale our workers - instead it causes duplication.

Here's an example of duplicative efforts. We deploy our application over docker-compose

```bash

export PLAYERS=10
export WORKERS=2
docker-compose --env-file .env -f compose/docker-compose.redis.yml build && \
docker-compose --env-file .env -f compose/docker-compose.redis.yml up --scale worker=${WORKERS} --scale player=${PLAYERS}

```

Once the simulation has completed, we can review the paquet file creation from the worker instances

```bas

docker exec -it compose-worker-1 ls data/superhero/GAME_PODIUM
00cb4536-10ff-4df5-a358-a0eca45451cf_c434711b159f.gz  3719ced6-1746-4615-a9da-9136a76814f4_c434711b159f.gz
8412f6ab-b8ac-48be-b3af-a120254d9941_c434711b159f.gz  aa06fe55-72eb-4a12-a6b5-329f1fb3298c_c434711b159f.gz
0cf6a6f1-9c12-471b-ad64-7e1ba359d13c_c434711b159f.gz  3b3a1816-4f6b-47d0-80a9-6540b6c3a72d_c434711b159f.gz
87802b81-e513-4bf8-9843-f6868419ed61_c434711b159f.gz  b4de9241-a71b-4c4e-8afd-7fd93ecaa527_c434711b159f.gz
1119e940-e6af-46ca-8c8a-9b5b2486e511_c434711b159f.gz  43ed338a-2d08-47f4-9c78-d5fbb875a4b8_c434711b159f.gz
8cdf6df0-ce14-4228-a94c-b47ed44d6842_c434711b159f.gz  ba829501-6f88-4d39-83ba-3a50ade19ad6_c434711b159f.gz
163d7ec9-c04c-4c84-b5a8-a95dbbe2dff6_c434711b159f.gz  4911add9-3734-43fa-8e7b-afebc4e1fb1a_c434711b159f.gz
8d85d184-cca5-4551-9f21-df4225febc34_c434711b159f.gz  cb60288e-9d3c-4219-bd36-06381ac74854_c434711b159f.gz
18c16771-37a3-4ea8-b294-b8e8200d98ca_c434711b159f.gz  4c6b65c0-b638-4828-83ff-9e36a21af199_c434711b159f.gz
95dc03d2-8939-4158-ad06-dc5d468439e3_c434711b159f.gz  cd29510f-c235-46f3-b9a8-d00b376d433d_c434711b159f.gz
22500bbc-dcbc-47c6-87f5-df4bd847c55b_c434711b159f.gz  520ee98d-2801-40c9-91ba-bd7c60db252d_c434711b159f.gz
9b0d3f76-5b20-4266-99b9-91fa66d65170_c434711b159f.gz  d2b845d7-3c68-4c30-99eb-851589575d17_c434711b159f.gz
26b99668-b4e9-4780-9cb9-55f0aab4a274_c434711b159f.gz  5f0c8b9c-9361-4540-9edf-0827a8dc3e37_c434711b159f.gz
9c04e4de-1072-446e-8283-7947ccf60a30_c434711b159f.gz  dc2b9a65-19c9-44ba-b571-4d433d9ff55c_c434711b159f.gz
317a5d68-597e-423d-94ad-66ce255d19f0_c434711b159f.gz  65b0b2c3-e99f-450b-8fd3-04de803c0ea7_c434711b159f.gz
9c0f0b94-9f3c-424a-b003-e22911a998bd_c434711b159f.gz  e64c32dc-c198-4115-86bf-f37a0b675864_c434711b159f.gz
323d24f9-d123-4d0c-b962-2b89e76e761d_c434711b159f.gz  6934141d-9f87-49b6-90b5-5ad28e5e7ccd_c434711b159f.gz
9cdd2577-5a2c-4eeb-b513-3eaed3c76cbc_c434711b159f.gz  f22883ec-43f9-4392-95de-84f939b598f2_c434711b159f.gz
345927c1-77fa-4104-b1ff-1751d9a6f693_c434711b159f.gz  7588cad0-4f8f-4807-bdbc-0ae304e21ed9_c434711b159f.gz
a40bec3f-6267-4e46-9e28-71ff08ece46c_c434711b159f.gz  f81e79d5-379b-4540-b98b-3ce49424dc0a_c434711b159f.gz

docker exec -it compose-worker-1 ls data/superhero/GAME_PODIUM
00cb4536-10ff-4df5-a358-a0eca45451cf_4123ba141fe8.gz  3719ced6-1746-4615-a9da-9136a76814f4_4123ba141fe8.gz
8412f6ab-b8ac-48be-b3af-a120254d9941_4123ba141fe8.gz  aa06fe55-72eb-4a12-a6b5-329f1fb3298c_4123ba141fe8.gz
0cf6a6f1-9c12-471b-ad64-7e1ba359d13c_4123ba141fe8.gz  3b3a1816-4f6b-47d0-80a9-6540b6c3a72d_4123ba141fe8.gz
87802b81-e513-4bf8-9843-f6868419ed61_4123ba141fe8.gz  b4de9241-a71b-4c4e-8afd-7fd93ecaa527_4123ba141fe8.gz
1119e940-e6af-46ca-8c8a-9b5b2486e511_4123ba141fe8.gz  43ed338a-2d08-47f4-9c78-d5fbb875a4b8_4123ba141fe8.gz
8cdf6df0-ce14-4228-a94c-b47ed44d6842_4123ba141fe8.gz  ba829501-6f88-4d39-83ba-3a50ade19ad6_4123ba141fe8.gz
163d7ec9-c04c-4c84-b5a8-a95dbbe2dff6_4123ba141fe8.gz  4911add9-3734-43fa-8e7b-afebc4e1fb1a_4123ba141fe8.gz
8d85d184-cca5-4551-9f21-df4225febc34_4123ba141fe8.gz  cb60288e-9d3c-4219-bd36-06381ac74854_4123ba141fe8.gz
18c16771-37a3-4ea8-b294-b8e8200d98ca_4123ba141fe8.gz  4c6b65c0-b638-4828-83ff-9e36a21af199_4123ba141fe8.gz
95dc03d2-8939-4158-ad06-dc5d468439e3_4123ba141fe8.gz  cd29510f-c235-46f3-b9a8-d00b376d433d_4123ba141fe8.gz
22500bbc-dcbc-47c6-87f5-df4bd847c55b_4123ba141fe8.gz  520ee98d-2801-40c9-91ba-bd7c60db252d_4123ba141fe8.gz
9b0d3f76-5b20-4266-99b9-91fa66d65170_4123ba141fe8.gz  d2b845d7-3c68-4c30-99eb-851589575d17_4123ba141fe8.gz
26b99668-b4e9-4780-9cb9-55f0aab4a274_4123ba141fe8.gz  5f0c8b9c-9361-4540-9edf-0827a8dc3e37_4123ba141fe8.gz
9c04e4de-1072-446e-8283-7947ccf60a30_4123ba141fe8.gz  dc2b9a65-19c9-44ba-b571-4d433d9ff55c_4123ba141fe8.gz
317a5d68-597e-423d-94ad-66ce255d19f0_4123ba141fe8.gz  65b0b2c3-e99f-450b-8fd3-04de803c0ea7_4123ba141fe8.gz
9c0f0b94-9f3c-424a-b003-e22911a998bd_4123ba141fe8.gz  e64c32dc-c198-4115-86bf-f37a0b675864_4123ba141fe8.gz
323d24f9-d123-4d0c-b962-2b89e76e761d_4123ba141fe8.gz  6934141d-9f87-49b6-90b5-5ad28e5e7ccd_4123ba141fe8.gz
9cdd2577-5a2c-4eeb-b513-3eaed3c76cbc_4123ba141fe8.gz  f22883ec-43f9-4392-95de-84f939b598f2_4123ba141fe8.gz
345927c1-77fa-4104-b1ff-1751d9a6f693_4123ba141fe8.gz  7588cad0-4f8f-4807-bdbc-0ae304e21ed9_4123ba141fe8.gz
a40bec3f-6267-4e46-9e28-71ff08ece46c_4123ba141fe8.gz  f81e79d5-379b-4540-b98b-3ce49424dc0a_4123ba141fe8.gz

```

In this example, the ETL jobs were run once on each worker serverice. This solution isn't viable for our needs. Instead, we would like to have our workers take tasks from a queue whereby they run unique operations simultaneously, but never the identical task. We've validated some other popular services within the repo for you to explore.

# How to Use

## Local Development

To test/debug these services, each service can be started locally by executing the script in bash. A Redis service must be running, and can easily be started separate from the other docker services. The following commands will have the server application running locally

```bash

export $(cat .env) && \
docker-compose -f compose/docker-compose.redis.yml up -d redis build_db && \
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
docker-compose -f compose/docker-compose.redis.yml up -d build_db

```

## Production

Spinning up a production application with docker-compose is simple. Follow the commands below, replacing `${PLAYERS}` with the required participants.

```bash

export PLAYERS=10
docker-compose --env-file .env -f compose/docker-compose.redis.yml build && \
docker-compose --env-file .env -f compose/docker-compose.redis.yml up --scale player=${PLAYERS}

```

We can scale the workers with the following

```bash

export PLAYERS=10
export WORKERS=4
docker-compose --env-file .env -f compose/docker-compose.redis.yml build && \
docker-compose --env-file .env -f compose/docker-compose.redis.yml up --scale worker=${WORKERS} --scale player=${PLAYERS}

```

