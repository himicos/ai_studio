# Twitter Agent Debugging Summary - 2025-04-14

## Overview

This session focused on resolving critical issues preventing the Twitter Agent panel from correctly displaying and managing tracked users. The primary problems involved database interactions (corruption, locking, incorrect queries) and frontend state synchronization (failure to update UI automatically).

## Progress & Fixes Implemented:

1.  **Database Integrity Restored:**
    *   **Problem:** Backend failed to start due to `sqlite3.DatabaseError: file is not a database`.
    *   **Cause:** The main database file (`memory/memory.sqlite`) was corrupted (only 25 bytes) and residual WAL files (`-wal`, `-shm`) were present.
    *   **Fix:** Manually deleted `memory.sqlite`, `memory.sqlite-wal`, and `memory.sqlite-shm`. Restarting the backend allowed `init_db()` in `db_enhanced.py` to create a fresh, valid database file.

2.  **User Addition Logic Corrected (`/add_user`):**
    *   **Problem:** Users added via the API did not appear in the database or UI, despite the endpoint returning a 200 OK status. Attempts also triggered `database is locked` errors.
    *   **Cause 1 (Locking):** Concurrent access between the API request and background tracker, exacerbated by external tools (DB Browser) holding locks.
    *   **Fix 1:** Instructed user to close DB Browser. Modified `get_db_connection` in `db_enhanced.py` to increase the `timeout` parameter to 10 seconds and enable `PRAGMA journal_mode=WAL` for potentially better concurrency.
    *   **Cause 2 (Incorrect Insert):** The `INSERT` statement in `twitter_agent.py`'s `add_user` function was omitting the `id` column. Since `id` is a `TEXT PRIMARY KEY` in the `tracked_users` table, it must be explicitly provided during insertion.
    *   **Fix 2:** Modified the `INSERT` statement to include `id` and use the unique `handle` value for it: `INSERT INTO tracked_users (id, handle, tags, added_on) VALUES (?, ?, ?, ?)`. 

3.  **User Retrieval Logic Corrected (`/get_tracked_users`):**
    *   **Problem:** API endpoint was returning `500 Internal Server Error` or empty lists `[]` even when users were expected.
    *   **Cause:** Original code attempted to select a non-existent `date_added` column. Later versions correctly filtered `WHERE id IS NOT NULL`, but this returned empty lists because the `add_user` fix (inserting the ID) hadn't been applied yet.
    *   **Fix:** Corrected the `SELECT` statement in `twitter_agent.py`'s `get_tracked_users` function to use the correct column name `added_on` (`SELECT id, handle, tags, added_on ...`). The `WHERE id IS NOT NULL` clause remains correct.

4.  **Core Functionality Verified (with Workaround):**
    *   Successfully demonstrated that:
        *   Users can be added via the UI -> API -> Database.
        *   The tracked users list loads correctly in the UI *after a manual page refresh (F5)*.
        *   Users can be deleted via the UI -> API -> Database.
        *   The UI list reflects the deletion *after a manual page refresh (F5)*.

## Current Known Issues & State:

1.  **Frontend: No Automatic UI Update on Add (`onUserAdded` error):**
    *   **Symptom:** The error `UserSearch.tsx:42 onUserAdded prop is not a function! Received: undefined` consistently appears in the browser console upon clicking the "Add User" button. Consequently, the "Tracked Users" list does not refresh automatically to show the newly added user.
    *   **Workaround:** User must **manually refresh the page (F5)** to see the updated list after adding a user.
    *   **Diagnosis:** This indicates a failure in passing the `fetchTrackedUsers` function (or a correctly bound version of it) as the `onUserAdded` prop from the parent `TwitterAgentPanel.tsx` to the child `UserAddDirect.tsx` component. Despite attempts (renaming components, clearing Vite cache (`rm -rf node_modules/.vite`)), the issue persists, suggesting a stubborn build system artifact or a subtle error in the React component hierarchy/state flow.

2.  **Frontend: Potential Double Delete API Call:**
    *   **Symptom:** When deleting a user, backend logs show two consecutive `DELETE /api/twitter-agent/remove_user/{id}` requests for the same user ID. The first succeeds (200 OK), the second fails (404/500 Not Found, as the user is already gone).
    *   **Cause:** This strongly suggests an issue within the `onClick` handler attached to the delete button in `TwitterAgentPanel.tsx`. The handler function (`deleteTrackedUser`) appears to be invoked twice per single button click.

## Next Steps / Recommendations:

1.  **Address Double Delete:**
    *   **Priority:** Investigate this next as it indicates a clear frontend bug.
    *   **Action:** Examine the `onClick` handler for the delete button in `spyderweb/spyderweb/src/components/panels/agents/TwitterAgentPanel.tsx`.
    *   **Debugging:** Add `console.log('Delete button clicked for user:', user.id)` *inside* the `onClick` function (or the function it calls, like `handleDelete`) *before* the `api.deleteTrackedUser(userId)` call. Observe the browser console when clicking delete to see if the log appears once or twice. Check for potential causes like nested clickable elements, event bubbling issues (`e.stopPropagation()` might be needed), or effects/state updates unintentionally triggering the delete logic multiple times.

2.  **Handle `onUserAdded` Issue:**
    *   **Recommendation:** Temporarily accept the manual refresh (F5) workaround. The core functionality works, and debugging this frontend build/state issue could be time-consuming.
    *   **Future Investigation (If needed):**
        *   Deep dive into Vite's HMR (Hot Module Replacement) and caching behavior.
        *   Systematically review the state management and prop flow within `TwitterAgentPanel.tsx`, potentially using React DevTools to trace prop values.
        *   Consider a global state management solution (like Zustand or Redux Toolkit) if prop drilling becomes too complex, although this adds overhead.

3.  **Further Testing:**
    *   Test the "Start Tracking" / "Stop Tracking" functionality again now that the user list is stable. Observe backend logs during these actions.
    *   Monitor the background scan process (`run_twitter_scan_loop`) for any errors, especially related to database access or tweet processing, now that user IDs are correctly populated.