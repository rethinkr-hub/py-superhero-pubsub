# Super Hero Combat Simulator - Pub/Sub - Redis - Parquet - Fanout

From the Pub/Sub - Redis example, we quickly saw the drawbacks to using Redis' Out-of-the-Box (OOTB) solution for this application's requirements. Instead, the simulator worker is more suitable to a queue messaging system where all workers are given unique tasks to complete.

In this example, we can create our own **Fanout** within Redis' Pub/Sub framework to broadcast unique messages to all the workers.

# Overview

## Worker_Fanout

The Fanout service is a middleware subscriber we dedicate to receiving all messages in the `redis.lib.server.lobby` channel, and then randomly publishing back to a worker's unique channel - following the pattern `redis.lib.server.lobby-*`. Middleware is a common technique used to insert logic between the Publisher and Subscriber.

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

Similar to the test in Pub/Sub Redis, we can deploy the application following this code sample below

```bash

export PLAYERS=10
export WORKERS=4
docker-compose --env-file .env -f compose/docker-compose.fanout.yml build && \
docker-compose --env-file .env -f compose/docker-compose.fanout.yml up --scale worker=${WORKERS} --scale player=${PLAYERS}

```

Once the simulation has completed, we can review the paquet file creation from the worker instances

```bas

docker exec -it compose-worker-1 ls data/superhero/GAME_PODIUM
028cc172-ce6e-444a-ad7f-d0f60651aee4_016cea10bfcb.gz  20eacc76-c0b4-4968-8963-149a0a0ebf4d_016cea10bfcb.gz
d16d2f54-022a-4eab-a7ed-060bad6753ec_016cea10bfcb.gz  fbfc2120-f178-4e8c-85b5-99f0b91a9aae_016cea10bfcb.gz
0892bc91-834b-439b-b382-08882b7ae489_016cea10bfcb.gz  6351bcba-3e18-45b4-aab9-625faf2db56a_016cea10bfcb.gz
d245d11a-b2f1-4ddc-abc9-e08400b3e2a9_016cea10bfcb.gz  146d1f50-da16-47e4-bdcc-639ab8d25229_016cea10bfcb.gz
afdc2bb6-c302-4847-b8f0-fe75f2bb5f90_016cea10bfcb.gz  f49fb27d-0c16-4d71-8c9b-56df195f8d0c_016cea10bfcb.gz

docker exec -it compose-worker-2 ls data/superhero/GAME_PODIUM
24d206e8-f8d2-4c09-a591-0e7edbe27d6b_6265457077b3.gz  7a071df1-044c-4e58-ad9d-e10e4ac4e3f4_6265457077b3.gz
a3c4d894-5248-4abf-9827-1463eb59f780_6265457077b3.gz  5d97cd46-285d-47cc-a1ac-e290c310b571_6265457077b3.gz
80ecd360-ab17-4a4d-a99b-6d34ee34264d_6265457077b3.gz  dcac55d8-c5c9-4cb6-bd78-83cf736484df_6265457077b3.gz
64822852-1164-4619-a7ce-1fe956c9e231_6265457077b3.gz  8a0d081f-8abe-4fdf-8a4d-ccc9381617cf_6265457077b3.gz
f4084ab7-9335-471f-aa73-c377ecbb16cb_6265457077b3.gz

docker exec -it compose-worker-3 ls data/superhero/GAME_PODIUM
0bb9bbde-d329-425c-adc7-b56d9b7a5869_6327963e7360.gz  60489b45-dd8c-4414-b49c-2c47215fbe28_6327963e7360.gz
8e0b34b7-b535-4ac8-b823-541977b0fe26_6327963e7360.gz  cb214239-233d-45bf-9a35-204fd0ecb730_6327963e7360.gz
566acc9c-f48a-48ab-aec5-b1e524f85b6f_6327963e7360.gz  71bc9451-a7d9-4c87-bf94-d4290e6da661_6327963e7360.gz
b067a742-71ab-4f87-b821-794cff69e777_6327963e7360.gz  f0c047bb-c371-46ce-afc4-75d56edbadf4_6327963e7360.gz

docker exec -it compose-worker-4 ls data/superhero/GAME_PODIUM
01085fd7-e3a4-48a5-bbbb-04da114a4146_46e3cbfe99f2.gz  01500a78-1ab4-4df5-84b7-e0e6c2b951fb_46e3cbfe99f2.gz
141dbb59-d1c7-4a00-a08e-6fc97510fafb_46e3cbfe99f2.gz  23a977dc-5dfa-4d04-ac64-8c61b9488109_46e3cbfe99f2.gz
6be21d0f-6610-4ed3-8a2b-f3ffdba5fd5d_46e3cbfe99f2.gz  9cbef64e-65e1-4297-8ca1-b481fd2caad1_46e3cbfe99f2.gz
a5e579f3-d208-4df3-a13a-c4da2a4c3748_46e3cbfe99f2.gz  c0b87cc3-d4df-4e68-b9c6-cd28860bba9b_46e3cbfe99f2.gz
cede7812-39cd-4a44-a203-1aaa68fa65cd_46e3cbfe99f2.gz  d5838d7a-d10c-486b-9d0a-9c691ce498b7_46e3cbfe99f2.gz
dcccc8a5-e7b0-4269-891d-e87bce6550d0_46e3cbfe99f2.gz

```

Here we've come one step closer to building a sustainable Pub/Sub service which processes independent tasks scaled over multiple workers. The Fanout service was a quick way to spread out tasks amongst the workers, so that nothing was being processed more than once. This example doesn't actually replicate a message queue system, but instead fans out a broadcast message to a narrower focus group.

In terms of sustainability, this approach still doesn't meet other service's levels of fail-over supoport and resiliency in message delivery/acknowledgment. This is where other popular solutions will be used, instead of trying to recreate the wheel with Redis.

# How to Use

## Local Development

To test/debug these services, each service can be started locally by executing the script in bash. A Redis service must be running, and can easily be started separate from the other docker services. The following commands will have the server application running locally

```bash

export $(cat .env) && \
docker-compose -f compose/docker-compose.fanout.yml up -d redis build_db && \
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
docker-compose -f compose/docker-compose.fanout.yml up -d build_db

```

## Production

Spinning up a production application with docker-compose is simple. Follow the commands below, replacing `${PLAYERS}` with the required participants.

```bash

export PLAYERS=10
docker-compose --env-file .env -f compose/docker-compose.fanout.yml build && \
docker-compose --env-file .env -f compose/docker-compose.fanout.yml up --scale player=${PLAYERS}

```

We can scale the workers with the following

```bash

export PLAYERS=10
export WORKERS=4
docker-compose --env-file .env -f compose/docker-compose.fanout.yml build && \
docker-compose --env-file .env -f compose/docker-compose.fanout.yml up --scale worker=${WORKERS} --scale player=${PLAYERS}

```

