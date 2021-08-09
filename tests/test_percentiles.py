import base64
from datetime import datetime, timedelta


class TestPercentiles:
    @staticmethod
    def test_percentile_calculation(client):
        """
        Tests that percentiles are correct for
        the following longest streaks
        1, 2, 2, 3, 3, 4
        expected percentiles
        None, None, None, 50.0, 50.0, 83.33
        """

        for i in range(6):
            client.post("/user", json=dict(username=f"user{i}", password="pass"))

        _create_streak(client, b"user0:pass", 1)
        response = _get_moods(client, b"user0:pass")
        assert response.json["streakPercentile"] == 83.33

        _create_streak(client, b"user1:pass", 2)
        response = _get_moods(client, b"user1:pass")
        assert response.json["streakPercentile"] == 83.33

        _create_streak(client, b"user2:pass", 2)
        response = _get_moods(client, b"user2:pass")
        assert response.json["streakPercentile"] == 66.67

        _create_streak(client, b"user3:pass", 3)
        response = _get_moods(client, b"user3:pass")
        assert response.json["streakPercentile"] == 83.33

        _create_streak(client, b"user4:pass", 3)
        response = _get_moods(client, b"user4:pass")
        assert response.json["streakPercentile"] == 66.67

        _create_streak(client, b"user5:pass", 4)
        response = _get_moods(client, b"user5:pass")
        assert response.json["streakPercentile"] == 83.33

        assert "streakPercentile" not in _get_moods(client, b"user0:pass").json
        assert "streakPercentile" not in _get_moods(client, b"user1:pass").json
        assert "streakPercentile" not in _get_moods(client, b"user2:pass").json
        assert _get_moods(client, b"user3:pass").json["streakPercentile"] == 50.0
        assert _get_moods(client, b"user4:pass").json["streakPercentile"] == 50.0
        assert _get_moods(client, b"user5:pass").json["streakPercentile"] == 83.33


def _create_streak(client, user_pass, length):
    for i in range(length + 1):
        timestamp = int((datetime.now() + timedelta(days=i)).timestamp())
        client.post(
            "/mood",
            json=dict(mood="CHEERFUL", timestamp=timestamp),
            headers={
                "Authorization": "Basic " + base64.b64encode(user_pass).decode("utf-8")
            },
        )


def _get_moods(client, user_pass):
    return client.get(
        "/mood",
        headers={
            "Authorization": "Basic " + base64.b64encode(user_pass).decode("utf-8")
        },
    )
