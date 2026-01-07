"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivityEndpoints:
    """Test activity-related endpoints"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Basketball Team" in data
        assert "Tennis Club" in data

    def test_get_activities_contains_required_fields(self):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data


class TestSignup:
    """Test activity signup functionality"""

    def test_signup_new_participant(self):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

    def test_signup_activity_not_found(self):
        """Test signup to non-existent activity"""
        response = client.post(
            "/activities/NonExistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_participant(self):
        """Test that duplicate signup is prevented"""
        # First signup
        response1 = client.post(
            "/activities/Basketball Team/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Attempt duplicate signup
        response2 = client.post(
            "/activities/Basketball Team/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_special_characters_in_email(self):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Tennis Club/signup?email=user+test@mergington.edu"
        )
        assert response.status_code == 200
        
    def test_signup_updates_participant_list(self):
        """Test that signup updates the participant list"""
        email = "participant-test@mergington.edu"
        
        # Get initial state
        response1 = client.get("/activities")
        initial_participants = response1.json()["Art Studio"]["participants"].copy()
        
        # Sign up
        response2 = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify participant was added
        response3 = client.get("/activities")
        updated_participants = response3.json()["Art Studio"]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1


class TestActivityValidation:
    """Test activity validation"""

    def test_get_activities_has_participants(self):
        """Test that all activities have participant lists"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            # Verify participants are strings (emails)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation

    def test_max_participants_is_positive(self):
        """Test that max_participants is a positive number"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert activity_data["max_participants"] > 0

    def test_participant_count_not_exceeded(self):
        """Test that participants count does not exceed max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert len(activity_data["participants"]) <= activity_data["max_participants"]
