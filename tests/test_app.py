"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities_data = response.json()
        assert isinstance(activities_data, dict)
        assert len(activities_data) == 9
        
        # Check that Basketball Team exists
        assert "Basketball Team" in activities_data
        assert activities_data["Basketball Team"]["max_participants"] == 15
        assert "alex@mergington.edu" in activities_data["Basketball Team"]["participants"]
    
    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_consistency(self, client):
        """Test that multiple calls return consistent data"""
        response1 = client.get("/activities")
        response2 = client.get("/activities")
        
        assert response1.json() == response2.json()


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()
    
    def test_signup_adds_participant(self, client):
        """Test that signup adds a new participant to an activity"""
        email = "newsignup@mergington.edu"
        activity_name = "Chess Club"
        
        # Get initial state
        activities_response_before = client.get("/activities")
        initial_participants = activities_response_before.json()[activity_name]["participants"].copy()
        
        # Perform signup
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Get updated state
        activities_response_after = client.get("/activities")
        updated_participants = activities_response_after.json()[activity_name]["participants"]
        
        # Verify new participant is added
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1
    
    def test_signup_response_message(self, client):
        """Test that signup returns a message"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=coder@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert isinstance(result["message"], str)
    
    def test_signup_validates_activity_name(self, client):
        """Test various activity name encodings"""
        valid_activities = [
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
        ]
        
        for activity in valid_activities:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup?email=test@mergington.edu"
            )
            assert response.status_code == 200


class TestActivityDetails:
    """Tests for activity details and constraints"""
    
    def test_all_activities_present(self, client):
        """Test that all expected activities are present"""
        expected_activities = [
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity in expected_activities:
            assert activity in activities_data
    
    def test_max_participants_property(self, client):
        """Test that all activities have max_participants"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert "max_participants" in activity_details
            assert isinstance(activity_details["max_participants"], int)
            assert activity_details["max_participants"] > 0
    
    def test_participants_is_list(self, client):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert isinstance(activity_details["participants"], list)
            for participant in activity_details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Should be an email
    
    def test_description_and_schedule_present(self, client):
        """Test that description and schedule are present for all activities"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert "description" in activity_details
            assert len(activity_details["description"]) > 0
            assert "schedule" in activity_details
            assert len(activity_details["schedule"]) > 0
