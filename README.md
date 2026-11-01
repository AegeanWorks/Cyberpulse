# cyberpulse

<!-- aegean:media:start -->
<p align="center"><img src="assets/social-preview.png" alt="Cyberpulse social preview" width="100%"></p>
<p align="center"><a href="LICENSE"><img src="https://img.shields.io/badge/license-AGL--1.1-7048e8" alt="License"></a> <a href="https://github.com/AegeanWorks/AIKit"><img src="https://img.shields.io/badge/AIKit-integrated-6f42c1" alt="AIKit Integrated"></a></p>
<!-- aegean:media:end -->


CyberPulse is a retro-cyberpunk terminal hacking simulation game designed around empirical behavioral psychology: procedural puzzle nodes, seeded side-subnet hosts, ICE defenses, push-your-luck extraction, persistent career progression and a five-act story campaign, played in the terminal or the Web Cyberdeck.

It also features variable-ratio reward schedules, near-miss striatal feedback, an operative relationship system, a dynamic quest board, combo/overdrive risk-reward mechanics, and a living-grid world simulation with an in-game clock, corporate alert, generated news, ambient events, host re-securing, a drifting black market, tactical shifts, lay-low downtime, and a deadline-bound Syndicate contract market.

## ⚡ 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: Python 3.10+ (standard library only; zero third-party packages required); a modern browser for the Web Cyberdeck.
- **Canonical Regression Shield Gate**:
  ```bash
  python aikit.py check cyberpulse
  ```

### 🚀 Instant One-Click Launch (Zero-Friction)
From inside the `projects/cyberpulse` directory:
- **Windows**: Double-click `start.bat` (or run `start.bat` in CMD / PowerShell)
- **Universal**: Run `python start.py` (or `./start.sh` on POSIX / macOS / Linux)
*(Defaults to launching the visual Web Cyberdeck; custom flags like `python start.py --seed 1337` are forwarded directly to the CLI)*

### 🛠️ AIKit Commands (run from the AIKit folder)
| Role | Command |
|---|---|
| Status, task and gates | `python aikit.py status cyberpulse` |
| Phase 4: every gate | `python aikit.py check cyberpulse` |
| Repair memory and map, then check | `python aikit.py fix cyberpulse` |
| Resume an interrupted task | `python aikit.py resume cyberpulse` |

## 📦 What's Inside

```text
cyberpulse/
├── .aikit/                   <- this project's memory: record, ledger, decisions
├── .gitignore                <- transient AIKit state excluded
├── LICENSE                   <- Aegean Game License 1.1 (AGL-1.1): DRM-free personal play
├── LICENSES/                 <- REUSE license texts
├── REUSE.toml                <- Machine-readable SPDX metadata
├── ASSETS.md                 <- Asset/data manifest: what the license covers
├── README.md
├── assets/
├── COMMANDS.md  <- in-game command reference
├── COMMERCIAL.md
├── CHANGELOG.md              <- release history
├── pyproject.toml            <- build and package configuration
├── start.bat                 <- Windows one-click launcher
├── start.py                  <- universal launcher (defaults to --web)
├── start.sh                  <- POSIX / Linux / macOS launcher
├── cyberpulse/               <- core game engine and CLI
│   ├── __init__.py
│   ├── achievements.py       <- career milestone catalog & settlement unlocks
│   ├── cli.py                <- interactive terminal interface & REPL
│   ├── daily.py              <- date-derived daily keys & seeds
│   ├── difficulty.py         <- difficulty normalization & modifiers
│   ├── engine.py             <- deterministic game state coordinator
│   ├── factions.py           <- standing normalization & reputation bonuses
│   ├── models.py             <- frozen dataclasses & domain state models
│   ├── network.py            <- procedural network grid generator
│   ├── puzzles.py            <- cyber-intrusion puzzle nodes & near-miss detection
│   ├── rewards.py            <- variable-ratio loot tables & reward schedules
│   ├── rivals.py             <- deterministic rival-netrunner generation
│   ├── scoring.py            <- transparent run score & legacy weights
│   ├── server.py             <- zero-dependency HTTP REST & cyberdeck server
│   ├── shop.py               <- black market tech vendor & hardware catalog
│   ├── story.py              <- story acts, quest blueprints, operative dialogue
│   ├── static/               <- Web Cyberdeck UI (HTML, CSS, JS)
│   │   ├── app.js
│   │   ├── index.html
│   │   └── style.css
│   ├── tutorial.py           <- first-run field manual steps
│   ├── world.py              <- living-grid clock, alert, news, ambient events
│   └── storage.py            <- atomic persistence & career dossier management
└── tests/                    <- unit & integration test suite (about eight seconds)
    ├── __init__.py
    ├── test_achievements.py
    ├── test_cli.py
    ├── test_daily.py
    ├── test_difficulty.py
    ├── test_engine.py
    ├── test_factions.py
    ├── test_forecast.py
    ├── test_grid.py
    ├── test_init.py
    ├── test_models.py
    ├── test_network.py
    ├── test_puzzles.py
    ├── test_rewards.py
    ├── test_rivals.py
    ├── test_scoring.py
    ├── test_server.py
    ├── test_shop.py
    ├── test_sim_life.py
    ├── test_storage.py
    ├── test_tutorial.py
    ├── test_version.py
    ├── test_visuals.py
    └── test_world.py
```

