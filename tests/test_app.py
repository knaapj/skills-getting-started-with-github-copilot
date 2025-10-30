"""
Test suite for Mergington High School Activities API

Tests all endpoints and edge cases for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities data to initial state before each test."""
    # Store original activities data
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Reset activities to original state after test
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/")
        assert response.status_code == 200
        # The redirect should be followed by the test client


class TestGetActivities:
    """Test the GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successful retrieval of activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that Chess Club exists
        assert "Chess Club" in data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_activities_structure(self, client, reset_activities):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            required_fields = ["description", "schedule", "max_participants", "participants"]
            for field in required_fields:
                assert field in activity_data, f"Missing field {field} in {activity_name}"
            
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            assert activity_data["max_participants"] > 0


class TestSignupActivity:
    """Test the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        email = "test@mergington.edu"
        activity = "Chess Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        initial_count = len(initial_participants)
        
        # Sign up for activity
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert len(updated_participants) == initial_count + 1
        assert email in updated_participants
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test signup when student is already registered."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity."""
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_url_encoded_activity(self, client, reset_activities):
        """Test signup with URL-encoded activity name."""
        email = "test@mergington.edu"
        activity = "Programming Class"  # Has space in name
        
        response = client.post(f"/activities/Programming%20Class/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert email in updated_participants


class TestUnregisterActivity:
    """Test the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        initial_count = len(initial_participants)
        assert email in initial_participants
        
        # Unregister from activity
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was removed
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert len(updated_participants) == initial_count - 1
        assert email not in updated_participants
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregistration when student is not registered."""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistration from non-existent activity."""
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple operations."""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up and then unregistering from an activity."""
        email = "integration@mergington.edu"
        activity = "Art Workshop"
        
        # Initial state
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"]
        assert email not in initial_participants
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup_response = client.get("/activities")
        after_signup_participants = after_signup_response.json()[activity]["participants"]
        assert email in after_signup_participants
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity]["participants"]
        assert email not in final_participants
        assert len(final_participants) == len(initial_participants)
    
    def test_multiple_signups_different_activities(self, client, reset_activities):
        """Test signing up for multiple activities."""
        email = "multi@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Workshop"]
        
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all signups
        final_response = client.get("/activities")
        final_data = final_response.json()
        
        for activity in activities_to_join:
            assert email in final_data[activity]["participants"]


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_email_signup(self, client, reset_activities):
        """Test signup with empty email."""
        response = client.post("/activities/Chess%20Club/signup?email=")
        # This should work as the API doesn't validate email format
        assert response.status_code == 200 or response.status_code == 400
    
    def test_special_characters_in_email(self, client, reset_activities):
        """Test signup with special characters in email."""
        import urllib.parse
        
        email = "test+special@mergington.edu"
        activity = "Chess Club"
        
        # URL encode the email to handle special characters properly
        encoded_email = urllib.parse.quote(email)
        response = client.post(f"/activities/{activity}/signup?email={encoded_email}")
        assert response.status_code == 200
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity]["participants"]
        assert email in updated_participants
    
    def test_case_sensitive_activity_names(self, client, reset_activities):
        """Test that activity names are case sensitive."""
        email = "test@mergington.edu"
        
        # Correct case should work
        response = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        assert response.status_code == 200
        
        # Different case should fail
        response = client.post("/activities/chess%20club/signup?email=test2@mergington.edu")
        assert response.status_code == 404


class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_participant_count_consistency(self, client, reset_activities):
        """Test that participant counts remain consistent."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            
            # Check that we don't exceed maximum (though API doesn't enforce this)
            # This is more of a data integrity check
            assert participant_count <= max_participants, \
                f"{activity_name} has {participant_count} participants but max is {max_participants}"
    
    def test_data_persistence_across_requests(self, client, reset_activities):
        """Test that data persists across multiple requests."""
        email = "persistence@mergington.edu"
        activity = "Drama Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Make multiple GET requests to ensure data persists
        for _ in range(3):
            response = client.get("/activities")
            participants = response.json()[activity]["participants"]
            assert email in participants