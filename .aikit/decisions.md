# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Architecture, Game State Machine, and Zero-Dependency Engine for CyberPulse
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players and AI agents need a compelling, deterministic retro-cyberpunk terminal hacking simulation game that runs instantly on any terminal without external dependencies, supports saved state, and provides sub-second automated test verification.
- **Decision**: Build CyberPulse using pure Python 3 standard library. Structure it into modular domain models (`Node`, `Deck`, `Exploit`, `NetworkGrid`), an engine with deterministic state transitions and seed support, an atomic save/load manager, interactive hacking puzzles (frequency alignment, code sequence matching, hash cracking), and an ANSI-powered interactive CLI.
- **Consequences**: Zero external package installation overhead on Python 3.10+. Game mechanics are fully reproducible with fixed random seeds for automated test suites.

### ADR-002: Behavioral Psychology & Addiction Loop Mechanics: Variable Rewards, Near-Miss Feedback, Loss Aversion, and Meta-Progression
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Literature on human gaming behavior and engagement (Ryan, Rigby & Przybylski's Self-Determination Theory PENS model; Skinner's variable-ratio reinforcement schedules; Clark et al.'s near-miss striatal activation; Kahneman & Tversky's loss aversion and prospect theory; and Csikszentmihalyi's flow channel) proves that games become intensely engaging when they combine autonomy, competence scaffolding, unpredictable reward magnitude, near-miss tension, and push-your-luck risk/reward decisions. CyberPulse v0.1.0 had deterministic rewards and binary outcomes without persistent progression or risk-hedging.
- **Decision**: Introduce five evidence-based behavioral mechanics into CyberPulse:
  1. *Compulsion Loop & Black Market Shop*: A core loop of Action (node hack) -> Variable Reward -> Deck Customization (spending CryptoCreds on permanent hardware upgrades: CPU overclock, RAM modules, ICE dampeners).
  2. *Variable-Ratio Reward Schedules (Skinner/Schultz)*: Node breaches yield variable payouts: Standard (70%), Critical Data Jackpot (20% with 2.5x payout), or Hardware Chip Drop (10%).
  3. *Loss Aversion & Push-Your-Luck (Prospect Theory)*: Players can `jackout` from any breached node to safely bank stolen creds into their persistent career ledger. Reaching 100% trace burns unbanked loot from the current run.
  4. *Near-Miss Feedback Engine (Clark et al.)*: In puzzles and trace thresholds, generate high-arousal near-miss signals (e.g. "NEAR MISS! Resonance aligned within 0.1 GHz" or "CRITICAL TRACE WARNING: 85%").
  5. *Persistent Career Meta-Progression & Syndicate Contracts (Zeigarnik Effect)*: Career stats, rank, and bounty contracts tracked in `.cyberpulse/career.json`.
- **Consequences**: Deepens tactical decision-making and intrinsic motivation (competence and autonomy), while creating thrilling dopamine anticipation loops without manipulative paywalls or external dependencies.

### ADR-003: Operational Gap Remediation: Crash-Safe Shadow Recovery, Career Synchronization, Dynamic CPU/RAM Constraints, and Usable Exploit Chips
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: A comprehensive codebase audit revealed several architectural gaps and usability weaknesses:
  1. `cyberpulse/shop.py` used `Optional` in type annotations without importing it from `typing`, triggering `NameError` on Python 3.14 PEP 649 annotation evaluation.
  2. `cyberpulse/storage.py` created `.bak` backups during atomic writes, but failed to fall back to `.bak` when reading a corrupted `savegame.json` or `career.json`, risking total loss of player meta-progression.
  3. `cyberpulse/cli.py` initialized `GameEngine` with default deck stats (100 creds, 0 upgrades), failing to apply persistent upgrades and banked credits from `career.json` to the player's active deck.
  4. CPU cycles never regenerated across moves or turns, permanently disabling the `spoof` command after 3 uses.
  5. Cyberdeck RAM capacity (`ram_mb`) and shop RAM upgrades were never checked or consumed by any game action or puzzle.
  6. Exploit chips (`logic_bomb`, `ghost_protocol`, `brute_miner`) dropped as loot or purchased in the shop were inert with no activation mechanism.
  7. Only a single static syndicate contract was issued with no replenishment.
- **Decision**: Remediate all gaps systematically:
  1. Fix typing import in `shop.py` and verify annotation evaluation across all modules.
  2. Implement automatic `.bak` recovery with corruption quarantine in `storage.py`.
  3. Introduce `apply_career_profile(deck, profile)` and synchronize deck/career credits across runs.
  4. Implement turn-based CPU cycle regeneration (+1 per move/turn up to `max_cpu`).
  5. Enforce RAM buffer capacity requirements for high-tier node intrusions (`node.security_level * 16` MB).
  6. Implement an active `exploit <name> [target]` system allowing players to deploy chips tactically.
  7. Dynamically dispatch new syndicate bounty contracts upon contract fulfillment.
- **Consequences**: Closes all meta-progression and resource disconnects, elevates player agency and tactical depth, guarantees zero-data-loss power-loss resilience, and maintains 100% test pass rate in sub-second execution with zero external dependencies.

### ADR-004: Zero-Dependency Web Cyberdeck Interface with Interactive Matrix Canvas and Web Audio Synthesizer
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players seeking maximum immersion benefit from rich visual and auditory feedback (retro CRT phosphor scanlines, real-time node matrix topology visualization, interactive waveform oscilloscopes, and responsive audio feedback). External web frameworks or heavy dependencies (Flask, FastAPI, npm packages) violate AIKit's zero-friction onboarding and standard-library-only constraints (PRINCIPLE-011).
- **Decision**: Build a zero-dependency Web Cyberdeck Interface:
  1. *Backend*: Lightweight Python standard library HTTP server (`http.server.ThreadingHTTPServer`) exposing JSON REST APIs (`/api/state`, `/api/action`, `/api/shop`, `/api/career`, `/api/puzzle`).
  2. *Frontend*: Pure Vanilla HTML5, CSS3, and JavaScript served directly from `cyberpulse/static/`.
  3. *Visual Design*: Retro CRT aesthetic (phosphor green, cyber-cyan, amber alert themes), glassmorphic telemetry panels, scanlines, and animated HUD meters.
  4. *Cyberspace Node Matrix Canvas*: Real-time interactive 2D canvas visualizing network topology, node statuses (`LOCKED`, `DISCOVERED`, `BREACHED`), and pulsing connection vectors.
  5. *Web Audio API Synthesizer*: Native in-browser algorithmic sound engine (zero audio asset downloads), synthesizing retro terminal beeps, modem handshake hums, near-miss heartbeats, and victory fanfare.
- **Consequences**: Delivers a rich, cinematic audiovisual experience accessible in any modern browser via `python -m cyberpulse.cli --web` without installing any third-party packages or node modules.

### ADR-005: Authentic Hacker Simulation Pivot: Realistic IP Networking, Port Exploitation, Virtual Filesystems, and Data Theft Contracts
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Player feedback revealed that abstract math/puzzle mini-games (frequency tuning, hex matching, hash ciphers) created high cognitive friction and felt alienating rather than immersive ("Gaming is too complex and hard to get inside"). Players desire an authentic, immersive hacker simulation grounded in realistic networking concepts (IP addresses, open service ports, vulnerability exploitation, file browsing, data theft, and log scrubbing) inspired by genre classics like *Uplink* and *Hacknet*.
- **Decision**: Pivot CyberPulse into an authentic hacker simulation:
  1. *IP-Based Network Architecture*: Hosts have realistic IPv4 addresses (`192.168.1.1`, `10.0.4.15`, `172.16.80.1`), hostnames, subnet topology, and network gateways.
  2. *Port & Service Vulnerability Model*: Hosts expose standard network ports (SSH:22, HTTP:80, FTP:21, SQL:3306, SMTP:25). Players use `probe <ip>` to scan ports and deploy targeted exploits (`exploit <ip> <port>`) to obtain root shell access.
  3. *Virtual Filesystem & Data Theft*: Breached hosts provide realistic directory structures (`/bin`, `/etc`, `/var/log`, `/home/corporate/`). Players explore with `ls`, inspect with `cat <file>`, exfiltrate high-value files with `download <file>` / `steal <file>`, and cover tracks with `wipe_logs`.
  4. *Espionage & Data Theft Mission Contracts*: Syndicate contracts provide narrative corporate espionage objectives (e.g. steal employee payroll, exfiltrate AI weights, or erase audit logs) with cash payouts upon safe extraction.
- **Consequences**: Replaces arbitrary abstract mini-games with intuitive, natural, and compelling hacker simulation mechanics that players instantly understand and enjoy, while maintaining pure Python standard library zero-dependency guarantees.

### ADR-006: Virtual Netrunner Rig, Malware Workshop Crafting, Phishing Infiltration, and Background Daemon Exploits
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players requested expanding the simulation with their own personal cyberdeck computer identity ("Our Computer Files", "Our IP"), social engineering vectors (phishing attacks to harvest credentials), custom virus/payload synthesis in a netrunner workshop, and background persistence tools (keylogger daemons).
- **Decision**: Introduce synthetic in-game mechanics within CyberPulse:
  1. *Virtual Localhost Rig*: CyberDeck maintains its own virtual host identity (`127.0.0.1` / `10.99.0.2`, hostname `rig.netrunner.local`) and persistent local filesystem (`/home/deck/`, `/loot/`, `/tools/`). Stolen exfiltrated files are archived into the player's local loot drive.
  2. *In-Game Social Engineering (Phishing Dispatch)*: Players can dispatch simulated spear-phishing campaigns (`phish <ip>`) targeting employee credentials, which bypasses port firewalls on success to leak credentials or reduce security tiers.
  3. *In-Game Malware Crafting Workshop*: A modular virus synthesis bay (`craft` / `workshop`) allows assembling custom in-game payload scripts by combining injection vectors (e.g. stealth, brute, worm replication) and payloads (credit siphon, trace dampening, credential scrapers).
  4. *In-Game Background Keylogger Daemons*: Deploy in-game background listener scripts (`deploy_keylogger <ip>`) onto compromised remote hosts to passively harvest unbanked credits turn-by-turn until scrubbed or detected.
  5. *Strict Synthetic Sandbox Isolation*: All files, IPs, and payloads are strictly simulated in-memory Python dataclasses; no real-world host files, network sockets, or external systems are ever accessed.
- **Consequences**: Deepens tactical variety, strategic pre-planning, and immersion while maintaining pure Python 3 standard library zero-dependency constraints and sub-second test execution.

### ADR-007: Tactical Exploits, Host Antivirus Detection, Network Firewalls, and Multi-Vector Social Engineering
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players requested deeper tactical cyber-warfare layers: "Add Exploits, Add Antivirus Mechanics, Add Firewalls, Add Social Engineering Component to the GAME". Straightforward open-port zero-days and single-tier phishing need to evolve into an interlocking tactical system featuring stateful network firewalls, active host antivirus heuristics and daemon quarantine sweeps, a diverse catalog of specialized exploit CVE payloads, and interactive multi-vector social engineering campaigns (pretexting IT support, baiting USB drops, executive impersonation).
- **Decision**: Introduce four interlocking tactical simulation systems:
  1. *Network Firewalls (`FirewallRule`, `HostFirewall`)*:
     - Hosts can run active packet-filtering firewalls with rules (`DEFAULT_DROP`, `PORT_FILTER`, `STATEFUL_IDS`).
     - Ports can be `FILTERED` by firewalls, preventing direct exploitation unless bypassed or knocked.
     - Mechanics: `firewall <ip>` to inspect rules, `bypass <ip> [method]` via port knocking, packet fragmentation, or proxy tunneling.
  2. *Host Antivirus Systems (`HostAntivirus`, `AVStatus`)*:
     - Target hosts (especially Tier 2+ enterprise nodes) run active Antivirus suites (e.g. *SentinelCore*, *AegisShield*, *CyberDefender*).
     - AV maintains an `alert_level` (0 to 100%) and runs periodic memory heuristic scans.
     - If alert level exceeds threshold, AV quarantines/kills active background daemons (`keyloggers`, `worms`) and triggers an immediate spike in ICE trace.
     - Mechanics: `av <ip>` to inspect AV status, `evade <ip>` / `kill_av <ip>` to inject rootkit evasion hooks or suppress AV processes.
  3. *Expanded Exploit Payload Matrix (`ExploitPayload`, `CVE`)*:
     - Players discover and weaponize specific vulnerability CVEs (`CVE-2024-SHELLSHOCK`, `CVE-2023-MEMCORRUPT`, `CVE-2025-SQLINJECT`, `CVE-2024-BUFFERLEAK`).
     - Each exploit payload has specific RAM requirements, target service affinities, stealth ratings (affecting AV detection), and payload yields.
     - Commands: `cve` / `exploits` to view catalog, `exploit <ip> <port> [cve_id]` to select matched exploit payloads.
  4. *Multi-Vector Social Engineering Component (`SocialVector`, `EmployeeProfile`)*:
     - Expands beyond basic phishing into multi-vector social engineering:
       - `pretext`: Masquerading as internal IT support requesting emergency access.
       - `bait`: Dropping infected simulated USB drives / payload PDFs.
       - `spear_phish`: Executive CEO fraud urgent wire / credential lure.
       - `vishing`: Voice-phishing helpdesk operator for MFA token bypass.
     - Hosts feature dynamic employee security awareness profiles (Naive, Standard, Paranoid).
     - Commands: `social <ip> [vector]` (e.g. `social 192.168.1.10 pretext`).
  5. *Zero External Dependencies & Synthetic Invariant*:
     - 100% in-memory standard library dataclasses, deterministic RNG generation, zero external pip dependencies, sub-second test execution.
- **Consequences**: Deepens the hacker simulation with strategic counters (Firewalls block ports -> require Bypass or Social Eng; Antivirus hunts Keyloggers -> requires Evade or Rootkit; CVEs give tactical choices).

### ADR-008: System-Wide Engine Hardening, Full CVE Network Matrix, CLI Completion Lifecycle, and Probed Port HUD
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: A holistic audit across `cyberpulse` identified several gaps, edge-case risks, and user-experience opportunities:
  1. Several engine methods (`spoof_ip`, `scan_surroundings`, `use_exploit`, `list_files`, `read_file`, `craft_virus`) lacked `is_game_over` / `is_jacked_out` guards, allowing operations to execute after terminal disconnect or trace lockout.
  2. Engine string parameters (e.g. `exploit_name`, `recipe_name`, `query`, `method`, `filepath`) lacked defensive `None`/type coercion, risking `AttributeError` on malformed API payloads or empty CLI inputs.
  3. Turn progression was inconsistent: `exploit_service` did not advance `turns_elapsed` or tick daemons, and `SaveManager.load()` did not re-seed the engine RNG with turn offset.
  4. The CVE exploit catalog had gaps: `CyberDeck.known_cves` referenced `CVE-2025-9901` which was missing from `KNOWN_CVES`, and no CVEs existed for `https` or the AI Supercore.
  5. The CLI batch execution mode (`--exec`) bypassed career completion hooks upon victory/game-over.
  6. The Web Cyberdeck only rendered open ports when a host was already breached; probing an unbreached host only logged text into the terminal, missing an opportunity for interactive visual port exploration and direct exploit/bypass buttons.
- **Decision**:
  1. Add universal session state checks (`is_game_over`, `is_jacked_out`) and defensive string sanitization across all engine methods.
  2. Implement turn progression and daemon ticks in `exploit_service`, and ensure RNG persistence determinism on save load.
  3. Expand `KNOWN_CVES` to include `CVE-2025-9901` (Project Omega Neural Core Deserialization RCE, target_service: `"any"`) and `CVE-2022-0778` (OpenSSL BN_mod_sqrt loop on `"https"`), aligning with `CyberDeck.known_cves`.
  4. Unify CLI run completion logic (`handle_run_completion`) across interactive and batch modes.
  5. Add visual Probed Ports Subsystem, keyboard shortcuts, and interactive exploit selectors in Web Cyberdeck UI.
- **Consequences**: Hardens system integrity, eliminates runtime exceptions, provides complete CVE network coverage, and delivers an enriched, seamless hacker simulation experience.


### ADR-009: Post-Review Defect Remediation: Command Dispatch, Static Containment, Save Honesty, Career Accounting, and Offline Assets
- **Date**: 2026-10-18
- **Status**: Accepted
- **Context**: An independent review of the shipped game confirmed several user-facing defects: the `buy` branch never returned, so every purchase printed "Unknown command: 'buy'"; `serve_static` joined raw request paths onto the static root, allowing `../` path traversal (arbitrary local file read); numeric ports from CLI and REST input were parsed with a bare `int()` (ValueError tracebacks in the REPL and dropped connections from the API); a piped batch run tracebacked when a minigame read EOF; `_write_atomic` returned the target path after five failed replaces, so the CLI printed "progress saved" although nothing landed; every jackout added the entire wallet to `lifetime_creds`, double-counting the previously banked credits (fresh career starts at 100/100); the Web Cyberdeck workshop posted a nonexistent `recipe.recipe_id`, so every browser craft failed with "Unknown recipe ''"; the UI advertised wrong bypass CPU/trace costs; and two static assets loaded Google Fonts.
- **Decision**: Return `True` after a handled `buy`; resolve static requests and reject paths outside the static root via `is_relative_to`; parse ports inside try/except (the REST API answers 400 `{"ok": false, "error": ...}`, the CLI prints a usage line); catch `EOFError` in the batch loop and stop the batch gracefully; make `_write_atomic` return `Optional[Path]`, create temp files with `tempfile.mkstemp` (cleaned in a `finally`), and have the CLI report an unpersisted save instead of claiming success; compute `gained = max(0, deck + unbanked - banked_before)` on jackout and victory paths (CLI and REST) and add only that to `lifetime_creds`; send `recipe.name` from the workshop client and render `[vector]` in the card; align the Web UI bypass cost labels with the engine's cost table; drop the Google Fonts links and extend the CSS font variables with local fallbacks.
- **Consequences**: Purchases and browser crafting work, the web server cannot read files outside its static root, malformed input yields messages instead of tracebacks, saves never claim false success, `lifetime_creds` grows by the run's net gain over the starting bank instead of re-counting banked credits, and the UI renders fully offline. Test suite: 94 tests, 100% green in about a second.

### ADR-010: Run-State Coherence: Idempotent Breaches, Persistent Puzzles, One-Shot Settlement, and Session Hardening
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: A second coherence audit found several state-lifecycle defects that survived the earlier reviews: `complete_breach` and `worm_replicator` could re-award a node already breached; `spoof_ip` always reported a 25% reduction even near zero; daemons kept harvesting after a trace lockout; `bypass_firewall`, `evade_antivirus`, and social engineering accepted targets outside the direct subnet; reopening a CLI/Web puzzle regenerated its attempts; the CLI victory path counted unbanked loot in `lifetime_creds` but never added it to the bank; the Web session settled only on jackout, not on victory or lockout; workshop affordability ignored banked credits; `wipe_logs` could be repeated for free trace loss; the initial extraction contract completed on a bare breach; the API sent wildcard CORS; a non-integer reset seed crashed the server; request bodies and JSON types were unvalidated; and shared session state was mutated concurrently by `ThreadingHTTPServer`.
- **Decision**:
  1. Make `complete_breach` reject terminal runs and already-breached nodes, clear any pending puzzle, and award rewards exactly once; require extraction contracts (target file/IP/log wipe) to complete through `download_file` plus `wipe_logs`, while simple sector contracts still complete on breach.
  2. Persist one puzzle instance per node in `GameEngine.pending_puzzles`; CLI and REST resume remaining attempts and clear the entry on solve or exhaustion.
  3. Add `GameEngine.settle_career` as the single one-shot run lifecycle used by CLI and Web: victory and jackout bank unbanked loot, lockout records a failure, and `lifetime_creds` grows only by net gain. Crafting and purchases persist banked spending immediately.
  4. Guard daemon ticks, spoof reporting, wipe idempotence, and subnet reachability; advance daemon ticks for probes and log wipes.
  5. Remove wildcard CORS, serialize state mutation with a session lock, validate body size/type and seeds (including float seeds), cap request bodies, read request bodies and serve static assets outside the lock, and keep the API same-origin.
  6. Fix Web workshop affordability to use banked plus unbanked credits and make port-card bypass buttons target the selected port.
  7. Do not delete a savegame from the Web session; it never loads one, so terminal Web runs must not destroy a CLI-owned save. Enforce the same terminal-state guards on every CLI-reachable mutating action and stop batch execution at victory/lockout.
- **Consequences**: Rewards and career totals are truthful and idempotent; puzzle retries cost their remaining attempts; runs settle once across both interfaces; Web state is race-free and not readable by cross-site scripts; slow clients and static assets cannot hold the state lock; malformed input cannot crash the server or delete unrelated saves. Test suite: 119 tests, 100% green in about a second.

### ADR-011: Story Campaign, Operative Relationships, Quest Board, and Combo/Overdrive Loop
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: CyberPulse had a strong tactical loop but no main menu, no narrative framing, no persistent goals beyond random contracts, no characters to interact with, and no moment-to-moment reward escalation. The Web and CLI also started abruptly, which made the game harder to onboard and gave the world no context.
- **Decision**:
  1. Add a CLI main menu (new run, continue, story briefing, operatives, career, help) and a Web main-menu overlay with the same entry points.
  2. Add a five-act story campaign in `story.py`: Gateway, Money, Black ICE, Nexus Protocol, Zero Day. Story acts advance when main quests complete; story log seed lines and act titles are persisted.
  3. Add persistent `Quest` and `ContactProfile` models on `GameState`. Seven quests cover main story and side objectives (breach types, file theft, log wipes, crafting, daemon deployment). Main quests auto-accept on act unlock; side quests are accepted through contacts or the mission board.
  4. Add four operatives (Mira, Kilo, The Archivist, Agent Zero) with act-gated dialogue, trust, jobs, and one-time favors that reduce trace, restore CPU, reveal a locked node, or grant a chip.
  5. Add combo-streak rewards (up to +50% breach bonus) and `overdrive` (2 CPU + 8% trace for +1 combo and +10 unbanked credits), with combo reset on lockout.
  6. Expose story, quests, contacts, overdrive, contacts/interaction, and quest acceptance through the REST API and the Web CRT UI; keep CLI and Web behavior aligned.
  7. Backfill story state in `SaveManager.load` for saves created before this feature, and persist all new fields atomically with the existing savegame.
- **Consequences**: Players get a clear entry point, a narrative campaign, relationship-driven side content, and a risk/reward combo loop. Existing commands and saves remain compatible; the CLI/Web schemas grow additively. Test suite: 138 tests, 100% green.

### ADR-012: Endgame Legacy Summary, Story Epilogues, and Career Best Combo
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: The story, quest, contact, and combo systems ended abruptly. Terminal runs showed a generic banner, combo skill was not recorded in the career dossier, and operative relationships never paid off after the run ended.
- **Decision**:
  1. Add `run_summary()` to the engine, deriving outcome, best combo, quest completion, unlocked operatives, and an epilogue from existing run state.
  2. Add outcome, contact, and combo epilogue data in `story.py`; epilogues reflect victory/jackout/lockout, trust or favors spent, and combo milestones.
  3. Add `best_combo` to `CareerProfile` with a default, update it on every settlement (including failures), and show it in the CLI dossier and Web career modal.
  4. Include `run_summary` in `/api/state`; print the legacy block in CLI completion/jackout and show epilogue plus run stats in the Web victory/lockout banner.
  5. Keep old saves compatible: missing `best_combo` defaults to 0 and story state is backfilled on load.
- **Consequences**: Runs now end with narrative and statistical closure, combo mastery persists across the career, and operative relationships visibly affect the epilogue. Test suite: 143 tests, 100% green.

### ADR-013: Act III Alliance Choice and Branching Operative Consequences
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: Operative interactions changed trust and rewards but never branched the story or ending. Agent Zero was introduced as a rival with no meaningful decision attached, so character relationships were still mostly cosmetic.
- **Decision**:
  1. Add persistent `GameState.story_choice` with an empty default for backward compatibility.
  2. Offer a one-time Act III choice when Agent Zero is unlocked: ally (`zero_ally`) or defy (`zero_defy`).
  3. Ally grants Zero trust and a ghost_protocol chip (or 150 unbanked credits if already owned); defy grants Mira trust and 150 unbanked credits.
  4. Add choice-specific dialogue for Acts III/IV/V, a locked-choice label in the story payload, and choice-specific epilogue lines.
  5. Expose the choice through the same `contact` mode on CLI and REST; the Web contacts modal shows ALLY/DEFY controls only when the pact is available.
- **Consequences**: The story now has a consequential character branch that changes relationships, rewards, late dialogue, and the ending. The choice is persisted and old saves remain valid. Test suite: 148 tests, 100% green.

### ADR-014: Order-Robust Story Progression, Settled-Run Guards, and the Act IV Core Seal
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: A hardening audit of the story campaign found three coherence defects. One-shot story objectives only counted while their quest was accepted: breaching Black ICE before Act III made `q_blackice` impossible (the node cannot be breached twice) and permanently stalled the campaign, while early target thefts and log wipes were likewise uncounted. `accept_quest` lacked terminal-state guards, so the REST API could accept quests and grant trust after a lockout or jackout. The Nexus supercore could also be breached before Act IV, producing a victory whose run summary reported an incomplete main story.
- **Decision**:
  1. Extract quest completion into `_complete_quest` and reconcile one-shot progress from world state (`_quest_progress_from_state`) whenever a quest is accepted, including auto-accepted main quests; retroactive progress can complete a quest and advance the act chain immediately.
  2. Guard `accept_quest` against lockout, jackout, and victory like every other mutating action.
  3. Seal the central core until Act IV in `can_hack_node`, `complete_breach`, and `exploit_service`, so the node refuses even a direct engine call and no CPU or trace is paid.
  4. Correct the README claim about save continuation in the Web main menu and add `ally | defy` to the CLI contact usage line.
- **Consequences**: Any exploration order can complete the campaign; one-shot objectives credit events that already happened; settled runs cannot mutate; the final breach is consistent with the narrative. No save schema changed and old saves remain valid. Test suite: 154 tests, 100% green.

### ADR-015: Living-Grid Simulation: Clock, Corporate Alert, Generated News, Ambient Events, Host Re-Securing, and Market Drift
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: The grid outside the player's current node was static. Turns advanced only to tick daemons, hosts never reacted to loud intrusions, black-market prices never moved, and nothing inside or outside the game reported on the player's actions. Requested behavior: more simulation-like mechanics, so the world reads as running on its own rather than waiting for input.
- **Decision**:
  1. Add `WorldState` (minute, day, alert level, market index, events cooldown, re-secured count, news feed) and `NewsItem` to `state` with defaults; backfill missing world state for old saves in `GameState.from_dict`.
  2. Add `world.py` as a pure simulation module: clock and shift math, alert clamping, bounded market random-walk, deterministic per-tick ambient events, and grid re-secure planning. World rolls use their own per-tick RNG stream seeded from `(seed, tick, stream)` so the engine's reward RNG sequence, and every existing seeded outcome, is untouched.
  3. Route all nine turn advance sites through `GameEngine.advance_turn()`, which ticks daemons and then the world. Every turn advances a 15-minute clock, drifts the market, decays or sustains alert based on trace, may fire an ambient event, applies NetWatch patrol trace at alert 50/75+, and may re-secure a host.
  4. Make alert actionable: breaches raise it by node security, daemons raise it, extraction cools it, and ambient events can move it. Negative ambient events only enter the pool at alert 35+, so quiet early runs stay fair.
  5. Re-secure rules: alert 50+, 12-turn cooldown since breach, at most one host per turn, never the player's current host or the central core. Re-securing restores ports, firewall, and antivirus, restores wiped logs, recalls embedded daemons, publishes a NetWatch headline, and bumps `resecured_count`.
  6. Add a per-host breach ledger (`breached_turn`, `reward_claimed`): a re-secured host pays no second reward, no combo, and no quest credit when re-breached, closing the farm loop introduced by host healing.
  7. Apply the market index to shop prices through an optional `price_multiplier` (default 1.0), surfaced in CLI shop output, `buy`, `shop_buy`, and `/api/shop`; keep `base_cost` visible.
  8. Surface the grid in both clients: CLI `world`/`news` commands plus a HUD grid line, `GET /api/world`, a `world` block in `/api/state`, and a Web Cyberdeck ticker bar showing clock, shift, alert, market index, and the newest headline.
- **Consequences**: The grid now reacts to player behavior and reports on it, giving loud play visible and mechanical consequences. Save schema changes are additive and old saves load with a fresh day-1 world. Seeded reward determinism is preserved by the separate world RNG stream. Test suite: 189 tests, 100% green.

### ADR-016: NetWatch Counter-Infiltration & Active Hunters: Autonomous Grid Pursuit, Connection Interception, Scent Confusion, and Tactical Countermeasures
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: While the living-grid simulation (ADR-015) introduced corporate alert, news headlines, and sysadmin host re-securing, high corporate alert (60%+) lacked a direct predatory spatial threat navigating the network topology. Players could remain on breached nodes without fear of being tracked down or cornered across subnets, blunting late-game infiltration tension.
- **Decision**:
  1. Add `NetWatchHunter` model (`hunter_id`, `name`, `current_node_id`, `status`, `turns_active`, `target_node_id`, `confused_turns`) and `WorldState.hunters: List[NetWatchHunter]` with default factories and backward-compatible `to_dict`/`from_dict` serialization.
  2. Implement BFS shortest-path graph traversal and hop-distance calculation in `world.py` (`find_shortest_path`, `calculate_distance`).
  3. Deploy active NetWatch hunters (`deploy_hunter`) when `world.alert_level >= 60` from the Nexus Central Core or highest-tier host, broadcasting alert news headlines.
  4. Step hunters turn-by-turn during `tick_world()`: hunters track the player's active subnet along the shortest path. On connection interception (hunter reaches player's current host), trigger an ICE clash (+15% trace spike, -2 CPU cycles drain, news headline). When entering a breached non-player host, hunters quarantine active background daemons.
  5. Scent confusion & countermeasures: `spoof_ip` and `wipe_logs` scramble hunter radar for 2 turns; `counter_hunter` allows netrunners to deploy tactical countermeasures: `logic_bomb` payload neutralizes the hunter, `ghost_protocol` masks signature, sheds 30% trace, and banishes the hunter back to core with 4 confused turns, or 3 CPU cycles can be burned for active jamming.
  6. Surface hunters across both interfaces: CLI `hunter`/`radar` command and HUD proximity warnings (`[⚠️ HUNTER CLOSE: Aegis-1 (1 hop)!]`); Web Cyberdeck ticker chip (`grid-hunter`) and animated pulsing red threat beacon on the 2D network canvas; REST API endpoints and state telemetry (`/api/world`, `/api/state`, `/api/action`).
