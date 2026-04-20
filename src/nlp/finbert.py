"""Lv3 — FinBERT financial sentiment pipeline.

Classifies financial text as Positive / Negative / Neutral
and computes hawkish/dovish scores for FOMC-related content.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MODEL_NAME = "yiyanghkust/finbert-tone"
CHUNK_SIZE = 400  # safe token budget per chunk


@dataclass
class SentimentResult:
    text: str
    label: str          # Positive | Negative | Neutral
    score: float        # confidence
    hawk_score: float   # 0-1, higher = more hawkish
    dove_score: float   # 0-1, higher = more dovish


class FinBERTAnalyzer:
    """Lazy-loads FinBERT on first call to avoid slow import at startup."""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._pipeline = None

    def _load(self):
        if self._pipeline is None:
            from transformers import pipeline
            logger.info("Loading FinBERT model: %s", self.model_name)
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                truncation=True,
                max_length=512,
            )
        return self._pipeline

    def _chunk(self, text: str) -> list[str]:
        words = text.split()
        chunks, current = [], []
        for word in words:
            current.append(word)
            if len(" ".join(current)) >= CHUNK_SIZE:
                chunks.append(" ".join(current))
                current = []
        if current:
            chunks.append(" ".join(current))
        return chunks or [text]

    def analyze(self, text: str) -> SentimentResult:
        pipe = self._load()
        chunks = self._chunk(text)
        results = pipe(chunks)

        pos = sum(1 for r in results if r["label"] == "Positive")
        neg = sum(1 for r in results if r["label"] == "Negative")
        n = len(results)

        # Majority label
        counts = {"Positive": pos, "Negative": neg, "Neutral": n - pos - neg}
        label = max(counts, key=counts.get)
        top_score = next(r["score"] for r in results if r["label"] == label)

        # Hawkish = negative tone in monetary context (tightening language)
        hawk_score = neg / n
        dove_score = pos / n

        return SentimentResult(
            text=text[:120] + "…" if len(text) > 120 else text,
            label=label,
            score=round(top_score, 4),
            hawk_score=round(hawk_score, 4),
            dove_score=round(dove_score, 4),
        )

    def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        return [self.analyze(t) for t in texts]


def fomc_statement_delta(prev: str, curr: str) -> float:
    """Measure textual change between two FOMC statements (0=identical, 1=completely different)."""
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, prev.lower(), curr.lower()).ratio()
    return round(1 - ratio, 4)


# ─── Quick demo ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    analyzer = FinBERTAnalyzer()

    samples = [
        "The Federal Reserve raised interest rates by 25 basis points, signaling further tightening ahead.",
        "Inflation has declined significantly and the Committee is prepared to cut rates if conditions warrant.",
        "The economy added 187,000 jobs in October, in line with expectations.",
    ]

    for text in samples:
        r = analyzer.analyze(text)
        print(f"\nText : {r.text}")
        print(f"Label: {r.label} ({r.score:.2%})")
        print(f"Hawk : {r.hawk_score:.2f} | Dove: {r.dove_score:.2f}")