## 🧠 Behavioral Psychology & Engagement Mechanics

CyberPulse's mechanics are grounded in cognitive neuroscience and behavioral game design:

1. **Variable Ratio Reinforcement Schedules (Skinner / Schultz Dopamine Reward Prediction Error)**:
   - Node breach rewards utilize randomized reward schedules (70% standard yield, 20% high-yield 2.5x jackpot, 10% rare hardware chip).
   - Unpredictable payoff magnitude induces striatal dopamine bursts, maximizing engagement compared to fixed rewards.
2. **Near-Miss Effect & Striatal Dopamine Response (Clark et al., 2009)**:
   - Narrow failures (frequency inside the harmonic band, keyword within 1 letter, first buffer block aligned) trigger explicit near-miss sensory feedback.
   - The first near miss on each puzzle becomes a **NEAR-MISS SURGE**: one bonus tuning/keyword attempt, or one free buffer retry. Later near misses are flavor only, so the comeback is real but cannot be farmed.
   - Neuroimaging proves near-misses activate the same reward pathways (nucleus accumbens and anterior insula) as wins, driving re-engagement and persistent play.
3. **Push-Your-Luck & Loss Aversion (Kahneman & Tversky Prospect Theory)**:
   - Breached credits remain *unbanked* during an active run. Reaching 100% ICE trace triggers Burnout Lockout, destroying all unbanked bounty.
   - `jackout` applies a **Black ICE extraction surge** (+5% at 50% trace, +10% at 70%, +15% at 85%, mitigated by the ICE dampener). A projected 100% burns the run at the extraction point, so disciplined banking matters as much as deep intrusion.
4. **Zeigarnik Effect (Incomplete Contract Tension)**:
   - Active Syndicate Bounty Contracts track unfulfilled goals (e.g. breach 2 encryption nodes). Unfinished objectives create cognitive tension that motivates session continuation.
5. **Autonomy & Competence Loop (Ryan & Deci Self-Determination Theory - PENS)**:
   - Tactical agency through branching network topologies, upgrade pathways, and cyberdeck customization in the Black Market vendor.
6. **Deadline Pressure & Goal Gradient (Kivetz et al.)**:
   - Each job carries a visible deadline and rush bonus, so `lay_low`, detours, and loud play spend a finite reward window. Completed work raises giver trust and payout; a missed deadline costs both and raises alert.
6. **Combo Streaks & Voluntary Risk (Sensation Seeking / Flow Channel)**:
   - Consecutive successful breaches build a reward multiplier (up to +50%). `overdrive` lets the player voluntarily burn CPU and trace to prime the next combo, tightening the flow channel between boredom and lockout. Any detected failure (burned puzzle, flagged social lure, hunter clash, antivirus quarantine) breaks the streak, so the multiplier is a real stake rather than a ratchet. A burned puzzle also seals its host's ICE for two turns, so failure costs tempo instead of granting a free retry. Best combo is recorded in the career dossier, and combo milestones appear in the run epilogue.
7. **Narrative Transportation & Character Attachment**:
   - Five story acts, a mission board, and four persistent operatives turn abstract objectives into relationships. Act progression unlocks new dialogue, jobs, and one-time favors that materially change the run, while trust tracks your standing with each operative.
8. **Implementation Intentions (Gollwitzer)**:
   - Accepted quests and the story objective card make the next concrete action salient, reducing choice paralysis while preserving player autonomy.
