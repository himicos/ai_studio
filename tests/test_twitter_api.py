import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

# Import the class we are mocking for spec
from data.twitter_tracker import TwitterTracker 
from ai_studio_package.web.routes.twitter import TweetPost

# Assuming your FastAPI app instance is named 'app' in 'main.py'
# Adjust the import path if your main file is located differently
from main import app 

# --- Mocking Fixture ---
@pytest.fixture(autouse=True)
def mock_twitter_tracker_init():
    """Automatically mocks TwitterTracker initialization for all tests in this module."""
    # Use a class to manage mock state easily
    class MockTrackerState:
        def __init__(self):
            self._accounts = []
            self._keywords = []

        def update_accounts(self, accounts: list):
            print(f"MOCK: Updating accounts to {accounts}")
            self._accounts = accounts

        def update_keywords(self, keywords: list):
            print(f"MOCK: Updating keywords to {keywords}")
            self._keywords = keywords

        def get_status(self):
            print(f"MOCK: Getting status: accounts={self._accounts}, keywords={self._keywords}")
            return {"accounts": self._accounts, "keywords": self._keywords}

        def cleanup(self):
            print("MOCK: Cleanup called")
            pass # Mock cleanup if needed

        def scan(self):
            print("MOCK: Scan called")
            return [] # Mock scan if needed
            
    mock_state = MockTrackerState()
    
    # Create a MagicMock that delegates calls to the stateful object
    mock_instance = MagicMock(spec=TwitterTracker) # Use spec for better mocking
    mock_instance.update_accounts.side_effect = mock_state.update_accounts
    mock_instance.update_keywords.side_effect = mock_state.update_keywords
    mock_instance.get_status.side_effect = mock_state.get_status
    mock_instance.cleanup.side_effect = mock_state.cleanup
    mock_instance.scan.side_effect = mock_state.scan
    
    # Patch the class within the 'main' module
    with patch('main.TwitterTracker', return_value=mock_instance) as mock_class:
        yield mock_class

# --- Test Twitter API Endpoints ---

def test_initial_twitter_status():
    """Test GET /api/twitter/status before starting the scanner."""
    # TestClient context manager handles lifespan
    with TestClient(app) as client:
        response = client.get("/api/twitter/status")
        # Now that tracker init is mocked successfully, we expect 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is False
        # Check against the default status returned by the mocked get_status
        assert data["accounts"] == [] 
        assert data["keywords"] == [] 
        print("\nInitial Twitter Status Test Passed (with mocking):", data)

