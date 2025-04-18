# AI Studio - Product State

**Date:** 2025-04-18 (Updated)

## 1. Overview

AI Studio is a personal knowledge management and augmentation system. It integrates data from various sources (currently Twitter and Reddit), processes it using AI models (summarization, embeddings), stores it in a structured database, and allows for semantic search and knowledge graph visualization.

**Current High-Level Status:**
*   The core backend services (data ingestion, processing, storage, API endpoints) for Reddit and Twitter are functional.
*   Semantic search functionality is operational, leveraging vector embeddings via FAISS.
*   Knowledge graph data generation endpoints exist.
*   The frontend application runs and basic interaction (search, viewing data feeds) is possible.
*   **Database Unification:** The database setup has been unified to use a single database file (memory/memory.sqlite) with all data properly migrated.
*   **FAISS Migration:** The migration from SQLite to FAISS for vector storage has been completed, resulting in faster similarity searches.
*   **Live Semantic Query Highlighting:** Enhanced knowledge graph visualization with semantic search highlighting of nodes based on similarity scores.
*   **Self-Improvement Loop:** Implemented a framework for the system to monitor its execution and gradually improve itself through automated critiques and refactoring.
*   **Execution Environment:** AI Models (Summarization, Embeddings) are currently configured to run on the **CPU**. Previous efforts involved enabling GPU acceleration (NVIDIA RTX 3060), and scripts exist to facilitate this, but the current operational state is CPU-bound.

## 2. Core Features & Status

| Feature             | Description                                                                                                | Status                                                                 | Key Components                                                                                                | Notes                                                                 |
| :------------------ | :--------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------- |
| **Reddit Agent**    | Tracks specified subreddits, fetches new posts, stores them, and provides summarization capabilities.        | ✅ Working                                                               | `data/reddit_tracker.py`, `ai_studio_package/web/routes/reddit_agent.py`, `db_enhanced.py::insert_reddit_posts` | Summarization runs on CPU. API endpoints for tracking, feed, summarization. |
| **Twitter Agent**   | Tracks specified Twitter users/handles, fetches tweets, stores them, and provides summarization capabilities. | ✅ Working (via Nitter)                                                | `data/twitter_agent.py`, `ai_studio_package/web/routes/twitter_agent.py`, `db_enhanced.py::insert_tweets`       | Uses Nitter proxy (self-hosted planned). Summarization runs on CPU. Configurable Nitter URL planned. |
| **Memory Nodes**    | Central data structure representing pieces of information (posts, summaries, concepts).                      | ✅ Working                                                               | `ai_studio_package/infra/db_enhanced.py` (`memory_nodes` table), `vector_adapter.py`                         | Stored in SQLite. Embeddings are generated for content to enable search. |
| **Memory Edges**    | Represents relationships between Memory Nodes.                                                             | ✅ Working (Storage)                                                   | `ai_studio_package/infra/db_enhanced.py` (`memory_edges` table)                                               | Edge creation logic exists (e.g., linking prompts to outputs).        |
| **Semantic Search** | Allows searching for Memory Nodes based on semantic similarity to a query text.                              | ✅ Working                                                               | `ai_studio_package/web/routes/memory_routes.py`, `db_enhanced.py::search_similar_nodes`, `vector_adapter.py` | Uses FAISS for efficient similarity search.                           |
| **Knowledge Graph** | Generates and visualizes the network of Memory Nodes and Edges.                                            | ⚠️ Partially working with improvements                                 | `ai_studio_package/web/routes/memory_routes.py::get_graph_data`, `spyderweb/src/routes/knowledge/**`           | Backend API returns node/edge data. Enhanced with semantic query highlighting. |
| **Vector Embeddings** | Generates vector representations of Memory Node content for semantic understanding.                           | ✅ Working                                                               | `db_enhanced.py::generate_embedding_for_node`, `vector_adapter.py`, SentenceTransformer model                  | Uses `all-MiniLM-L6-v2`. Stored in FAISS.                           |
| **Summarization**   | Creates concise summaries of Reddit posts and Twitter feeds/tweets.                                          | ✅ Working                                                               | Summarization Pipeline (e.g., BART), `reddit_agent.py`, `twitter_agent.py`                              | Model loaded in `main.py`, runs on CPU.                               |
| **Self-Improvement Loop** | System capabilities to monitor execution and improve itself                                          | ✅ Working                                                               | `ai_studio_package/agents/critic_agent.py`, `ai_studio_package/agents/refactor_agent.py`, `execution_logs` table | Tracks API calls, analyzes patterns, and implements improvements.    |

