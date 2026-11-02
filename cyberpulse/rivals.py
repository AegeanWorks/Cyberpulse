"""Deterministic rival-netrunner generation."""

import random
from typing import Dict, Tuple

from cyberpulse.models import RivalNetrunner

RIVAL_ROSTER: Tuple[Tuple[str, str, int, str], ...] = (
    (
        "Vex",
        "vex_01",
        3,
        "A razor-thin ghost who treats every contract as a personal auction.",
    ),
    (
        "Marrow",
        "marrow",
        2,
        "A patient cold-storage specialist who never leaves a clean extraction.",
    ),
    (
        "Static",
        "static_9",
        1,
        "A loud street runner whose botnet makes up for what finesse lacks.",
    ),
    (
        "Nulljack",
        "nulljack",
        2,
        "A quiet ledger-forger who steals board payouts before the ink dries.",
    ),
)


def generate_rival(seed: int) -> RivalNetrunner:
    """Create the run's rival from a deterministic seed stream."""
    rng = random.Random(int(seed) ^ 0x5A17)
    name, handle, skill, tagline = rng.choice(RIVAL_ROSTER)
    return RivalNetrunner(
        name=name,
        handle=handle,
        skill=skill,
        tagline=tagline,
        next_move_turn=6 + rng.randint(0, 2),
    )


# Per-act pressure on the rival's board cadence, in turns. Later acts run
# hotter: the base steal delay shrinks so the rival grabs more often and
# counter-trace timing matters more. Unknown acts fall back to baseline.
RIVAL_ACT_PRESSURE: Dict[int, int] = {1: 2, 2: 1, 3: 0, 4: -1}

RIVAL_MIN_DELAY = 3


def rival_move_delay(skill: int, story_act: int, jitter: int) -> int:
    """Deterministic rival board delay: skill base, act pressure, RNG jitter."""
    base = max(4, 8 - int(skill))
    pressure = RIVAL_ACT_PRESSURE.get(int(story_act), 0)
    return max(RIVAL_MIN_DELAY, base + pressure + int(jitter))
