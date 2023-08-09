import logging
import random
import gzip
import json
import os

# Environment Variables
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')
OUTPUT_DIR=os.getenv('OUTPUT_DIR', '/usr/local/data')
HOSTNAME=str(os.getenv('HOSTNAME', random.randint(1000, 9999)))

# Setup
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
    
    def load(self, data, table_name):
        file_path = os.path.join(OUTPUT_DIR, 'superhero', table_name, f'{self.game_token}_{HOSTNAME}.gz')
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        
        with gzip.open(file_path, 'wt') as f:
            f.write(json.dumps(data))

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
    