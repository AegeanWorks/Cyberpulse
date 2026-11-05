"""Transparent run scoring for legacy and Hall of Fame rankings."""

import math
from typing import Any, Dict


def _safe_count(value: Any) -> int:
    """Coerce a scoring input to a finite non-negative int; hostile values become 0."""
    try:
        if isinstance(value, bool):
            return 0
        if isinstance(value, float) and not math.isfinite(value):
            return 0
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


# Transparent run-score weights, tuned from data. Single source for the
# Hall of Fame formula; change here, never inline.
SCORE_WEIGHTS = {
    "combo": 75,
    "quests": 150,
    "breaches": 25,
    "contract": 200,
    "victory": 500,
    "jackout": 250,
    "story": 100,
}


def score_run(
    *,
    gained: int,
    best_combo: int,
    quests_done: int,
    nodes_breached: int,
    outcome: str,
    contract_completed: bool,
    main_story_complete: bool,
) -> Dict[str, Any]:
    """Return a score and its itemized breakdown for one settled run."""
    weights = SCORE_WEIGHTS if isinstance(SCORE_WEIGHTS, dict) else {}
    def _weight(key: str, fallback: int) -> int:
        try:
            value = weights.get(key, fallback)
            if isinstance(value, bool):
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            return max(0, int(value))
        except (TypeError, ValueError, OverflowError):
            return fallback
    breakdown = {
        "credits": _safe_count(gained),
        "combo": _safe_count(best_combo) * _weight("combo", 75),
        "quests": _safe_count(quests_done) * _weight("quests", 150),
        "breaches": _safe_count(nodes_breached) * _weight("breaches", 25),
        "contract": _weight("contract", 200) if contract_completed else 0,
        "outcome": _weight("victory", 500) if outcome == "victory" else (_weight("jackout", 250) if outcome == "jackout" else 0),
        "story": _weight("story", 100) if main_story_complete else 0,
    }
    return {"score": sum(breakdown.values()), "breakdown": breakdown}
