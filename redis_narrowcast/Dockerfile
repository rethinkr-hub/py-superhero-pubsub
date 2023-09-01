FROM python/datasim/superhero

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./lib/pubsub/redis.py ./lib/pubsub
COPY ./lib/model ./lib/model
COPY ./lib/worker ./lib/worker
COPY ./worker_narrowcast.py .
COPY ./worker.py .
