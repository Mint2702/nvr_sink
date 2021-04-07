import re
from functools import wraps
import asyncio
from loguru import logger
import time
import sys
import smtplib

from .settings import settings


GOOGLE = "google"
NVR = "nvr"
RUZ = "ruz"

sem_dict = {
    NVR: asyncio.Semaphore(100),
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


def token_check(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.creds or self.creds.expired:
            logger.info("Refresh google tokens")
            self.refresh_token()

        self.HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.creds.token}",
        }

        return await func(self, *args, **kwargs)

    return wrapper


def handle_google_errors(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        try:
            error = result["error"]
        except Exception:
            error = None
            return result

        if error:
            try:
                error_reason = error["errors"][0]["reason"]
            except Exception:
                error_reason = None

            if error_reason == "rateLimitExceeded":
                logger.error("Rate limit for google exceeded")
                time.sleep(11)
                return await wrapper(self, *args, **kwargs)
            elif error_reason == "quotaExceeded":
                logger.error("Usage limit for google exceeded")
                sys.exit(1)
            else:
                logger.error(f"Other reason  -  {result}")

        else:
            return result

    return wrapper


def alert(mail: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
            except Exception as error:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(mail, settings.gmail_password)
                logger.info("Login success")
                message = f"Gcalendar_ruz has an error - {error}"
                server.sendmail(mail, mail, message)
                logger.info("Email sent!")
                server.close()
                raise Exception

        return wrapper

    return decorator
