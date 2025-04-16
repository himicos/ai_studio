import asyncio
import logging
from dotenv import load_dotenv

# Configure logging to see output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

async def run_test():
    log.info("--- Starting Direct RedditTracker Test ---")
    
    # Load environment variables from .env file
    log.info("Loading .env variables...")
    load_dotenv()
    log.info(".env variables loaded.")

    # Import the tracker *after* loading env vars
    try:
        from data.reddit_tracker import RedditTracker
        log.info("RedditTracker imported successfully.")
    except ImportError as e:
        log.error(f"Failed to import RedditTracker: {e}")
        return
    except Exception as e:
         log.error(f"An unexpected error occurred during import: {e}", exc_info=True)
         return

    # Initialize the tracker
    log.info("Initializing RedditTracker...")
    try:
        tracker = RedditTracker()
        if not tracker.reddit:
             log.error("Tracker initialized, but PRAW client failed. Check credentials in .env and Reddit app setup.")
             return
        log.info("RedditTracker initialized successfully.")
    except Exception as e:
        log.error(f"Failed to initialize RedditTracker: {e}", exc_info=True)
        return

    # Test adding a subreddit
    subreddit_to_add = 'python'
    log.info(f"Attempting to add subreddit: r/{subreddit_to_add}")
    try:
        add_success = await tracker.add_subreddit(subreddit_to_add)
        log.info(f"add_subreddit('{subreddit_to_add}') returned: {add_success}")
    except Exception as e:
        log.error(f"Error calling add_subreddit: {e}", exc_info=True)

    # Test listing tracked subreddits
    log.info("Attempting to get tracked subreddits...")
    try:
        tracked_list = await tracker.get_tracked_subreddits()
        log.info(f"get_tracked_subreddits() returned: {tracked_list}")
    except Exception as e:
        log.error(f"Error calling get_tracked_subreddits: {e}", exc_info=True)
        
    # Test adding a non-existent subreddit
    non_existent_sub = 'thissubredditdefinitelydoesntexist123'
    log.info(f"Attempting to add non-existent subreddit: r/{non_existent_sub}")
    try:
        add_fail_success = await tracker.add_subreddit(non_existent_sub)
        log.info(f"add_subreddit('{non_existent_sub}') returned: {add_fail_success}")
        if add_fail_success:
             log.warning("Adding a non-existent subreddit unexpectedly returned True!")
    except Exception as e:
        log.error(f"Error calling add_subreddit for non-existent sub: {e}", exc_info=True)

    # Optional: Test scanning (might take time)
    # log.info("Attempting to scan...")
    # try:
    #     await tracker.scan()
    #     log.info("Scan completed.")
    # except Exception as e:
    #     log.error(f"Error during scan: {e}", exc_info=True)

    log.info("--- Direct RedditTracker Test Finished ---")

if __name__ == "__main__":
    asyncio.run(run_test())