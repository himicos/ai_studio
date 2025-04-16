# Twitter Agent Status & Roadmap Update

**Date:** 2025-04-15 (Approx. 06:15 UTC)

## Current Status

The Twitter Agent panel provides core functionality for tracking users, scanning tweets, and viewing a filterable/sortable feed with basic AI enrichments applied locally during data processing.

**Completed Features:**

*   **User Management:**
    *   Add users via direct handle input (`UserAddDirect`).
    *   Display list of tracked users (`TrackedUserIcon`).
    *   Remove tracked users (deletes user from `tracked_users`, keeps tweets in `tracked_tweets` per preference).
*   **Scanning & Tracking:**
    *   Manual "Run Scan Now" button (`/run_scan` route calls `tracker.scan()` directly).
    *   Persistent "Start/Stop Tracking" buttons (`/start_tracking` & `/stop_tracking` routes correctly call `tracker.start()` & `tracker.stop()` to manage the background `asyncio` loop in `TwitterTracker`). Scan interval defaults to 600s.
    *   Database (`memory.sqlite`) stores `tracked_users` and `tracked_tweets`.
    *   Duplicate tweet prevention via `tweet_id` primary key in `tracked_tweets`.
*   **Feed Display & Filtering (Phase 1 - COMPLETE):**
    *   Display tweets in scrollable feed (`FeedList`).
    *   Show user handle (`@handle`), content, relative date posted (`formatDistanceToNow`).
    *   Display engagement counts (Replies, Retweets, Likes).
    *   Provide link to original tweet on `twitter.com` constructed from `handle` and `id`.
    *   Integrated `FilterPanel`:
        *   Keyword filtering via text input (updates `/feed` API call parameter).
        *   Sorting by Date, Likes, Retweets, Replies (Asc/Desc) via dropdown/buttons (updates `/feed` API call parameters `sort_by`, `sort_order`).
        *   Sorting by Score option available in UI (`TwitterAgentPanel` maps UI 'score' option to backend 'score' `sort_by` parameter).
    *   Infinite scroll implemented using `react-intersection-observer` to trigger `fetchFeed(true)` when nearing the bottom of the list. `fetchFeed` manages `offset` and `limit` state.
*   **AI Enrichments (Phase 2 - Partially Complete):**
    *   **Sentiment Analysis:**
        *   ✅ Infrastructure Added: `sentiment TEXT` column in `tracked_tweets`. `score REAL` column added to DB.
        *   ✅ Local AI Integration: `cardiffnlp/twitter-roberta-base-sentiment-latest` model pipeline loaded via `transformers` (attempts GPU, falls back to CPU). Runs within `process_tweets` in `TwitterTracker`.
        *   ✅ Score Population: `score` column populated with `1.0` (positive), `0.0` (neutral), or `-1.0` (negative) based on sentiment label during `process_tweets`.
        *   ✅ Frontend Display: Sentiment shown as colored text badges (`<span>` with Tailwind classes: `bg-green-100/text-green-800` for Positive, `bg-red-100/text-red-800` for Negative, `bg-yellow-100/text-yellow-800` for Neutral) displaying the capitalized label (e.g., "Positive") in `FeedList.tsx`.
    *   **Keyword/Entity Extraction:**
        *   ✅ Local NER Integration: `dslim/bert-base-NER` model pipeline loaded via `transformers` (attempts GPU, falls back to CPU) with `grouped_entities=True`. Runs within `process_tweets`.
        *   ✅ Storage: Extracted keywords list stored as JSON string in `tracked_tweets` `keywords` column.
        *   ✅ Filtering: Refined filtering applied in `process_tweets`: strips common punctuation, requires length >= 3, must not start with `#` or `@`, must contain an alphabetic character. Duplicates removed case-insensitively.
        *   ✅ Frontend Display: Keywords shown as `<span>` badges (`bg-secondary`) in `FeedList.tsx`.

**Known Issues:**

