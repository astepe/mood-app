"""
Contains all application routes
"""
import time
from datetime import datetime
from typing import Tuple

from flask import current_app as app
from flask import g, jsonify, request
from flask_httpauth import HTTPBasicAuth
from jsonschema import ValidationError, validate
from sqlalchemy import asc

from .models import Mood, MoodEnum, User
from . import schemas

auth = HTTPBasicAuth()


@app.route("/mood", methods=["POST", "GET"])
@auth.login_required
def mood_post():
    """
    If the HTTP method is POST, record a new mood
    for the curent user. Calculate new mood streaks
    when needed.

    If the HTTP method is GET, return the /mood
    response.

    Returns:
        tuple: Response body, status code
    """
    if request.method == "GET":
        return jsonify(create_mood_response()), 200

    is_valid, error_msg = validate_request(request.json, schemas.mood_request_schema)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    mood = request.json.get("mood")
    timestamp = request.json.get("timestamp", time.time())
    new_mood = Mood(
        mood=getattr(MoodEnum, mood),
        user_id=g.user.id,
        date=datetime.fromtimestamp(timestamp),
    )
    if g.user.moods:
        calculate_streaks(new_mood)
    g.user.moods.append(new_mood)
    response = create_mood_response()
    app.session.commit()

    return jsonify(response), 200


@app.route("/user", methods=["POST"])
def register_post():
    """
    Register a new user onto the mood app.

    Returns:
        tuple: response body, status code
    """
    is_valid, error_msg = validate_request(
        request.json, schemas.register_request_schema
    )
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    username = request.json.get("username")
    password = request.json.get("password")

    if app.session.query(User).filter_by(username=username).first() is not None:
        return (
            jsonify(
                {
                    "error": f"username '{username}' already exists. Please try again."
                }
            ),
            400,
        )
    user = User(username=username, password=password)
    app.session.add(user)
    app.session.commit()

    return jsonify({"username": username}), 201


@auth.verify_password
def verify_password(username: str, password: str) -> bool:
    """
    Given a username and password, verify that
    both the user exists in the DB and that the password
    is correct. If correct, set the associated user
    as the current user (g.user).

    Args:
        username (str): The username
        password (str): The password

    Returns:
        bool: True if the username and password are correct.
    """
    user = app.session.query(User).filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


def calculate_streaks(new_mood: Mood) -> None:
    """
    Given a new mood object for the current
    user (g.user), increment the user's current
    streak if the user's previous mood record
    was recorded on the previous calendar day.
    If the previous mood was not recorded on the
    previous day, reset the current streak to 0.
    After incrementing the current streak, if the
    new current streak is longer than the user's
    longest streak, update the longest streak
    and recalculate all streak rankings for all users.

    Args:
        new_mood (Mood): The new mood being recorded for
                         the current user (g.user)
    """
    g.user.moods.sort(reverse=True, key=lambda mood: mood.date)
    day_difference = new_mood.date.day - g.user.moods[0].date.day
    if day_difference > 1:
        g.user.current_streak = 0
    elif day_difference == 1:
        g.user.current_streak += 1
        if g.user.current_streak > g.user.longest_streak:
            g.user.longest_streak = g.user.current_streak
            app.session.merge(g.user)
            users = (
                app.session.query(User)
                .order_by(asc(User.longest_streak))
                .with_for_update()
                .all()
            )
            longest_streak = -1
            count = 0
            users_below = 0
            for user in users:
                if user.longest_streak > longest_streak:
                    users_below = count
                longest_streak = user.longest_streak
                user.streak_percentile = round((users_below / len(users)) * 100, 2)
                app.session.merge(user)
                count += 1


def create_mood_response() -> dict:
    """
    Generate a response object for the /mood
    endpoint. Calculate the current user's
    streak percentile. If the streak percentile
    is greater than or equal to 50%, return it
    in the response.

    Returns:
        dict: The /mood response object.
    """
    g.user.moods.sort(reverse=True, key=lambda mood: mood.date)
    response = {
        "currentStreak": g.user.current_streak,
        "longestStreak": g.user.longest_streak,
        "moodHistory": [
            {
                "mood": mood.mood.name,
                "date": mood.date.strftime("%a, %b %d at %I:%M %p"),
            }
            for mood in g.user.moods
        ],
    }

    if g.user.streak_percentile >= 50:
        response["streakPercentile"] = g.user.streak_percentile

    return response


def validate_request(instance: dict, schema: dict) -> Tuple[bool, str]:
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as error:
        return False, error.message
    return True, ""
