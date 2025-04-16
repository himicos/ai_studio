# AI Studio Documentation

## System Overview

AI Studio is a modular, agentic operating system for real-time web tracking and prompt-driven automation. It monitors Twitter/X (via nitter.net) and Reddit, processes unstructured "schizoprompts," manages proxy rotation, and stores data for analysis.

## Architecture

The system is organized into the following components:

### Agents
- **prompt_router.py**: Routes schizoprompts to appropriate AI models (Grok, Claude, GPT-4o, Manus)
- **action_executor.py**: Processes detected items from trackers and executes appropriate actions
- **real_time_scanner.py**: Coordinates Twitter and Reddit trackers and passes detected items to the action executor

### Data Collection
- **twitter_tracker.py**: Monitors Twitter accounts via nitter.net using Selenium
- **reddit_tracker.py**: Monitors subreddits using the Reddit JSON API

### Infrastructure
- **db.py**: SQLite database interface for storing posts, contracts, logs, and prompts
- **scheduler.py**: Runs periodic tasks like scanning Twitter and Reddit

### Web Interface
- **app.py**: Core web server with WebSocket support and REST API endpoints
- **static/**: Frontend assets and components built with Next.js
  - Modern, responsive UI with dark/light theme support
  - Real-time updates via WebSocket
  - Proxy management dashboard with world map visualization
  - Prompt laboratory with multi-tab workspace
  - Analytics center with dynamic graphs
  - Memory management with knowledge graph visualization

### Tools
- **burner_manager.py**: Manages proxy rotation and user-agent switching to avoid rate limiting

### Tests
- **test_prototype.py**: Example prototype implementation for experimental features

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure your settings
4. Initialize the database: `python -c "from infra.db import init_db; init_db()"`

## Configuration

Edit the `.env` file to configure:

- **API Keys**: Set your OpenAI, Claude, and Grok API keys
- **Monitoring**: Configure Twitter accounts, subreddits, and keywords to track
- **Burners**: Add proxies and user-agents for rotation
- **System**: Adjust scan intervals and other system settings

## Usage

### Running the Scanner

```bash
python main.py --scan
```

This will start the real-time scanner that monitors Twitter accounts and Reddit subreddits based on your configuration.

### Processing Schizoprompts

```bash
python main.py --prompt "Build a bot to track crypto scams"
```

This will process the prompt through the schizoprompt router and execute the appropriate action.

### Running the Scheduler

```bash
python main.py --schedule
```

This will start the scheduler that runs periodic tasks like scanning Twitter and Reddit at regular intervals.

## Testing

Run the integration tests to verify that all components work together correctly:

```bash
./integration_test.sh
```

## Data Storage

All data is stored in `memory/memory.sqlite` with the following tables:

- **posts**: Stores posts from Twitter and Reddit
- **post_history**: Tracks changes in post scores and comments over time
- **contracts**: Stores detected contract addresses
- **logs**: Records system actions and events
- **prompts**: Stores processed schizoprompts and their results

## Extending AI Studio

### Adding Trackers

To add a new tracker:

1. Create a new file in the `data/` directory
2. Implement a class with a `scan()` method that returns detected items
3. Add the tracker to `agents/real_time_scanner.py`

### Creating Prototypes

To create a new prototype:

1. Create a new file in the `tests/` directory
2. Implement a class with a `run()` method
3. Add command-line interface if needed

### Adding AI Models

To add a new AI model to the prompt router:

1. Add the model to the intent keywords in `agents/prompt_router.py`
2. Implement a routing method for the model
3. Update the `process()` method to use the new routing method

## API Reference (Prompts Module)

The `prompts.py` router provides the following REST API endpoints for interacting with the AI prompt system and memory:

### POST /api/prompts/run

Executes a prompt using the specified AI model and stores the interaction in memory.

**Request Body:** (`application/json`)

```json
{
  "prompt": "string (required) - The prompt text to execute.",
  "model": "string (required) - The AI model ID (e.g., 'gpt4o', 'claude').",
  "use_context": "boolean (optional, default: false) - Whether to search memory for relevant context.",
  "context_query": "string (optional, default: null) - Specific query for context search (uses 'prompt' if null).",
  "context_limit": "integer (optional, default: 3) - Max number of context items to retrieve.",
  "system_prompt": "string (optional, default: null) - A system prompt to guide the AI's behavior/personality."
}
```

**Response Body:** (`application/json`) - `PromptResponse` Model

```json
{
  "id": "string - Unique ID for the stored prompt memory node.",
  "prompt": "string - The original user prompt.",
  "model": "string - The AI model used.",
  "output": "string - The AI model's response.",
  "created_at": "float - Timestamp of creation.",
  "tokens": {
    "prompt": "integer - Tokens in the prompt.",
    "completion": "integer - Tokens in the completion.",
    "total": "integer - Total tokens used."
  }
}
```

**Details:**
*   If `use_context` is true, the system performs a semantic search on memory nodes using `context_query` (or `prompt`) and prepends the found context to the user prompt before sending it to the AI.
*   The `system_prompt` allows customizing the AI's persona or giving high-level instructions.
*   The entire interaction (prompt, context used, system prompt, response, model, tokens) is stored as metadata within the created prompt memory node.

### PUT /api/prompts/score/{prompt_node_id}

Assigns a score and optional notes to a previously executed prompt node in memory.

**Path Parameters:**
*   `prompt_node_id`: (string, required) - The unique ID of the prompt memory node to score.

**Request Body:** (`application/json`)

```json
{
  "score": "number | string (required) - The score value (e.g., 0.8, 5, 'good').",
  "notes": "string (optional, default: null) - Optional textual notes about the score."
}
```

**Response Body:** (`application/json`) - `PromptNodeResponse` Model

```json
{
  "node_id": "string",
  "node_type": "string",
  "content": "string",
  "metadata": {
    "score": "number | string",
    "score_notes": "string | null",
    "...": "other metadata like original request details"
  },
  "tags": ["string"],
  "created_at": "float",
  "updated_at": "float - Timestamp reflects the score update."
}
```

**Details:**
*   Updates the `metadata` field of the specified memory node, adding or overwriting `score` and `score_notes`.
*   Updates the `updated_at` timestamp of the node.

### GET /api/prompts/history

Retrieves a paginated list of previously executed prompt nodes from memory.

**Query Parameters:**
*   `limit`: (integer, optional, default: 50) - Maximum number of history items to return (1-200).
*   `offset`: (integer, optional, default: 0) - Number of items to skip for pagination.

**Response Body:** (`application/json`) - `List[PromptNodeResponse]` Model

```json
[
  {
    "node_id": "string",
    "node_type": "string (prompt)",
    "content": "string (Original user prompt)",
    "metadata": { "...": "request/response details" },
    "tags": ["string"],
    "created_at": "float",
    "updated_at": "float"
  },
  ...
]
```

**Details:**
*   Returns nodes with `node_type`='prompt'.
*   Results are ordered by `created_at` timestamp, descending (most recent first).

### GET /api/prompts/models

Retrieves a list of AI models available through the prompt controller.

**Response Body:** (`application/json`) - `List[AIModel]` Model

```json
[
  {
    "id": "string",
    "name": "string",
    "provider": "string",
    "max_tokens": "integer"
  },
  ...
]
```

## Troubleshooting

### Common Issues

- **Selenium errors**: Make sure Chrome is installed and webdriver-manager is up to date
- **API key errors**: Check that your API keys are correctly configured in `.env`
- **Database errors**: Try reinitializing the database with `python -c "from infra.db import init_db; init_db()"`

### Logs

Check the logs in `memory/logs/` for detailed error messages and debugging information.

## License

This project is licensed under the MIT License.