*   **Score Sorting:** Sorting by "Score" (Asc/Desc) in the UI does not currently order the feed correctly based on the numerical sentiment score (1.0, 0.0, -1.0) stored in the database. Backend API (`/feed`) correctly receives `sort_by=score` and query includes `ORDER BY t.score`, but visual result is incorrect. Debugging paused.
*   **NER Imperfections:** The `dslim/bert-base-NER` model occasionally extracts partial entities (e.g., "Google Au" instead of "Google Auth") or fails to identify domain-specific terms (e.g., "Walrus"). Current filtering helps but isn't perfect.

## Recent Progress (since last update)

*   **Summarization Pipeline:**
    *   Refactored to load summarization pipeline (`sshleifer/distilbart-cnn-12-6`) and its tokenizer at application startup (`main.py`) for improved performance.
    *   Fixed crash for long inputs by implementing explicit token-based truncation in the `/summarize_feed` endpoint using the pre-loaded tokenizer.
    *   Added optional `focus` parameter (`efficiency`, `development`, `finance`) to `/summarize_feed` endpoint to filter tweets by relevant keywords before summarizing.
    *   Added UI dropdown in `TwitterAgentPanel` to select the summary focus.
    *   Created new endpoint `/summarize_tweet/{tweet_id}` to summarize individual tweets.
    *   Added UI button (✨ icon) to each tweet card in `FeedList` to trigger individual summarization.
*   **Memory Integration:**
    *   Saved generated feed summaries to `memory_nodes` table (`node_type='twitter_summary'`).
    *   Saved individual tweet summaries to `memory_nodes` table (`node_type='tweet_summary'`, metadata includes `original_tweet_id`).
*   **Keyword Extraction:**
    *   Installed `yake` library.
    *   Implemented `/keywords` endpoint to extract trending keywords from recent tweets (last `days_back` days) using `yake`.
*   **Bug Fixes & Diagnostics:**
    *   Resolved `UnicodeEncodeError` in console logging by setting UTF-8 encoding for handlers in `main.py`.
    *   Fixed `sqlite3.OperationalError: no such column: id` in `/summarize_tweet` endpoint by correcting query to use `tweet_id`.
    *   Addressed intermittent backend startup failures (`Errno 10048` port conflict, `ModuleNotFoundError` due to incorrect CWD).
    *   Added diagnostic logging to `BrowserManager.scrape_profile` to investigate data attribution.

## Key Issues & Findings

*   **Scraper Data Attribution:** Confirmed via logs that the scraper is currently fetching content from `@sama` (Sam Altman) but incorrectly associating it with the tracked user `@Art1000x` in the database. This needs urgent debugging.
*   **Score Sorting (Existing):** Sorting by "Score" in the UI still doesn't visually order correctly.

## Next Steps (Roadmap - Phase II Focus)

Based on the **Spyderweb MVP Roadmap — Phase II: Multi-Agent Extension**:

1.  **Immediate:**
    *   **Debug Scraper Attribution:** Prioritize fixing the `BrowserManager` logic to ensure tweets are fetched and stored for the *correct* tracked user handle.
    *   **Display Keywords UI:** Add a component to `TwitterAgentPanel` to fetch and display the trending keywords from the `/keywords` endpoint.
