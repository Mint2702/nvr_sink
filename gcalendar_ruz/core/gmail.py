import smtplib
from loguru import logger
from functools import wraps

from typing import Optional
from pydantic import BaseSettings, Field


class Gmail_info(BaseSettings):
    gmail_password: Optional[str] = Field(None, env="GMAIL_PASSWORD")
    gmail: Optional[str] = Field(None, env="GMAIL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Gmail:
    def __init__(self) -> None:
        self.server = None
        self.password = self.get_password()
        self.gmail = self.get_gmail()
        if self.password is None:
            logger.warning("Password not found, alert can't be done")
        if self.gmail is None:
            logger.warning("Gmail not found, alert can't be done")

    def __del__(self) -> None:
        if self.server:
            self.server.close()

    def get_password(self) -> str or None:
        gmail_info = Gmail_info(_env_file="../.env")
        password = gmail_info.gmail_password
        return password

    def get_gmail(self) -> str or None:
        gmail_info = Gmail_info(_env_file="../.env")
        mail = gmail_info.gmail
        return mail

    def start_server(self) -> None:
        try:
            self.server = smtplib.SMTP("smtp.gmail.com", 587)
            self.server.starttls()
        except:
            logger.warning("SMTP server failed to start")
            self.server = None

    def login(self) -> bool:
        try:
            self.server.login(self.gmail, self.password)
            logger.info("Login success")
            return True
        except:
            logger.warning("Login failed")
            return False

    def create_message(self, error: str) -> str:
        message = f"Gcalendar_ruz module failed with an error - {error}"
        return message

    def send_gmail_to_myself(self, message: str):
        self.start_server()
        if self.server:
            loged = self.login()
            if loged:
                self.server.sendmail(self.gmail, self.gmail, message)
                logger.info("Gmail sent")


gmail = Gmail()


def alert_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as error:
            message = gmail.create_message(error)
            gmail.send_gmail_to_myself(message)
            raise Exception

    return wrapper


def alert_sync(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as error:
            message = gmail.create_message(error)
            gmail.send_gmail_to_myself(message)
            raise Exception

    return wrapper