- **Consequences**: Escalates high-alert gameplay into a thrilling cat-and-mouse spatial chase across subnets, elevating player agency, evasive lateral movement, and countermeasure timing. Additive dataclass defaults preserve full backward compatibility with legacy saves. Test suite: 204 tests, 100% green.

### ADR-017: Shift Dynamics & Downtime: Tactical Shift Profiles, Shift-Aware Grid Modifiers, and the Lay-Low Downtime Action
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The living-grid clock (ADR-015) advanced time and named shifts, but shift names were cosmetic: patrol pressure, re-secure chance, hunter deployment, and market drift behaved identically at 03:00 and 15:00, so the clock carried no tactical weight. Players also had no deliberate way to recover CPU and let a dangerous shift pass without spending trace elsewhere.
- **Decision**:
  1. Add a frozen `ShiftProfile` dataclass and a `SHIFT_PROFILES` registry (`late_night`, `morning`, `afternoon`, `evening`) to `world.py`, with `SHIFT_BOUNDS`, `shift_profile(minute)`, and `shift_effect_text(profile)` rendering its mechanical modifiers; the profile carries `market_bias`, `alert_decay_bonus`, `resecure_chance_delta`, and `hunter_threshold_delta`.
  2. Make each shift tactically legible: quiet nights cool alert faster (`+1/turn`) but re-secure less and push hunters to 70%+, morning audits re-secure aggressively (`+10%`) and discount the market (`-3%`), afternoons are hair-trigger (`-5` hunter threshold, `+5%` re-secure), and evening handovers lag re-secures (`-5%`) while patrols stay wired (`+5` hunter threshold, `+1/turn` alert cool).
  3. Apply the modifiers inside `tick_world`: `drift_market` takes a `bias`, `_decay_alert` takes a `shift_bonus`, `plan_resecures` takes a `chance_delta`, and `deploy_hunter` derives its threshold from `shift_profile(world.minute).hunter_threshold_delta`. All new parameters default to their prior behavior.
  4. Expose `shift_key`, `shift_tagline`, `shift_effect`, and a `shift_modifiers` block from `world_summary`; the shift is derived from `world.minute`, so existing saves need no migration and Morning defaults preserve today's tests.
  5. Add `GameEngine.lay_low(turns=1)` (cap `MAX_LAY_LOW_TURNS = 3`): it rejects terminal runs and non-integer or out-of-range input, then per turn regenerates 1 CPU and calls `advance_turn`, stopping early if the run reaches a terminal state, and reports a before/after summary of CPU, trace, alert, and clock.
  6. Surface downtime and doctrine across both clients: CLI `lay_low`/`wait`/`laylow`/`rest` command with 1-3 turn parsing plus a shift doctrine line in the world panel and HUD; REST has no wildcard grant and routes `lay_low`/`wait` through `POST /api/action`; the Web Cyberdeck gains a `LAY LOW` button with an `[L]` hotkey and a `#grid-shift-effect` chip populated from `world_summary.shift_effect`.