2.  **Short-Term (Post-Scraper Fix):**
    *   Revisit **Reddit Agent Upgrade (Roadmap #1)** or start **Memory Intelligence Agent (Roadmap #2)**.
    *   Address the Score Sorting bug if time permits.
3.  **Longer-Term:** Continue with Phase II roadmap items (Workspace Manager, Browser Automation, etc.).

---

# Memory Panel - Knowledge Graph Visualization Status

**Date:** 2025-04-15 (Approx. 07:00 UTC)

## Current Status & Goal

*   **Goal:** Implement an interactive 2D force-directed graph visualization within the "Knowledge Graph" tab of the Memory Panel (`MemoryPanel.tsx`) using `react-force-graph-2d`.
*   **Current State:** The graph visualization is currently **not rendering** in the designated area, despite backend data fetching and generation working correctly. UI responsiveness issues related to graph rendering have been addressed by removing `forceMount`, but the core visibility problem persists.

## Accomplishments

*   **Backend:**
    *   API endpoints created and confirmed functional for generating knowledge graphs from text (`/api/memory/generate-graph`) via OpenAI.
    *   API endpoints created and confirmed functional for fetching graph nodes (`/api/memory/nodes`) and edges (`/api/memory/edges`) from the database.
    *   Necessary database functions (`get_memory_nodes`, `get_memory_edges`) and API route handlers (`MemoryController`) implemented and debugged (e.g., fixed `TypeError` related to missing `self` parameter).
*   **Frontend (`MemoryPanel.tsx`):**
    *   Logic implemented to call the graph generation API (`handleCreateFromPrompt`).
    *   Logic implemented to fetch existing graph data when the "Knowledge Graph" tab is active (`fetchGraphData` triggered by `useEffect`).
    *   State management set up for graph nodes (`graphNodes`), edges (`graphEdges`), loading status (`isLoadingGraph`), and errors (`graphError`).
    *   Data mapping implemented to convert fetched nodes/edges into the format required by `react-force-graph-2d` (`graphData`).
    *   `react-force-graph-2d` library installed and TypeScript type declaration file (`react-force-graph-2d.d.ts`) created to resolve initial import errors.
    *   Debugging infrastructure added (console logs for data fetching, state checks, dimension measurements).

## Struggles & Challenges

*   **Graph Not Rendering:** The primary issue is the failure of the `<ForceGraph2D>` component to visually render within its container `div` (`ref={graphContainerRef}`).
*   **Dimension Calculation:** Debugging revealed issues with reliably obtaining the width and height of the container `div`.
    *   Initial attempts using `ResizeObserver` or `setTimeout` within `useEffect` failed as `graphContainerRef.current` was often `null` or measured `0x0` pixels, likely due to the timing of tab content mounting.
*   **Responsiveness Issue (Resolved):** Using `forceMount` on the "Knowledge Graph" `TabsContent` caused the entire UI to become unresponsive, likely due to the graph simulation running constantly in the background. Removing `forceMount` resolved this.
*   **Current Hypothesis:** Even with `forceMount` removed and dimension calculation attempted within the `useEffect` triggered by tab activation, the graph still doesn't appear. This suggests a potential issue with:
    *   The timing of the dimension calculation relative to the DOM update.
    *   The layout properties of the container `div` preventing it from having measurable dimensions.
    *   An internal issue or configuration error within the `<ForceGraph2D>` component itself.

## Next Steps (Debugging)

1.  **Verify Container Layout:** Double-check the CSS/Tailwind classes applied to the container `div` and its parent elements within the "Knowledge Graph" `TabsContent`. Ensure it's using `flex-1`, `min-h-0`, or similar properties that allow it to expand and occupy space correctly within the flexbox layout.
2.  **Simplify Rendering Condition:** Temporarily simplify the conditional rendering logic for `<ForceGraph2D>`. Instead of checking `graphDimensions.width > 0`, perhaps check only if `graphNodes.length > 0` and hardcode small dimensions (e.g., `width={300} height={200}`) just to see if the component *can* render at all, isolating the dimension calculation issue.
3.  **Test Basic Placeholder:** Replace the `<ForceGraph2D>` component entirely with a simple `<div>` that uses the `graphDimensions` state to set its style (e.g., `<div style={{ width: graphDimensions.width, height: graphDimensions.height, backgroundColor: 'red' }}>Test</div>`). This will confirm if the `graphDimensions` state is being updated and applied correctly, even if the graph component isn't rendering.
4.  **Examine `graphData`:** Add a `console.log(JSON.stringify(graphData))` right before the `<ForceGraph2D>` component is rendered to ensure the data being passed to it is valid and has the expected structure (`nodes`, `links`).