def test_start_twitter_scanner():
    """Test POST /api/twitter/start and subsequent status."""
    with TestClient(app) as client:
        # 1. Check initial status (should be stopped due to fixture reset per test)
        initial_response = client.get("/api/twitter/status")
        assert initial_response.status_code == 200
        assert initial_response.json()["is_running"] is False

        # 2. Start the scanner
        start_response = client.post("/api/twitter/start")
        assert start_response.status_code == 200
        start_data = start_response.json()
        # The start endpoint itself returns the *new* status
        assert start_data["is_running"] is True 
        print("\nStart Scanner Response:", start_data)

        # 3. Verify status endpoint reflects running state immediately after
        status_response = client.get("/api/twitter/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["is_running"] is True
        print("Status After Start:", status_data)

def test_stop_twitter_scanner():
     """Test POST /api/twitter/stop and subsequent status."""
     with TestClient(app) as client:
        # 1. Start the scanner first (or ensure it's running)
        # We can rely on the start endpoint working from the previous test
        client.post("/api/twitter/start") 
        status_response = client.get("/api/twitter/status")
        assert status_response.status_code == 200
        assert status_response.json()["is_running"] is True
        print("\nStatus Before Stop:", status_response.json())

        # 2. Stop the scanner
        stop_response = client.post("/api/twitter/stop")
        assert stop_response.status_code == 200
        stop_data = stop_response.json()
        # The stop endpoint itself returns the *new* status
        assert stop_data["is_running"] is False
        print("Stop Scanner Response:", stop_data)

        # 3. Verify status endpoint reflects stopped state
        final_status_response = client.get("/api/twitter/status")
        assert final_status_response.status_code == 200
        assert final_status_response.json()["is_running"] is False
        print("Status After Stop:", final_status_response.json())

def test_set_twitter_accounts():
    """Test POST /api/twitter/set-accounts."""
    test_accounts = ["test_user1", "test_user2"]
    with TestClient(app) as client:
        # Get the mock instance from the app state *after* startup
        mock_tracker_instance = client.app.state.twitter_scanner
        # Reset call counts for this specific test
        mock_tracker_instance.update_accounts.reset_mock()

        # Call the endpoint
        response = client.post("/api/twitter/set-accounts", json={"accounts": test_accounts})
        assert response.status_code == 200
        data = response.json()
        # Endpoint should return the updated status
        assert data["accounts"] == test_accounts
        print("\nSet Accounts Response:", data)

        # Verify the mock tracker method was called
        mock_tracker_instance.update_accounts.assert_called_once_with(test_accounts)

        # Verify /status reflects the change
        status_response = client.get("/api/twitter/status")
        assert status_response.status_code == 200
        assert status_response.json()["accounts"] == test_accounts
        print("Status After Set Accounts:", status_response.json())

def test_set_twitter_keywords():
    """Test POST /api/twitter/set-keywords."""
    test_keywords = ["keyword1", "#keyword2"]
    with TestClient(app) as client:
        # Get the mock instance from the app state *after* startup
        mock_tracker_instance = client.app.state.twitter_scanner
        # Reset call counts for this specific test
        mock_tracker_instance.update_keywords.reset_mock()

        # Call the endpoint
        response = client.post("/api/twitter/set-keywords", json={"keywords": test_keywords})
        assert response.status_code == 200
        data = response.json()
        # Endpoint should return the updated status
        assert data["keywords"] == test_keywords
        print("\nSet Keywords Response:", data)

        # Verify the mock tracker method was called
        mock_tracker_instance.update_keywords.assert_called_once_with(test_keywords)

        # Verify /status reflects the change
        status_response = client.get("/api/twitter/status")
        assert status_response.status_code == 200
        assert status_response.json()["keywords"] == test_keywords
        print("Status After Set Keywords:", status_response.json())

@patch('ai_studio_package.web.routes.twitter.get_memory_nodes', new_callable=AsyncMock)
def test_get_twitter_posts(mock_get_nodes):
    """Test GET /api/twitter/posts (mocking DB call)."""
    # Define sample data structured like DB results
    sample_db_data = [
        {
            'id': 'db123', 'type': 'tweet', 'content': 'Sample tweet 1 from DB',
            'tags': ['test', 'db'], 'metadata': {'author': 'userA', 'source': 'twitter_api'},
            'created_at': '2024-01-01T12:00:00Z', # Use Z suffix
            'updated_at': '2024-01-01T12:00:00Z'  # Use Z suffix
        },
        {
            'id': 'db456', 'type': 'tweet', 'content': 'Sample tweet 2 #test',
            'tags': [], 'metadata': {'author': 'userB'},
            'created_at': '2024-01-01T12:05:00Z', # Use Z suffix
            'updated_at': '2024-01-01T12:05:00Z'  # Use Z suffix
        }
    ]
    # Expected response structure (matches TweetPost model)
    expected_response = [
        {
            'id': 'db123', 'type': 'tweet', 'content': 'Sample tweet 1 from DB',
            'tags': ['test', 'db'], 'metadata': {'author': 'userA', 'source': 'twitter_api'},
            'created_at': '2024-01-01T12:00:00Z', 
            'updated_at': '2024-01-01T12:00:00Z'
        },
        {
            'id': 'db456', 'type': 'tweet', 'content': 'Sample tweet 2 #test',
            'tags': [], 'metadata': {'author': 'userB'},
            'created_at': '2024-01-01T12:05:00Z', 
            'updated_at': '2024-01-01T12:05:00Z'
        }
    ]

    # Configure the mock DB function
    mock_get_nodes.return_value = sample_db_data
    
    with TestClient(app) as client:
        # Call the endpoint (without search query to trigger get_memory_nodes)
        response = client.get("/api/twitter/posts")
        assert response.status_code == 200
        data = response.json()
        
        # Verify the response data matches the expected structure
        assert data == expected_response

        # Verify the mock DB function was called correctly
        mock_get_nodes.assert_called_once_with(
            node_type="tweet", 
            limit=50, # Default limit from get_posts signature
            offset=0, # Default offset from get_posts signature
            sort_by="created_at", 
            sort_order="desc"
        )
