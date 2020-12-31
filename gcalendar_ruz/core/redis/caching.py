import redis
import sys
from datetime import timedelta
import json

from ..settings import settings


HOST = settings.host
PORT = settings.port


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


def get_routes_from_cache(key: str) -> str:
    """ Get data from redis """

    value = client.get(key)
    return value


def set_routes_to_cache(key: str, value: str) -> bool:
    """ Set data to redis """

    state = client.setex(key, timedelta(seconds=300), value=value)
    return state


def cach(func):
    import time

    def wrapper(key: str, *args, **kwargs) -> dict:
        """ Decorator """

        start = time.time()
        data = get_routes_from_cache(key)

        if data is not None:
            data = json.loads(data)
            print("Cach")
            # data["cache"] = True
            end = time.time()
            print("[*] Время выполнения: {} секунд.".format(end - start))
            return data

        else:
            data = func(*args, **kwargs)
            if data:
                # data["cache"] = False
                data = json.dumps(data)
                state = set_routes_to_cache(key=key, value=data)

                if state is True:
                    end = time.time()
                    print("[*] Время выполнения: {} секунд.".format(end - start))
                    return json.loads(data)
        end = time.time()
        print("[*] Время выполнения: {} секунд.".format(end - start))
        return data

    return wrapper


client = redis_connect()
