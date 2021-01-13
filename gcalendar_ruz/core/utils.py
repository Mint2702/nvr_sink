import re
from functools import wraps
import asyncio
from loguru import logger


GOOGLE = "google"
NVR = "nvr"
RUZ = "ruz"

sem_dict = {
    NVR: asyncio.Semaphore(3),
    GOOGLE: asyncio.Semaphore(1),
    RUZ: asyncio.Semaphore(3),
}


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def semlock(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        service = self.SERVICE
        print(service)
        sem = sem_dict.get(service)
        if not sem:
            logger.error("Unsupported service")

        print(f"{service} - {sem._value} ")
        async with sem:
            logger.debug(f"{service} semaphore for function {func.__name__}")
            return await func(self, *args, **kwargs)

    return wrapper
