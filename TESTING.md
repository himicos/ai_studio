# AI Studio Testing Guide

This guide provides instructions on how to test the AI Studio, focusing on recently implemented features.

## Test Environment Setup

1. **Install AI Studio Package in Development Mode**:
   ```bash
   # From the project root directory
   cd ai_studio_package
   pip install -e .
   cd ..
   ```

2. **Start Backend Server**:
   ```bash
   # From the project root directory
   python main.py
   ```

3. **Start Frontend Server** (in a new terminal):
   ```bash
   # From the project root directory
   cd spyderweb/spyderweb
   npm run dev
   ```

## Testing Self-Improvement Loop (SIL)

The Self-Improvement Loop includes the Critic Agent, Refactor Agent, and execution logging.

### Method 1: Using the Test Script

```bash
# From the project root directory
python test_all_functionality.py --test sil
```

### Method 2: Manually Testing Components

1. **Initialize Execution Logs**:
   ```bash
   python -m ai_studio_package.scripts.initialize_execution_logs
   ```

2. **Run Critic Agent**:
   ```bash
   python -m ai_studio_package.agents.critic_agent
   ```

3. **Run Refactor Agent**:
   ```bash
   # Get a critique ID from the database first
   python -m ai_studio_package.agents.refactor_agent --critique-id YOUR_CRITIQUE_ID
   ```

4. **Run Scheduler** (runs both agents):
   ```bash
   python -m ai_studio_package.scripts.schedule_critic --run-now
   ```

### Checking Results

To check critique nodes created:
```bash
python -c "import sqlite3; conn = sqlite3.connect('memory/memory.sqlite'); conn.row_factory = sqlite3.Row; cursor = conn.cursor(); cursor.execute('SELECT id, content FROM memory_nodes WHERE type=\"critique\" ORDER BY created_at DESC LIMIT 5'); [print(f'ID: {row[\"id\"]}, Content: {row[\"content\"][:100]}...') for row in cursor.fetchall()]"
```

## Testing Live Semantic Query Highlighting

This feature enhances the knowledge graph visualization with highlighting based on semantic search.

### Method 1: Using the Test Script

```bash
# From the project root directory
python test_all_functionality.py --test vector
```

### Method 2: Using the Web Interface

1. Start both backend and frontend servers
2. Open `http://localhost:5173/knowledge` in your browser
3. Enter search terms in the graph search field
4. Observe how nodes are highlighted based on similarity
5. The graph should zoom to focus on the relevant nodes

### Method 3: Testing the API Directly

```bash
# Using curl (Windows PowerShell syntax)
Invoke-RestMethod -Uri "http://localhost:8000/api/search/semantic" -Method Post -ContentType "application/json" -Body '{"query":"artificial intelligence","limit":5,"min_similarity":0.1}'

# Using Python
python -c "import requests; response = requests.post('http://localhost:8000/api/search/semantic', json={'query': 'artificial intelligence', 'limit': 5, 'min_similarity': 0.1}); print(response.status_code); print(response.text)"
```

## Troubleshooting

### Module Import Errors

If you see `ModuleNotFoundError: No module named 'ai_studio_package'`, make sure you've installed the package in development mode as outlined in setup step 1.

### API Errors

- Check that the backend server is running (`python main.py`)
- Ensure the API endpoint paths are correct (they should start with `/api/`)
- For semantic search, try lowering the `min_similarity` threshold (e.g., to 0.01)

### No Search Results

If semantic search returns no results:
1. Verify the vector store has data (check `data/vector_store_metadata.json`)
2. Try different search terms related to the content in your vector store
3. Lower the similarity threshold further (to 0.01 or even 0.001) 