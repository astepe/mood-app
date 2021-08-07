"""
Contains request and response schemas
"""
from .models import MoodEnum


mood_request_schema = {
    "type": "object",
    "properties": {
        "timestamp": {"type": "integer"},
        "mood": {
            "type": "string",
            "enum": [mood.name for mood in MoodEnum.__members__.values()],
        },
    },
    "required": ["mood"],
}


register_request_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"},
    },
    "required": ["username", "password"],
}
