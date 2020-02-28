from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    tracking_state = Column(Boolean, default=False)
    sources = relationship('Source', backref='room', lazy=False)
    drive = Column(String(200))
    calendar = Column(String(200))

    sound_source = Column(String(100))
    main_source = Column(String(100))
    tracking_source = Column(String(100))
    screen_source = Column(String(100))

    auto_control = Column(Boolean, default=True)

    def to_dict(self):
            return dict(id=self.id,
                        name=self.name,
                        tracking_state=self.tracking_state,
                        sources=[source.to_dict() for source in self.sources],
                        drive=self.drive,
                        calendar=self.calendar,
                        sound_source=self.sound_source,
                        main_source=self.main_source,
                        tracking_source=self.tracking_source,
                        screen_source=self.screen_source,
                        auto_control=self.auto_control)

class Source(Base):
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), default='источник')
    ip = Column(String(200))
    port = Column(String(200))
    rtsp = Column(String(200), default='no')
    audio = Column(String(200))
    merge = Column(String(200))
    tracking = Column(String(200))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    
    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    ip=self.ip,
                    port=self.port,
                    rtsp=self.rtsp,
                    audio=self.audio,
                    merge=self.audio,
                    tracking=self.tracking,
                    room_id=self.room_id)
