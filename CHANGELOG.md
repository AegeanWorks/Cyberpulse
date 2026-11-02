# Changelog

All notable changes to CyberPulse are recorded here. The format follows Keep a Changelog, and versions use semantic versioning.

## [Unreleased] - 0.5.0 simulation + arcs + DeckOS

### Added

- In-game DeckOS computer layer: `ps` / `sysinfo` / `uptime` / `kill <pid>` / `history`, with a deterministic process table (system daemons, keylogger daemons, hunter probes, rogue miners) wired into CLI, REST (`/api/deckos`, `kill_process`), and the Web SIM modal.
- Operative loyalty arcs: three trust stages per contact with tracker (`arcs` command, `/api/arcs`, Web ARCS modal) plus two trust-gated side quests (Cold Wallet, Dead Letter Drop).
- Street-level district simulation: five districts with deterministic load/patrol/market-mood rows in `world` output, `districts` command, `/api/districts`, grid-bar chip, and SIM modal.
- Web cyberdeck upgrades: SIM + ARCS rail buttons and modals, DeckOS kill controls, alert-tier body theming, high-contrast toggle (H), keyboard shortcuts (G/T/S/O/V/L/J/Q/N/D), responsive narrow-screen layout, focus-visible outlines, and security-scaled canvas node glow.
- Live arc bonuses: Zero trust 2+ halves counter-trace to 1 CPU; Kilo trust 4+ lifts daemon yields 10%; Archivist trust 4+ deepens wipe-logs to 25% trace; Mira trust 6+ cools alert an extra point per turn on Syndicate contracts. The `arcs` panel flags live bonuses.
- District sweep pressure: under BLACK alert (75%+), two or more heavy-patrol districts run a coordinated +1% trace sweep each turn.
- Deterministic district rolls now use SHA-256 instead of `hash()`, so street simulation is stable across processes and replays.
- Arc epilogues: operatives at loyalty stage 3 (trust 6) add a dedicated stanza to the run legacy in both interfaces.
- Cross-interface shell history: Web cyberdeck actions mirror into the run-scoped DeckOS `history` (meta actions like save/load stay out), so the terminal and the Web HUD read the same command log.
- Trace-critical HUD state: the TRACE gauge pulses red at 80%+ via a `trace-critical` body class, alongside the existing alert-tier theming.
- The SIM modal's DeckOS section now shows the run-scoped shell history (last 8 entries), so Web players can see the shared terminal/cyberdeck command log the `history` command reads.
- Hosts live on the street map: every node is deterministically assigned to one of the five districts, shown in `probe` reports, the Web target card, and `/api/state`. Breaching a host while its district runs a heavy patrol adds +1% trace (DISTRICT HEAT) — the street layer now bites the core loop.
- Districts are navigable: the `districts` command and SIM modal list each district's host roster, and hosts under heavy patrol wear a dashed red cordon on the matrix.
- Breach forecasts stay honest under patrol pressure: `forecast quickhack` adds the mitigated DISTRICT HEAT point and names it when the target's district is heavy.
- The matrix legend now documents the HOT trace-heat core and the SWEEP heavy-patrol cordon, and district host rosters click through to the target card.
- District heat is warned at decision points: the BREACH button tooltip names the hot district, breached hosts highlight in SIM rosters, and quickhack tooltips already carry the live forecast.
- Hunters walk named streets: deployment, clash, and proximity messages name the host's district grid, and DeckOS hunter probes report which district they are sweeping.
- The job board went street-level: active contracts and posted offers print their target district in the terminal and Web HUD (`/api/state` carries per-offer tags), the hunter radar names each unit's district, and re-secure headlines note which grid the corp took back.
- Movement reads the map: crossing into a new district prints its name and flavor, and informant reveals name the district grid the new host sits on.
- The wire reads the map too: ambient grid events carry their district (fixed beats keep home turf; brownouts and ICE patrols strike the heaviest-load grid), on both the feed and the news wire.
- Recon and social paths name streets: intel reveals, social success/fail lines, and social forecasts all carry the target's district grid.
- The run legacy tracks territory: `run_summary` reports compromised districts and the legacy banner prints grid coverage (N/5 districts), so conquest reads as city control.
- The Web end-of-run banner shows GRID HELD territory alongside hosts breached, fed by the same summary the terminal prints.
- The wire names territory too: re-secure headlines carry the district grid, and the `world` readout lists host counts per district.
- `forecast move` previews terminal transfers (CPU, trace, turn) and names the district grid being entered, so the district-crossing beat never surprises.
- `forecast social` / `bypass` / `evade` close the preview gap on infiltration prep: lure odds with shift context, cheapest-method bypass costs against live blocked ports, and EDR evasion costs — all sharing the execution formulas.
- `forecast deploy` / `reveal` / `forge` complete the preview system: passive daemon yields (Kilo-boosted), fragment-gated intel scans, and forge costs — every resource-spending action is now previewable.
- `forecast proxy` / `sever` cover tunnel play (dampening math, 15% dump), the Web OVERDRIVE tooltip now shows the 1-CPU Kilo price when the arc is live, and the `arcs` tracker names the cheap-overdrive bonus.
- `forecast counter_hunter` lists ready vs missing countermeasures (logic_bomb, ghost_protocol, cpu_burst) against the active hunter, so EDR duels are planned, not improvised.
- Arc-unlock announcements: every trust gain flows through one choke point that posts a `ARC ADVANCE` story beat (with the stage bonus) whenever a loyalty threshold is crossed — quest accepts, favors, alliances, and contract payouts all feed it.
- Archivist arc opens a fourth contract-offer slot at trust 2+, so the job board visibly widens as the Dead Letters arc progresses.
- District sweeps hit the news wire, so coordinated lockdowns read as city events rather than silent trace.
- Arc bonuses are visible everywhere: `arcs` output, the Web ARCS cards, and operative `talk` channels name the live arc stage, so relationship progress is discoverable before it pays off.
- Trace-heat cockpit light: the current-node core on the matrix cools cyan and heats toward red as trace climbs past 25%.
- Kilo's first arc stage is real: trust 2+ halves overdrive to 1 CPU, with the forecast and combat message showing the discount.
- The remaining arc stages are now mechanical too: Mira holds rush windows a turn longer (trust 2+) and covers contract declines (trust 4+); Kilo's legend earns +1 street standing on victory (trust 6+); Zero's Black ICE reads appear in probe forecasts (trust 4+) and equals get an extended Act III epilogue (trust 6+). Every loyalty stage now does something.
- Operative channels carry the loyalty arc: `contacts`, `contact talk`, `list_contacts`, and the Web contacts modal all name the live arc stage.
- Arc-aware forecasts: `forecast counter`/`counter_rival` shows the Zero-discounted 1 CPU cost, and `forecast wipe` shows the Archivist deep-scrub 25% reduction with projected trace — previews can never drift from the real costs.

