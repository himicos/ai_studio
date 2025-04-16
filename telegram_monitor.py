"""
Monitor Telegram chats with AI analysis
"""
import os
import asyncio
from dotenv import load_dotenv
from tools.telegram_handler import TelegramHandler

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize handler
    handler = TelegramHandler(
        api_id=os.getenv("TELEGRAM_API_ID"),
        api_hash=os.getenv("TELEGRAM_API_HASH"),
        sample_rate=0.1  # Analyze 10% of messages
    )
    
    try:
        # Start monitoring
        await handler.start()
        
        # Keep running
        print("Monitoring Telegram messages... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping Telegram monitor...")
        await handler.stop()
        
if __name__ == "__main__":
    asyncio.run(main())
