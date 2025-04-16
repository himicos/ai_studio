from .browser_manager import BrowserManager
import logging
import asyncio
from typing import List, Dict, Optional
import json
from datetime import datetime, timezone
from transformers import pipeline

# Import the database function
from ai_studio_package.infra.db_enhanced import create_memory_from_post, get_db_connection, get_memory_node

logger = logging.getLogger(__name__)

class TwitterTracker:
    def __init__(self, browser_manager: BrowserManager):
        # Store the passed BrowserManager instance
        self.browser_manager = browser_manager 
        self.tracked_users: List[str] = [] 
        self.is_running = False
        self.scan_task: Optional[asyncio.Task] = None
        self._scan_lock = asyncio.Lock()
        
        # <<< LOAD SENTIMENT PIPELINE >>>
        try:
            logger.info("Loading sentiment analysis pipeline (cardiffnlp/twitter-roberta-base-sentiment-latest)...")
            # First try with GPU (device=0)
            try:
                import torch
                cuda_available = torch.cuda.is_available()
                logger.info(f"CUDA available: {cuda_available}, device count: {torch.cuda.device_count() if cuda_available else 0}")
                self.sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=0)
                logger.info("✅ Sentiment analysis pipeline loaded successfully on GPU.")
            except Exception as gpu_err:
                logger.warning(f"GPU acceleration failed for sentiment analysis: {gpu_err}")
                # Fallback to CPU
                self.sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=-1)
                logger.info("⚠️ Sentiment analysis pipeline loaded on CPU (GPU failed).")
        except Exception as e:
            logger.error(f"Failed to load sentiment analysis pipeline: {e}", exc_info=True)
            self.sentiment_pipeline = None # Set to None if loading fails
        # ---------------------------------
        
        # <<< LOAD NER PIPELINE >>>
        try:
            logger.info("Loading NER pipeline (dslim/bert-base-NER)...")
            # Attempt GPU first, fallback to CPU
            try:
                import torch
                cuda_available = torch.cuda.is_available()
                device_info = f"CUDA available: {cuda_available}, device count: {torch.cuda.device_count() if cuda_available else 0}"
                logger.info(device_info)
                self.ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True, device=0)
                logger.info("✅ NER pipeline loaded successfully on GPU.")
            except Exception as gpu_ner_err:
                logger.warning(f"GPU acceleration failed for NER pipeline: {gpu_ner_err}")
                # Fallback to CPU with a clear message
                self.ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True, device=-1)
                logger.info("⚠️ NER pipeline loaded on CPU (GPU failed).")
        except Exception as e:
            logger.error(f"Failed to load NER pipeline completely: {e}", exc_info=True)
            self.ner_pipeline = None
        # ---------------------------------
        
        # Initial load on creation might be useful too - can be uncommented if needed
        # asyncio.create_task(self.load_users_from_db())
        
    async def add_user(self, username: str):
        """Add a user to track."""
        if username not in self.tracked_users:
            self.tracked_users.append(username)
            logger.info(f"Added user {username} to tracking list")
            
    async def remove_user(self, username: str):
        """Remove a user from tracking."""
        if username in self.tracked_users:
            self.tracked_users.remove(username)
            logger.info(f"Removed user {username} from tracking list")
            
    async def scan(self):
        """Scan for new tweets from tracked users. Ensures only one scan runs at a time."""
        if self._scan_lock.locked():
            logger.info("Scan lock is already held. Skipping concurrent scan request.")
            return # Prevent concurrent execution
            
        async with self._scan_lock:
            logger.info("Starting Twitter scan cycle...")
            if not self.tracked_users:
                logger.info("No users to track in the current tracker instance.")
                return
                
            conn = None # Move DB connection setup inside lock if needed by map?
            user_id_map = {}
            try:
                # Get user IDs mapped to handles for creating memory nodes
                conn = get_db_connection() # Get connection inside lock
                cursor = conn.cursor()
                # Normalize handles from DB for the map keys AND use lowercase
                cursor.execute("SELECT handle, id FROM tracked_users")
                for row in cursor.fetchall():
                    handle = row[0]
                    user_db_id = row[1]
                    if handle:
                        normalized_handle = handle.lstrip('@').strip()
                        if normalized_handle:
                            user_id_map[normalized_handle.lower()] = user_db_id
                        else:
                            logger.warning(f"Skipping row with invalid handle from DB for user_id_map: '{handle}'")
                    else:
                         logger.warning(f"Skipping row with NULL handle from DB for user_id_map (ID: {user_db_id})")
            except Exception as map_err:
                 logger.error(f"Error building user_id_map: {map_err}", exc_info=True)
                 # If map fails, we probably can't process tweets correctly
                 return # Exit scan if we can't map users
            finally:
                if conn: conn.close() # Close connection
            
            logger.info(f"Scanning {len(self.tracked_users)} users: {self.tracked_users}")
            
            # Use asyncio.gather to run user scans concurrently (optional improvement)
            scan_tasks = []
            for username in self.tracked_users:
                scan_tasks.append(self._scan_single_user(username, user_id_map))
            
            if scan_tasks:
                await asyncio.gather(*scan_tasks)
                    
            logger.info("Finished Twitter scan cycle.")
            
    async def _scan_single_user(self, username: str, user_id_map: Dict[str, str]):
        """Scans and processes tweets for a single user."""
        # Ensure the username from the tracker list is also normalized AND lowercased for lookup
        normalized_username = username.lstrip('@').strip().lower()
        logger.info(f"Checking account (normalized/lowercase): {normalized_username}")
        user_db_id = user_id_map.get(normalized_username) # Use normalized lowercase key
        if not user_db_id:
            logger.warning(f"User handle '{normalized_username}' (normalized from '{username}') not found in user_id_map keys: {list(user_id_map.keys())}. Skipping.")
            return
            
        try:
            # Pass the original username format expected by the scraping method
            tweets = await self.browser_manager.get_user_tweets(username) 
            
            if tweets:
                logger.info(f"Found {len(tweets)} tweets for {username}. Processing...")
                # Process and store tweets - pass normalized lowercase handle
                await self.process_tweets(user_db_id, tweets, normalized_username) 
            else:
                logger.info(f"No new tweets found for {username}.")
                
        except Exception as e:
            logger.error(f"Error scanning account {username}: {e}", exc_info=True)

    async def process_tweets(self, user_db_id: str, tweets: List[dict], username_handle: str):
        """Process tweets: create memory nodes, analyze sentiment, and insert into tables."""
        processed_count = 0
        skipped_existing_count = 0 # Count tweets already in tracked_tweets
        error_count = 0
        
        # Data collection lists
        memory_nodes_to_insert = []
        tracked_tweets_to_insert = []
        tweet_ids_processed_in_batch = set() # Track IDs added in this batch

        # --- Pre-fetch existing tweet IDs for this user to avoid checks inside loop --- 
        existing_tweet_ids = set()
        conn_check = None
        try:
            conn_check = get_db_connection()
            cursor_check = conn_check.cursor()
            # Fetch IDs for the current user being processed
            cursor_check.execute("SELECT tweet_id FROM tracked_tweets WHERE user_id = ?", (user_db_id,))
            existing_tweet_ids = {row[0] for row in cursor_check.fetchall()}
            logger.debug(f"Found {len(existing_tweet_ids)} existing tweet IDs for user {user_db_id} in tracked_tweets.")
        except Exception as check_err:
            logger.error(f"Error pre-fetching existing tweets for {user_db_id}: {check_err}")
            # If check fails, we proceed but might insert duplicates if they exist 
            # (INSERT OR IGNORE will handle it, but it's less efficient)
        finally:
            if conn_check: conn_check.close()
        # --------------------------------------------------------------------------

        for tweet in tweets:
            try:
                tweet_id_str = str(tweet['id'])
                
                # Skip if already exists in DB or was just processed
                if tweet_id_str in existing_tweet_ids or tweet_id_str in tweet_ids_processed_in_batch:
                    skipped_existing_count += 1
                    continue 

                # --- Prepare data for memory_nodes --- 
                node_id = f"tweet_{tweet_id_str}"
                content_mem = tweet.get('content', '')
                created_utc_mem = int(tweet['timestamp']) if tweet.get('timestamp') else int(datetime.now(timezone.utc).timestamp())
                tags_mem = json.dumps(['tweet', 'twitter', username_handle]) # Simple tags for now
                metadata_mem = json.dumps({ 
                     'user_id': user_db_id,
                     'user_handle': username_handle,
                     'likes': tweet.get('stats', {}).get('likes', 0),
                     'retweets': tweet.get('stats', {}).get('retweets', 0),
                     'replies': tweet.get('stats', {}).get('replies', 0),
                     'timestamp_ms': tweet.get('timestamp_ms'),
                     'url': tweet.get('url')
                 })
                source_id_mem = tweet_id_str
                source_type_mem = 'twitter'
                updated_at_mem = int(datetime.now().timestamp())

                memory_nodes_to_insert.append((
                    node_id, source_type_mem, content_mem, tags_mem, created_utc_mem, 
                    source_id_mem, source_type_mem, metadata_mem, 0, updated_at_mem
                ))
                # ------------------------------------

                # --- Prepare data for tracked_tweets --- 
                content_trk = tweet.get('content', '')
                date_posted_iso = tweet.get('timestamp_iso')
                likes_trk = tweet.get('stats', {}).get('likes', 0)
                retweets_trk = tweet.get('stats', {}).get('retweets', 0)
                replies_trk = tweet.get('stats', {}).get('replies', 0)
                url_trk = tweet.get('url')
                keywords_json_trk = json.dumps([]) 
                sentiment_trk = None # Default to None
                # <<< ANALYZE SENTIMENT >>>
                if self.sentiment_pipeline and content_trk:
                    try:
                        # Pipelines often expect lists, even for single items
                        # Truncate long tweets to avoid model errors (models have input limits)
                        max_length = 512 # Common limit, adjust if needed
                        truncated_content = content_trk[:max_length]
                        results = self.sentiment_pipeline(truncated_content) 
                        # Result format is often [{'label': 'positive', 'score': 0.9...}]
                        if results and isinstance(results, list):
                           # Map model labels (e.g., LABEL_0, LABEL_1, LABEL_2) to readable names
                           # This mapping depends *highly* on the specific model!
                           # For cardiffnlp/twitter-roberta-base-sentiment-latest:
                           # label 0 -> negative
                           # label 1 -> neutral
                           # label 2 -> positive
                           raw_label = results[0]['label'].lower() 
                           if raw_label == 'label_2' or raw_label == 'positive': # Check both just in case
                               sentiment_trk = 'positive'
                           elif raw_label == 'label_1' or raw_label == 'neutral':
                               sentiment_trk = 'neutral'
                           elif raw_label == 'label_0' or raw_label == 'negative':
                               sentiment_trk = 'negative'
                           else:
                               logger.warning(f"Unknown sentiment label from pipeline: {results[0]['label']}")
                               sentiment_trk = results[0]['label'] # Store raw label if unknown
                               
                    except Exception as sentiment_err:
                        logger.error(f"Error analyzing sentiment for tweet {tweet.get('id', 'N/A')}: {sentiment_err}", exc_info=False) # Avoid overly verbose logs
                # <<< ADD Score Mapping >>>
                score_trk = None # Default to None
                if sentiment_trk == 'positive':
                    score_trk = 1.0
                elif sentiment_trk == 'negative':
                    score_trk = -1.0
                elif sentiment_trk == 'neutral':
                    score_trk = 0.0
                # --------------------------

                # <<< EXTRACT KEYWORDS/ENTITIES >>>
                keywords_list = []
                if self.ner_pipeline and content_trk:
                    try:
                        # Truncate long tweets for NER model as well
                        max_length_ner = 512 # Adjust if needed
                        truncated_content_ner = content_trk[:max_length_ner]
                        entities = self.ner_pipeline(truncated_content_ner)
                        
                        keywords_list = [] # Initialize keywords_list here
                        if entities and isinstance(entities, list):
                           # Extract and filter the entity words 
                           raw_keywords = [entity['word'] for entity in entities 
                                           if entity.get('entity_group') in ['ORG', 'PER', 'LOC', 'MISC']]
                           
                           # Filter keywords
                           filtered_keywords = []
                           for kw in raw_keywords:
                               # Corrected stripping logic
                               cleaned_kw = kw.strip("'., ") # Strip common surrounding chars
                               # <<< Refined Filter criteria >>>
                               if (
                                   len(cleaned_kw) >= 3 and
                                   not cleaned_kw.startswith('#') and 
                                   not cleaned_kw.startswith('@') and
                                   any(c.isalpha() for c in cleaned_kw) # Ensure at least one letter
                                  ): 
                                    filtered_keywords.append(cleaned_kw) 
                                    
                           # Remove duplicates (case-insensitive for this example, adjust if needed)
                           seen = set()
                           unique_keywords = []
                           for kw_final in filtered_keywords:
                               if kw_final.lower() not in seen:
                                   seen.add(kw_final.lower())
                                   unique_keywords.append(kw_final)
                           keywords_list = unique_keywords # Assign the final list
                                           
                    except Exception as ner_err:
                        logger.error(f"Error extracting entities for tweet {tweet.get('id', 'N/A')}: {ner_err}", exc_info=False)
                        # Ensure keywords_list is empty on error
                        keywords_list = []
                        
                else: # Handle case where pipeline didn't load or no content
                    keywords_list = []
                    
                keywords_json_trk = json.dumps(keywords_list) # Convert list to JSON string
                # --------------------------------
                
                tracked_tweets_to_insert.append((
                    tweet_id_str, user_db_id, content_trk, date_posted_iso,
                    likes_trk, retweets_trk, replies_trk, url_trk,
                    score_trk, sentiment_trk, keywords_json_trk # Ensure keywords_json_trk is included
                ))
                # ---------------------------------------

                tweet_ids_processed_in_batch.add(tweet_id_str) # Mark as processed for this batch

            except KeyError as ke:
                 logger.error(f"Missing expected key in tweet data for user {username_handle}: {ke}. Tweet data: {tweet}", exc_info=True)
                 error_count += 1
            except Exception as e:
                logger.error(f"Error preparing tweet data {tweet.get('id', 'N/A')} for batch insert: {e}", exc_info=True)
                error_count += 1

        # --- Perform Batch Inserts After Loop --- 
        conn = None
        inserted_memory_nodes = 0
        inserted_tracked_tweets = 0
        if memory_nodes_to_insert or tracked_tweets_to_insert:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                conn.execute("BEGIN") # Start transaction

                # Batch insert memory nodes
                if memory_nodes_to_insert:
                    logger.debug(f"Batch inserting {len(memory_nodes_to_insert)} memory nodes...")
                    cursor.executemany("""
                        INSERT OR IGNORE INTO memory_nodes 
                        (id, type, content, tags, created_at, source_id, source_type, metadata, has_embedding, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, memory_nodes_to_insert)
                    inserted_memory_nodes = cursor.rowcount
                    logger.debug(f"Batch insert memory nodes complete. Rows affected: {inserted_memory_nodes}")

                # Batch insert tracked tweets
                if tracked_tweets_to_insert:
                    logger.debug(f"Preparing to batch insert {len(tracked_tweets_to_insert)} tracked tweets. First few:")
                    for i, data_tuple in enumerate(tracked_tweets_to_insert[:3]): # Log first 3
                        logger.debug(f"  Tuple {i}: ID={data_tuple[0]}, Content='{str(data_tuple[2])[:50]}...'")
                    logger.debug(f"Batch inserting {len(tracked_tweets_to_insert)} tracked tweets...")
                    cursor.executemany("""
                        INSERT OR IGNORE INTO tracked_tweets 
                        (tweet_id, user_id, content, date_posted, engagement_likes, engagement_retweets, engagement_replies, url, score, sentiment, keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tracked_tweets_to_insert)
                    inserted_tracked_tweets = cursor.rowcount
                    logger.debug(f"Batch insert tracked tweets complete. Rows affected: {inserted_tracked_tweets}")

                # --- Log before/after commit --- 
                logger.info("Attempting to commit transaction...")
                conn.commit() # Commit transaction
                logger.info("Transaction committed successfully.")
                # --- End log --- 
                
                processed_count = inserted_tracked_tweets # Count successful tracked_tweet inserts as processed
                logger.info(f"Batch inserts completed successfully.") # Keep this for overall confirmation

            except Exception as batch_err:
                logger.error(f"Error during batch database inserts: {batch_err}", exc_info=True)
                if conn: 
                    logger.info("Rolling back transaction due to error...") # Log rollback
                    conn.rollback() # Rollback transaction on error
                error_count += len(memory_nodes_to_insert) + len(tracked_tweets_to_insert) # Count all potential inserts as errors
            finally:
                if conn:
                    conn.close()
        else:
            logger.info("No new tweets found to insert in this batch.")
        # ----------------------------------------

        # Optional: Trigger embedding generation for newly inserted memory nodes
        # This might still cause issues if generate_embedding_for_node is blocking or inefficient.
        # Consider making embedding generation a separate background task queue.
        # if inserted_memory_nodes > 0:
        #     try:
        #         new_node_ids = [node_data[0] for node_data in memory_nodes_to_insert]
        #         logger.info(f"Triggering embedding generation for {inserted_memory_nodes} new nodes...")
        #         # This needs refinement - how to efficiently generate for many?
        #         # for node_id in new_node_ids:
        #         #     asyncio.create_task(generate_embedding_for_node_async(node_id)) # If an async version exists
        #     except Exception as embed_err:
        #         logger.error(f"Error triggering embedding generation: {embed_err}")
        
        logger.info(f"Finished processing for {username_handle}. Inserted: {processed_count}, Skipped (Already Existed): {skipped_existing_count}, Errors: {error_count}")
        
    async def start(self, scan_interval: int = 600):
        """Start the tracking process."""
        if self.is_running:
            logger.warning("Tracker is already running")
            return
            
        self.is_running = True
        self.scan_task = asyncio.create_task(self._scan_loop(scan_interval))
        logger.info("Twitter tracker started")
        
    async def stop(self):
        """Stop the tracking process."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.scan_task:
            self.scan_task.cancel()
            try:
                await self.scan_task
            except asyncio.CancelledError:
                pass
                
        self.browser_manager.cleanup()
        logger.info("Twitter tracker stopped")
        
    async def _scan_loop(self, scan_interval: int):
        """Main scanning loop."""
        while self.is_running:
            try:
                await self.scan()
                await asyncio.sleep(scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying 

    async def load_users_from_db(self):
        """Loads/reloads the list of tracked user handles from the database."""
        logger.info("Loading tracked users from database into tracker instance...")
        conn = None
        new_user_list = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT handle FROM tracked_users WHERE id IS NOT NULL") # Fetch handles
            rows = cursor.fetchall()
            for row in rows:
                handle = row[0]
                if handle:
                    normalized_handle = handle.lstrip('@').strip()
                    if normalized_handle:
                        new_user_list.append(normalized_handle)
                    else:
                        logger.warning(f"Skipping row with invalid handle from DB during load: '{handle}'")
                else:
                    logger.warning("Skipping row with NULL handle from DB during load.")
            
            # Atomically update the list
            self.tracked_users = new_user_list
            logger.info(f"Successfully loaded {len(self.tracked_users)} users into tracker instance: {self.tracked_users}")

        except Exception as e:
            logger.error(f"Failed to load users from database into tracker: {e}", exc_info=True)
            # Decide: should we clear the list or keep the old one on error?
            # Keeping the old list might be safer to avoid stopping tracking unexpectedly.
            # self.tracked_users = [] # Optionally clear list on error
        finally:
            if conn:
                conn.close() 