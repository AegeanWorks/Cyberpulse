"""Stated-vs-coded odds check for CyberPulse (stdlib only, deterministic).

Verifies the 70/20/10 reward schedule, 2.5x jackpot math, extraction-surge
preview parity and forecast-vs-actual cost parity. Exit 0 when every stated
number matches the coded number within tolerance, else exit 1.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cyberpulse.engine import GameEngine
from cyberpulse.models import Node, NodeType
from cyberpulse.rewards import REWARD_SCHEDULE, roll_breach_reward


class FixedRng:
    """Deterministic RNG stub returning a fixed roll."""

    def __init__(self, roll):
        self.roll = roll

    def random(self):
        return self.roll

    def choice(self, seq):
        return seq[0]


def make_node(base=200):
    return Node(
        node_id="vault_odds",
        name="Odds Vault",
        node_type=NodeType.DATA_VAULT,
        security_level=2,
        credits_reward=base,
    )


def check_bands():
    """Band mapping: chip below chip_rate, jackpot below chip+jackpot, else standard."""
    chip = REWARD_SCHEDULE["chip_rate"]
    jackpot_edge = chip + REWARD_SCHEDULE["jackpot_rate"]
    node = make_node()
    _, _, drop = roll_breach_reward(node, rng=FixedRng(chip - 1e-9))
    assert drop is not None, "roll just below chip_rate must drop a chip"
    creds, desc, drop = roll_breach_reward(node, rng=FixedRng(chip + 1e-9))
    assert drop is None and "JACKPOT" in desc, "roll just above chip_rate must jackpot"
    creds, desc, drop = roll_breach_reward(node, rng=FixedRng(jackpot_edge + 1e-9))
    assert drop is None and "JACKPOT" not in desc, "roll above jackpot band must be standard"
    numer = REWARD_SCHEDULE["jackpot_numer"]
    denom = REWARD_SCHEDULE["jackpot_denom"]
    for base in (60, 100, 101, 200, 350):
        creds, _, _ = roll_breach_reward(make_node(base), rng=FixedRng(chip + 0.01))
        assert creds == base * numer // denom, f"jackpot math drift at base {base}"
    return f"bands ok: chip<{chip} jackpot<{round(jackpot_edge, 4)} {numer}/{denom}x"


def check_distribution(n=20000, seed=1234):
    """Empirical frequencies must match stated 10/20/70 within tolerance."""
    rng = random.Random(seed)
    node = make_node()
    chip = jackpot = 0
    for _ in range(n):
        creds, _, drop = roll_breach_reward(node, rng=rng)
        if drop is not None:
            chip += 1
        elif creds > node.credits_reward:
            jackpot += 1
    chip_rate = chip / n
    jackpot_rate = jackpot / n
    assert abs(chip_rate - 0.10) <= 0.02, f"chip drift: {chip_rate:.4f}"
    assert abs(jackpot_rate - 0.20) <= 0.02, f"jackpot drift: {jackpot_rate:.4f}"
    return f"distribution ok: chip={chip_rate:.3f} jackpot={jackpot_rate:.3f} standard={1 - chip_rate - jackpot_rate:.3f} (n={n})"


def check_surge_parity():
    """extraction_risk() preview must equal the mitigated surge jackout applies."""
    checked = 0
    for difficulty in ("easy", "normal", "hard"):
        for dampener in (0, 2):
            for trace in (0, 49, 50, 69, 70, 84, 85, 99):
                engine = GameEngine(seed=7, difficulty=difficulty)
                engine.deck.ice_dampener_level = dampener
                engine.state.trace_percent = trace
                risk = engine.extraction_risk()
                expected_surge = engine.mitigated_trace(engine.extraction_surge())
                assert risk["surge"] == expected_surge, (
                    f"surge mismatch {difficulty} damp={dampener} trace={trace}"
                )
                assert risk["projected_trace"] == min(100, trace + expected_surge)
                assert risk["lethal"] == (risk["projected_trace"] >= 100)
                checked += 1
    return f"surge parity ok: {checked} cases"


def check_forecast_parity():
    """Forecasts must derive from the same mitigated_trace() as the actions."""
    checked = 0
    for difficulty in ("easy", "normal", "hard"):
        engine = GameEngine(seed=7, difficulty=difficulty)
        for action, raw in (("scan", 5), ("probe", 4), ("overdrive", 8)):
            forecast = engine.action_forecast(action, "node_gateway" if action == "probe" else "")
            if not forecast["ok"]:
                continue
            assert forecast["trace_gain"] == engine.mitigated_trace(raw), (
                f"forecast drift: {action} {difficulty}"
            )
            checked += 1
    assert checked > 0, "no forecast cases evaluated"
    return f"forecast parity ok: {checked} cases"


def main():
    results = [
        check_bands(),
        check_distribution(),
        check_surge_parity(),
        check_forecast_parity(),
    ]
    for line in results:
        print(line)
    print("check_odds: all stated odds match coded odds")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"ODDS MISMATCH: {exc}")
        sys.exit(1)