- **Consequences**: The clock becomes a resource: each shift has a distinct tactical identity and `lay_low` lets players trade grid momentum for CPU while accepting patrol, hunter, and ambient risk. The contract grows additively (`world_summary` keys and optional keyword parameters) with no persisted schema change and no disturbance to seeded reward determinism. Test suite: 218 tests, 100% green.

### ADR-018: Living-Grid Momentum & Escalation: Failure-Break Combos, Corporate Alert Tiers, Shift-Aware Social Vectors, Market-Fenced Loot, Host-Scaled Daemons, and Ghost-Cooled Downtime
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: A mechanics audit found the simulation's pressure systems and the push-your-luck loop pulling against each other. The combo streak (ADR-015-era) only reset on a 100% trace lockout, so the reward multiplier was a risk-free ratchet rather than a stake. Alert decay (-2/turn at low trace) outpaced the alert a breach adds (+5..13) over a typical 2-4 turn action cadence, so re-secures (50%+) and hunters (60%+) rarely deployed - two whole systems were dead content in normal play. The shift system (ADR-017) touched alert, market, re-secures, and hunters but not the human layer, so time of day had no bearing on social engineering. The black-market index drifted every turn but only priced shop purchases, never loot income, and daemons paid a flat 25 CR/turn whether planted on a border gateway or the Nexus supercore. Finally, lay_low recovered CPU while the grid moved but offered no trace relief, leaving it dominated by spoof and wipe_logs.
- **Decision**:
  1. Add `GameEngine.break_combo(reason)`: it resets `combo_streak` to 0 (preserving `best_combo`) and logs a COMBO BROKEN line, and is a no-op on an empty streak. Wire it into every detected failure: CLI and Web puzzle exhaustion (frequency, buffer, hash), flagged social-engineering lures, NetWatch hunter clashes, and antivirus daemon quarantines. Successful breaches and `overdrive` still build the streak.
  2. Add `ALERT_TIERS` (GREEN <30, AMBER 30-54, RED 55-74, BLACK 75+), `alert_tier(level)`, and `tier_rank(tier)` to `world.py`; `world_summary` now exposes `alert_tier`, and the CLI status, world panel, and hunter radar plus the Web ticker render it.
  3. Slow alert decay by the live intrusion footprint: `GameEngine._intrusion_footprint()` counts breached non-GATEWAY hosts and `_decay_alert` adds `min(3, footprint // 2)` to the turn delta, so a wide compromised perimeter keeps sysadmins mobilized and hunters on the grid. Posture changes publish news in both directions (`_announce_alert_tier`), with an engine-transient `_last_alert_tier` baseline that is silently resynced in `ensure_story_state()` after a save load.
  4. Add `ShiftProfile.social_delta` (late night -15%, morning +10%, afternoon 0, evening +5%) with `social_shift_modifier(minute)` and `apply_social_shift(chance, minute)` clamping to 5-95%; `social_engineer` reports `shift` and `shift_modifier`, notes the timing in its outcome messages, and `shift_effect_text` lists the social modifier in the doctrine line.
  5. Fence stolen data at the live black-market index: `download_file` captures `market_multiplier(world)` before its turn advance, pays `max(1, round(value_creds * rate))` for valuable files, and reports the fence rate in the exfiltration message.
  6. Scale daemon yield by host tier: `deploy_daemon` sets `yield_per_turn = 15 + security_level * 5` (20-40 CR/turn) and reports the live rate; deep hosts pay more but carry hotter EDR heuristics.
  7. Cool trace during downtime: each `lay_low` turn removes up to `LAY_LOW_TRACE_COOLING = 2` trace before the grid tick, and the summary names the ghost cooling rate.
