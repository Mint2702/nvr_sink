from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CommonMixin:
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())


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

    def to_dict(self):
        return dict(
            name=self.name,
            calendar=self.calendar,
        )
