"""Shared engagement scoring — used by Step 5's LLM report and by the (data-gated)
posting-time recommendation, so both agree on what "good engagement" means instead
of drifting apart into two separate formulas.
"""

from typing import Any


def engagement_score(m: dict[str, Any]) -> int:
    return m["likes"] + 2 * m["comments"] + 3 * m["shares"] + m["views"] // 10