- **Consequences**: The push-your-luck loop now has stakes on three axes (loot, combo, trace), loud play escalates the city in a legible GREEN-to-BLACK arc, the clock matters for the human layer, looting and daemon placement become timing/placement decisions, and downtime becomes a genuine third trace tool. All changes are additive: no new persisted fields (the tier baseline is engine-transient and load-resynced), seeded reward determinism is untouched, and the market is captured pre-tick. Test suite: 238 tests, 100% green.

### ADR-019: Consequential Failure & Trustworthy Tension: Host Lockdown, Near-Miss Comebacks, Extraction Surge, Deterministic Save Integrity, and Terminal-State Safety
- **Date**: 2026-10-22
- **Status**: Accepted
- **Context**: A follow-up mechanics audit found the risk loop still leaking pressure. A burned hacking puzzle could be reopened immediately for a fresh set of attempts, costing only one trace tick, so failure had no tempo cost and every node was an unlimited free roll. Near-miss feedback (the strongest re-engagement cue) was purely cosmetic, while `add_trace` inflated `near_miss_count` on ordinary 80%+ warnings, corrupting the metric. `jackout` was guaranteed from any breached node, so trace above 60% forced a bank rather than creating a final decision. Save/load reseeded the reward RNG to `seed + turns_elapsed`, rerolling reward outcomes, and pending puzzle attempts were not saved, enabling deterministic save-scumming. Several actions called `advance_turn()` and then continued to award credits, complete contracts, bypass firewalls, or blind EDR after that same tick had already burned the deck. Finally, an intercepted hunter did not block a second deployment, so late runs could stack two permanent clamps and die in one tick.
- **Decision**:
  1. Persist per-host failure state (`Node.failed_attempts`, `Node.lockdown_until_turn`) and add `GameEngine.register_puzzle_failure(node_id, reason)`: each burned script adds escalating trace (`host.trace_rate + 4` per prior failure, capped at 30), raises host EDR alert by 10, breaks the combo, and seals the host for `LOCKDOWN_TURNS = 2` turns. `can_hack_node` and service `exploit_service` refuse locked hosts; `apply_resecure` clears the lockdown. CLI and Web puzzle exhaustion now share this one handler.
  2. Give near misses a capped mechanical payoff: each puzzle tracks `near_miss`/`near_miss_awarded`, exposes `claim_near_miss_bonus()` (one extra tuning/keyword attempt, or one buffer retry), and `GameEngine.resolve_puzzle_near_miss(puzzle)` records the encounter and grants the first bonus with a NEAR-MISS SURGE message. Later near misses still count but grant nothing; the Web buffer bay keeps the puzzle open when the bonus is granted.
  3. Make late extraction a deterministic gamble: `EXTRACTION_SURGE_BANDS` apply +5 at 50% trace, +10 at 70%, and +15 at 85%, mitigated by the ICE dampener. `extraction_risk()` previews the surge, projected trace, and lethality; `jackout` applies the surge before banking, and a projected 100% burns the run and loses unbanked loot. The CLI HUD and Web trace gauge show the surge and mark lethal extractions.
  4. Make saves trustworthy: persist `random.Random.getstate()` as JSON-safe `rng_state` and restore it on load (legacy saves without it keep the old `seed + turns_elapsed` fallback). Persist pending puzzle payloads through `FrequencyPuzzle/BufferPuzzle/HashCrackPuzzle.to_dict/from_dict` and `puzzle_from_dict`, including remaining attempts and near-miss state.
  5. Enforce terminal-state safety after the world tick: `download_file`, `wipe_logs`, `social_engineer`, `bypass_firewall`, and `evade_antivirus` re-check the terminal state after `advance_turn()` and abort without paying, completing contracts, or mutating host defenses; `brute_miner` and `data_siphon` add their trace before crediting so a lethal surge cannot report a fake payout; `scan`, `move_to`, and `probe_host` report when the deck burned during the action. Stop counting 80%+ trace warnings as near misses.
  6. Prevent hunter stacking: `deploy_hunter` treats `intercepted` as active, so only one hunter can clamp the player at a time.
- **Consequences**: Failure now costs tempo, trace, and combo, which makes other hosts and `lay_low` tactically meaningful; near misses become a capped comeback rather than flavor; high-trace extraction is a genuine final decision; reloading a save no longer rerolls rewards or resets puzzle attempts; and action results no longer contradict a lockout. All schema changes are additive with old-save defaults. Test suite: 259 tests, 100% green.

### ADR-020: Living Syndicate Contract Market: Concrete Objectives, Risk Tiers, Deadlines, Rush Bonuses, Trust-Scaled Terms, and Visible Job Clocks
- **Date**: 2026-10-22
- **Status**: Accepted
- **Context**: The Syndicate contract was the only persistent goal besides the static story board, but after the opening heist it collapsed into a generic "breach any node of type X" order. It named no host, had no deadline, offered no reason to hurry, and never touched operative trust. That removed the clock from the economy: `lay_low` and detours had no job opportunity cost, contract rewards were flat, and repeated jobs were interchangeable. Verification of the previous heat layer also exposed two deadline-adjacent hazards: an action that advanced the turn before finalizing could complete the replacement contract instead of the old one, and a wipe at high trace could clear logs yet leave a stealth contract permanently unconfirmable.
- **Decision**:
  1. Extend `BountyContract` additively with `giver`, `risk_tier`, `objective`, `expires_turn`, `rush_turn`, `bonus_creds`, `failed`, and `description`. Add `objective_kind`, which uses the explicit objective or infers `wipe`/`extract`/`breach` from legacy fields, so old saves and hand-built contracts keep their behavior.
  2. Replace the generic contract dispatcher with a deterministic live-grid generator using a dedicated `world_rng(seed, turn, "contract")` stream. Each job names a specific host and objective: `breach` a host, `extract` a named valuable file, or `wipe` a host's logs (optionally after stealing its file). Feasibility filters exclude the Nexus core before Act IV, already breached hosts for breach jobs, and already looted files/logs for extraction/wipe jobs.
  3. Add `CONTRACT_RISK` tiers (`standard`/`priority`/`black`) with risk-scaled base payout, 80/70/60 trace limits, rush rates, and tighter deadlines. Deadlines scale with objective, host security, risk, and giver trust; the rush turn is halfway through the window. Base rewards were deliberately tuned down to 120/200/220 plus 20 per security level with 1.0/1.2/1.5 risk multipliers, keeping contract pay in line with the 150-350 Cred shop.
  4. Attribute jobs to real givers (Mira, the Archivist, or Zero when unlocked). Completion adds giver trust and pays a trust bonus capped at 25%; a missed deadline costs one trust, raises grid alert by 3, records a Syndicate news headline, and posts a replacement job. `contract_notice` carries the latest deadline warning or expiry into both clients.
  5. Run `_check_contract_clock` from `tick_world`: warn at 5 and 2 turns remaining, expire at zero, and repost when the board is empty. `_finalize_contract` centralizes payout, rush/trust bonuses, trust gain, news, logging, and dispatch so breach, extraction, and wipe paths cannot drift.
  6. Enforce stealth and timing in every completion path: breach jobs require their named target and the trace limit, extraction re-checks the named file and trace limit (allowing a cooled re-download), and wipe jobs allow a cooled `wipe_logs` sign-off when logs are already cleared. `download_file` and `wipe_logs` capture the active contract before their turn tick, so an expiry can no longer complete the replacement job by accident.
  7. Surface the job loop: CLI `contract`/`bounty` briefing, HUD job clock plus `contract_notice`, post-command notice printing, and a Web contract card showing risk, trace limit, remaining turns, rush bonus, and the latest notice. README and command help document the flow.
- **Consequences**: Contracts now create a real goal gradient: specific targets, a finite window, a rush decision, and a relationship stake. `lay_low` and detours spend reward time, loud play can miss stealth limits, and high-trust givers offer better terms. Determinism is preserved because the contract stream is separate from reward RNG. The change is additive for saves; legacy contracts without deadlines keep working. Test suite: 269 tests, 100% green.

