"""Story acts, quest blueprints, and operative dialogue for CyberPulse."""

from typing import Dict, List, Tuple

from cyberpulse.models import ContactProfile, NodeType, Quest

STORY_INTRO = (
    "Neon rain falls on the Sprawl. A dead courier left you a black market deck "
    "and one name: NEXUS. The Syndicate wants the supercore. The streets want answers. "
    "Jack in before someone else does."
)

STORY_ACTS: Dict[int, Tuple[str, str]] = {
    1: ("ACT I", "Ghost in the Gateway"),
    2: ("ACT II", "Follow the Money"),
    3: ("ACT III", "The Black ICE"),
    4: ("ACT IV", "Nexus Protocol"),
    5: ("FINALE", "Zero Day"),
}

STORY_LOG_SEED = [
    "A dead courier's deck boots with one encrypted name: NEXUS.",
    "Mira Voss is waiting on the encrypted channel. She pays in creds and secrets.",
]

MAIN_QUEST_IDS = {"q_gateway", "q_money", "q_blackice", "q_core"}


def initial_quests() -> List[Quest]:
    """Return the persistent quest board for a new run."""
    return [
        Quest(
            quest_id="q_gateway",
            title="Ghost in the Gateway",
            description="Breach two FIREWALL routers to map the Syndicate's inner subnet.",
            objective="breach_type",
            target=NodeType.FIREWALL,
            required=2,
            reward_creds=120,
            giver="mira",
            story_act=1,
            story_chapter=1,
            accepted=True,
        ),
        Quest(
            quest_id="q_money",
            title="Follow the Money",
            description="Steal /data/corporate_slush_fund.csv from the Financial Ledger Vault.",
            objective="steal_file",
            target="/data/corporate_slush_fund.csv",
            required=1,
            reward_creds=250,
            giver="archivist",
            story_act=2,
            story_chapter=1,
            accepted=False,
        ),
        Quest(
            quest_id="q_blackice",
            title="Break the Black ICE",
            description="Breach the Black ICE Defense Cluster and take its root clearance key.",
            objective="breach_type",
            target=NodeType.ICE_DEFENSE,
            required=1,
            reward_creds=300,
            giver="zero",
            story_act=3,
            story_chapter=1,
            accepted=False,
        ),
        Quest(
            quest_id="q_core",
            title="Nexus Protocol",
            description="Infiltrate the Nexus Central Supercore and end the Omega protocol.",
            objective="breach_type",
            target=NodeType.CENTRAL_CORE,
            required=1,
            reward_creds=500,
            giver="mira",
            story_act=4,
            story_chapter=1,
            accepted=False,
        ),
        Quest(
            quest_id="q_side_craft",
            title="Script Kiddie No More",
            description="Synthesize a trace_cleaner chip in the malware workshop.",
            objective="craft_recipe",
            target="trace_cleaner",
            required=1,
            reward_creds=80,
            giver="kilo",
            story_act=1,
            story_chapter=1,
            accepted=False,
        ),
        Quest(
            quest_id="q_side_ghost",
            title="Ghost in the Wires",
            description="Deploy two keylogger daemons on breached hosts.",
            objective="deploy_daemon",
            target="keylogger",
            required=2,
            reward_creds=100,
            giver="kilo",
            story_act=1,
            story_chapter=1,
            accepted=False,
            required_trust=1,
        ),
        Quest(
            quest_id="q_side_wipe",
            title="Clean Sweep",
            description="Wipe the access logs on the Financial Ledger Vault (10.0.4.15).",
            objective="wipe_logs",
            target="10.0.4.15",
            required=1,
            reward_creds=150,
            giver="archivist",
            story_act=2,
            story_chapter=1,
            accepted=False,
        ),
        Quest(
            quest_id="q_arc_cold_wallet",
            title="Cold Wallet",
            description="Steal 2 data files from any breached hosts for Kilo's ghost-boot fund.",
            objective="steal_file",
            target="",
            required=2,
            reward_creds=160,
            giver="kilo",
            story_act=2,
            story_chapter=2,
            accepted=False,
            required_trust=2,
        ),
        Quest(
            quest_id="q_arc_dead_letter",
            title="Dead Letter Drop",
            description="Deploy 1 keylogger daemon for the Archivist's dead-letter network.",
            objective="deploy_daemon",
            target="keylogger",
            required=1,
            reward_creds=140,
            giver="archivist",
            story_act=2,
            story_chapter=2,
            accepted=False,
            required_trust=2,
        ),
    ]


