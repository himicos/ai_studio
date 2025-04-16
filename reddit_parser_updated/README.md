# Reddit Topic Parser with Upvotes Tracking

A Python application for parsing Reddit data from specific subreddits, tracking upvotes, and storing data in an SQL database.

## Overview

This application allows you to:

- Parse Reddit data from specific subreddits based on keywords or queries
- Collect post details including upvotes, comments, and other metadata
- Avoid hitting Reddit's rate limits through proxy rotation and rate limiting
- Store all data in an SQL database for future retrieval
- Track changes in post upvotes over time

## Components

### 1. Reddit API Integration (`reddit_api.py`)

Handles interaction with Reddit's API using PRAW (Python Reddit API Wrapper). This module provides functionality to:

- Connect to Reddit using API credentials
- Fetch posts from subreddits with various sorting options
- Retrieve comments from posts
- Search for posts based on queries

### 2. Proxy Rotation (`proxy_rotator.py`)

Manages a pool of proxies to avoid rate limiting. This module provides:

- Loading proxies from a text file
- Rotating between proxies for API requests
- Testing proxies to ensure they're working
- Automatic retry with different proxies on failure

### 3. Data Scraping (`data_scraper.py`)

Handles the scraping of Reddit data, including posts and comments. Features include:

- Scraping posts from subreddits
- Scraping comments from posts
- Searching for posts and scraping the results
- Saving scraped data to JSON files

### 4. Database Storage (`database.py`)

Manages the storage of Reddit data in an SQL database. This module provides:

- Creating the database schema
- Storing posts and comments
- Tracking changes in post and comment scores over time
- Exporting data to JSON files

### 5. Rate Limiting (`rate_limiter.py`)

Handles rate limiting and error handling for Reddit API requests. Features include:

- Limiting request rates to avoid API throttling
- Exponential backoff for rate limit errors
- Handling network and server errors
- Decorators for easy application of rate limiting and error handling

### 6. Main Application (`reddit_parser.py`)

Integrates all components into a complete solution with a command-line interface. Features include:

- Parsing posts from subreddits
- Searching for posts based on queries
- Tracking upvotes for specific posts over time
- Exporting data from the database

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reddit-topic-parser.git
cd reddit-topic-parser
```

2. Install the required dependencies:
```bash
pip install praw requests backoff
```

3. Create a `proxies.txt` file with your proxies (optional):
```
# Format: ip:port
123.123.123.123:8080
234.234.234.234:8080
```

4. Register your app with Reddit to get API credentials:
   - Go to https://www.reddit.com/prefs/apps
   - Click "create app" or "create another app"
   - Fill in the required information
   - Select "script" as the app type
   - Set the redirect URI to http://localhost:8080
   - Note your client ID and client secret

## Usage

### Command Line Interface

The application provides a command-line interface with several operation modes:

#### 1. Parse Subreddit

Parse posts from a subreddit and store them in the database:

```bash
python reddit_parser.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --user-agent "YOUR_USER_AGENT" subreddit python --limit 100 --sort-by new
```

#### 2. Search Posts

Search for posts in a subreddit and store the results in the database:

```bash
python reddit_parser.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --user-agent "YOUR_USER_AGENT" search python "web scraping" --limit 50
```

#### 3. Track Upvotes

Track upvotes for specific posts over time:

```bash
python reddit_parser.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --user-agent "YOUR_USER_AGENT" track post_id1 post_id2 --interval 1800 --duration 86400
```

#### 4. Export Data

Export data from the database to files:

```bash
python reddit_parser.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --user-agent "YOUR_USER_AGENT" export --output-dir exports --format json
```

### Common Options

- `--proxy-file`: Path to the proxy file (optional)
- `--db-path`: Path to the SQLite database file (default: reddit_data.db)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Database Schema

The application uses an SQLite database with the following tables:

### 1. `subreddits`
- `id`: Subreddit ID (primary key)
- `name`: Subreddit name
- `display_name`: Subreddit display name
- `subscribers`: Number of subscribers
- `created_utc`: Creation timestamp
- `description`: Subreddit description
- `last_updated`: Last update timestamp

### 2. `posts`
- `id`: Post ID (primary key)
- `title`: Post title
- `author`: Post author
- `created_utc`: Creation timestamp
- `score`: Post score (upvotes - downvotes)
- `upvote_ratio`: Ratio of upvotes to total votes
- `num_comments`: Number of comments
- `permalink`: Post permalink
- `url`: Post URL
- `is_self`: Whether the post is a self post
- `is_video`: Whether the post contains a video
- `is_original_content`: Whether the post is original content
- `over_18`: Whether the post is NSFW
- `spoiler`: Whether the post contains spoilers
- `stickied`: Whether the post is stickied
- `subreddit`: Subreddit name
- `subreddit_id`: Subreddit ID (foreign key)
- `domain`: Post domain
- `selftext`: Post text content
- `selftext_html`: Post text content in HTML
- `link_flair_text`: Post flair text
- `gilded`: Number of gildings
- `total_awards_received`: Total number of awards
- `scraped_at`: Timestamp when the post was scraped
- `last_updated`: Last update timestamp

### 3. `comments`
- `id`: Comment ID (primary key)
- `post_id`: Post ID (foreign key)
- `author`: Comment author
- `created_utc`: Creation timestamp
- `score`: Comment score
- `body`: Comment text content
- `body_html`: Comment text content in HTML
- `permalink`: Comment permalink
- `is_submitter`: Whether the comment is from the post submitter
- `stickied`: Whether the comment is stickied
- `parent_id`: Parent comment or post ID
- `gilded`: Number of gildings
- `total_awards_received`: Total number of awards
- `scraped_at`: Timestamp when the comment was scraped
- `last_updated`: Last update timestamp

### 4. `search_queries`
- `id`: Query ID (primary key, auto-increment)
- `query`: Search query
- `subreddit`: Subreddit name
- `sort_by`: Sort method
- `time_filter`: Time filter
- `num_results`: Number of results
- `search_time`: Timestamp when the search was performed

### 5. `post_history`
- `id`: History ID (primary key, auto-increment)
- `post_id`: Post ID (foreign key)
- `score`: Post score
- `upvote_ratio`: Upvote ratio
- `num_comments`: Number of comments
- `recorded_at`: Timestamp when the history was recorded

### 6. `comment_history`
- `id`: History ID (primary key, auto-increment)
- `comment_id`: Comment ID (foreign key)
- `score`: Comment score
- `recorded_at`: Timestamp when the history was recorded

## Example Code

### Initializing the Parser

```python
from reddit_parser import RedditTopicParser