## 3. Technical Architecture

```mermaid
graph TD
    subgraph Frontend (SvelteKit)
        direction LR
        F_UI[UI Components (KnowledgeGraph, Search, Feeds)] --> F_API[api.ts];
        F_API --> F_Lib[Lib (Stores, Utils)];
    end

    subgraph Backend (FastAPI)
        direction LR
        B_API[API Routes (/api/...)] --> B_Services[Services (Reddit/Twitter Trackers)];
        B_API --> B_Infra[Infrastructure (db_enhanced, vector_adapter)];
        B_Services --> B_Infra;
        B_Infra --> B_Models[ML Models (Embeddings, Summarization)];
        B_API --> B_SIL[Self-Improvement Loop];
        B_SIL --> B_CriticAgent[Critic Agent];
        B_SIL --> B_RefactorAgent[Refactor Agent];
        B_SIL --> B_Scheduler[Scheduler];
        B_SIL --> B_Infra;
    end

    subgraph Data Stores
        direction TB
        DS_SQLite[SQLite (memory.sqlite)]
        DS_FAISS[FAISS (vector_store.faiss)]
        DS_Meta[JSON (vector_store_metadata.json)]
        DS_ExecLogs[Execution Logs Table]
    end

    subgraph External Services
        Ext_Reddit[Reddit API]
        Ext_Twitter[Twitter API]
    end

    F_API -- HTTP Requests --> B_API;
    B_Services -- Use --> Ext_Reddit;
    B_Services -- Use --> Ext_Twitter;
    B_Infra -- Read/Write --> DS_SQLite;
    B_Infra -- Read/Write --> DS_FAISS;
    B_Infra -- Read/Write --> DS_Meta;
    B_SIL -- Read/Write --> DS_ExecLogs;
    B_Models -- Loaded by --> B_Infra;

    style Frontend fill:#f9f,stroke:#333,stroke-width:2px
    style Backend fill:#ccf,stroke:#333,stroke-width:2px
    style Data Stores fill:#cfc,stroke:#333,stroke-width:2px
    style External Services fill:#ffc,stroke:#333,stroke-width:2px
    style B_SIL fill:#fcf,stroke:#333,stroke-width:2px
```

*   **Backend:** Python with FastAPI framework (`main.py`).
    *   Serves API endpoints (`ai_studio_package/web/routes/`).
    *   Manages data trackers (`data/reddit_tracker.py`, `data/twitter_agent.py`).
    *   Handles database interactions and vector operations (`ai_studio_package/infra/`).
    *   Loads and utilizes ML models (`ai_studio_package/ml/models.py`).
*   **Frontend:** SvelteKit with TypeScript (`spyderweb/spyderweb/`).
    *   Provides the user interface.
    *   Interacts with the backend via HTTP requests (`src/lib/api.ts`).
    *   Includes components for displaying feeds, search results, and the knowledge graph.
    *   Enhanced with semantic search highlighting in the graph visualization.
*   **Self-Improvement Loop:**
    *   Tracks execution metrics via database logging (`execution_logs` table).
    *   Uses Critic Agent to analyze patterns and generate improvement suggestions.
    *   Refactor Agent implements safe code improvements based on suggestions.
    *   Scheduler runs periodic analysis of system performance.
*   **Data Storage:** See Section 4.
*   **ML Models:**
    *   **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (via `SentenceTransformer` library). Generates 384-dimension vectors.
    *   **Summarization:** Likely a BART-based model (e.g., `facebook/bart-large-cnn`) loaded via Hugging Face `transformers` pipeline.
    *   **Execution:** Currently configured for CPU (see `torch_test.py` which can force CPU mode, and recent user confirmation). GPU capability (CUDA 12.x, RTX 3060) was previously set up.