def initial_contacts() -> List[ContactProfile]:
    """Return the operatives available to a new run."""
    return [
        ContactProfile(
            contact_id="mira",
            name="Mira Voss",
            handle="@mira_v",
            role="Syndicate Fixer",
            faction="The Syndicate",
            tagline="Pays on time. Never tells you the whole job.",
            unlock_act=1,
            quest_id="q_gateway",
        ),
        ContactProfile(
            contact_id="kilo",
            name="Kilo",
            handle="@kilo_ghost",
            role="Street Techie",
            faction="Ghost Circuit",
            tagline="Keeps your deck cool and your secrets cheaper.",
            unlock_act=1,
            quest_id="q_side_craft",
            secondary_quest_id="q_side_ghost",
        ),
        ContactProfile(
            contact_id="archivist",
            name="The Archivist",
            handle="@dead_letter",
            role="Data Broker",
            faction="The Library",
            tagline="Everything is for sale. Some things are worth burning.",
            unlock_act=2,
            quest_id="q_money",
            secondary_quest_id="q_side_wipe",
        ),
        ContactProfile(
            contact_id="zero",
            name="Agent Zero",
            handle="@zero_day",
            role="Rival Netrunner",
            faction="Black ICE Collective",
            tagline="Won the last war. Wants to see if you can survive this one.",
            unlock_act=3,
            quest_id="q_blackice",
        ),
    ]


CONTACT_DIALOGUE: Dict[str, Dict[int, str]] = {
    "mira": {
        1: "Mira: 'Two routers, two ways in. Break the FIREWALL nodes and the Syndicate will believe you are useful.'",
        2: "Mira: 'Good. The money trail runs through the Financial Ledger Vault. The Archivist knows the account.'",
        3: "Mira: 'Black ICE is awake. It learned your signature from the last job. Make it forget.'",
        4: "Mira: 'The supercore is the only thing between us and a very short future. Finish it.'",
        5: "Mira: 'The Sprawl is still standing. That is more than most runners get.'",
    },
    "kilo": {
        1: "Kilo: 'Your deck runs hot, choom. Craft a trace cleaner before the Black ICE cooks your brain.'",
        2: "Kilo: 'Daemons are cheap labor. Plant two keyloggers and let the grid pay your rent.'",
        3: "Kilo: 'The Archivist is paranoid, but the good kind. Do not lie to them.'",
        4: "Kilo: 'If you make it to the core, name a subroutine after me.'",
        5: "Kilo: 'You actually did it. Drinks are on the dead courier.'",
    },
    "archivist": {
        2: "The Archivist: 'The vault file is not money. It is a confession with a routing number.'",
        3: "The Archivist: 'Black ICE guards the root key. Steal it and the vault opens itself.'",
        4: "The Archivist: 'Omega is not a weapon. It is a door. Do not open it on your knees.'",
        5: "The Archivist: 'The archive remembers you now. Try to be worth remembering.'",
    },
    "zero": {
        3: "Agent Zero: 'I cracked Black ICE once. It grew back. Let us see what you are made of.'",
        4: "Agent Zero: 'The core is a mirror. It shows you the version of yourself that already lost.'",
        5: "Agent Zero: 'Not bad, runner. Next time I will not go easy.'",
    },
}

FAVOR_DESCRIPTIONS: Dict[str, str] = {
    "mira": "Burn a Syndicate favor to reduce trace by 20%.",
    "kilo": "Call in a cooling favor to fully restore CPU cycles.",
    "archivist": "Ask the Archive to expose one locked node on the grid.",
    "zero": "Borrow a ghost_protocol exploit chip from a rival.",
}

CHOICE_LABELS: Dict[str, str] = {
    "zero_ally": "ALLIED WITH AGENT ZERO",
    "zero_defy": "DEFIED AGENT ZERO",
}

