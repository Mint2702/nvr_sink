import redis
import sys
from ..settings import settings


HOST = settings.host
PORT = settings.port
print(HOST)


def redis_connect() -> redis.client.Redis:
    try:
        client = redis.Redis(host=HOST, port=PORT)
        ping = client.ping()
        if ping is True:
            print("OK")
            return client
    except Exception:
        print("Exception")
        sys.exit(1)


client = redis_connect()
