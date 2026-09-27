import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        activity_name: list(activity["participants"])
        for activity_name, activity in activities.items()
    }

    yield

    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert set(response.json()["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_signup_adds_participant():
    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@example.com for Soccer Club"
    }
    assert "student@example.com" in activities["Soccer Club"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "student@example.com"

    first_response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )
    duplicate_response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities["Soccer Club"]["participants"].count(email) == 1


@pytest.mark.parametrize("method", ["post", "delete"])
def test_signup_endpoints_reject_unknown_activity(method):
    response = getattr(client, method)(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant():
    email = "student@example.com"
    activities["Soccer Club"]["participants"].append(email)

    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered student@example.com from Soccer Club"
    }
    assert email not in activities["Soccer Club"]["participants"]


def test_unregister_rejects_unknown_participant():
    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
