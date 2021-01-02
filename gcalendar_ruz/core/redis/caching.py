import asyncio
from aredis import StrictRedis
import sys
from datetime import timedelta
import json

from ..settings import settings


HOST = settings.host
PORT = settings.port


async def redis_connect() -> StrictRedis:
    """ Connecting with redis """

    try:
        client = StrictRedis(host=HOST, port=PORT)
        ping = await client.ping()
        if ping is True:
            print("Connection successful")
            return client
    except Exception:
        print("Connection with redis failed")
        sys.exit(1)


async def get_routes_from_cache(key: str) -> str:
    """ Get data from redis """

    value = await client.get(key)
    return value


async def set_routes_to_cache(key: str, value: str) -> bool:
    """ Set data to redis """

    state = await client.setex(key, timedelta(seconds=600), value=value)
    return state


def cach(key: str):
    def decorator(func):
        import time

        async def wrapper(*args, **kwargs) -> dict:
            """
            Checks if info with given key is in redis
            If it is, returns data, if not, sends a request
            If a function has it's unique value that needs to be used as a key in redis, it must start with '_'
            """

            new_key = key
            for arg_name, arg_value in kwargs.items():
                if arg_name[0] == "_":
                    new_key = f"{key}_{arg_value}"
                    break
            data = await get_routes_from_cache(new_key)

            if data is not None:
                data = json.loads(data)
                print("Getting data from cach")
                return data

            print("Getting data from remote source")
            data = await func(*args, **kwargs)
            if data:
                data = json.dumps(data)
                print(new_key)
                state = set_routes_to_cache(key=new_key, value=data)

                if state is True:
                    return json.loads(data)

            return data

        return wrapper

    return decorator


@cach("lol")
async def job(*args, **kwargs):
    print("example_results")


async def main():
    global client
    client = await redis_connect()
    await job(111)


asyncio.run(main())