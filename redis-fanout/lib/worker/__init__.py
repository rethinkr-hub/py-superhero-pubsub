#!/usr/bin/env python

# Fork of websockets Quick Start
# https://websockets.readthedocs.io/en/stable/intro/quickstart.html

# Websocket History & Areas of Improvement
# https://ably.com/topic/websockets

from lib.worker.parser import ETL_Game_Meta, ETL_Game_Podium
from lib.model import model_parquet

import importlib
import logging
import redis
import json
import sys
import os

# Enviornment Variables
REDIS_HOST=os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT=int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB=os.getenv('REDIS_DB', 0)
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'CLEAN').upper()
CLEAN_ROUTINE=eval(os.getenv('WORKER_ROUTINE', 'False'))
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

# Setup
logger_module = importlib.import_module('lib.utils.loggers.%s' % LOGGER_MODULE)

QUEUE='worker.%s' % __name__
logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

R_POOL = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
R_CONN = redis.Redis(connection_pool=R_POOL, decode_responses=True)

def clean(msg, host):
    logger.info('Cleaning Records', (msg['game_token'], msg['user_token']))
    
    participants = int(R_CONN.get('games:%s:participants' % msg['game_token']))
    R_CONN.expire('games:%s:order' % msg['game_token'], REDIS_EXPIRY)
    R_CONN.expire('games:%s:status' % msg['game_token'], REDIS_EXPIRY)
    R_CONN.expire('games:%s:participants' % msg['game_token'], REDIS_EXPIRY)
    R_CONN.expire('games:%s:host' % msg['game_token'], REDIS_EXPIRY)
                
    R_CONN.zrem('games:participants', msg['game_token'])
    R_CONN.lrem('games:participants:%d' % participants, 1, msg['game_token'])
    R_CONN.lrem('games:%s:logs' % msg['game_token'])

def etl_game_meta(msg):
    logger.info('Running Game Meta ETL')
    client = ETL_Game_Meta()
    client.game_token = msg['game_token']
    
    # Extract
    participants = client.extract(R_CONN.smembers('games:%s' % msg['game_token']))
    ids = client.extract([R_CONN.hget('games:%s:superheros:%s' % (msg['game_token'], p), 'id') for p in participants])

    if len(participants) > 1:
        # Transform
        data = client.transform_game_meta(participants, ids)

        # Load
        if len(data) > 1:
            client.load(data, model_parquet.SCHEMA_GAME_META_PQ, 'GAME_META')

def etl_game_podium(msg):
    logger.info('Running Game Podium ETL')
    client = ETL_Game_Podium()
    client.game_token = msg['game_token']

    # Extract
    participants = client.extract(R_CONN.get('games:%s:participants' % msg['game_token']))
    logs = client.extract(R_CONN.lrange('games:%s:logs' % msg['game_token'], 0, -1))
    logs = [json.loads(l) for l in logs]

    if len(logs) > 0:
        # Transform
        data = client.transform_game_podium(participants, logs)
    
        # Load
        client.load(data, model_parquet.SCHEMA_GAME_PODIUM_PQ, 'GAME_PODIUM')

def sub_routine(msg):
    logger.info('Running Subscription Routine')
    if isinstance(msg, bytes):
        msg = json.loads(msg.decode('utf8'))
    elif isinstance(msg, str):
        msg = json.loads(msg)
    
    if msg['log_message'] == 'Cleaning Game Records':
        host = R_CONN.get('games:%s:host' % msg['task']['game_token'])
        if host and host.decode('utf8') == msg['task']['user_token']:
            etl_game_meta(msg['task'])
            etl_game_podium(msg['task'])
            
        if CLEAN_ROUTINE:
            R_CONN.expire('games:%s:superheros:%s' % (msg['task']['game_token'], msg['task']['user_token']), REDIS_EXPIRY)
                
            if host:
                clean(msg['task'])