# AI Studio

A modular, agentic operating system for real-time web tracking and prompt-driven automation. AI Studio monitors Twitter/X and Reddit, executes unstructured "schizoprompts," manages burners (proxies, user-agents), and stores data for analysis.

## Features

- **Real-time Twitter/X Tracking**: Monitor Twitter accounts via nitter.net for keywords and contract addresses
- **Real-time Reddit Tracking**: Monitor subreddits for posts, track upvotes, and analyze content
- **Schizoprompt Router**: Parse raw thoughts into actions and route to appropriate AI models
- **Burner Management**: Rotate proxies and user-agents to avoid rate limits
- **Data Storage**: Store all data in SQLite for analysis and retrieval

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-studio.git
cd ai-studio
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Initialize the database:
```bash
python -c "from infra.db import init_db; init_db()"
```

## Usage

### Monitoring Twitter and Reddit

```bash
python main.py --scan
```

This will start the real-time scanner that monitors Twitter accounts and Reddit subreddits based on your configuration in the `.env` file.

### Processing Schizoprompts

```bash
python main.py --prompt "Build a bot to track crypto scams"
```

This will process the prompt through the schizoprompt router and execute the appropriate action.

### Configuration

Edit the `.env` file to configure:

- **API Keys**: Set your OpenAI, Claude, and Grok API keys
- **Monitoring**: Configure Twitter accounts, subreddits, and keywords to track
- **Burners**: Add proxies and user-agents for rotation
- **System**: Adjust scan intervals and other system settings

## Adding Trackers

### Twitter Accounts

Add Twitter accounts to monitor in your `.env` file:

```
TWITTER_ACCOUNTS=elonmusk,vitalikbuterin,SBF_FTX
```

### Subreddits

Add subreddits to monitor in your `.env` file:

```
SUBREDDITS=wallstreetbets,cryptocurrency,ethtrader
```

### Keywords

Add keywords to track in your `.env` file:

```
KEYWORDS=crypto,bitcoin,ethereum,contract,0x
```

## Extending AI Studio

### Adding Agents

Create new agent modules in the `agents/` directory to extend functionality.

### Creating Prototypes

Add prototype implementations in the `tests/` directory for experimental features.

## Architecture

```
ai_studio/
├── .env                    # API keys, burner configs
├── .env.example            # Sample env
├── README.md               # Setup, usage
├── core_memory.md          # System philosophy
├── agents/                 # AI agents
│   ├── __init__.py
│   ├── prompt_router.py
│   ├── action_executor.py
│   ├── real_time_scanner.py
├── data/                   # Scrapers
│   ├── __init__.py
│   ├── reddit_tracker.py
│   ├── twitter_tracker.py
├── infra/                  # Backend, DB
│   ├── __init__.py
│   ├── scheduler.py
│   ├── db.py
├── memory/                 # Logs, outputs
│   ├── logs/
│   ├── prompt_outputs/
│   └── memory.sqlite
├── tools/                  # Utilities
│   ├── __init__.py
│   ├── burner_manager.py
├── tests/                  # Prototypes
│   ├── __init__.py
│   ├── test_prototype.py
├── main.py                 # CLI entrypoint
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