### ADR-021: Syndicate Job Board: Three Rotating Offers, Accept/Decline Choice, Offer Shelf Life, and Deadline-on-Acceptance
- **Date**: 2026-10-22
- **Status**: Accepted
- **Context**: ADR-020 gave contracts concrete targets and deadlines, but the player still received exactly one auto-assigned job. Risk tiers, givers, and objectives were therefore not a choice, which undercut the autonomy half of the engagement loop and made declining or shopping for work impossible. Offers also needed their own shelf life so the board could rotate without silently starting a deadline the player never accepted.
- **Decision**:
  1. Add `GameState.contract_offers` and the additive `BountyContract` fields `offer_expires_turn` and `deadline_turns`. Offers carry a full risk/reward/target description but `expires_turn=0`; the deadline clock starts only when accepted.
  2. Generate up to three distinct offers (`CONTRACT_BOARD_SIZE`) from the same live-grid generator, excluding the active job's `(objective, target_ip, target_file)` signature. Standard/priority/black offers have 10/8/6-turn shelf lives via `CONTRACT_RISK[risk]["offer_ttl"]`.
  3. `_refresh_contract_offers` expires stale offers and backfills the board every tick. It runs on engine creation, after acceptance, after decline, after completion, and from `_check_contract_clock`, so the board stays current without auto-assigning work.
  4. `accept_contract(id)` refuses while another job is active, starts the stored deadline/rush window at the current turn, removes the offer, writes a JOB ACCEPTED notice, and refills the board. `decline_contract()` marks the active job failed, costs one giver trust without raising alert, clears the active slot, sets a one-turn broker repost cooldown (`contract_decline_until_turn`), and refreshes the board. A declined or expired job leaves `active_contract` empty until the player chooses an offer; the cooldown prevents free decline-fishing at the trust floor.
  5. Completion now clears the active job and refreshes the board instead of dispatching a replacement. Expiry still posts a pending notice; the next tick fills the board and tells the player to `accept_job <id>`.
  6. Surface the board: CLI `contract`/`bounty` shows the active brief plus posted offers with IDs, risk, window, shelf life, and accept hints; `accept_job <id>` and `decline_contract` commands; HUD shows the offer count when no job is active; the Web mission modal renders the active job with a DECLINE button and three offer cards with ACCEPT buttons. Server actions `accept_contract` and `decline_contract` mirror the engine.
- **Consequences**: Players now choose risk, objective, target, and giver, while deadlines remain honest because they start on acceptance. The board rotates on the clock, so waiting has a cost, and declining is a relationship decision rather than a free reroll. Legacy saves load with an empty board and backfill on the first tick; old active contracts keep their existing deadlines. Save/load round-trips offers and their stored windows. Test suite: 276 tests, 100% green.

### ADR-022: Closing the Job-Board Gaps: Paid Offer Drops, Persistent Contract IDs, Trust Tiers with Dialogue and Unlocks, and Recon Fallback Jobs
- **Date**: 2026-10-22
- **Status**: Accepted
- **Context**: ADR-021 gave the player three offers, but four gaps remained. A bad single offer could only be waited out, offer IDs could collide after reload because the generation sequence reset, trust changed contract terms but not dialogue or any unlock, and a fully stripped grid stopped posting work. These gaps weakened autonomy, save integrity, relationship progression, and late-run continuity.
- **Decision**:
  1. Add `GameState.contract_seq` and use it in deterministic contract IDs (`cnt_<turn>_<seq>`). The sequence is persisted with the state; old saves that contain offers but no sequence are migrated to a high starting value so newly posted offers cannot collide with saved IDs. Covered by a save/load collision test.
  2. Add single-offer removal: `drop_offer(id)` removes exactly that offer and refills the board, charging a 30 Cred broker fee from banked credits when available or a one-turn broker cooldown when the runner is broke. CLI `drop_offer`/`pass_offer`, Web PASS buttons, and the server `drop_offer` action expose it; a broke runner takes the cooldown instead of being locked out, and can only drop one free offer per broker window. Player-initiated accept/drop/decline results stay in the action log instead of overwriting the tick-level `contract_notice`, preventing duplicate CLI alerts.
  3. Add relationship tiers on `ContactProfile` (`Neutral`/`Trusted`/`Inner Circle`). Trusted and Inner Circle append tier-specific dialogue (`TRUST_DIALOGUE`); Inner Circle unlocks a second favor via `bonus_favor_used`. CLI and Web show the tier and a favor-ready/INNER CIRCLE FAVOR state, and the run summary records the tier.
  4. Add trust-gated quests: `Quest.required_trust` participates in `is_quest_locked`, `accept_quest` returns a trust-specific denial, and `list_quests` exposes `lock_reason`. Kilo's secondary job (`q_side_ghost`) requires trust 1, reachable by accepting Kilo's primary job or calling in a favor; the CLI and Web mission board display the requirement.
  5. Add a recon fallback objective. When no breach/extract/wipe candidate exists, the generator posts repeatable low-paying `recon` offers against discovered/breached hosts (`CONTRACT_BASE_REWARD["recon"] = 80`). `probe_host` captures the active contract before its turn tick, confirms the recon target under the trace limit (with a cooled retry path), and finalizes the job. This keeps a fully stripped grid economically alive without creating an infinite high-value farm.
- **Consequences**: Players can now pass a specific bad offer for a real fee, reload without ID collisions, see trust reflected in dialogue, unlock a second favor and a trust-gated side job, and keep working when the grid is exhausted. Additive fields default safely for old saves; trust-gated quests remain ungated in legacy saves because their stored quest data lacks `required_trust`. Test suite: 283 tests, 100% green.

## Licensing migration (v0.1.0-agpl)

- New versions use the Aegean Game License 1.1 (AGL-1.1); versions up to and including `v0.1.0-agpl` remain under GNU AGPL-3.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.

## License notice cleanup (2026-10-26)

- The license-history notes were removed from README.md and COMMERCIAL.md: the project is offered only under the Aegean Game License 1.1 (AGL-1.1), with commercial use under ACL-1.0.

### ADR-023: Procedural Side-Subnet Layer: Seeded Contract Hosts Beside the Fixed Campaign Spine
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: `generate_network(seed)` documented a deterministic network generated from the seed but never consumed its `random.Random` stream, so every run produced the same seven hosts with the same edges, security, puzzles and payouts. Scans, routes, loot and contract-generation candidates therefore repeated exactly, contradicting the README's reproducibility-by-seed promise and flattening replay value. The campaign spine cannot simply be randomized: the opening contract, story quests, tests and the Web matrix all depend on the canonical gateway/proxy/vault/ICE/core hosts and their IPs and files.
- **Decision**:
  1. Keep the seven campaign hosts, their IDs, IPs, files, security and edges exactly as they are. Add an additive layer of two or three side hosts built from six thematic `DATA_VAULT` templates after the spine exists.
  2. Seed the selection: the generator's existing `rng` chooses the template subset, each host's security level (1-3), puzzle type (`frequency`/`buffer`/`hash`), payout (60 + 20 per security level + 0-30) and trace rate. Side hosts use `node_side_NN` IDs and reserved `10.0.9.20-22` IPs, and each carries one target-data file with `value_creds` equal to its breach payout plus a log file.
  3. Wire every side host to an early proxy anchor (and optionally the Black ICE cluster) with reciprocal `connected_ids`, so breaching an anchor reveals it naturally and no story gate is bypassed. Side hosts stay `LOCKED` at generation and need no engine changes: existing reveal, hacking, reward, contract, daemon and re-secure paths already treat them as ordinary vaults.
  4. Surface them in the Web Cyberdeck with three reserved canvas slots, per-run labels taken from the host name, and a hit test that ignores absent hosts. Document the layer in the README guarantees and cover determinism, cross-seed variation, spine invariants, reveal/hack/contract eligibility and `/api/state` serialization with tests.
- **Consequences**: Two runs with different seeds now differ in which side hosts exist, how hard they are, what they hold and where they hang, while the campaign path and its targets remain stable. Contract offers draw from a wider target pool, giving the job board more variety without changing payouts or deadlines. Same-seed runs and save/load remain deterministic because generation uses its own local RNG stream; old saves keep their saved node map. Test suite: 318 tests, 100% green.

### ADR-024: Cross-Interface Save Parity: Web Save/Load Through the Terminal's Atomic Store
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The Web Cyberdeck is the default launcher, but the run lived only in server memory: the server persisted career totals when a run settled but never the run itself, so closing the server or browser lost all unbanked progress. The terminal already had crash-safe save/load backed by `SaveManager` (atomic replace, shadow backup, corruption quarantine, RNG and pending-puzzle persistence), and both interfaces default to the same `.cyberpulse` data directory.
- **Decision**:
  1. Add `SaveManager.has_save()`, which reports a save when either `savegame.json` or its shadow `.bak` exists, so recovery candidates are not hidden.
  2. Add `CyberdeckSession.save_run()` and `load_run()`: saving refuses a terminal (`victory`/`lockout`/`jackout`) run and reports a failed atomic replace; loading replaces the session engine, clears the transient puzzle UI references, and keeps `engine.pending_puzzles` from the saved file. The session tracks whether it saved or loaded the file, and settlement deletes only an owned save after the career write succeeds, so a CLI-owned save is never destroyed by an unrelated browser run (ADR-010 R7) while a finished run cannot be replayed from its own save.
  3. Wire `POST /api/action` actions `save` and `load`, expose `has_save` in every state payload, and allow `load` in the victory guard so a player can return to an earlier run after finishing one.
  4. Surface it in the Web Cyberdeck with a header **SAVE** button (disabled once the run ends) and a **CONTINUE RUN** main-menu button that appears only when `has_save` is true; both reuse the existing terminal log and state refresh paths.
  5. Test the session semantics (round trip with a pending puzzle, missing save, terminal refusal) and the HTTP round trip (no save, scan, save, diverge, load restores trace/turn).
- **Consequences**: Browser runs now survive a server restart, and the same save can move between the Web Cyberdeck and the terminal because both use the identical file and schema. Finishing a run removes the mid-run save after the career write, so the terminal's anti-replay behavior is preserved. No storage schema, CLI behavior or career settlement changes. Test suite: 323 tests, 100% green.

### ADR-025: Save Slots & Autosave: Three Manual Checkpoints, Change-Tracked Autosave, and Run-Scoped Purge
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-024 gave both interfaces one manual save file. Players still lost progress if they forgot to save, could not keep parallel runs apart, and had no way to see what a save contained before loading it. Slot 1 also had to keep loading existing `savegame.json` files, and the ADR-024 ownership rule had to survive: a browser run must not delete a save another interface owns.
- **Decision**:
  1. Keep slot 1 mapped to the legacy `savegame.json` (and `savegame.bak`), add `savegame_slot2.json` and `savegame_slot3.json`, and give autosave its own `autosave.json`. `SaveManager.normalize_slot` accepts `1`, `2`, `3`, `auto`/`autosave`, and rejects everything else with a clear error.
  2. Extend the atomic store with `slot_path`, `has_save(slot)`, `list_saves`, `claim_slot`, `mark_autosave_baseline`, `autosave`, and `delete_run`. Save payloads gain additive `run_id` and `meta` fields; old payloads without them still load as slot 1.
  3. Give each `GameEngine` a `run_id`. `delete_run` removes only checkpoints this interface claimed and whose file belongs to the settled run (or has no run identity, for legacy files), preserving ADR-024's cross-interface ownership guard while purging every owned slot and the autosave at settlement.
  4. Autosave hashes run state, deck, node status and pending puzzles. It writes once per real change to the autosave file only, never to a manual slot. New runs and loaded slots are baselined first, so opening a page or loading an older run cannot overwrite another run's autosave.
  5. Terminal: `save 1|2|3`, `load 1|2|3|auto`, and `saves`; `CONTINUE` opens a slot picker; autosave runs after each command in interactive and batch mode.
  6. Web Cyberdeck: expose `saves` in every state payload, accept a `slot` on `save`/`load`, and replace the single header action with a slot archive modal listing turn, credits, trace, act and timestamp for each checkpoint, with per-slot SAVE and LOAD controls.
  7. Cover slot isolation, legacy loading, listing metadata, autosave deduplication and terminal refusal, run-scoped purge, CLI commands, session semantics and the HTTP round trip with tests.
