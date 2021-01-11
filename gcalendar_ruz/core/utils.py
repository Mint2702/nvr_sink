import re
from functools import wraps
import asyncio
from loguru import logger


GOOGLE = "google"
NVR = "nvr"
RUZ = "ruz"


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def semlock(service: str):
    def wrap(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> dict:
            sem = sem_dict.get(service)
            if not sem:
                logger.error("Unsupported service")

            async with sem:
                logger.debug(f"{service} semaphore for function {func.__name__}")
                return await func(*args, **kwargs)

        return wrapper

    return wrap


async def main():
    global sem_google
    global sem_ruz
    global sem_nvr
    global sem_dict

    sem_google = asyncio.Semaphore(10)
    sem_ruz = asyncio.Semaphore(10)
    sem_nvr = asyncio.Semaphore(10)
    sem_dict = {NVR: sem_nvr, GOOGLE: sem_google, RUZ: sem_ruz}


asyncio.run(main())
