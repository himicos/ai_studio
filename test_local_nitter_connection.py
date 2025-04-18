import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Nitter instance URL (adjust if your docker-compose uses a different port)
NITTER_URL = "http://localhost:8080"

def test_nitter_connection():
    """Tests the connection to the local Nitter instance."""
    logging.info(f"Attempting to connect to Nitter at: {NITTER_URL}")
    try:
        # Try fetching the main page
        response = requests.get(NITTER_URL, timeout=10)
        logging.info(f"Received status code: {response.status_code}")

        # Check for successful status codes (2xx) or common 'not found' (404)
        if 200 <= response.status_code < 300:
            logging.info("Nitter connection successful (Status code 2xx).")
            print("Nitter connection test: PASSED (Status code 2xx)")
            return True
        elif response.status_code == 404:
             logging.warning("Nitter connection returned 404 Not Found. This might be okay if the base path doesn't render anything, but specific user/tweet paths should work.")
             print("Nitter connection test: PASSED (Status code 404 - Check specific paths if needed)")
             return True
        else:
            logging.error(f"Nitter connection failed. Status code: {response.status_code}")
            logging.error(f"Response content sample: {response.text[:200]}") # Log first 200 chars
            print(f"Nitter connection test: FAILED (Status code {response.status_code})")
            return False

    except requests.exceptions.ConnectionError as e:
        logging.error(f"Nitter connection failed: Could not connect to {NITTER_URL}. Is the service running?")
        logging.error(f"Error details: {e}")
        print("Nitter connection test: FAILED (ConnectionError)")
        return False
    except requests.exceptions.Timeout:
        logging.error(f"Nitter connection timed out after 10 seconds.")
        print("Nitter connection test: FAILED (Timeout)")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"Nitter connection test: FAILED (Unexpected Error: {e})")
        return False

if __name__ == "__main__":
    test_nitter_connection() 