import re
from functools import wraps
from loguru import logger
import time
import sys
from httpx import ConnectTimeout, ReadTimeout


def handle_web_errors(func):
    @wraps(func)
    def wrapper(self, *args, recursion_depth=0, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return result
        except ConnectTimeout or ReadTimeout:
            sleep_time = 10 + 5 * recursion_depth
            logger.error(f"Web error. Sleeping for {sleep_time} sec...")
            time.sleep(sleep_time)
            return wrapper(self, *args, recursion_depth=recursion_depth + 1, **kwargs)

    return wrapper
