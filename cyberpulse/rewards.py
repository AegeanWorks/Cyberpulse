"""Variable-ratio reward engine and dopamine loot schedules for CyberPulse."""

import random
from typing import Optional, Tuple

from cyberpulse.models import Node, RewardType


EXPLOIT_CHIP_DROPS = ["logic_bomb", "ghost_protocol", "brute_miner"]


def roll_breach_reward(node: Node, rng: Optional[random.Random] = None) -> Tuple[int, str, Optional[str]]:
    """
    Calculate variable-ratio reward payout and drops (Skinner box reinforcement schedule).
    Returns: (credits_awarded, reward_description, optional_exploit_drop)
    """
    if rng is None:
        rng = random.Random()

    base_creds = node.credits_reward
    if base_creds <= 0:
        return 0, "No monetary reserves on this node.", None

    roll = rng.random()

    # 10% Chance: Exploit Chip Drop
    if roll < 0.10:
        drop = rng.choice(EXPLOIT_CHIP_DROPS)
        desc = f"💾 HARDWARE EXPLOIT CHIP DISCOVERED: [{drop.upper()}]!"
        return base_creds, desc, drop

    # 20% Chance: Critical Jackpot (2.5x payout)
    if roll < 0.30:
        jackpot = base_creds * 5 // 2
        desc = f"★★★ CRITICAL DATA HEIST! 2.5X JACKPOT (+{jackpot} Creds) ★★★"
        return jackpot, desc, None

    # 70% Chance: Standard Payout
    return base_creds, f"Extracted standard ledger balance (+{base_creds} Creds).", None
