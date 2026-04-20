"""Market data collector using yfinance.

Downloads OHLCV data for US indices, Korean indices, BTC, and individual stocks.
"""

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

from configs.settings import settings

logger = logging.getLogger(__name__)

RAW_DIR = settings.data_dir / "raw" / "market"
RAW_DIR.mkdir(parents=True, exist_ok=True)


class MarketCollector:

    def fetch_ticker(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        logger.info("Fetching %s", ticker)
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        return df

    def fetch_group(self, group: str, **kwargs) -> dict[str, pd.DataFrame]:
        tickers = settings.tickers.get(group, [])
        return {t: self.fetch_ticker(t, **kwargs) for t in tickers}

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        results = {}
        for group in settings.tickers:
            results.update(self.fetch_group(group))
        return results

    def save(self, data: dict[str, pd.DataFrame]) -> None:
        for ticker, df in data.items():
            safe = ticker.replace("^", "").replace("-", "_").replace(".", "_")
            path = RAW_DIR / f"{safe}.parquet"
            df.to_parquet(path)
            logger.info("Saved %s → %s", ticker, path)


def collect() -> dict[str, pd.DataFrame]:
    collector = MarketCollector()
    data = collector.fetch_all()
    collector.save(data)
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = collect()
    for ticker, df in data.items():
        print(f"{ticker}: {len(df)} rows, latest {df.index[-1].date()}")
