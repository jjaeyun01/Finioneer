"""News collector: NewsAPI + RSS feeds.

Fetches financial news, filters for market-relevant articles,
and saves them for downstream NLP processing.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import feedparser
import requests

from configs.settings import settings

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "fed_press":    "https://www.federalreserve.gov/feeds/press_all.xml",
    "reuters_biz":  "https://feeds.reuters.com/reuters/businessNews",
    "wsj_markets":  "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "bloomberg":    "https://feeds.bloomberg.com/markets/news.rss",
}

MARKET_KEYWORDS = [
    "federal reserve", "fed", "fomc", "interest rate", "inflation", "cpi",
    "nasdaq", "s&p", "kospi", "bitcoin", "btc", "earnings", "gdp",
    "unemployment", "payroll", "powell", "rate cut", "rate hike",
    "삼성전자", "sk하이닉스", "코스피", "한국은행", "기준금리",
]


@dataclass
class Article:
    title: str
    summary: str
    url: str
    source: str
    published: str
    relevance_score: float = 0.0
    sentiment_label: str = ""
    sentiment_score: float = 0.0
    tags: list[str] = field(default_factory=list)


class NewsCollector:

    def __init__(self):
        self.api_key = settings.news_api_key

    # ── NewsAPI ──────────────────────────────────────────────────────────────

    def fetch_newsapi(self, query: str = "stock market OR federal reserve OR CPI", days: int = 1) -> list[Article]:
        if not self.api_key:
            logger.warning("NEWS_API_KEY not set — skipping NewsAPI fetch")
            return []

        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 100,
            "apiKey": self.api_key,
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
        except Exception as e:
            logger.error("NewsAPI fetch failed: %s", e)
            return []

        results = []
        for a in articles:
            results.append(Article(
                title=a.get("title", ""),
                summary=a.get("description", "") or "",
                url=a.get("url", ""),
                source=a.get("source", {}).get("name", ""),
                published=a.get("publishedAt", ""),
            ))

        logger.info("NewsAPI: fetched %d articles", len(results))
        return results

    # ── RSS feeds ────────────────────────────────────────────────────────────

    def fetch_rss(self, feed_name: str, url: str) -> list[Article]:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.error("RSS parse failed (%s): %s", feed_name, e)
            return []

        results = []
        for entry in feed.entries:
            results.append(Article(
                title=entry.get("title", ""),
                summary=entry.get("summary", ""),
                url=entry.get("link", ""),
                source=feed_name,
                published=entry.get("published", ""),
            ))

        logger.info("RSS (%s): %d entries", feed_name, len(results))
        return results

    def fetch_all_rss(self) -> list[Article]:
        articles = []
        for name, url in RSS_FEEDS.items():
            articles.extend(self.fetch_rss(name, url))
        return articles

    # ── Relevance filtering ───────────────────────────────────────────────────

    def filter_relevant(self, articles: list[Article], threshold: float = 0.1) -> list[Article]:
        """Score articles by keyword hits; keep those above threshold."""
        relevant = []
        for a in articles:
            text = (a.title + " " + a.summary).lower()
            hits = sum(1 for kw in MARKET_KEYWORDS if kw in text)
            a.relevance_score = round(hits / len(MARKET_KEYWORDS), 4)
            if a.relevance_score >= threshold:
                relevant.append(a)

        logger.info("Filtered %d → %d relevant articles", len(articles), len(relevant))
        return sorted(relevant, key=lambda x: x.relevance_score, reverse=True)

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def collect(self) -> list[Article]:
        articles: list[Article] = []
        articles.extend(self.fetch_newsapi())
        articles.extend(self.fetch_all_rss())
        return self.filter_relevant(articles)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    collector = NewsCollector()
    articles = collector.collect()
    for a in articles[:5]:
        print(f"[{a.relevance_score:.2f}] {a.source}: {a.title[:80]}")