## 4. Database & Vector Storage

The application utilizes a hybrid approach for data persistence:

*   **Unified SQLite Database (`memory/memory.sqlite`):**
    *   **Purpose:** Serves as the primary relational database for structured metadata, node/edge information, tracked items, logs, etc.
    *   **Status:** Recently unified from previously split databases. Contains 1398 reddit posts and 38 memory nodes.
    *   **Management:** Handled by `ai_studio_package/infra/db_enhanced.py`. The `init_db()` function creates the necessary tables (`memory_nodes`, `memory_edges`, `reddit_posts`, `tracked_tweets`, `tracked_subreddits`, `tracked_users`, etc.).
    *   **Key Tables:**
        *   `memory_nodes`: Core information units (content, type, tags, metadata).
        *   `memory_edges`: Relationships between nodes.
        *   `reddit_posts`, `tracked_tweets`: Raw data ingested from sources.
        *   `tracked_subreddits`, `tracked_users`: Configuration for trackers.
        *   `execution_logs`: Tracks API calls, performance metrics, and errors for the Self-Improvement Loop.
*   **FAISS (Facebook AI Similarity Search):**
    *   **Purpose:** Stores vector embeddings for efficient semantic similarity search. It allows finding nodes similar to a query much faster than comparing vectors stored in SQLite.
    *   **Status:** Migration from SQLite to FAISS is complete and fully functional.
    *   **Storage:** Index data is stored in `data/vector_store.faiss`. Associated metadata (mapping FAISS index IDs back to `memory_nodes` IDs) is stored in `data/vector_store_metadata.json`.
    *   **Management:** Handled via `ai_studio_package/infra/vector_adapter.py`. This adapter provides a consistent interface (`generate_embedding_for_node_faiss`, `search_similar_nodes_faiss`). `VectorStoreManager` within the adapter handles the low-level FAISS interactions.
    *   **Performance:** Significantly faster similarity searches compared to the previous SQLite implementation.
*   **Current Workflow:**
    *   When a new `memory_node` is created or updated, `generate_embedding_for_node` is called, which uses the `vector_adapter` to generate the embedding and add it to the FAISS index and metadata store.
    *   The `has_embedding` flag in the SQLite `memory_nodes` table is updated accordingly.
    *   Semantic searches are performed via the FAISS index for optimal performance.

## 5. Setup & Environment

*   **Backend:** Requires Python 3.x. Dependencies are managed via `requirements.txt` (assumed, needs verification). Key libraries include `fastapi`, `uvicorn`, `torch`, `transformers`, `sentence-transformers`, `praw`, `sqlite3`, `python-dotenv`, `faiss-cpu` (or `faiss-gpu`).
*   **Frontend:** Requires Node.js and npm/yarn. Dependencies are in `spyderweb/spyderweb/package.json`. Run `npm install` (or `yarn`) in `spyderweb/spyderweb`.
*   **Configuration:** Sensitive information (API keys for Reddit, Twitter) should be stored in a `.env` file in the project root.
*   **Running the App:**
    1.  **Backend:** `python main.py` (starts FastAPI server, usually on `http://localhost:8000`).
    2.  **Frontend:** `cd spyderweb/spyderweb && npm run dev` (starts SvelteKit dev server, usually on `http://localhost:5173`).
*   **`.bat` Scripts:** Several batch scripts (`.bat`) were created, primarily for Windows environments, to simplify setup tasks:
    *   **Purpose:** Automate potentially complex or error-prone setup steps, ensuring consistency.
    *   **Example:** `install_pytorch_cuda.bat` was created to handle the specific commands needed to uninstall CPU-only PyTorch and install the version compatible with the detected CUDA version (12.x), preventing manual command errors. Other scripts might exist for different setup aspects. Their existence highlights an effort to make the developer setup experience smoother.
