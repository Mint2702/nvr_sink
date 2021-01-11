import asyncio
from aredis import StrictRedis
from datetime import timedelta
import json
from functools import wraps
from loguru import logger

from ..settings import settings


HOST = settings.host
PORT = settings.port


async def redis_connect() -> StrictRedis:
    """ Connecting with redis """

    global client

    try:
        client = StrictRedis(host=HOST, port=PORT)
        ping = await client.ping()
        if ping is True:
            logger.info("Connection with redis successful")
            return client
    except Exception:
        logger.error("Connection with redis failed")
        client = None


async def get_routes_from_cache(key: str) -> str:
    """ Get data from redis """

    value = await client.get(key)
    return value


async def set_routes_to_cache(key: str, value: str) -> bool:
    """ Set data to redis """

    state = await client.setex(key, timedelta(seconds=600), value=value)
    return state


def cache(func):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> dict:
        """
        Checks if info with given key is in redis
        If it is, returns data, if not, sends a request
        """

        if client:
            cache_key = f"{func.__name__}({args[1:]}, {kwargs})"
            data = await get_routes_from_cache(cache_key)

            if data:
                logger.info("Getting data from cach")
                data = json.loads(data)
                return data

        logger.info("Getting data from remote source")
        data = await func(*args, **kwargs)
        if data:
            if client:
                state = await set_routes_to_cache(key=cache_key, value=json.dumps(data))
            return data

        return None

    return wrapper
