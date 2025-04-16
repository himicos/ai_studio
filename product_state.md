# AI Studio - Product State

**Date:** 2025-04-16

## 1. Overview

AI Studio is a personal knowledge management and augmentation system. It integrates data from various sources (currently Twitter and Reddit), processes it using AI models (summarization, embeddings), stores it in a structured database, and allows for semantic search and knowledge graph visualization.

**Current High-Level Status:**
*   The core backend services (data ingestion, processing, storage, API endpoints) for Reddit and Twitter are functional.
*   Semantic search functionality is operational, leveraging vector embeddings.
*   Knowledge graph data generation endpoints exist.
*   The frontend application runs and basic interaction (search, viewing data feeds) is possible.
*   **Key Issue:** The knowledge graph visualization on the frontend has known issues, although some basic rendering/filtering might be partially working.
*   **Execution Environment:** AI Models (Summarization, Embeddings) are currently configured to run on the **CPU**. Previous efforts involved enabling GPU acceleration (NVIDIA RTX 3060), and scripts exist to facilitate this, but the current operational state is CPU-bound.

## 2. Core Features & Status

| Feature             | Description                                                                                                | Status                                                                 | Key Components                                                                                                | Notes                                                                 |
| :------------------ | :--------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------- |
| **Reddit Agent**    | Tracks specified subreddits, fetches new posts, stores them, and provides summarization capabilities.        | ✅ Working                                                               | `data/reddit_tracker.py`, `ai_studio_package/web/routes/reddit_agent.py`, `db_enhanced.py::insert_reddit_posts` | Summarization runs on CPU. API endpoints for tracking, feed, summarization. |
| **Twitter Agent**   | Tracks specified Twitter users/handles, fetches tweets, stores them, and provides summarization capabilities. | ✅ Working                                                               | `data/twitter_agent.py`, `ai_studio_package/web/routes/twitter_agent.py`, `db_enhanced.py::insert_tweets`       | Summarization runs on CPU. API endpoints for tracking, feed, summarization. |
| **Memory Nodes**    | Central data structure representing pieces of information (posts, summaries, concepts).                      | ✅ Working                                                               | `ai_studio_package/infra/db_enhanced.py` (`memory_nodes` table), `vector_adapter.py`                         | Stored in SQLite. Embeddings are generated for content to enable search. |
| **Memory Edges**    | Represents relationships between Memory Nodes.                                                             | ✅ Working (Storage)                                                   | `ai_studio_package/infra/db_enhanced.py` (`memory_edges` table)                                               | Edge creation logic exists (e.g., linking prompts to outputs).        |
| **Semantic Search** | Allows searching for Memory Nodes based on semantic similarity to a query text.                              | ✅ Working                                                               | `ai_studio_package/web/routes/memory_routes.py`, `db_enhanced.py::search_similar_nodes`, `vector_adapter.py` | Uses FAISS (via vector_adapter) for efficient similarity search.        |
| **Knowledge Graph** | Generates and visualizes the network of Memory Nodes and Edges.                                            | ⚠️ Backend OK, Frontend Issues                                         | `ai_studio_package/web/routes/memory_routes.py::get_graph_data`, `spyderweb/src/routes/knowledge/**`           | Backend API returns node/edge data. Frontend visualization needs debugging. |
| **Vector Embeddings** | Generates vector representations of Memory Node content for semantic understanding.                           | ✅ Working                                                               | `db_enhanced.py::generate_embedding_for_node`, `vector_adapter.py`, SentenceTransformer model                  | Currently uses `all-MiniLM-L6-v2`. Stored via FAISS adapter.        |
| **Summarization**   | Creates concise summaries of Reddit posts and Twitter feeds/tweets.                                          | ✅ Working                                                               | Summarization Pipeline (e.g., BART), `reddit_agent.py`, `twitter_agent.py`                              | Model loaded in `main.py`, runs on CPU.                               |

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
    end

    subgraph Data Stores
        direction TB
        DS_SQLite[SQLite (memory.sqlite)]
        DS_FAISS[FAISS (vector_store.faiss)]
        DS_Meta[JSON (vector_store_metadata.json)]
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
    B_Models -- Loaded by --> B_Infra;

    style Frontend fill:#f9f,stroke:#333,stroke-width:2px
    style Backend fill:#ccf,stroke:#333,stroke-width:2px
    style Data Stores fill:#cfc,stroke:#333,stroke-width:2px
    style External Services fill:#ffc,stroke:#333,stroke-width:2px
