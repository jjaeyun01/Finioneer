"""FOMC statement parser and change detector.

Measures textual divergence between consecutive FOMC statements
to quantify how much the Fed's language shifted meeting-to-meeting.
"""

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff

logger = logging.getLogger(__name__)

# Key hawkish / dovish phrase pairs (simplified lexicon)
HAWK_PHRASES = [
    "inflation remains elevated",
    "strongly committed",
    "higher for longer",
    "additional firming",
    "ongoing increases",
    "not yet confident",
]
DOVE_PHRASES = [
    "inflation has eased",
    "greater confidence",
    "appropriate to reduce",
    "labor market has come into better balance",
    "risks are more balanced",
    "prepared to adjust",
]


@dataclass
class StatementDelta:
    similarity: float       # 0=completely different, 1=identical
    change_score: float     # 1 - similarity
    hawk_hits: int
    dove_hits: int
    tone: str               # "hawkish" | "dovish" | "neutral"
    added_lines: list[str]
    removed_lines: list[str]


class FOMCParser:

    @staticmethod
    def clean(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s.,;:'\"-]", "", text)
        return text.strip().lower()

    def compare(self, prev: str, curr: str) -> StatementDelta:
        prev_clean = self.clean(prev)
        curr_clean = self.clean(curr)

        similarity = SequenceMatcher(None, prev_clean, curr_clean).ratio()
        change_score = round(1 - similarity, 4)

        hawk_hits = sum(1 for p in HAWK_PHRASES if p in curr_clean)
        dove_hits = sum(1 for p in DOVE_PHRASES if p in curr_clean)
        tone = "hawkish" if hawk_hits > dove_hits else ("dovish" if dove_hits > hawk_hits else "neutral")

        prev_lines = prev_clean.split(". ")
        curr_lines = curr_clean.split(". ")
        diff = list(unified_diff(prev_lines, curr_lines, lineterm=""))
        added   = [l[2:] for l in diff if l.startswith("+ ")]
        removed = [l[2:] for l in diff if l.startswith("- ")]

        logger.info(
            "FOMC statement delta: %.1f%% change | hawk=%d dove=%d | tone=%s",
            change_score * 100, hawk_hits, dove_hits, tone,
        )
        return StatementDelta(
            similarity=round(similarity, 4),
            change_score=change_score,
            hawk_hits=hawk_hits,
            dove_hits=dove_hits,
            tone=tone,
            added_lines=added[:10],    # top 10
            removed_lines=removed[:10],
        )

    def hawk_score(self, text: str) -> float:
        """0-1 hawkishness score for a single statement."""
        clean = self.clean(text)
        h = sum(1 for p in HAWK_PHRASES if p in clean)
        d = sum(1 for p in DOVE_PHRASES if p in clean)
        total = h + d
        return round(h / total, 4) if total else 0.5


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    prev = (
        "The Committee decided to raise the target range for the federal funds rate. "
        "Inflation remains elevated. The Committee is strongly committed to returning "
        "inflation to its 2 percent objective."
    )
    curr = (
        "The Committee decided to maintain the target range for the federal funds rate. "
        "Inflation has eased but remains somewhat elevated. The Committee has gained "
        "greater confidence that inflation is moving sustainably toward 2 percent."
    )

    parser = FOMCParser()
    delta = parser.compare(prev, curr)

    print(f"\n=== FOMC Statement Delta ===")
    print(f"Change score : {delta.change_score:.1%}")
    print(f"Tone         : {delta.tone}")
    print(f"Hawk hits    : {delta.hawk_hits}")
    print(f"Dove hits    : {delta.dove_hits}")
    print(f"\nNew language added:")
    for line in delta.added_lines[:3]:
        print(f"  + {line}")
    print(f"\nLanguage removed:")
    for line in delta.removed_lines[:3]:
        print(f"  - {line}")
