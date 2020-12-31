import redis
import sys

def redis_connect() -> redis.client.Redis:
          try:
                    client = redis.Redis(host = "localhost", port=6379)
                    ping = client.ping()
                    if ping is True:
                              print("OK")
                              return client
          except Exception:
                    print("Exception")
                    sys.exit(1)

client = redis_connect()