- **Consequences**: Players can keep three independent runs and recover from a crash without saving manually. The legacy save file and schema remain readable, the Web and terminal archives are interchangeable, and finishing a run still cannot be replayed from any checkpoint this interface created. Test suite: 341 tests, 100% green.

### ADR-026: Slot Archive Management: Run Labels, Rename, and Delete
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-025 shipped three manual slots and autosave, but every checkpoint was still called SLOT 1/2/3, stale runs could not be removed, and relabeling a run required loading and re-saving it. The archive was functional but not usable as a library.
- **Decision**:
  1. Store an additive `meta.name` on manual saves. Names collapse whitespace, cap at 32 characters, and are optional; saving with no name preserves the existing label, while an explicit empty name clears it. Old saves without a name load normally and show an empty label.
  2. Add `SaveManager.rename_slot`, which rewrites the same atomic payload with a new `meta.name` while preserving the checkpoint, `run_id`, `saved_at`, and progress. Renaming a missing or autosave slot is refused.
  3. Expose `name` in `list_saves` and in every state payload. Terminal adds `save [1-3] [name]`, `rename <slot> <name>`, and `delete <slot>`; delete requires an explicit slot, removes only that checkpoint and its backup, and leaves the live engine untouched.
  4. Web Cyberdeck adds an editable run-label field plus RENAME and DELETE actions in the slot archive. Delete asks for confirmation; every action refreshes the archive from the returned state.
  5. Add `rename_save` and `delete_save` API actions, keep `save` accepting an optional `name`, and reject invalid or autosave renames with a clear message.
  6. Cover name normalization and capping, label preservation across saves, rename preserving timestamp/progress, missing-slot refusal, delete isolation, CLI commands, session semantics, and the HTTP round trip.
- **Consequences**: The slot archive now works as a labeled library: players can distinguish parallel runs, relabel old checkpoints without touching them, and clear stale ones. Legacy saves without metadata keep their original display timestamp when renamed. No save schema break occurs; the new field is additive and optional. Test suite: 353 tests, 100% green.

### ADR-027: Career Run Archive: Bounded Per-Run History in the Dossier
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The career profile kept totals, streaks, best combo and upgrades, but the RUN LEGACY moment vanished as soon as the next run started. Players could not compare seeds, recall which run produced a combo or contract clear, or see their recent outcomes after a break.
- **Decision**:
  1. Add an additive `run_history` list to `CareerProfile`, defaulting to an empty list so old career files keep loading. Sanitize non-list payloads on read.
  2. Append one record inside `settle_career` after the existing one-shot guard, so duplicate settlement cannot double-record. The record captures outcome (`victory`, `jackout`, `lockout`), `run_id`, seed, turns, banked credits, net gain, best combo, story act, completed quests, contract completion and finish time.
  3. Cap the archive at the 20 most recent runs in `GameEngine.MAX_RUN_HISTORY`, bounding `career.json` growth.
  4. Show the last five records in the terminal career dossier and the last six (newest first) in the Web career dossier, including a timestamp and outcome color.
  5. Cover victory and lockout records, capping, old-career defaults, persistence, and both display paths with tests.
- **Consequences**: The dossier now preserves the arc of recent runs and gives seed/outcome context to the save archive, while old careers remain valid and career files stay bounded. Test suite: 359 tests, 100% green.

### ADR-028: Career Milestones: Settlement-Evaluated Achievements and Dossier Badges
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The dossier had totals and recent runs but no long-term goals. Players could clear many runs without a visible mastery ladder, and unusual outcomes such as a ghost victory or a black contract disappeared into the history list.
- **Decision**:
  1. Add a twelve-entry milestone catalog in `cyberpulse/achievements.py`: first extraction, five clears, x5/x10 combo, ghost victory, speed victory, black contract, three vaults, 50 turns, 1,000 banked credits, hot extraction, and Act V.
  2. Store unlocked identifiers in `CareerProfile.achievements`, an additive list. Old or malformed career payloads default to an empty, de-duplicated list of strings.
  3. Evaluate only inside `settle_career`, after the one-shot guard and after profile counters update, so re-settling cannot farm unlocks. Store the newly earned IDs on the engine and in the run-history record.
  4. Surface new unlocks in the terminal `RUN LEGACY` summary, the terminal career dossier, the Web run banner (count) and the Web dossier (unlocked/locked badge grid). `/api/career` returns the catalog annotated with unlocked state.
  5. Cover catalog integrity, threshold rules, de-duplication, old-career defaults, persistence, CLI display and the API payload with tests.
- **Consequences**: The dossier now carries a permanent mastery ladder, and rare outcomes remain visible after the run ends. Career files stay compatible and unlocks are idempotent. Test suite: 366 tests, 100% green.

### ADR-029: Daily Runs: Date-Derived Seeds and Per-Day Best Gains
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Runs are deterministic by seed, but the game offered no common daily challenge. Players had no reason to return on a given date or compare a fixed seed with their own best, and the run archive could not distinguish a daily attempt from an ordinary run.
- **Decision**:
  1. Add `cyberpulse/daily.py` with `daily_key(day)` (ISO date), `daily_seed(day)` (`YYYYMMDD`) and `daily_run(day)`. The date is resolved once when a daily run starts, so crossing midnight does not change an active run.
  2. Add `GameEngine.daily_key`, persisted in save payloads and restored on load. Old saves load with an empty key. Web sessions accept an initial daily key for `--web --daily`.
  3. Start daily runs from `python -m cyberpulse.cli --daily`, main-menu option 7, or the Web **DAILY RUN** button. `CyberdeckSession.reset_game(daily=True)` and the `reset` API action resolve the date and seed; the API returns the key and a daily-specific message.
  4. At settlement, record `max(existing, gained)` under the day key in `CareerProfile.daily_best`, capped to the 30 most recent dates. Tag the run-history record with `daily_key`, show a HUD/ticker chip and run-legacy tag, and show the last five daily bests in the career dossier.
  5. Sanitize malformed daily keys/values on career load; cover key/seed determinism, save/load persistence, settlement max behavior, CLI `--daily`, session/API reset, and the Web payload with tests.
- **Consequences**: Players get a fresh date-seeded challenge each day with a persistent personal best, while ordinary seeded runs and old saves are unaffected. Daily keys remain stable inside a run, and no network or clock service is required. Test suite: 374 tests, 100% green.

### ADR-030: Seed Replay from the Run Archive
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-027 stores each settled run's seed, but the archive was read-only. Replaying an interesting layout or a daily seed required copying the number and starting a run manually, and the Web dossier offered no path at all.
- **Decision**:
  1. Index the last five terminal history records newest-first (`[1]` = newest). `replay <1-5>` rebuilds a fresh `GameEngine` from that record's seed with the current career profile, replaces the live engine, and resets the autosave baseline. Out-of-range or malformed indexes print the usage line and change nothing.
  2. Replays are ordinary runs: the archived `daily_key` is intentionally ignored, so replaying a past daily seed cannot rewrite that day's historical best.
  3. Add a **REPLAY** button to each Web dossier history row. It confirms the live-run replacement, calls the existing `reset` action with the archived seed, and refreshes the HUD; rows without a numeric seed disable the button.
  4. Cover the valid replay path and out-of-range rejection in the CLI, and validate the JavaScript entry point with the syntax check.
- **Consequences**: Seeds become reusable content rather than a read-only field, while daily records stay immutable and no save/career schema changes are needed. Test suite: 376 tests, 100% green.

### ADR-031: Shadow Backup Integrity and Non-Finite Metadata Guards
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: `_write_atomic` refreshed the `.bak` shadow from any existing primary before replacing it. If the primary was corrupt while the backup was good, a save could overwrite the only recoverable copy, defeating the crash-safety claim. Separately, the archive trusted `meta.saved_at`, so `NaN`/`Infinity` crashed `list_saves`, and malformed `daily_best` numbers crashed `CareerProfile.from_dict`.
- **Decision**:
  1. Validate an existing primary as JSON before copying it to the shadow backup. A corrupt primary leaves the prior backup untouched; the new payload still replaces the primary through the normal five-retry atomic path.
  2. Treat non-finite, boolean or non-positive `saved_at` metadata as unusable and fall back to the file's modification time, keeping the archive listable.
  3. Filter non-finite `daily_best` values during career load, coerce finite numbers to non-negative integers, and keep valid entries.
  4. Cover corrupt-primary backup preservation, non-finite archive timestamps, and malformed daily values with failing-first tests.
- **Consequences**: A corrupt primary can no longer destroy the last good recovery copy, and damaged metadata degrades to a safe fallback instead of crashing the Web state payload or career dossier. Valid saves behave exactly as before. Test suite: 378 tests, 100% green.

### ADR-032: Daily Streaks: Consecutive-Day Participation and Same-Day Idempotence
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-029 records a best daily gain per date, but a player who returns every day has no visible streak or long-term daily goal. Without explicit same-day handling, repeated daily runs could also inflate a naive counter.
- **Decision**:
  1. Add `daily_streak`, `best_daily_streak` and `last_daily_key` to `CareerProfile`. Old careers default to zero/empty; malformed negative or non-integer values sanitize to zero and `best` is raised to at least `daily_streak`.
  2. At settlement of a daily run, compare the run key with `last_daily_key`: same day is idempotent (streak stays, minimum 1), exactly the next ISO day increments, any gap or bad key resets to 1. Update `best_daily_streak` and `last_daily_key` in the same one-shot settlement path.
  3. Show `Daily Streak: N (Best: M)` in the terminal dossier, a `// STREAK N (BEST M)` suffix in the Web dossier's daily section, and append the current streak to the Web HUD daily chip.
  4. Add `is_next_day` to the daily helper module and cover first participation, consecutive days, same-day repeats, gaps, bad keys, old-career defaults, and the CLI dossier.
- **Consequences**: The daily challenge gains a retention signal and a durable best, while same-day experimentation cannot farm the streak. No save schema change is required and ordinary runs are unaffected. Test suite: 383 tests, 100% green.

### ADR-033: Dead Man's Switch: One-Use Lockout Insurance
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: A trace lockout wipes all unbanked loot. The push-your-luck loop had no way to price that risk mid-run, and the Black Market only sold permanent hardware and exploits, leaving no consumable decision.
- **Decision**:
  1. Add `extraction_insurance` to `CyberDeck` (default false, persisted in saves; old saves load uninsured).
  2. Add a `dead_mans_switch` Black Market item (150 CR, category `consumable`, max level 1). Its shop status reads `ONE USE`/`ARMED`; buying it while already armed is refused.
  3. On the first lockout of a run, if insured and unbanked loot is positive, bank `lost_loot // 2` into `deck.cryptocreds`, reduce `state.lost_creds` to the actual lost amount, clear the insurance, and log the payout. Existing lockout messaging still reports the remainder.
  4. Exclude consumables from career persistence in both CLI and Web shop purchases, so the switch never becomes a permanent upgrade or a fake exploit.
  5. Cover shop purchase/arming, lockout payout, save round-trip, CLI career exclusion and the HTTP purchase path with tests.
