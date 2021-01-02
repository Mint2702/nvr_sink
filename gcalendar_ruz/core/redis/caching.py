import redis
import sys
from datetime import timedelta
import json

from ..settings import settings


HOST = settings.host
PORT = settings.port


def redis_connect() -> redis.client.Redis:
    """ Connecting with redis """

    try:
        client = redis.Redis(host=HOST, port=PORT)
        ping = client.ping()
        if ping is True:
            print("Connection successful")
            return client
    except Exception:
        print("Connection with redis failed")
        sys.exit(1)


def get_routes_from_cache(key: str) -> str:
    """ Get data from redis """

    value = client.get(key)
    return value


def set_routes_to_cache(key: str, value: str) -> bool:
    """ Set data to redis """

    state = client.setex(key, timedelta(seconds=600), value=value)
    return state


def cache(key: str):
    def decorator(func):
        import time

        def wrapper(*args, **kwargs) -> dict:
            """
            Checks if info with given key is in redis
            If it is, returns data, if not, sends a request
            If a function has it's unique value that needs to be used as a key in redis, it must start with '_'
            """

            start = time.time()
            new_key = key
            for arg_name, arg_value in kwargs.items():
                if arg_name[0] == "_":
                    new_key = f"{key}_{arg_value}"
                    break
            data = get_routes_from_cache(new_key)

            if data is not None:
                data = json.loads(data)
                print("Getting data from cach")
                end = time.time()
                print("Время выполнения: {} секунд.".format(end - start))
                return data

            print("Getting data from remote source")
            data = func(*args, **kwargs)
            if data:
                data = json.dumps(data)
                print(new_key)
                state = set_routes_to_cache(key=new_key, value=data)

                if state is True:
                    end = time.time()
                    print("Время выполнения: {} секунд.".format(end - start))
                    return json.loads(data)

            end = time.time()
            print("Время выполнения: {} секунд.".format(end - start))
            return data

        return wrapper

    return decorator


client = redis_connect()
