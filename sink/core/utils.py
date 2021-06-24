import re
from functools import wraps
import asyncio
from loguru import logger
import time
import sys
from aiohttp import client_exceptions


GOOGLE = "google"
NVR = "nvr"
RUZ = "ruz"

sem_dict = {
    NVR: asyncio.Semaphore(50),
    GOOGLE: asyncio.Semaphore(5),
    RUZ: asyncio.Semaphore(10),
}


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def semlock(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        service = self.SERVICE
        sem = sem_dict.get(service)
        if not sem:
            logger.error("Unsupported service")

        async with sem:
            return await func(self, *args, **kwargs)

    return wrapper


def handle_ruz_error(func):
    @wraps(func)
    async def wrapper(self, *args, recursion_depth=0, **kwargs):
        try:
            result = await func(self, *args, **kwargs)
            return result
        except client_exceptions.ClientOSError or client_exceptions.ServerDisconnectedError:
            sleep_time = 10 + 5 * recursion_depth
            logger.error(f"Ruz exception. Sleeping for {sleep_time} sec...")
            time.sleep(sleep_time)
            return await wrapper(
                self, *args, recursion_depth=recursion_depth + 1, **kwargs
            )

    return wrapper
