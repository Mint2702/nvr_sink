import re
from functools import wraps
import asyncio
from loguru import logger


GOOGLE = "google"
NVR = "nvr"
RUZ = "ruz"

sem_dict = {
    NVR: asyncio.Semaphore(10),
    GOOGLE: asyncio.Semaphore(10),
    RUZ: asyncio.Semaphore(10),
}


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