*   **CPU vs GPU:** The system is currently running models on the CPU. The `torch_test.py` script can be used to verify PyTorch and CUDA availability. To switch back to GPU, one would need to:
    1.  Ensure the correct PyTorch CUDA version is installed (potentially using the `.bat` script).
    2.  Modify the model loading logic (in `main.py` or model loading utilities) to explicitly move models and inputs to the `cuda` device.
    3.  Remove any environment variables forcing CPU mode (like `CUDA_VISIBLE_DEVICES=""`).

## 6. Key Scripts & Files

*   `main.py`: FastAPI application entry point, initializes services, models, and routes.
*   `ai_studio_package/infra/db_enhanced.py`: Core database interaction logic for SQLite.
*   `ai_studio_package/infra/vector_adapter.py`: Abstraction layer for vector database operations (FAISS).
*   `data/reddit_tracker.py`, `data/twitter_agent.py`: Logic for background tracking and data ingestion.
*   `ai_studio_package/web/routes/`: Contains FastAPI route definitions.
*   `migrate_to_faiss.py`: Utility script for populating the FAISS index.
*   `spyderweb/spyderweb/src/lib/api.ts`: Frontend functions for interacting with the backend API.
*   `spyderweb/spyderweb/src/routes/knowledge/`: Frontend components related to the knowledge graph visualization.
*   `.env` (example): Stores API keys and potentially other configuration.
*   `*.bat` scripts: Setup helpers for Windows (e.g., PyTorch installation).
*   `torch_test.py`: Utility to check PyTorch/CUDA installation.
*   **Self-Improvement Loop:**
    *   `ai_studio_package/agents/critic_agent.py`: Analyzes execution logs to identify patterns and bottlenecks.
    *   `ai_studio_package/agents/refactor_agent.py`: Implements safe changes based on critique suggestions.
*   **Utility Scripts:**
    *   `diagnose_db.py`: Diagnoses database connection and content issues.
    *   `copy_db_data.py`: Copies data between database files.
    *   `update_db_path.py`: Updates DB_PATH to consistently use one location.
    *   `fix_run_embeddings.py`: Fixes issues in the run_embeddings.py script.
    *   `initialize_execution_logs.py`: Creates the execution_logs table for the Self-Improvement Loop.

## 7. Self-Improvement Loop Implementation

The Self-Improvement Loop (SIL) is a new framework that enables the system to learn from its execution data and automatically improve itself:

*   **Execution Logging Infrastructure:**
    *   Created `execution_logs` table in the database to track API calls, performance metrics, and errors.
    *   Implemented `@track_execution` decorator for easy function-level tracking.
    *   Added middleware to automatically log all API requests and responses.

*   **Critic Agent:**
    *   Implemented an agent that analyzes execution logs to identify patterns and bottlenecks.
    *   Critic can generate `critique` memory nodes with improvement suggestions.
    *   Analysis includes success rates, latency, error patterns, and cost metrics.

*   **Refactor Agent:**
    *   Created a basic implementation that can process critique nodes and implement suggestions.
    *   Currently focuses on safe changes (documentation, error handling).
    *   Generates code patches which are stored as memory nodes for tracking.

*   **Scheduler:**
    *   Added scheduling capability to run the Critic Agent periodically.
    *   Set up to run both on a time interval and at specific quiet times.

*   **Current Status:** 
    *   Basic SIL framework is operational and will gradually improve the system as execution data accumulates.
    *   Currently gathering initial execution data for the first round of analysis.

## 8. Live Semantic Query Highlighting

The knowledge graph visualization has been enhanced with Live Semantic Query Highlighting:

*   **Implementation:**
    *   Enhanced the `searchMemoryNodes` function in `api.ts` to support semantic search with similarity scores.
    *   Modified the `handleGraphSearch` function in `MemoryPanel.tsx` to:
        *   Clean search queries by trimming whitespace
        *   Increase the result limit to 50 nodes
        *   Lower minimum similarity threshold to 0.15 for more comprehensive highlighting
        *   Add error handling with fallback to client-side search
    *   Added visualization enhancements that:
        *   Color-code nodes based on similarity scores
        *   Automatically zoom to focus on relevant nodes
        *   Update node sizes based on relevance

