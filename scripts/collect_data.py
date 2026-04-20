"""One-shot data collection script.

Run daily via cron or GitHub Actions:
    python scripts/collect_data.py

Or on first setup:
    python scripts/collect_data.py --start 2010-01-01
"""

import argparse
import logging
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logging
from src.collectors.fred import collect as collect_fred
from src.collectors.market import collect as collect_market

setup_logging()
logger = logging.getLogger(__name__)


def main(start: str = "2010-01-01") -> None:
    logger.info("=== Data collection started ===")

    logger.info("--- FRED macro data ---")
    try:
        df = collect_fred(start=start)
        logger.info("FRED: %d rows, %d series", *df.shape)
    except Exception as e:
        logger.error("FRED collection failed: %s", e)

    logger.info("--- Market / price data ---")
    try:
        data = collect_market()
        logger.info("Market: %d tickers collected", len(data))
    except Exception as e:
        logger.error("Market collection failed: %s", e)

    logger.info("=== Data collection complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect market and macro data")
    parser.add_argument("--start", default="2010-01-01", help="Start date (YYYY-MM-DD)")
    args = parser.parse_args()
    main(start=args.start)
