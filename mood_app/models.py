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
    username = sa.Column(sa.String(20), nullable=False, unique=True)
    password_hash = sa.Column(sa.String(128), nullable=False)
    current_streak = sa.Column(sa.Integer, nullable=False, default=0)
    longest_streak = sa.Column(sa.Integer, nullable=False, default=0)
    streak_ranking = sa.Column(sa.Integer, nullable=True, default=0)
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
            f"streak_ranking: {self.streak_ranking}"
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


class MetaData(Base):
    """
    Stores the current user count to
    prevent the need to scan all rows in
    the user table.
    """
    __tablename__ = "metadata"
    id = sa.Column(sa.Integer, primary_key=True)
    user_count = sa.Column(sa.Integer, nullable=False, default=0)


def set_postgres_event_listeners():
    """
    Add a postgres trigger function that
    keeps a running count of all users in the database.
    This helps prevent running a full scan of
    the users table when an exact count of
    all users is needed.
    """
    user = sa.inspect(User).local_table
    metadata = sa.inspect(MetaData).local_table
    postgres_function = sa.DDL(
        """
        CREATE OR REPLACE FUNCTION public.user_count_trigger_function()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
        IF (TG_OP = 'INSERT') THEN
            UPDATE metadata SET user_count = user_count + 1 WHERE id = 0;
        RETURN NEW;
        END IF;
        END;
        $function$
        """
    )

    insert_metadata_row = sa.DDL(
        """
        INSERT INTO metadata VALUES (0, 0);
        """
    )

    postgres_trigger = sa.DDL(
        """
        CREATE TRIGGER user_after_insert_trigger AFTER INSERT ON public.user EXECUTE FUNCTION user_count_trigger_function()
        """
    )

    sa.event.listen(
        user,
        "after_create",
        postgres_function.execute_if(dialect="postgresql")
    )
    sa.event.listen(
        user,
        "after_create",
        postgres_trigger.execute_if(dialect="postgresql")
    )
    sa.event.listen(
        metadata,
        "after_create",
        insert_metadata_row.execute_if(dialect="postgresql")
    )

set_postgres_event_listeners()
