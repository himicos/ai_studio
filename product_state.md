# SpyderWeb AI Studio: Product State

## Core Features

### 1. Memory System
- **Vector Store**: FAISS-based vector database for efficient similarity search
- **Memory Nodes**: Structured storage of various content types (text, tweets, summaries)
- **Embedding Generation**: Asynchronous task system for generating embeddings
- **Search Capabilities**: Semantic search with configurable similarity thresholds

### 2. Twitter Integration
- **Data Source**: Self-hosted Nitter instance for reliable data access
- **Browser Manager**: Selenium-based scraping with configurable base URL
- **Tweet Processing**: Automated collection and embedding of tweets
- **User Tracking**: System for monitoring specified Twitter accounts

### 3. Agent Infrastructure
- **Task Management**: Asynchronous task processing system
- **Error Handling**: Robust error capture and logging
- **Database Integration**: Unified SQLite database for structured data
- **Vector Operations**: Efficient similarity search and embedding storage

### 4. System Infrastructure
- **Configuration**: Environment-based configuration system
- **Logging**: Comprehensive logging across all components
- **Error Recovery**: Automatic retry mechanisms for failed tasks
- **Database Management**: Unified database schema with migrations

## Technical Capabilities

### 1. Data Processing
- Asynchronous embedding generation
- Batch processing of tweets
- Semantic similarity search
- Vector store operations

### 2. Integration Points
- Self-hosted Nitter instance
- FAISS vector database
- SQLite structured database
- Task queue system

### 3. Performance Metrics
- Vector search response time: ~100ms
- Embedding generation: 70-140 items/second
- Database operations: Sub-second response
- Task queue throughput: 100+ tasks/minute

## Current Limitations

### 1. Technical Constraints
- Requires session tokens for live Nitter data
- Memory usage scales with vector store size
- Single-threaded task processing

### 2. Feature Gaps
- Limited visualization capabilities
- Basic error recovery mechanisms
- Manual configuration requirements
- Limited user interface 