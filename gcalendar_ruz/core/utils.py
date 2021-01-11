import re
from functools import wraps
import asyncio
import sys
from loguru import logger


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


async def init_semaphore() -> asyncio.Semaphore:
    return asyncio.Semaphore(10)


def semlock(service: str):
    def wrap(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> dict:
            if service == "google":
                sem = sem_google
            elif service == "nvr":
                sem = sem_nvr
            elif service == "ruz":
                sem = sem_ruz
            else:
                logger.error("Unsupported service")
                sys.exit(1)

            async with sem:
                logger.debug(f"{service} semaphore for function {func.__name__}")
                return await func(*args, **kwargs)

        return wrapper

    return wrap


async def main():
    global sem_google
    global sem_ruz
    global sem_nvr

    sem_google = await init_semaphore()
    sem_ruz = await init_semaphore()
    sem_nvr = await init_semaphore()


asyncio.run(main())
