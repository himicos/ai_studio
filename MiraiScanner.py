import re
import time
import threading
import socket
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Optional
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class NitterMonitor:
    def __init__(self, target_account="Mirai_terminal"):
        self.target_account = target_account
        # Only most reliable instances
        self.instances = [
            "https://nitter.net",
            "https://nitter.poast.org"
        ]
        self.current_instance = 0
        self.contract_regex = r"0x[a-fA-F0-9]{40}"
        self.last_tweet_id = None
        self.driver = None
        self.last_check_time = None
        self.setup_browser()

    def setup_browser(self):
        """Initialize Chrome in headless mode with specific options."""
        try:
            chrome_options = Options()
            # Headless settings
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Performance settings
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
            
            # Anti-detection settings
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Suppress logging
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Initialize the Chrome WebDriver with service
            service = Service(ChromeDriverManager().install())
            service.creation_flags = 0x08000000  # Suppress console window
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(10)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Browser initialized successfully")
        except Exception as e:
            print(f"Error setting up browser: {e}")
            if self.driver:
                self.driver.quit()
            raise

    def _rotate_instance(self):
        """Rotate to next instance."""
        self.current_instance = (self.current_instance + 1) % len(self.instances)
        print(f"Switched to instance: {self.instances[self.current_instance]}")

    def _send_contract_to_sniper(self, contract: str) -> bool:
        """Send contract address to local sniper."""
        try:
            with socket.create_connection(('127.0.0.1', 9999), timeout=5) as sock:
                sock.sendall(f"{contract}\n".encode())
                print(f"Contract {contract} sent to sniper")
                return True
        except Exception as e:
            print(f"Failed to send contract to sniper: {e}")
            return False

    def set_target_account(self, account: str):
        """Change target account."""
        self.target_account = account
        self.last_tweet_id = None  # Reset last tweet ID
        print(f"Now monitoring: {account}")

    def check_new_tweets(self) -> bool:
        """Check for new tweets from target account using Selenium."""
        instance = self.instances[self.current_instance]
        url = f"{instance}/{self.target_account}"
        
        try:
            self.last_check_time = datetime.now()
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for tweets to load
            wait = WebDriverWait(self.driver, 10)
            tweets = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "timeline-item")))
            
            if not tweets:
                print("No tweets found")
                return False

            # Get first non-pinned tweet
            tweet = None
            for t in tweets:
                try:
                    # Check if tweet is pinned
                    pinned = t.find_elements(By.CLASS_NAME, "pinned")
                    if not pinned:
                        tweet = t
                        break
                except:
                    continue

            if not tweet:
                return False

            # Get tweet ID from permalink
            try:
                permalink = tweet.find_element(By.CLASS_NAME, "tweet-link")
                tweet_id = permalink.get_attribute("href").split("/")[-1]
                
                if tweet_id == self.last_tweet_id:
                    return False
            except:
                return False

            # Get tweet content
            try:
                content = tweet.find_element(By.CLASS_NAME, "tweet-content")
                tweet_text = content.text
                
                # Store this for status updates
                self.last_tweet_text = tweet_text[:50] + "..." if len(tweet_text) > 50 else tweet_text
            except:
                return False

            # Look for contract address
            contract_match = re.search(self.contract_regex, tweet_text)
            if contract_match:
                contract = contract_match.group(0)
                print(f"\nFound contract in new tweet: {contract}")
                if self._send_contract_to_sniper(contract):
                    self.last_tweet_id = tweet_id
                    return True

            self.last_tweet_id = tweet_id
            return False

        except TimeoutException:
            print(f"Timeout accessing {url}")
            self._rotate_instance()
            return False
        except WebDriverException as e:
            print(f"Browser error: {e}")
            # Try to recover the browser session
            try:
                self.driver.quit()
            except:
                pass
            self.setup_browser()
            self._rotate_instance()
            return False
        except Exception as e:
            print(f"Error checking tweets: {e}")
            self._rotate_instance()
            return False

    def get_status(self) -> dict:
        """Get current monitoring status."""
        return {
            'account': self.target_account,
            'instance': self.instances[self.current_instance],
            'last_check': self.last_check_time.strftime('%H:%M:%S') if self.last_check_time else 'Never',
            'last_tweet': self.last_tweet_text if hasattr(self, 'last_tweet_text') else 'No tweets found'
        }

    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

class NitterMonitorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nitter Monitor")
        self.geometry("800x600")
        self.monitor = NitterMonitor()
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        self.status_update = threading.Event()
        self.create_widgets()
        
        # Ensure cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Settings frame
        settings_frame = ttk.Frame(self)
        settings_frame.pack(padx=10, pady=10, fill='x')
        
        # Account input
        ttk.Label(settings_frame, text="Account to monitor:").grid(row=0, column=0, sticky="w")
        self.account_entry = ttk.Entry(settings_frame, width=30)
        self.account_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.account_entry.insert(0, "Mirai_terminal")
        
        # Check interval
        ttk.Label(settings_frame, text="Check interval (seconds):").grid(row=1, column=0, sticky="w")
        self.interval_entry = ttk.Entry(settings_frame, width=10)
        self.interval_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.interval_entry.insert(0, "5")
        
        # Status frame
        status_frame = ttk.LabelFrame(self, text="Monitor Status")
        status_frame.pack(padx=10, pady=5, fill='x')
        
        self.status_labels = {}
        for idx, label in enumerate(['Current Account', 'Current Instance', 'Last Check', 'Latest Tweet']):
            ttk.Label(status_frame, text=f"{label}:").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
            self.status_labels[label] = ttk.Label(status_frame, text="Not started")
            self.status_labels[label].grid(row=idx, column=1, sticky="w", padx=5, pady=2)
        
        # Buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(padx=10, pady=5, fill='x')
        self.start_button = ttk.Button(buttons_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(buttons_frame, text="Stop Monitoring", command=self.stop_monitoring_func, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Output area
        self.output_text = ScrolledText(self, height=20)
        self.output_text.pack(padx=10, pady=10, fill='both', expand=True)

    def update_status(self):
        """Update status labels with current monitoring info."""
        if hasattr(self.monitor, 'get_status'):
            status = self.monitor.get_status()
            self.status_labels['Current Account'].config(text=status['account'])
            self.status_labels['Current Instance'].config(text=status['instance'])
            self.status_labels['Last Check'].config(text=status['last_check'])
            self.status_labels['Latest Tweet'].config(text=status['last_tweet'])
        self.after(1000, self.update_status)  # Update every second

    def start_monitoring(self):
        """Start monitoring thread."""
        try:
            self.check_interval = int(self.interval_entry.get().strip())
            if self.check_interval < 1:
                raise ValueError("Interval must be at least 1 second")
        except ValueError as e:
            self.log(f"Invalid interval: {e}")
            return

        # Update monitor with current account
        account = self.account_entry.get().strip()
        if not account:
            self.log("Please enter an account to monitor")
            return
            
        self.monitor.set_target_account(account)
        self.stop_monitoring.clear()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.update_status()  # Start status updates
        self.log(f"Started monitoring {account}")

    def stop_monitoring_func(self):
        """Stop monitoring."""
        self.stop_monitoring.set()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log("Stopped monitoring")

    def monitor_loop(self):
        """Main monitoring loop."""
        while not self.stop_monitoring.is_set():
            if self.monitor.check_new_tweets():
                self.log("New contract found and sent to sniper!")
            time.sleep(self.check_interval)

    def log(self, message: str):
        """Log message to GUI."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        print(formatted.strip())
        self.output_text.insert(tk.END, formatted)
        self.output_text.see(tk.END)

    def on_closing(self):
        """Handle window closing."""
        self.stop_monitoring.set()
        if self.monitor:
            self.monitor.cleanup()
        self.destroy()

if __name__ == "__main__":
    app = NitterMonitorGUI()
    app.mainloop()
