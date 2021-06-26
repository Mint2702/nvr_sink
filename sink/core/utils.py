import re
from functools import wraps
from loguru import logger
import time
import sys
from httpx import ConnectTimeout, ReadTimeout


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def handle_web_errors(func):
    @wraps(func)
    def wrapper(self, *args, recursion_depth=0, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except ConnectTimeout or ReadTimeout:
            sleep_time = 10 + 5 * recursion_depth
            logger.error(f"Ruz exception. Sleeping for {sleep_time} sec...")
            time.sleep(sleep_time)
            return wrapper(self, *args, recursion_depth=recursion_depth + 1, **kwargs)

    return wrapper
