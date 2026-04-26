import os
from huey import RedisHuey, SqliteHuey

REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    huey = RedisHuey('playto_payouts', url=REDIS_URL)
else:
    huey = SqliteHuey('playto_payouts')
