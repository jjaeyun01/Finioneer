from pydantic_settings import BaseSettings
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    # API keys
    fred_api_key: str
    news_api_key: str = ""

    # Database
    database_url: str = f"sqlite:///{ROOT_DIR}/data/market_intel.db"

    # Cache
    redis_url: str = "redis://localhost:6379"

    # Alerts
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    data_dir: Path = ROOT_DIR / "data"

    # FRED series IDs — centralised here so changing one key fixes everything
    fred_series: dict = {
        "cpi":    "CPIAUCSL",    # Consumer Price Index
        "ppi":    "PPIACO",      # Producer Price Index
        "fed":    "FEDFUNDS",    # Federal Funds Rate
        "unemp":  "UNRATE",      # Unemployment Rate
        "gdp":    "GDP",         # Nominal GDP
        "m2":     "M2SL",        # Money Supply M2
        "t10y":   "GS10",        # 10-Year Treasury Yield
        "wage":   "CES0500000003",# Average Hourly Earnings
        "vix":    "VIXCLS",      # CBOE VIX
        "dxy":    "DTWEXBGS",    # Dollar Index (broad)
    }

    # Markets to track via yfinance
    tickers: dict = {
        "us": ["^GSPC", "^NDX", "^DJI"],
        "kr": ["^KS11", "^KQ11"],
        "btc": ["BTC-USD"],
        "stocks": ["AAPL", "NVDA", "MSFT", "TSLA", "META", "AMZN", "GOOGL"],
        "kr_stocks": ["005930.KS", "000660.KS"],  # 삼성전자, SK하이닉스
    }

    class Config:
        env_file = ROOT_DIR / "configs" / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