9. **Meaningful Narrative Choice (Self-Concordance)**:
   - In Act III, Agent Zero offers a one-time alliance or defiance decision. The choice changes trust, rewards, late-act dialogue, and the run epilogue, making the relationship feel authored rather than cosmetic.
10. **Diegetic Feedback & Situational Awareness (Presence)**:
   - The living grid runs its own clock, alert level, market, and news wire. Loud play raises alert, which raises patrol trace, re-secures breached hosts, and marks up the black market, while generated headlines report the consequences. The world reacts and narrates, so choices feel embedded in a place rather than a menu.

## 🎮 How to Play

### 1. Web Cyberdeck (Visual CRT & Web Audio)
Launch the browser cyberdeck: main menu, story/mission board, operative channels, interactive 2D node matrix, tactical stance/proxy dock, visual mini-games, a living-grid ticker (clock, alert, market, headlines), and synthesized 8-bit FX. The header **SAVE** button opens the slot archive: three manual slots hold independent runs, each can carry a run label, and **AUTOSAVE** follows the active run after every change. Name or rename a checkpoint without replaying it, delete stale runs with a confirmation, and use **CONTINUE RUN** on the main menu to restore any slot after a restart. **DAILY RUN** starts today's date-seeded challenge and records your best net gain for the day. The files are interchangeable with the terminal:

```bash
# Launch interactive Web Cyberdeck (auto-opens browser at http://127.0.0.1:8420)
python -m cyberpulse.cli --web

# Launch with custom world seed and port
python -m cyberpulse.cli --web --port 9000 --seed 42069
```

### 2. Interactive Terminal CLI
Or operate purely in the retro terminal REPL harness. Both interfaces open with a main menu for a new run, story briefing, operative channels, career dossier, and help; the terminal also offers slot continuation with `save [1|2|3] [name]`, `load [1|2|3|auto]`, `saves`, `rename`, and `delete`, while autosave runs after every command:

```bash
# Launch interactive terminal game with default seed
python -m cyberpulse.cli

# Launch terminal game with custom world seed
python -m cyberpulse.cli --seed 42069

# Launch on hard mode with a Syndicate patron
python -m cyberpulse.cli --difficulty hard --allegiance syndicate

# Print the installed version
python -m cyberpulse.cli --version

# Start today's deterministic daily challenge
python -m cyberpulse.cli --daily
```

### In-Game Commands (Authentic Simulation & Tactical Netrunning)

The full reference of 56 commands, with each one's action and simulation role, is in [COMMANDS.md](COMMANDS.md).

### 🕹️ Authentic Cyber Warfare Infiltration Workflow
1. **Network Reconnaissance**: Discover network topology with `scan` or read host configuration files with `cat /etc/hosts`. Scan active network ports using `probe 192.168.1.10`.
2. **Perimeter Firewall Inspection & Ingress Bypass**: Check host firewall with `firewall 192.168.1.20`. If port 22 is blocked, craft a port-knocking sequence or packet fragmentation with `bypass 192.168.1.20 22 knock` to deactivate the rule!
3. **Multi-Vector Social Engineering**: Exploit the human factor with `social 192.168.1.10 pretext "Sarah Chen"` or `social 192.168.1.10 vishing`. Compromised staff leak authentication tokens, downgrade node security level, and override blocked firewall rules!
4. **Endpoint Antivirus Evasion**: Inspect endpoint protection with `av 192.168.1.10`. If SentinelCore or DefenderBasic alert levels rise, deploy a kernel hook via `evade 192.168.1.10 rootkit` to blind heuristic sweeps and protect active daemons.
5. **Weaponized CVE Exploits**: Consult your exploit repertoire with `cve`. Launch zero-days matching target services via `exploit 192.168.1.10 21 CVE-2011-2523` or `exploit 192.168.1.20 22 CVE-2024-6387`.
6. **Deploy Persistent Malware**: Plant passive listeners with `keylogger 192.168.1.10` to siphon crypto credits every turn. Unevaded AV will actively hunt daemons unless blinded.
7. **Exfiltrate High-Value Data**: Traverse directories with `ls`, inspect files with `cat`, and extract proprietary databases with `steal /data/corporate_slush_fund.csv`. Stolen data archives straight into your local rig at `/loot/`!
8. **Sanitize & Cash Out**: Scrub audit records with `wipe_logs` to shed ICE trace, then extract via `cash_out` before trace reaches 85% — the Black ICE extraction surge can burn the run at the jack. Banking early locks in bounty and grows your career dossier!
9. **Live With the Grid**: Watch `world` and `news` between jobs. A hot alert invites NetWatch patrol trace, black-market markups, and sysadmins re-securing the hosts you left behind (with any daemons inside), while a quiet grid cools down and discounts gear.
10. **Choose and Beat the Job Clock**: `contract` shows the offer board; `accept_job <id>` starts the clock. Early completion pays the rush bonus and raises trust; a missed deadline costs trust, raises alert, and refreshes the board.

