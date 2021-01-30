import re
from functools import wraps
import asyncio
from loguru import logger


GOOGLE = "google"
NVR = "nvr"
RUZ = "ruz"

sem_dict = {
    NVR: asyncio.Semaphore(100),
    GOOGLE: asyncio.Semaphore(3),
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
            # logger.debug(f"{service} semaphore for function {func.__name__}")
            return await func(self, *args, **kwargs)

    return wrapper


def token_check(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.creds or self.creds.expired:
            logger.info("Refresh google tokens")
            self.refresh_token()

        return await func(self, *args, **kwargs)

    return wrapper
