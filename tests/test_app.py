from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

BASE_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture

def activities_state(monkeypatch):
    isolated_activities = deepcopy(BASE_ACTIVITIES)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture

def client(activities_state):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_available_activities(client, activities_state):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities_state
    assert expected_activity in response.json()


def test_signup_adds_participant(client, activities_state):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities_state[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client, activities_state):
    # Arrange
    activity_name = "Chess Club"
    email = activities_state[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities_state[activity_name]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, activities_state):
    # Arrange
    activity_name = "Chess Club"
    email = activities_state[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities_state[activity_name]["participants"]


def test_unregister_rejects_unregistered_participant(client, activities_state):
    # Arrange
    activity_name = "Chess Club"
    email = "not-signed-up@mergington.edu"
    original_participants = activities_state[activity_name]["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities_state[activity_name]["participants"] == original_participants


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
