import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_state = {
        activity_name: list(details["participants"])
        for activity_name, details in activities.items()
    }

    yield

    for activity_name, details in activities.items():
        details["participants"] = list(original_state[activity_name])


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()

    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow(client):
    activity_name = "Chess Club"
    email = "test-student@mergington.edu"

    signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert signup_response.status_code == 200
    assert email in activities[activity_name]["participants"]

    unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    assert unregister_response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_duplicate_signup_is_rejected(client):
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")

    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_unregister_unknown_participant_returns_not_found(client):
    response = client.delete("/activities/Chess Club/unregister?email=missing@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not registered for this activity"
