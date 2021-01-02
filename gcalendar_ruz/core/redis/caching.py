import asyncio
from aredis import StrictRedis
import sys
from datetime import timedelta
import json
import copy

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
                print("Getting data from cach")
                data_list = copy.deepcopy(data)
                data_list = json.loads(data_list)
                return data_list

            print("Getting data from remote source")
            data = await func(*args, **kwargs)
            if data:
                print(type(data))
                data_list = copy.deepcopy(list(data))
                print(type(data_list))
                data_list = json.dumps(data_list)
                # new_data = json.dumps(data)
                state = await set_routes_to_cache(key=new_key, value=data_list)
                if state is True:
                    return json.loads(data_list)

            return []

        return wrapper

    return decorator


async def main():
    """ Creating redis client """

    global client
    client = await redis_connect()


asyncio.run(main())
