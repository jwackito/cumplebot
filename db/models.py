from sqlalchemy import Boolean, Column, Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    birthday = Column(Date, nullable=False)
    custom_message = Column(String, nullable=True)
    is_private = Column(Boolean, default=False)
    registered_by_tg_id = Column(Integer, nullable=False)

    subscriptions = relationship("Subscription", back_populates="person", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    subscriber_tg_id = Column(Integer, nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    last_notified_date = Column(Date, nullable=True)

    person = relationship("Person", back_populates="subscriptions")

    __table_args__ = (UniqueConstraint("subscriber_tg_id", "person_id", name="uq_subscriber_person"),)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    tg_id = Column(Integer, primary_key=True)
    notification_time = Column(String, nullable=False, default="09:00")


class BotUser(Base):
    __tablename__ = "bot_users"

    tg_id = Column(Integer, primary_key=True)