CHOICE_EPILOGUES: Dict[str, str] = {
    "zero_ally": "Zero meets you on the far side of the core. Two ghosts walk out of the Sprawl together.",
    "zero_defy": "Zero logs your defiance and vanishes. The Sprawl will remember which of you blinked first.",
}

CHOICE_DIALOGUE: Dict[Tuple[str, str, int], str] = {
    ("zero", "zero_ally", 3): "Agent Zero: 'Alliance accepted. We are in this together now. Try to keep up.'",
    ("zero", "zero_defy", 3): "Agent Zero: 'You chose the hard way. Good. I was getting bored.'",
    ("zero", "zero_ally", 4): "Agent Zero: 'We are in this together now. Do not make me regret the paperwork.'",
    ("zero", "zero_ally", 5): "Agent Zero: 'The core is ours. Same time next apocalypse?'",
    ("zero", "zero_defy", 4): "Agent Zero: 'You chose the hard way. Good. I was getting bored.'",
    ("zero", "zero_defy", 5): "Agent Zero: 'You broke it alone. That is either courage or a very expensive habit.'",
    ("mira", "zero_defy", 4): "Mira: 'Zero will come for you. I will make sure they regret it.'",
    ("mira", "zero_ally", 4): "Mira: 'You trust Zero. I hope your deck is insured.'",
}


def act_title(act: int) -> Tuple[str, str]:
    return STORY_ACTS.get(act, ("EPILOGUE", "The Sprawl Remembers"))


def dialogue_for(contact_id: str, act: int, choice: str = "") -> str:
    if choice:
        choice_line = CHOICE_DIALOGUE.get((contact_id, choice, act))
        if choice_line:
            return choice_line
    lines = CONTACT_DIALOGUE.get(contact_id, {})
    if act in lines:
        return lines[act]
    if lines:
        return lines[max(lines)]
    return "The channel is silent."

OUTCOME_EPILOGUES: Dict[str, str] = {
    "victory": "NEXUS falls silent. The Sprawl wakes up without a leash, and your handle becomes a rumor.",
    "jackout": "You pull the jack before the ICE closes. The job is unfinished, but the creds are real.",
    "lockout": "The deck burns hot and goes dark. Somewhere in the Sprawl, a fixer deletes your number.",
    "active": "The run is still open. The city is waiting to see how it ends.",
}

CONTACT_EPILOGUES: Dict[str, str] = {
    "mira": "Mira keeps her promise and scrubs your name from the Syndicate ledger.",
    "kilo": "Kilo leaves a cold drink and a spare cooling cell on your rig.",
    "archivist": "The Archivist files your run under 'still breathing' and quietly opens a new door.",
    "zero": "Agent Zero sends one line: 'Next time, I pick the target.' You take it as respect.",
}

COMBO_EPILOGUES: Dict[int, str] = {
    3: "Your combo chain becomes a training reel for every runner in the lower Sprawl.",
    5: "Five clean breaches in a row. The grid starts calling you a ghost.",
    8: "The Black ICE logs your combo as an anomaly and stops trying to model you.",
}


TRUST_DIALOGUE: Dict[Tuple[str, str], str] = {
    ("mira", "Trusted"): "Mira: 'You deliver. That puts you on the short list for better terms.'",
    ("mira", "Inner Circle"): "Mira: 'My inner circle is small. Do not make me regret adding you.'",
    ("kilo", "Trusted"): "Kilo: 'I saved you a cooling cell. You can owe me a story later.'",
    ("kilo", "Inner Circle"): "Kilo: 'My back door is your back door, choom. Just do not burn it.'",
    ("archivist", "Trusted"): "The Archivist: 'Your name is in a clean file. Keep it that way.'",
    ("archivist", "Inner Circle"): "The Archivist: 'I keep what you need before you ask. That is the point of trust.'",
    ("zero", "Trusted"): "Agent Zero: 'You are still alive. That is a start.'",
    ("zero", "Inner Circle"): "Agent Zero: 'When the grid falls, I want you beside me.'",
}


def trust_dialogue_for(contact_id: str, tier: str) -> str:
    return TRUST_DIALOGUE.get((contact_id, tier), "")