```

*   **Backend:** Python with FastAPI framework (`main.py`).
    *   Serves API endpoints (`ai_studio_package/web/routes/`).
    *   Manages data trackers (`data/reddit_tracker.py`, `data/twitter_agent.py`).
    *   Handles database interactions and vector operations (`ai_studio_package/infra/`).
    *   Loads and utilizes ML models (`ai_studio_package/ml/models.py`).
*   **Frontend:** SvelteKit with TypeScript (`spyderweb/spyderweb/`).
    *   Provides the user interface.
    *   Interacts with the backend via HTTP requests (`src/lib/api.ts`).
    *   Includes components for displaying feeds, search results, and the knowledge graph (using likely D3 or a similar library).
*   **Data Storage:** See Section 4.
*   **ML Models:**
    *   **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (via `SentenceTransformer` library). Generates 384-dimension vectors.
    *   **Summarization:** Likely a BART-based model (e.g., `facebook/bart-large-cnn`) loaded via Hugging Face `transformers` pipeline.
    *   **Execution:** Currently configured for CPU (see `torch_test.py` which can force CPU mode, and recent user confirmation). GPU capability (CUDA 12.x, RTX 3060) was previously set up.

## 4. Database & Vector Storage

The application utilizes a hybrid approach for data persistence:

*   **SQLite (`memory/memory.sqlite`):**
    *   **Purpose:** Serves as the primary relational database for structured metadata, node/edge information, tracked items, logs, etc.
    *   **Management:** Handled by `ai_studio_package/infra/db_enhanced.py`. The `init_db()` function creates the necessary tables (`memory_nodes`, `memory_edges`, `reddit_posts`, `tracked_tweets`, `tracked_subreddits`, `tracked_users`, etc.).
    *   **Key Tables:**
        *   `memory_nodes`: Core information units (content, type, tags, metadata).
        *   `memory_edges`: Relationships between nodes.
        *   `reddit_posts`, `tracked_tweets`: Raw data ingested from sources.
        *   `tracked_subreddits`, `tracked_users`: Configuration for trackers.
*   **FAISS (Facebook AI Similarity Search):**
    *   **Purpose:** Stores vector embeddings for efficient semantic similarity search. It allows finding nodes similar to a query much faster than comparing vectors stored in SQLite.
    *   **Storage:** Index data is stored in `data/vector_store.faiss`. Associated metadata (mapping FAISS index IDs back to `memory_nodes` IDs) is stored in `data/vector_store_metadata.json`.
    *   **Management:** Abstracted via `ai_studio_package/infra/vector_adapter.py`. This adapter provides a consistent interface (`generate_embedding_for_node_faiss`, `search_similar_nodes_faiss`) whether using FAISS or potentially falling back to another method (though FAISS is currently the target). `VectorStoreManager` within the adapter likely handles the low-level FAISS interactions.
    *   **Flag:** `USE_FAISS_VECTOR_STORE = True` in `db_enhanced.py` indicates FAISS is the primary vector store.
*   **Migration & Synchronization:**
    *   **`migrate_to_faiss.py`:** A script exists to facilitate populating the FAISS index, likely by iterating through `memory_nodes` in SQLite, generating embeddings if needed, and adding them to the FAISS store via the `vector_adapter`.
    *   **`dual_write_enabled` flag (in `vector_adapter`):** This flag was introduced to allow writing embeddings to *both* SQLite (potentially legacy storage) and FAISS simultaneously during a transition period. It's unclear if this is currently active, but the mechanism exists.
    *   **Current Workflow:** When a new `memory_node` is created or updated, `generate_embedding_for_node` is called, which in turn uses the `vector_adapter` (`generate_embedding_for_node_faiss`) to generate the embedding and add it to the FAISS index and metadata store. The `has_embedding` flag in the SQLite `memory_nodes` table is likely updated.

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

## 7. Current Known Issues

1.  **Knowledge Graph Visualization:** The primary known issue. The frontend component responsible for rendering the graph (`spyderweb/src/routes/knowledge/**`) is not working correctly or fully. Needs debugging to understand if the issue is data fetching, data parsing, rendering logic (D3/SVG), or component state management.
2.  **`/api/memory/nodes/weights` 404 Error:** Logs indicate a `404 Not Found` error for this endpoint. Need to investigate:
    *   Is this endpoint still needed by the frontend?
    *   Was it removed or never implemented in the backend (`ai_studio_package/web/routes/memory_routes.py`)?
    *   If needed, implement it; if not, remove calls from the frontend (`api.ts`).
3.  **CPU Performance Bottleneck:** While functional, running embedding and summarization models on the CPU will be significantly slower than GPU, especially with larger amounts of data. This may become a noticeable issue as the database grows.
4.  **Error Handling/Robustness:** While many specific errors have been fixed, ongoing testing is needed to ensure robustness across different inputs and edge cases, especially in the tracker modules and API interactions.

## 8. Next Steps / Focus Areas

1.  **Debug Knowledge Graph Visualization:** This is the most pressing user-facing issue. Investigate the frontend component, data flow, and any console errors.
2.  **Investigate `/api/memory/nodes/weights` 404:** Determine the status and necessity of this endpoint and resolve accordingly.
3.  **Testing & Refinement:** Conduct thorough testing of all features (Reddit/Twitter tracking over time, summarization quality, search relevance, node/edge creation).
4.  **Performance Monitoring:** Keep an eye on performance, especially during data ingestion and semantic search, given the CPU-bound nature. Consider re-enabling GPU if necessary.
5.  **Documentation:** Continue to document code, architecture, and setup procedures. 