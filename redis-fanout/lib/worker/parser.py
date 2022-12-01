import pyarrow.parquet as pq
import pyarrow as pa
import importlib
import logging
import random
import os

# Environment Variables
OUTPUT_DIR=os.getenv('OUTPUT_DIR', '/usr/local/data')
HOSTNAME=str(os.getenv('HOSTNAME', random.randint(1000, 9999)))
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

# Setup
logger_module = importlib.import_module('lib.utils.loggers.%s' % LOGGER_MODULE)

QUEUE='worker.%s' % __name__
logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

class ETL_Client:
    
    @property
    def game_token(self):
        return self._game_token
    
    @game_token.setter
    def game_token(self, game_token):
        self._game_token = game_token

    def extract(self, msg):
        logging.debug('Extracting Message from bytes')
        if isinstance(msg, set):
            return [self.extract(m) for m in list(msg)]
        elif isinstance(msg, list):
            return [self.extract(m) for m in msg]
        
        return msg.decode('utf8')
    
    def load(self, data, schema, schema_name):
        def write(tbl, path, game_token):
            logger.debug('Writing Data to Parquet')
            file_path = '%s_%s.parquet.gz' % (os.path.join(path, game_token), HOSTNAME)
            handle = pq.ParquetWriter(file_path, schema, compression='gzip')
            if os.path.exists(file_path):
                tbl_original = pq.read_table(source=file_path,  pre_buffer=False, use_threads=True, memory_map=True)
                handle.write_table(tbl_original)

            handle.write_table(tbl)
            handle.close()

        logging.debug('Transforming/Loading Data to Paquet')
        map = {}
        for k in schema.names:
            map[k] = []
    
        for r in data:
            for k in r.keys():
                map[k].append(r[k])
    
        tbl = pa.Table.from_pydict(
            dict(zip(schema.names, tuple([map[c] for c in map.keys()]))),
            schema=schema
        )

        path = os.path.join(OUTPUT_DIR, 'superhero', schema_name)
        if not os.path.isdir(path):
            os.makedirs(path)
        
        #write(tbl, path, self.game_token)
        pq.write_table(
            tbl,
            where='%s_%s.gz' % (os.path.join(OUTPUT_DIR, 'superhero', schema_name, self.game_token), HOSTNAME),
            compression='gzip'
        )

class ETL_Game_Meta(ETL_Client):

    def transform_game_meta(self, participants, ids):
        logging.debug('Transforming Game Meta to Array')
        return [{
            'game_token': self.game_token,
            'user_token': p,
            'superhero_id': int(v)
        } for p,v in zip(participants, ids)]

class ETL_Game_Podium(ETL_Client):

    def transform_game_podium(self, participants, logs):
        def deliver(m):
            user_token = m['PAYLOAD']['USER_TOKEN']
            damage_delivered = m['STATUS']['DETAILS']['ENEMY_DAMAGE']

            if not user_token in podium:
                podium[user_token] = {
                    'rounds': 0,
                    'rank': 1,
                    'damage_delivered': 0,
                    'damage_received': 0
                }
                
            podium[user_token]['rounds'] = podium[user_token].get('rounds', 0) + 1
            podium[user_token]['damage_delivered'] = podium[user_token].get('damage_delivered', 0) + damage_delivered
        
        def receive(m, rank):
            user_token = m['STATUS']['DETAILS']['ENEMY_TOKEN']
            damage_received = m['STATUS']['DETAILS']['ENEMY_DAMAGE']

            if not user_token in podium:
                podium[user_token] = {
                    'rounds': 0,
                    'rank': 1,
                    'damage_delivered': 0,
                    'damage_received': 0
                }
            
            podium[user_token]['damage_received'] = podium[user_token].get('damage_received', 0) + damage_received
            if m['STATUS']['DETAILS']['ENEMY_HEALTH_POST'] == 0:
                podium[user_token]['rank'] = rank
                rank += 1
            
            return rank

        logging.debug('Transforming Game Podium to Array')
        podium = {}
        rank = int(participants)

        for m in logs:
            if 'STATUS' in m and 'ACTION' in m['STATUS'] and m['STATUS']['ACTION'] == 'ATTACK':
                deliver(m)
                rank = receive(m, rank)
        
        return [{
            'game_token': self.game_token,
            'user_token': p,
            'rounds': v['rounds'],
            'rank': v['rank'],
            'damage_delivered': v['damage_delivered'],
            'damage_received': v['damage_received'],
        } for p,v in podium.items()]
    