# Initialize the parser
parser = RedditTopicParser(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="YOUR_USER_AGENT",
    proxy_file="proxies.txt",  # Optional
    db_path="reddit_data.db"
)

# Parse a subreddit
summary = parser.parse_subreddit(
    subreddit_name="python",
    limit=100,
    sort_by="new",
    time_filter="all",
    store_comments=True,
    comments_limit=None
)

# Search for posts
search_summary = parser.parse_search_results(
    subreddit_name="python",
    query="web scraping",
    limit=50,
    sort_by="relevance",
    time_filter="all",
    store_comments=True,
    comments_limit=None
)

# Track post upvotes
tracking_summary = parser.track_post_upvotes(
    post_ids=["post_id1", "post_id2"],
    interval=3600,  # 1 hour
    duration=86400  # 24 hours
)

# Export data
export_summary = parser.export_data(
    output_dir="exports",
    format="json"
)

# Close the parser
parser.close()
```

## Testing

The application includes a test suite to verify the functionality of each component:

```bash
python test_reddit_parser.py
```

## Best Practices

1. **API Credentials**: Keep your Reddit API credentials secure and never commit them to version control.

2. **Proxy Rotation**: Use a large pool of proxies to avoid rate limiting. Rotate proxies after each request or when rate limited.

3. **Rate Limiting**: Introduce delays between requests to avoid being blocked by Reddit. The application handles this automatically.

4. **Database Backup**: Regularly back up your database to prevent data loss.

5. **Error Handling**: The application includes comprehensive error handling, but be prepared to handle unexpected errors.

## Limitations

1. Reddit's API has rate limits that may restrict the amount of data you can scrape.

2. The application may not be able to scrape all comments from very large threads due to Reddit's API limitations.

3. Proxy quality can significantly impact the performance and reliability of the scraper.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [PRAW](https://praw.readthedocs.io/) - Python Reddit API Wrapper
- [Requests](https://requests.readthedocs.io/) - HTTP library for Python
- [SQLite](https://www.sqlite.org/) - Embedded SQL database engine
- [Backoff](https://github.com/litl/backoff) - Function decoration for backoff and retry
