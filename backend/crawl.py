import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from logger import setup_logging
setup_logging(latest_only=True)

from crawler.crawler import run_full_crawl

if __name__ == "__main__":
    history_days = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    asyncio.run(run_full_crawl(history_days=history_days))
