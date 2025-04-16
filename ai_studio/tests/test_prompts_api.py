import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Define mock return data
mock_prompt_run_result = {
    "id": "test-run-id-123",
    "prompt": "Test prompt from request",
    "model": "mock-model",
    "output": "Mocked AI output",
    "created_at": 1678886400.0, # Example timestamp
    "tokens": {"prompt": 15, "completion": 30}
}

mock_store_result_node_id = "test-node-id-456"

# Assuming test_prompts_api.py is in ai_studio/tests/
# Calculate the project root (ai_studio directory)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock PromptController methods needed for the specific test
# (adjust return values as needed for different tests)
class MockPromptController:
    async def run_prompt(self, prompt, model, use_context=False, context_query=None, context_limit=3, system_prompt=None):
        """Mock for running a prompt"""
        return mock_prompt_run_result

    async def store_in_memory(self, data):
        """Mock for storing data in memory"""
        return {"id": "mock_id", "status": "stored"}

    async def get_available_models(self):
        """Mock for getting available AI models"""
        return [{"id": "gpt4o", "name": "GPT-4o", "provider": "OpenAI", "max_tokens": 4096}]

    async def store_prompt_result(self, prompt_data, result_data):
        """Mock for storing prompt result"""
        return "mock_node_id_123"

    async def save_to_memory(self, data):
        """Mock for saving data to memory"""
        return {"id": "mock_memory_id", "status": "saved"}

@pytest.fixture(scope="function")
def test_client_fixture():
    """Pytest fixture to set up mocks and provide a TestClient."""
    mock_controller_instance = MockPromptController()
    
    # Define expected return values for mocked methods if needed
    # e.g., mock_controller_instance.score_prompt_node.return_value = {...}

    # Apply patches using context managers INSIDE the fixture setup
    with patch('ai_studio.data.reddit_tracker.RedditTracker', MagicMock()), \
         patch('ai_studio.data.twitter_tracker.TwitterTracker', MagicMock()), \
         patch('ai_studio_package.infra.db_enhanced.init_db', MagicMock()), \
         patch('ai_studio_package.infra.db_enhanced.init_vector_db', MagicMock()), \
         patch('ai_studio_package.web.routes.memory.openai.Embedding.acreate', MagicMock()), \
         patch('ai_studio_package.web.routes.prompts.get_prompt_controller', return_value=mock_controller_instance), \
         patch('ai_studio_package.web.routes.memory.get_memory_controller', return_value=MagicMock()), \
         patch('ai_studio_package.infra.db_enhanced.create_memory_node', return_value="mock_node_id"), \
         patch('tools.burner_manager.BurnerManager', MagicMock()), \
         patch('fastapi.FastAPI.on_event', MagicMock()):
        # --- Explicitly add project root to sys.path ---
        original_sys_path = list(sys.path)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            path_added = True
        else:
            path_added = False
        # Debug: Print sys.path to confirm project root is at the front
        print(f"DEBUG: sys.path before import = {sys.path}")
        # -------------------------------------------------

        try:
            # Use importlib to dynamically import the FastAPI app from the root-level main.py
            import importlib.util
            main_spec = importlib.util.spec_from_file_location("root_main", os.path.join(project_root, "main.py"))
            main_module = importlib.util.module_from_spec(main_spec)
            main_spec.loader.exec_module(main_module)
            app = main_module.app
            yield TestClient(app)
        finally:
            # --- Clean up sys.path if we modified it ---
            if path_added:
                sys.path.pop(0)
            # Restore original just in case (though pop should be sufficient)
            # sys.path = original_sys_path
            # -------------------------

# Test function using the fixture
def test_run_prompt_success(test_client_fixture):
    """Test the POST /api/prompts/run endpoint for a successful execution."""
    client = test_client_fixture # Unpack client 

    request_payload = {"prompt": "Test prompt from request", "model": "gpt4o"}

    response = client.post("/api/prompts/run", json=request_payload)

    # Debug: Print response content if status code is not 200
    if response.status_code != 200:
        print(f"DEBUG: Response status code = {response.status_code}")
        print(f"DEBUG: Response content = {response.content}")

    # Check status code and response body
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == mock_prompt_run_result["id"]
    assert response_data["prompt"] == mock_prompt_run_result["prompt"] # Endpoint should return result data
    assert response_data["model"] == mock_prompt_run_result["model"]
    assert response_data["output"] == mock_prompt_run_result["output"]
    assert response_data["tokens"] == mock_prompt_run_result["tokens"]

    # Check that the mocked controller methods were called correctly
    # The endpoint decorator default values for use_context etc. should be passed
    mock_controller_instance.run_prompt.assert_called_once_with(
        prompt=request_payload["prompt"],
        model=request_payload["model"],
        use_context=False,       # Default from PromptRequest model
        context_query=None,      # Default from PromptRequest model
        context_limit=3,         # Default from PromptRequest model
        system_prompt=None       # Default from PromptRequest model
    )
    # Assuming the endpoint implementation calls store_in_memory after run_prompt
    # The exact data passed to store_in_memory might be the result dict
    mock_controller_instance.store_in_memory.assert_called_once_with(mock_prompt_run_result)

# Add more tests for other endpoints (/history, /models, /score/{id}) using the same fixture
# Example:
# def test_get_models_success(test_client_fixture):
#     client, mock_controller = test_client_fixture
#     mock_controller.get_available_models.return_value = [AIModel(...)] # Setup mock return
#     response = client.get("/api/prompts/models")
#     assert response.status_code == 200
#     # ... more assertions
