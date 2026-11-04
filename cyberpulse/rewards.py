"""Variable-ratio reward engine and dopamine loot schedules for CyberPulse."""

import random
from typing import Optional, Tuple

from cyberpulse.models import Node, RewardType


EXPLOIT_CHIP_DROPS = ["logic_bomb", "ghost_protocol", "brute_miner"]

# Variable-magnitude reward schedule (Skinner/Schultz), tuned from data.
# Bands partition [0.0, 1.0): [0, chip) chip drop, [chip, chip + jackpot)
# 2.5x jackpot, remainder standard payout. Stated odds: 10/20/70.
REWARD_SCHEDULE = {
    "chip_rate": 0.10,
    "jackpot_rate": 0.20,
    "jackpot_numer": 5,
    "jackpot_denom": 2,
}

CHIP_DROP_RATE = REWARD_SCHEDULE["chip_rate"]
JACKPOT_RATE = REWARD_SCHEDULE["jackpot_rate"]


def roll_breach_reward(node: Node, rng: Optional[random.Random] = None) -> Tuple[int, str, Optional[str]]:
    """
    Calculate variable-magnitude reward payout and drops (Skinner box reinforcement schedule).
    Magnitude is unpredictable per roll; every fresh breach pays (fixed-ratio FR1 timing).
    Returns: (credits_awarded, reward_description, optional_exploit_drop)
    """
    if rng is None:
        rng = random.Random()

    base_creds = node.credits_reward
    if base_creds <= 0:
        return 0, "No monetary reserves on this node.", None

    roll = rng.random()
    chip_rate = REWARD_SCHEDULE["chip_rate"]
    jackpot_band = chip_rate + REWARD_SCHEDULE["jackpot_rate"]

    # 10% Chance: Exploit Chip Drop
    if roll < chip_rate:
        drop = rng.choice(EXPLOIT_CHIP_DROPS)
        desc = f"💾 HARDWARE EXPLOIT CHIP DISCOVERED: [{drop.upper()}]!"
        return base_creds, desc, drop

    # 20% Chance: Critical Jackpot (2.5x payout)
    if roll < jackpot_band:
        jackpot = base_creds * REWARD_SCHEDULE["jackpot_numer"] // REWARD_SCHEDULE["jackpot_denom"]
        desc = f"★★★ CRITICAL DATA HEIST! 2.5X JACKPOT (+{jackpot} Creds) ★★★"
        return jackpot, desc, None

    # 70% Chance: Standard Payout
    return base_creds, f"Extracted standard ledger balance (+{base_creds} Creds).", None
