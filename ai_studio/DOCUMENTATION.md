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

## Troubleshooting

### Common Issues

- **Selenium errors**: Make sure Chrome is installed and webdriver-manager is up to date
- **API key errors**: Check that your API keys are correctly configured in `.env`
- **Database errors**: Try reinitializing the database with `python -c "from infra.db import init_db; init_db()"`

### Logs

Check the logs in `memory/logs/` for detailed error messages and debugging information.

## License

This project is licensed under the MIT License.