- **Consequences**: Players gain a meaningful mid-run risk tradeoff and a new Black Market choice, while old saves, career progression and uninsured lockouts behave exactly as before. Test suite: 388 tests, 100% green.

### ADR-034: Rival Netrunner: Contract Competition and Counter-Tracing
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The living grid pressures the player through alert, hunters and deadlines, but no peer netrunner competes for the Syndicate board. Offers disappeared only by expiry or player choice, so the world lacked a social competitor.
- **Decision**:
  1. Add a persisted `RivalNetrunner` object to `GameState` with name, handle, skill, tagline, absolute next-move turn, stolen count and status. A seeded roster (Vex, Marrow, Static) generates one deterministically per run; old saves without a rival backfill one on load.
  2. On a due turn inside `tick_world`, refresh the board and let the rival remove one posted offer, record a Syndicate headline, and schedule the next absolute turn from skill plus a seeded delay. If the board is empty, the rival probes the player's link for trace instead.
  3. Add `counter_rival` (aliases `trace_rival`): costs 2 CPU, refuses without CPU or an active rival, and adds 5 turns to the rival's next move. Expose it through the terminal, the `counter_rival` API action and a Web modal.
  4. Add a HUD rival chip, a RIVAL rail button/modal with status and counter action, and include the rival summary in every state payload and run summary.
  5. Cover seeded generation, board theft, scheduling, counter cost/delay, save persistence, old-save backfill, CLI inspection/counter, and the HTTP action.
- **Consequences**: The job board now has a visible peer antagonist and a CPU-priced counterplay loop, while existing saves gain a rival without losing progress. Test suite: 396 tests, 100% green.

### ADR-035: Transparent Run Scoring and Top-10 Hall of Fame
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Run history recorded outcomes but gave no single comparable performance number. The dossier had milestones and recent runs but no all-time ranking, so two victories could not be compared at a glance.
- **Decision**:
  1. Add `scoring.py` with a fixed, itemized formula: net credits, combo ×75, quests ×150, breaches ×25, contract +200, victory +500 or jackout +250, story completion +100. Negative inputs clamp to zero.
  2. Compute the score inside `settle_career` after stats update, store it and its breakdown in the run-history record, and expose it through the run summary.
  3. Maintain `CareerProfile.hall_of_fame` as the top ten records by score, deduplicated by `run_id`. Old or malformed halls sanitize to at most ten dict entries; duplicate settlement cannot add another entry.
  4. Show the score and rank in the terminal `RUN LEGACY`, the score in the Web banner, and the top five in both dossier leaderboards.
  5. Cover formula weights, clamping, ranking, cap/deduplication, persistence, career defaults, CLI display and the Web payload.
- **Consequences**: Every settled run now has a comparable result and a place on a persistent leaderboard, while old careers remain valid and the formula is visible in one module. Test suite: 402 tests, 100% green.

### ADR-036: Difficulty Modes: Trace, Starting Conditions and Contract Pay
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Every run used the same trace curve and contract economy. Experienced players had no explicit challenge dial, and newer players had no gentler entry point beyond reading the command list.
- **Decision**:
  1. Add `difficulty.py` with `easy`, `normal`, `hard`, normalization of unknown values to normal, and multipliers: trace 0.8/1.0/1.2; contract pay 1.1/1.0/0.9.
  2. Add `GameEngine.difficulty` with a default of normal. Easy grants +2 max CPU (and fills it); Hard starts the grid at +15 alert. Normal leaves the existing start state untouched.
  3. Apply the trace multiplier in `mitigated_trace` (after stance/dampener/proxy mitigation) and the contract multiplier in `_contract_payout`, so all trace sources and payouts use the same rules.
  4. Persist difficulty in save payloads, run-history records and Hall of Fame entries; old saves default to normal. Expose it through run summaries and state payloads.
  5. Add `--difficulty` to the terminal, a Web main-menu picker, HUD chips in both interfaces, and a `difficulty` field on reset API calls while keeping normal as the default.
  6. Cover normalization, trace/start modifiers, contract pay, save round-trip, CLI HUD, API reset fallback, and existing default behavior.
- **Consequences**: Runs now have an explicit challenge dial without changing Normal-mode behavior, and difficulty remains visible in the archive and leaderboard. Balance changes are isolated to one module and three call sites. Test suite: 409 tests, 100% green.

### ADR-037: First-Run Field Manual: State-Driven Onboarding Checklist
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The game exposes 51 commands and many interlocking systems, but onboarding was static help text. New players had no live signal for the core loop (scan, probe, breach, loot, extract), and established careers had no reason to see hints again.
- **Decision**:
  1. Add `tutorial.py` with five ordered steps: scan, probe, breach, loot and jackout. Each step is derived from persisted run state (`scanned`, `probed_nodes`, breached nodes, `looted_payloads`, terminal flags) rather than client-only bookkeeping.
  2. Add `GameState.scanned`, set only by a successful `scan_surroundings`, so scan progress survives save/load and old saves default to unscanned.
  3. Expose `engine.tutorial_progress()` and include it in every state payload. The terminal `tutorial` command renders a live checklist and the main loop prints a one-line first-run hint; the Web renders a dismissible panel only for careers with no settled runs.
  4. Hide the guide once all steps are complete, once any run has settled, or when dismissed in the current page session.
  5. Cover fresh-run state, step transitions, successful scan marking, CLI rendering and the API payload.
- **Consequences**: A new player gets a concrete path through the first run without new gameplay rules, while experienced careers never see the panel. The checklist is save-safe and cannot drift from actual progress. Test suite: 413 tests, 100% green.

### ADR-038: Daily Rule Modifiers: Date-Selected Twists for Daily Runs
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Daily runs already varied by seed, but the rules were identical to normal runs. The daily challenge had no distinct identity beyond a date and a best-gain record.
- **Decision**:
  1. Add a frozen `DailyModifier` table to `daily.py`: Hot Grid (+20 start alert), Blackout (-2 start CPU), Thin ICE (+15% trace), and Data Bloom (+20% contract pay). `daily_modifier(day)` selects deterministically by ordinal, and `modifier_by_id` resolves persisted ids.
  2. Add `GameEngine.daily_modifier`; apply starting effects in construction and the trace/contract multipliers in the central mitigation and payout methods alongside difficulty.
  3. Persist the modifier id in save payloads and run-history records; old saves and normal runs default to no modifier. Daily runs loaded from saves retain it.
  4. Compute the modifier in CLI/server daily starts, pass it through `--web`, expose it in state and run summaries, and show it in the HUD chip and banner.
  5. Cover deterministic selection, roster coverage, start conditions, trace/payout effects, save round-trip, CLI output and the API daily reset.
- **Consequences**: Each date now has both a seed and a rule identity, giving players a reason to adapt rather than replay the same plan. Normal runs remain unchanged, and the modifier is visible and archive-safe. Test suite: 416 tests, 100% green.

### ADR-039: Difficulty-Filtered Hall of Fame
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-035 ranks the top ten scores, and ADR-036 tags each run with a difficulty. The all-time board still compared Easy, Normal and Hard scores directly, so a high Easy score could outrank a strong Hard run even though the modes are not equivalent.
- **Decision**:
  1. Add `hall [all|easy|normal|hard]` to the terminal. `all` remains the default and the existing dossier view; an invalid filter prints the usage line without changing anything. Entries missing a difficulty are treated as Normal.
  2. Add ALL/EASY/NORMAL/HARD controls to the Web Hall of Fame. The selected filter re-renders the same cached career payload without a network round trip; the all-time view remains the initial state.
  3. Keep ranking logic unchanged: filters are read-only projections over the stored top ten, so a filtered board may show fewer than five entries and never alters the underlying hall.
  4. Cover command validation, filtered output, legacy entries defaulting to Normal, and the Web script syntax.
- **Consequences**: Players can compare runs within the mode they actually played, while the all-time board remains available. No save or career schema change is required. Test suite: 417 tests, 100% green.

### ADR-040: Career Alias and Persistent Web Preferences
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The career alias was fixed at `ZeroCool`, and the Web theme/audio/CRT controls reset on every reload. Players could not personalize the dossier or keep a preferred presentation.
- **Decision**:
  1. Sanitize `CareerProfile.alias` on load: collapse whitespace, cap at 24 characters, and default empty values to `ZeroCool`.
  2. Add `alias <name>` to the terminal, which updates and saves the career profile. Add a `rename_alias` API action and a Web dossier alias editor with the same trimming/cap rules.
  3. Persist the Web theme, audio and CRT choices in `localStorage` under `cyberpulse.*`, restore them during UI initialization, and save on every toggle/change. Storage failures degrade silently to defaults.
  4. Add a `prefers-reduced-motion` stylesheet path that shortens non-essential transitions and animations.
  5. Cover alias normalization, CLI persistence, the HTTP action and the existing default dossier behavior.
- **Consequences**: Players can set a lasting handle and keep their preferred presentation across reloads, while old careers and restricted storage contexts remain safe. No save schema change is required. Test suite: 420 tests, 100% green.

### ADR-041: Faction Standing: Syndicate Pay and Street Shop Discounts
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Contracts improved operative trust and per-run payments, and clean runs banked loot, but neither left a lasting faction identity. The career dossier had no reputation axis that changed how future runs played.
- **Decision**:
  1. Add `factions.py` with two standing tracks, Syndicate and Street. Normalize unknown/invalid values to zero, cap each at 100, and expose bounded bonuses.
  2. Persist `CareerProfile.faction_standing`; old careers default to zero. Completed contracts add +2 Syndicate; every victory or jackout adds +1 Street at settlement.
  3. Snapshot standing into `GameEngine` at run start. Apply `1%` Syndicate contract pay per point (cap +20%) in `_contract_payout`, and `1%` Street Black Market discount per point (cap 15%) through `shop_price_multiplier` for CLI and Web purchases.
  4. Surface standing and its active bonuses in the terminal career dossier, the Web faction panel and the Web shop header; expose the discount in `/api/shop` and the standings through career/state payloads.
  5. Cover normalization, caps, standing growth, effects, persistence, old-career defaults, CLI display and the shop API.
- **Consequences**: Contracts and clean extraction now build a persistent identity that changes future pay and prices, but effects are capped and only apply from the next run. Existing saves and careers remain compatible. Test suite: 426 tests, 100% green.

### ADR-042: Faction Snapshot Persistence Across Save/Load
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-041 snapshots faction standing at run start, but `SaveManager.load` rebuilt the engine without that snapshot. A loaded run lost its Syndicate/Street bonuses, and a later career change could silently alter the economics of an old checkpoint.
- **Decision**:
  1. Persist the normalized `faction_standing` snapshot in every save payload.
  2. On load, construct the engine with the current career profile for legacy fallback, then overwrite the standing snapshot from the save and recompute cached bonuses through `refresh_faction_bonuses`.
  3. Keep the older behavior for saves without the field: fall back to the current career standing.
  4. Add a regression test that saves a run at standing 10/10, changes the career to 20/20, and verifies the loaded run still uses 10/10.
- **Consequences**: Checkpointed runs retain their original contract and shop economics, while legacy saves remain loadable. No schema break occurs. Test suite: 427 tests, 100% green.

