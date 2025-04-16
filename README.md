# SpyderWeb AI Studio

A comprehensive AI-powered platform that integrates with various data sources, provides visualization tools, and enables semantic search capabilities.

## Current State

### Features

- **Memory Graph Visualization**
  - Interactive knowledge graph with node and edge visualization
  - Theme-sensitive UI (adapts to light/dark mode)
  - Violet particle animation on connections
  - Dynamic graph generation from text

- **Semantic Search**
  - Search for related content based on meaning, not just keywords
  - Similarity threshold adjustment
  - Scrollable results display

- **Social Media Integration**
  - Twitter feed tracking and analysis
  - Reddit subreddit monitoring
  - Content aggregation and insights

- **Data Management**
  - Vector database for efficient semantic storage
  - SQL query export capabilities
  - Connection management between nodes

### Architecture

- **Frontend**
  - React-based UI with TypeScript
  - ForceGraph2D for graph visualization
  - Tailwind CSS and custom UI components

- **Backend**
  - FastAPI server
  - Vector database for embeddings
  - Integration with external APIs (Twitter, Reddit)

## Setup

### Prerequisites

- Python 3.11+
- Node.js and npm/yarn
- Required Python packages (see requirements.txt)

### Configuration

1. Create a `.env` file with the required environment variables:
   ```
   # Database
   DB_PATH=./memory/vectors.sqlite
   
   # API Keys (replace with your own)
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   
   # Model settings
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   cd spyderweb/spyderweb
   npm install
   ```

### Running the Application

1. Start the backend server:
   ```
   python main.py
   ```

2. Start the frontend development server:
   ```
   cd spyderweb/spyderweb
   npm run dev
   ```

3. Access the application at http://localhost:8082 (or configured port)

## Development Status

This project is under active development. Recent improvements include:
- Enhanced knowledge graph visualization with theme support
- Improved semantic search UI with scrolling capabilities
- Fixed UI layout issues in panel components

## Known Issues

- Backend may require specific packages like transformers and torchvision
- Some API routes may need configuration troubleshooting
- Reddit tracker may have syntax issues in some environments

## Next Steps

- Further UI polish and responsiveness improvements
- Enhanced data visualization options
- Additional social media integration options
- Improved error handling and user feedback