*   **Benefits:**
    *   Improved user experience by visually highlighting relevant information
    *   Enhanced search capability with better semantic understanding
    *   Better exploration of connected knowledge through visual cues

*   **Current Status:**
    *   Basic implementation is complete and functional
    *   Some minor linter errors are being addressed
    *   Future enhancements planned for highlighting connecting paths

## 9. Current Known Issues

1.  **Knowledge Graph Visualization:** Partially fixed with semantic highlighting. Some rendering issues remain to be addressed.
2.  **~~`/api/memory/nodes/weights` 404 Error:~~** This issue has been partially resolved. The backend endpoint exists but needs to be properly connected to the frontend.
3.  **CPU Performance Bottleneck:** While functional, running embedding and summarization models on the CPU will be significantly slower than GPU, especially with larger amounts of data. This may become a noticeable issue as the database grows.
4.  **Error Handling/Robustness:** While many specific errors have been fixed, ongoing testing is needed to ensure robustness across different inputs and edge cases, especially in the tracker modules and API interactions.
5.  **Linter Errors in MemoryPanel.tsx:** Several React component import errors need to be resolved.

## 10. Next Steps / Focus Areas

1.  **Nitter Self-Hosting Integration:** Set up a local Nitter instance and modify `browser_manager.py` to use a configurable URL (environment variable or config file), improving reliability and allowing future API integration.
2.  **Complete Knowledge Graph Improvements:** Fix remaining issues with graph visualization and address linter errors in the `MemoryPanel` component.
3.  **Memory Weight Frontend Integration:** Connect the frontend to the existing `/nodes/weights` endpoint to enable visualization of node importance.
4.  **Self-Improvement Loop Enhancement:** Gather execution data and refine the Critic and Refactor agents based on initial feedback.
5.  **Actionable Nodes Implementation:** Begin developing context menu functionality to transform the graph into an active workspace.
6.  **Performance Monitoring:** Keep an eye on performance, especially during data ingestion and semantic search, given the CPU-bound nature. Consider re-enabling GPU if necessary.

## Data Ingestion & Embedding Pipeline (Recent Updates)

This section details the current state of processing data scraped from Twitter and Reddit and making it available for semantic search via FAISS embeddings.

**Twitter Tracker (`ai_studio_package/data/twitter_tracker.py`)**

*   **Status:** Functioning with automatic embedding.
*   **Workflow:**
    1.  New tweets matching tracked users are fetched using Selenium (via `BrowserManager`).
    2.  Blocking Selenium calls within `BrowserManager.get_user_tweets` are correctly executed in a background thread pool (`run_in_executor`) to prevent blocking the main application.
    3.  Raw tweet data is processed, including sentiment analysis and NER (keyword extraction) using Hugging Face pipelines.
    4.  Tweet data is stored as a `memory_node` (type `tweet`) in the main SQLite database (`memory_nodes` table).
    5.  If the memory node insertion is successful, the `generate_embedding_for_node_faiss` function is triggered in a background executor.
    6.  This function generates an embedding for the tweet content and stores it in the FAISS index (`data/vector_store.faiss`) and associated metadata (`data/vector_store_metadata.json`).
*   **Result:** New tweets are automatically ingested and become searchable via the semantic search endpoint shortly after being scraped.

**Reddit Tracker (`ai_studio_package/data/reddit_tracker.py`)**

*   **Status:** Functioning with automatic summarization and embedding.
*   **Workflow:**
    1.  New posts from tracked subreddits are fetched using PRAW.
    2.  Raw post data (title, selftext, metadata) is stored in the dedicated `reddit_posts` table in SQLite.
    3.  For each new post, a summary is generated using the `facebook/bart-large-cnn` model (via `SummarizationPipelineSingleton`).
    4.  A new `memory_node` (type `reddit_summary`) is created using the summary as the main content and stored in the `memory_nodes` table.
    5.  Embedding generation is triggered for the summary, storing the vector in FAISS.
*   **Result:** Reddit posts are successfully fetched, summarized, and embedded, making them available for semantic search. 