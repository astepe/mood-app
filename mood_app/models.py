"""
Contains all SQL table configurations
"""
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

Base = declarative_base()


class MoodEnum(Enum):
    """
    All possible mood choices
    """
    CHEERFUL = 1
    REFLECTIVE = 2
    GLOOMY = 3
    HUMOROUS = 4
    MELANCHOLY = 5
    IDYLLIC = 6
    WHIMSICAL = 7
    ROMANTIC = 8


class User(Base):
    """
    Stores username, password and mood streak
    information for each registered user.
    """
    __tablename__ = "user"
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(20), nullable=False, unique=True, index=True)
    password_hash = sa.Column(sa.String(128), nullable=False)
    current_streak = sa.Column(sa.Integer, nullable=False, default=0)
    longest_streak = sa.Column(sa.Integer, nullable=False, default=0)
    streak_percentile = sa.Column(sa.Float, nullable=True, default=0.0)
    moods = relationship("Mood", cascade="all, delete")

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Verify that the provided plain-text
        password matched its hashed value in the
        DB.

        Args:
            password (str): The incoming password to check.

        Returns:
            bool: True if the password is correct. False if
                  the password is incorrect.
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return (
            f"<User> username: {self.username}, \n"
            f"current_streak: {self.current_streak}, \n"
            f"longest_streak: {self.longest_streak}, \n"
            f"streak_percentile: {self.streak_percentile} \n"
        )


class Mood(Base):
    """
    Stores a user moods and dates when each mood
    was recorded.
    """
    __tablename__ = "mood"
    id = sa.Column(sa.Integer, primary_key=True)
    mood = sa.Column(sa.Enum(MoodEnum), nullable=False)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date = sa.Column(sa.DateTime(), default=sa.func.now())