### Changed

- `/api/state` now carries `deckos`, `arcs`, and `districts` snapshots for the Web HUD.
- `world` CLI output and the grid ticker surface district rows; saves record run-scoped command history (`cmd_history`).


## [0.4.0] - 2026-10-30

### Added

- Three manual save slots plus autosave, legacy slot-1 compatibility, slot names, rename/delete, and a slot archive in both interfaces.
- Bounded career run history, sixteen milestones, a transparent run score, and a difficulty-filtered top-ten Hall of Fame.
- Deterministic daily runs with date-seeded modifiers, per-day bests, and consecutive-day streaks.
- Seed replay from the run archive.
- Three difficulty modes with trace, starting-condition and contract-pay modifiers.
- A contract-stealing rival netrunner with counter-tracing, HUD chip and Web modal.
- A one-use Dead Man's Switch lockout insurance consumable.
- A first-run field manual with live scan/probe/breach/loot/extract checkpoints.
- Career aliases, persisted Web theme/audio/CRT preferences and reduced-motion styles.
- Syndicate and Street standing, named ranks, promotion rewards, contract-pay bonuses and Black Market discounts.
- Guarded career reset with automatic backup and save cleanup.

### Changed

- Centralized the version in `cyberpulse.__version__`, derived the CLI banner from it, and added `--version`.
- Aligned `pyproject.toml`, the CLI banner and package metadata at 0.4.0.
- Added difficulty and faction context to run history, hall entries, save payloads and state responses.

### Fixed

- Corrupt primary saves can no longer overwrite a good `.bak`; non-finite metadata falls back safely.
- Faction snapshots survive save/load and are not retroactively changed by later career standing.
- Autosave cannot overwrite another run's checkpoint after a load.
- Same-day daily repeats cannot inflate streaks.

## [0.3.0] - 2026-10-26

- Public baseline with procedural networks and puzzles, five-act story, operatives, Syndicate contracts, living-grid simulation, Web Cyberdeck and terminal client.
