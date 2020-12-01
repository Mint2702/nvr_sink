import os
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()
engine = create_engine(os.environ.get("DB_URL"))
Session = sessionmaker(bind=engine)


class IdMixin:
    id = Column(Integer, primary_key=True)


class TimeMixin:
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CommonMixin(IdMixin, TimeMixin):
    pass


class Room(Base, CommonMixin):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    tracking_state = Column(Boolean, default=False)
    ruz_id = Column(Integer)
    drive = Column(String(200))
    calendar = Column(String(200))

    sound_source = Column(String(100))
    main_source = Column(String(100))
    tracking_source = Column(String(100))
    screen_source = Column(String(100))

    auto_control = Column(Boolean, default=True)


class OnlineRoom(Base, CommonMixin):
    __tablename__ = "online_rooms"

    name = Column(String(100), nullable=False, unique=True)
    calendar = Column(String(200))


class Record(Base, CommonMixin):
    __tablename__ = "records"

    date = Column(String(100), nullable=False)
    start_time = Column(String(100), nullable=False)
    end_time = Column(String(100), nullable=False)
    event_name = Column(String(200))
    event_id = Column(String(200), unique=True)
    drive_file_url = Column(String(200))
    ruz_id = Column(Integer, unique=True)  # lessonOid from ruz API

    done = Column(Boolean, default=False)
    processing = Column(Boolean, default=False)
    error = Column(Boolean, default=False)

    room_id = Column(Integer, ForeignKey("rooms.id"))
    room = relationship("Room", back_populates="records")
    users = relationship("UserRecord", back_populates="record")


class UserRecord(Base, TimeMixin):
    __tablename__ = "user_records"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    record_id = Column(Integer, ForeignKey("records.id"), primary_key=True)

    user = relationship("User", back_populates="records")
    record = relationship("Record", back_populates="users")


class User(Base, CommonMixin):
    __tablename__ = "users"

    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), default=None)
    role = Column(String(50), default="user")
    email_verified = Column(Boolean, default=False)
    access = Column(Boolean, default=False)
    api_key = Column(String(255), unique=True)
    last_login = Column(DateTime, default=datetime.utcnow)

    records = relationship("UserRecord", back_populates="user")
