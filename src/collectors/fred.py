"""FRED API data collector.

Fetches US macroeconomic time series (CPI, PPI, Fed funds rate, etc.)
and saves them as Parquet files in data/raw/.
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from fredapi import Fred

from configs.settings import settings

logger = logging.getLogger(__name__)

RAW_DIR = settings.data_dir / "raw" / "fred"
RAW_DIR.mkdir(parents=True, exist_ok=True)


class FredCollector:
    """Thin wrapper around fredapi.Fred with caching and logging."""

    def __init__(self):
        self.client = Fred(api_key=settings.fred_api_key)

    def fetch(
        self,
        series_id: str,
        start: str = "2000-01-01",
        end: str | None = None,
    ) -> pd.Series:
        end = end or datetime.today().strftime("%Y-%m-%d")
        logger.info("Fetching FRED series %s (%s → %s)", series_id, start, end)
        data = self.client.get_series(series_id, observation_start=start, observation_end=end)
        data.name = series_id
        return data

    def fetch_all(self, start: str = "2000-01-01") -> pd.DataFrame:
        """Fetch every series in settings.fred_series and return as a DataFrame."""
        frames = {}
        for name, sid in settings.fred_series.items():
            try:
                frames[name] = self.fetch(sid, start=start)
            except Exception as exc:
                logger.warning("Failed to fetch %s (%s): %s", name, sid, exc)

        df = pd.DataFrame(frames)
        return df

    def save(self, df: pd.DataFrame, filename: str = "macro.parquet") -> Path:
        path = RAW_DIR / filename
        df.to_parquet(path)
        logger.info("Saved %d rows → %s", len(df), path)
        return path


def collect(start: str = "2000-01-01") -> pd.DataFrame:
    """Entry point: fetch all macro series and save to disk."""
    collector = FredCollector()
    df = collector.fetch_all(start=start)
    collector.save(df)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = collect()
    print(df.tail())