## 🛡️ Architecture & Guarantees

- **Zero Undeclared Dependencies**: Built with 100% pure Python standard library modules (`random`, `json`, `dataclasses`, `pathlib`, `argparse`).
- **Deterministic State Engine**: Every network grid and puzzle sequence can be reproduced using `--seed <int>`.
- **Seeded Side-Subnet Layer**: The seven-host campaign spine (gateway, proxies, vaults, Black ICE, supercore) is fixed so story targets stay honest, while every seed grows two or three extra `DATA_VAULT` hosts beside it. Template, security level, puzzle type, payout, trace rate and anchors vary, so scans, routes, loot and contract targets differ between runs; the Web matrix places them in three reserved slots with their real names.
- **Cross-Interface Save Slots**: Both interfaces use the terminal's atomic `SaveManager` across three manual slots plus a separate autosave file. Slot 1 remains the legacy `savegame.json`, so existing saves keep loading; the slot archive lists a run label, turn, credits, trace, act and timestamp for each checkpoint, and **CONTINUE RUN** restores any of them in either interface.
- **Slot Archive Management**: Manual checkpoints can be named up to 32 characters, renamed in place without changing their progress or timestamp, or deleted individually after confirmation. Deleting a checkpoint never touches the live run; the autosave checkpoint regenerates on the next state change.
- **Autosave by State Change**: A signature of run state, deck, node status and pending puzzles triggers one autosave per real change, so a crash or closed browser never costs more than the last action. New runs and freshly loaded slots are baselined first, so autosave never overwrites another run's checkpoint just because a page opened.
- **Run-Scoped Settlement Purge**: Every save carries a run identity. When a run settles, only that run's owned checkpoints and its autosave are removed; saves from other runs, or a save this interface never touched, survive. A finished run cannot be saved or replayed from its own checkpoints.
- **Power-Loss Safe Savegames & Shadow Backup**: Uses atomic temporary file writes, `fsync`, `.bak` shadow recovery, and corruption quarantine to eliminate state loss risk. A primary is verified as JSON before it refreshes the shadow backup, so a corrupt save can never overwrite the last good recovery copy; non-finite timestamps and career values fall back or are dropped instead of crashing the archive.
- **Dead Man's Switch**: The Black Market sells a 150 CR one-use failsafe. If trace reaches 100%, it banks 50% of the current unbanked loot before the ICE clears the rest and then expires. It is per-run, persists in saves, and is deliberately excluded from permanent career upgrades.
- **Rival Netrunner**: Every run seeds a named rival (Vex, Marrow or Static) who works the same Syndicate board. On a scheduled turn they snatch a posted contract, post a news headline, and reschedule; an empty board makes them probe your link for trace instead. `counter_rival` burns 2 CPU to delay their next move by 5 turns. The Web HUD shows the rival chip and a rail modal with the same counter action; the rival persists through saves and old saves backfill one deterministically.
- **Deterministic Save Integrity**: The reward RNG state and in-progress puzzle attempts/near-miss state are persisted, so save/load continues the exact seeded sequence instead of rerolling rewards or resetting attempts. Legacy saves without these fields fall back to the prior reseed behavior.
- **Deterministic Run Settlement**: Victory and `jackout` both bank all unbanked loot; trace lockout records a failed run. CLI and Web Cyberdeck share the same one-shot career lifecycle, so rewards are never double-counted or silently lost.
- **Persistent Puzzle Attempts & Consequential Failure**: Reopening a node resumes its remaining attempts, including across save/load, instead of granting a free retry. A fully burned script adds escalating trace, breaks the combo, raises host EDR alert, and seals the host for two turns (`HOST LOCKDOWN`), so the next attempt must wait for the grid to move or target another host.
- **Story, Quests & Operatives Persist**: Story act, log, quest progress, contact trust, and spent favors are stored in the savegame and backfilled for pre-story saves.
- **Run Legacy & Epilogues**: Victory, jackout, and lockout produce a run summary with quest/contact progress, best combo, and a story epilogue shown in both CLI and Web. Career dossiers record the highest combo across runs.
- **Career Run Archive**: Every settled run appends a bounded record to the career dossier with its outcome, seed, turns, banked credits, net gain, best combo, story act, quest count, contract completion and finish time. The terminal shows the last five runs and the Web dossier shows the last six, so the RUN LEGACY moment survives into the next session and different seeds are easy to compare.
- **Transparent Run Score & Hall of Fame**: Settlement scores each run from net credits, combo, quests, breaches, contract completion, outcome and story progress, then records the itemized breakdown. The top ten scores are deduplicated by run id and kept in the career Hall of Fame; the run legacy shows the score and rank, while both dossiers show the leaderboard. The board filters by difficulty (`hall [all|easy|normal|hard]` or Web ALL/EASY/NORMAL/HARD controls), so cross-mode scores are never presented as directly comparable; legacy entries count as Normal.
- **Career Milestones**: Sixteen permanent achievements are evaluated once at settlement: first extraction, five clears, x5/x10 combos, ghost and speed victories, a black contract, three vaults, 50 turns, 1,000 banked credits, a hot extraction, reaching Act V, a Hard clear, 7- and 30-day daily streaks, and 10 points with either faction. New unlocks appear in the run legacy and persist as dossier badges in both interfaces.
- **Difficulty Modes**: Easy grants +2 max CPU, -20% trace gain and +10% contract pay; Normal is the baseline; Hard starts at +15 grid alert with +20% trace gain and -10% contract pay. The choice persists in saves and run history, is selectable with `--difficulty` or the Web main-menu picker, and is shown in both HUDs.
- **First-Run Field Manual**: Careers with no settled runs get a live five-step checklist for `scan`, `probe`, `hack`, `steal` and `jackout`. The terminal exposes it as `tutorial`; the Web shows a dismissible panel that checks steps off from persisted state. Established careers never see it.
- **Career Alias & Preferences**: `alias <name>` sets the dossier handle (trimmed, capped at 24 characters); the Web dossier offers the same editor through `rename_alias`. The Web remembers theme, audio and CRT settings in local storage, and a `prefers-reduced-motion` stylesheet path disables non-essential animation for users who request it.
- **Faction Standing**: Completed Syndicate contracts add +2 Syndicate standing; every victory or jackout adds +1 Street. Standing snaps to the run at start, caps at 100, and pays 1% contract bonus per Syndicate point (max +20%) or 1% Black Market discount per Street point (max 15%). Standings persist in the career dossier, never decay, and apply only to future runs. The run-start snapshot is stored in savegames, so loading a checkpoint keeps its original bonuses even if the career changes later.
- **Faction Ranks**: Syndicate standing advances Associate → Fixer (10) → Broker (25) → Kingpin (50); Street advances Lookout → Runner (10) → Ghost (25) → Legend (50). Crossing a threshold awards a one-time 100/250/500 CR promotion bonus, records the promotion in the run legacy, and shows the rank in both dossiers.
- **Faction Allegiance**: Choose Independent, Syndicate or Street at run start (`--allegiance`, Web selector). Syndicate patrons get +10% contract pay and +1 extra Syndicate standing per completed contract; Street patrons get +5% Black Market discount and +1 extra Street standing per victory/jackout. Allegiance persists in saves/history and never overrides the standing snapshot.
- **Paid Contract Reroll**: `reroll` or the Web contract-card button spends 50 CR to replace the posted board with fresh offers. The active contract is excluded, and an empty candidate pool leaves the old board untouched without charging.
- **Guarded Career Reset**: `reset_career CONFIRM` or the Web career button (type RESET) writes `career.backup.json` before deleting the profile and every save slot, then starts a fresh run. Refusal paths leave all progress untouched, and a failed backup write aborts the reset before anything is deleted.
- **Daily Run**: The local date derives a stable seed (`YYYYMMDD`) and key at run start, available from `--daily`, main-menu option 7, or the Web **DAILY RUN** button. The key persists in saves, appears as a HUD chip and run-legacy tag, and settlement records the day's best net gain (capped to 30 days) in the career dossier. Consecutive daily runs build a streak (same-day repeats do not increment; gaps reset it), shown with the all-time best in both dossiers and the Web HUD chip. Old saves and careers default to no daily mode.
- **Daily Rule Modifiers**: The date also selects one deterministic twist from Hot Grid (+20 starting alert), Blackout (-2 starting CPU), Thin ICE (+15% trace) or Data Bloom (+20% contract pay). The modifier is selected once at run start, persists through saves, appears in the HUD/run summary, and never applies to normal seeded runs.
- **Seed Replay**: The last five archived runs are indexed newest-first in the terminal, so `replay 1` starts a fresh run from that record's seed with current career upgrades; the Web dossier offers a **REPLAY** button per run with confirmation. Replays are normal runs, not daily runs, so they never rewrite a historical daily best.
- **Branching Alliance**: The Act III Agent Zero choice is persisted in the savegame and changes trust, rewards, dialogue, and the epilogue; old saves default to no choice.
- **Same-Origin Web Cyberdeck**: The REST API sends no wildcard CORS grant and serializes state mutations, keeping the local game session private to its own page.
- **Dynamic Resource Loop**: Turn-based CPU cooling (+1/turn) and hardware RAM constraints (`security_level * 16` MB).
- **Living Grid Simulation**: Every turn advances a 15-minute in-game clock, drifts the black-market index (0.80x-1.35x, applied to shop prices and to the fence payout of stolen data), and cools or sustains the corporate alert level from your current trace.
- **Living Syndicate Contract Market**: Three rotating offers name a host/objective (`breach`, `extract`, `wipe`) with standard/priority/black risk, scaled pay and trace limits, an acceptance deadline, and a rush window. Exhausted grids post repeatable recon sweeps. Giver trust improves terms; missed deadlines cost trust and raise alert.
- **Reactive Corporate Response**: Alert 50%+ enables NetWatch patrol trace and sysadmin re-securing of breached hosts (12-turn cooldown, one host per turn, never your current host or the Nexus core); re-secured hosts restore their defenses and quarantine embedded daemons.
- **Corporate Posture Escalation**: The grid reports named postures (GREEN/AMBER/RED/BLACK). Breached hosts slow alert decay by up to 3/turn, and posture transitions post news bulletins reflecting city escalation.
- **Anti-Farm Breach Ledger**: A re-secured host pays no second reward, combo, or quest credit, so grid healing cannot be farmed for infinite credits.
- **Deterministic World Events**: Ambient events, headlines, and re-secure rolls use a per-tick RNG stream from `(seed, tick, stream)` for reproducible gameplay outcomes.
- **Backward-Compatible World State**: Old saves without a world clock load with a fresh Day 1 world; the new fields are additive and atomic with the existing savegame.
- **NetWatch Active Hunters & Pursuit Simulation**: Alert 60%+ mobilizes autonomous ICE hunters that track player location across network graph hops, trigger connection clashes on interception (+15% trace, -2 CPU), quarantine unmonitored daemons, and react to scent scrambling (`spoof`/`wipe_logs`) and countermeasures (`logic_bomb`/`ghost_protocol`). Only one hunter can hold the sector at a time; an intercepted hunter still counts as active, preventing a second clamp from stacking onto the first.
- **Tactical Shift Dynamics & Downtime**: The four in-game shifts (Late Night, Morning, Afternoon, Evening) apply distinct modifiers to alert decay, re-secure chance, market bias, hunter deployment thresholds, and social-engineering odds (staff answer lures differently at 03:00 than at 09:00), so the clock carries real tactical weight. `lay_low`/`wait` trades 1-3 turns of grid movement (with its patrol, hunter, and ambient risk) for CPU recovery, exposed in both the CLI and the Web Cyberdeck shift chip.
- **Fast Test Shield**: 100% test pass rate across 449 unit and integration tests in about eight seconds via `python -m unittest discover`.

<!-- aegean:brand-assets:start -->
## 🎨 Brand Assets

> **AI-Generated Brand Artwork.** The banner and logo are **AI-generated brand assets**. They are illustrative and may not literally depict every feature or the full project scope.
<!-- aegean:brand-assets:end -->

## 📜 License

Free for personal play under the Aegean Game License 1.1 (AGL-1.1); see [LICENSE](LICENSE). It is DRM-free: Licensor ships no DRM and a distributor may not add it. Streaming, modding and free mods are allowed. Commercial use, paid mods and AI training need the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).

<!-- aegean:screenshots:start -->
## Screenshots

<a href="https://github.com/AegeanWorks/Cyberpulse/commit/1215870"><img src="assets/screenshots/2026-10-28-index.png" alt="Cyberpulse interface at 2026-10-28"></a>

*commit `1215870` · 2026-10-28*
<!-- aegean:screenshots:end -->
