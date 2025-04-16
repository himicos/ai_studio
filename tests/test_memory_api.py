import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Assuming your FastAPI app instance is named 'app' in 'main.py'
from main import app

# --- Mocking Fixture for MemoryController ---
@pytest.fixture(autouse=True)
def mock_memory_controller():
    """Automatically mocks MemoryController for all tests in this module."""
    with patch('ai_studio_package.web.routes.memory.MemoryController') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        # Mock methods to return predefined results
        mock_instance.get_nodes = MagicMock(return_value=[
            {
                "id": "node1",
                "type": "test",
                "content": "Test content",
                "tags": ["test"],
                "metadata": {},
                "created_at": 1672531200.0,  # Unix timestamp for 2024-01-01T12:00:00Z
                "updated_at": 1672531200.0   # Unix timestamp for 2024-01-01T12:00:00Z
            }
        ])
        mock_instance.get_edges = MagicMock(return_value=[])
        mock_instance.get_stats = MagicMock(return_value={
            "node_count": 1,
            "edge_count": 0,
            "types": ["test"],
            "tags": ["test"],
            "relation_types": {"related_to": 1},
            "total_nodes": 1,
            "total_edges": 0,
            "node_types": {"test": 1}
        })
        yield mock_class

# Mock the get_memory_controller dependency
@pytest.fixture(autouse=True)
def mock_get_memory_controller():
    """Mock the get_memory_controller dependency to return a mocked MemoryController."""
    with patch('ai_studio_package.web.routes.memory.get_memory_controller', return_value=MagicMock(
        get_nodes=MagicMock(return_value=[
            {
                "id": "node1",
                "type": "test",
                "content": "Test content",
                "tags": ["test"],
                "metadata": {},
                "created_at": 1672531200.0,  # Unix timestamp for 2024-01-01T12:00:00Z
                "updated_at": 1672531200.0   # Unix timestamp for 2024-01-01T12:00:00Z
            }
        ]),
        get_edges=MagicMock(return_value=[]),
        get_stats=MagicMock(return_value={
            "node_count": 1,
            "edge_count": 0,
            "types": ["test"],
            "tags": ["test"],
            "relation_types": {"related_to": 1},
            "total_nodes": 1,
            "total_edges": 0,
            "node_types": {"test": 1}
        })
    )):
        yield

# --- Test Memory API Endpoints ---

def test_get_memory_nodes():
    """Test GET /api/memory/nodes to retrieve memory nodes."""
    with TestClient(app) as client:
        response = client.get("/api/memory/nodes")
        print("\nDebug: Response Status Code:", response.status_code)
        print("Debug: Response Content:", response.text)
        assert response.status_code in [200, 201], f"Unexpected status code: {response.status_code}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        print("Memory Nodes Test Passed:", data)

def test_get_memory_stats():
    """Test GET /api/memory/stats to retrieve memory statistics."""
    with TestClient(app) as client:
        response = client.get("/api/memory/stats")
        print("\nDebug: Response Status Code:", response.status_code)
        print("Debug: Response Content:", response.text)
        assert response.status_code in [200, 201], f"Unexpected status code: {response.status_code}"
        data = response.json()
        assert "node_count" in data or "total_nodes" in data, "Neither node_count nor total_nodes found in response"
        if "node_count" in data:
            assert data["node_count"] == 1
        if "total_nodes" in data:
            assert data["total_nodes"] == 1
        print("Memory Stats Test Passed:", data)