### ADR-043: Guarded Career Reset with Automatic Backup
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Permanent career progression had no in-game reset. Players who wanted a clean start had to delete files manually, risking the loss of a dossier they might want to keep, and old saves could resurrect pre-reset progress.
- **Decision**:
  1. Add `SaveManager.backup_career()` (atomic `career.backup.json`), `delete_career()` and `delete_all_saves()`.
  2. Add `reset_career CONFIRM` to the terminal. Any other token prints usage and changes nothing. A successful reset backs up the career, deletes the profile and all slots, rebuilds a fresh engine, and resets the autosave baseline.
  3. Add a `reset_career` API action requiring the exact `confirm: RESET` token. The Web career dossier exposes a RESET CAREER button with a typed RESET prompt and closes the dossier on success.
  4. Cover refusal, backup contents, profile deletion, slot cleanup and the HTTP action.
- **Consequences**: Players can start over safely, with a recoverable backup and no stale checkpoints, while accidental invocation leaves progress untouched. No save schema change is required. Test suite: 431 tests, 100% green.

### ADR-044: Milestone Catalog Expansion: Hard, Daily and Faction Goals
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: The original twelve milestones predated difficulty modes, daily streaks and faction standing. Those systems had their own records but no permanent badge in the dossier mastery ladder.
- **Decision**:
  1. Add four catalog entries: Hard Clear (victory on Hard), Daily Devotion (7-day streak), Daily Legend (30-day streak), and Faction Insider (10 standing with Syndicate or Street).
  2. Evaluate them in the existing settlement-time evaluator after stats and standing updates, so they unlock once and remain idempotent.
  3. Keep the catalog as the single source for CLI counts, Web badges and API status; old careers simply unlock eligible badges on their next settlement.
  4. Cover Hard versus Normal, streak thresholds, faction thresholds, catalog length and duplicate-settlement behavior.
- **Consequences**: The newer progression systems now feed the same permanent mastery ladder, without new commands or save fields. Test suite: 434 tests, 100% green.

### ADR-045: Faction Ranks and One-Time Promotion Rewards
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-041 made standing a linear percentage with no named identity or milestone payoff. Players could not see their rank, and crossing a major threshold felt the same as any other point.
- **Decision**:
  1. Add rank tables in `factions.py`: Syndicate Associate/Fixer/Broker/Kingpin at 0/10/25/50; Street Lookout/Runner/Ghost/Legend at the same thresholds.
  2. Add `rank_for` and `rank_up_reward`; ranks derive from standing, so they need no separate persistence.
  3. During settlement, compare old and new rank indices after standing growth. For each crossed threshold, award a one-time 100/250/500 CR bonus, add it to banked and lifetime credits, and record `{faction, rank, reward}` in the run history and summary.
  4. Display ranks in the terminal dossier, Web faction panel, run legacy and Web banner promotion count; expose ranks in `/api/career`.
  5. Cover thresholds, rewards, duplicate settlement, CLI and API display.
- **Consequences**: Faction investment now has named status and a one-time payoff, while the standing snapshot and existing bonuses remain unchanged. Test suite: 436 tests, 100% green.

### ADR-046: Version SSOT and the 0.4.0 Release
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: Runtime, packaging and CLI metadata disagreed (`0.1.0`, `0.2.0`, `0.3.0`), and the large feature set added since the last public baseline had no release record.
- **Decision**:
  1. Make `cyberpulse.__version__` the single runtime source at `0.4.0`; derive the CLI banner and a new `--version` flag from it.
  2. Align `pyproject.toml` at `0.4.0`.
  3. Add `tests/test_version.py` to enforce semver, package/pyproject parity and the CLI flag; remove the hardcoded `0.1.0` assertion from the init smoke test.
  4. Add `CHANGELOG.md` for the 0.4.0 release, covering save slots, history, milestones, dailies, difficulty, rival, insurance, tutorial, preferences, factions/ranks and the reset workflow, plus the storage/faction fixes.
- **Consequences**: Release metadata cannot drift silently, support can query the installed version, and the release history is legible. Test suite: 439 tests, 100% green.

### ADR-047: Run Allegiance: Syndicate Patron Pay and Street Patron Discounts
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-041/045 made standing and ranks permanent, but every run advanced both factions automatically. Players had no way to declare a patron or specialize a run, so the ranks lacked a role-play choice.
- **Decision**:
  1. Add `none`, `syndicate` and `street` allegiances with normalization to `none` for unknown values. Store the choice on the engine, persist it in saves and run history, and accept it on reset/CLI.
  2. Syndicate patrons gain +10% contract pay and one extra Syndicate standing per completed contract. Street patrons gain +5% Black Market discount and one extra Street standing per victory/jackout. Independent runs keep the existing baseline.
  3. Apply patron economics through the central contract-payout and shop-multiplier methods; keep the standing snapshot immutable across load.
  4. Expose the choice in the CLI (`--allegiance`), Web main-menu selector, HUD chip, run banner and state payload.
  5. Cover normalization, economics, standing growth, save/load, CLI and reset API.
- **Consequences**: Each run now has a faction identity and a start-of-run tradeoff, while old saves default to Independent and the existing standing caps stay intact. Test suite: 443 tests, 100% green.

### ADR-048: Paid Contract-Board Reroll
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: A three-offer Syndicate board could roll completely unusable jobs. The only options were waiting for expiry, paying a drop fee one offer at a time, or accepting a bad contract, with no direct paid reroll.
- **Decision**:
  1. Add `GameEngine.reroll_contract_offers(cost=50)`: refuse in terminal states or with insufficient credits, build a fresh candidate board while excluding the active contract, and only charge after a non-empty board is produced.
  2. Preserve the previous board and leave credits untouched when no candidates exist.
  3. Expose `reroll` in the terminal, `reroll_contracts` in the API and a REROLL 50 CR button on the Web contract card (disabled for terminal runs or under 50 credits).
  4. Cover success, credit deduction, board replacement, insufficient funds, terminal refusal and the HTTP action.
- **Consequences**: Players can buy their way out of a dead board, creating a small credit sink without adding save-schema fields or changing ordinary contract generation. Test suite: 447 tests, 100% green.

### ADR-049: Career Reset Fails Closed on Backup Failure
- **Date**: 2026-10-30
- **Status**: Accepted
- **Context**: ADR-043 promised a backup before career deletion, but both reset paths ignored a failed backup write. Because a missing career and a failed backup both returned `None`, a disk error could still delete the profile the backup was meant to protect.
- **Decision**:
  1. Distinguish "no career existed" from "backup write failed" by checking for the career file or its shadow before calling `backup_career`.
  2. If a career exists and the backup returns `None`, abort before deleting the profile, saves or engine.
  3. The terminal reports the abort and preserves the profile; the API returns HTTP 500 with a clear error and leaves state untouched.
  4. Keep empty-career resets and successful backup paths unchanged.
  5. Cover CLI and HTTP failure paths plus the existing success path.
- **Consequences**: The destructive reset now fails closed, so a backup failure cannot become data loss. Successful resets behave exactly as before. Test suite: 449 tests, 100% green.

### ADR-050: Visual Sprite System, Action Forecasts, and Lifelike Host Simulation
- **Date**: 2026-11-01
- **Status**: Accepted
- **Context**: The matrix canvas rendered every node type as an identical circle with no burst feedback; action costs were hidden so players burned CPU blind; hosts had no OS/uptime identity, no route readout, and staff were always available regardless of shift.
- **Decision**:
  1. Add presentation-only sprite registries (NODE_VISUALS, ENTITY_VISUALS, SHOP_VISUALS, PUZZLE_VISUALS, WORLD_VISUALS) plus type-shaped canvas sprites, breach particles, hunter reticles, and motion-safe reduced-motion paths; no save-schema change.
  2. Add read-only ction_forecast()/combo_rate_preview() on the engine, a GET /api/forecast endpoint, a orecast CLI command, and a GET /api/route endpoint backed by 	race_route(); all costs derive from the same mitigated_trace() formula as the real actions.
  3. Give hosts deterministic fingerprints (os_name, uptime_hours, patch_level) and staff work_shift values with host_fingerprint() reporting on-shift counts; add 	raceroute CLI and a ROUTE row on the web target card.
  4. Cover the new contracts with 	ests/test_visuals.py, 	ests/test_forecast.py, 	ests/test_sim_life.py, and /api/forecast + /api/route server tests.
- **Consequences**: Tactics become informed (exact mitigated costs, routes, host identity) while all tuned numbers stay identical; old saves load via dataclass defaults. Test suite: 473 tests, 100% green.

### ADR-051: Content Growth via Data Tables With Accepted Seed-Mapping Shift
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: The grid needed more content (hosts, payloads, rivals) without new generation code. All three content pools are plain data tables sampled by seed, so appending rows shifts per-seed outcomes.
- **Decision**: Add 3 SIDE_HOST_TEMPLATES rows (postgres:5433, smb:139, https:8443, existing services only), 2 KNOWN_CVES rows (postgres, smb, inside existing stat bands), and 1 RIVAL_ROSTER row (Nulljack, skill 2, appended). No generator, UI, or numbers logic changes; reachability is asserted at table level by tests.
- **Consequences**: Deterministic per code version, but run replays and dailies differ across this patch: rng.sample over 9 templates and rng.choice over 4 rivals remap seeds. Old saves load unchanged (additive rows only).

### ADR-052: Menu keeper at HEAD shows the grown main menu
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: The 10-28 menu keeper predates the longer briefing, difficulty/allegiance pickers and CONTINUE/DAILY RUN buttons; in-game views have no deep links and click control was unavailable.
- **Decision**: Register `2026-11-03-menu.png` (`python -m cyberpulse.cli --web --port 9000`, headless Edge 1440x900, commit `26693b8`) in `.aikit/media.json` and the README `aegean:screenshots` block; keep the 10-28 menu as the before in the pair. In-game views wait for click control.
- **Consequences**: README proves the menu evolution honestly. Reproduce with the serve plus headless `--screenshot` above.

### ADR-053: Lay-low forecast honesty, topology label legibility, puzzle tolerance display
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: Stage 1/2 audit found three narrow gaps: action_forecast(lay_low) reported trace_gain 0 with no cooling while lay_low cools -2%/turn pre-patrol; matrix canvas node/IP/type labels sat 11-12px apart with no halo so edges swallowed them and the stage could collapse to min-height 0; the frequency puzzle modal showed TRIES but hid the real +-0.8 GHz tolerance the server already sends, so players tuned blind. Frequency fairness proof (50-seed binary-search solver, 6/50 solved) shows the 0.8 tolerance over 20-99 GHz in 3 attempts remains hard; no tolerance/attempts numbers change here, only its display.
- **Decision**:
  1. Engine forecast only: lay_low returns trace_reduction=min(trace,2*turns) and projected_trace pre-patrol plus a note naming ghost cooling and residual patrol/hunter/ambient drift; trace_gain stays 0, no lay_low behavior change.
  2. Layout only: .matrix-stage min-height 380px and .matrix-canvas-container min-height 300px so the canvas keeps room at 1280px; legend wrap/scroll and responsive breakpoints unchanged.
  3. Presentation only: canvas labels get a dark halo stroke and +1-3px vertical breathing (label +15, IP +28, tag +40); frequency modal shows TRIES plus +-tolerance from the existing /api/puzzle payload and preserves it across retries.
- **Consequences**: Forecasts name cooling without promising post-ambient exactness; topology stays legible without node repositioning or new assets; puzzle odds are visible but unchanged (12% scripted solve rate filed as a Stage 4 balance failure for a follow-up DATA-table pass). Test suite: 555 tests, 100% green; aikit check 5/5 after map refresh.
