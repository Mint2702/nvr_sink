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


def dict_compare(d1: dict, d2: dict) -> bool:
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
    same = set(o for o in shared_keys if d1[o] == d2[o])
    if added == set() and removed == set() and modified == {}:
        return True
    else:
        return False
