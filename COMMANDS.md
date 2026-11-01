# CyberPulse In-Game Commands

## In-Game Commands (Authentic Simulation & Tactical Netrunning)

| Command | Action | Simulation Role |
|---|---|---|
| `myip` / `whoami` | Display player's local CyberDeck identity (`10.99.0.2` / `rig.netrunner.local`) | Virtual localhost identity & rig telemetry |
| `myfiles` / `ls local` | List files on player's local CyberDeck drive (`/home/deck`, `/bin`, `/loot`) | Local rig file inspection & stolen loot archive |
| `cat <file>` | Inspect local cyberdeck files or remote breached host files | Data surveillance & loot inspection |
| `probe <ip>` / `nmap <ip>` | Scan open network ports, service banners, and software versions; reports OS, uptime, patch train, and staff on shift | Reconnaissance & vulnerability detection |
| `traceroute <ip>` / `route <ip>` | Trace hop path and per-hop latency from the active terminal to the target | Route planning & network topography |
| `firewall <ip>` / `fw` | Inspect target host network firewall rules and packet filtering policies | Perimeter security intelligence |
| `bypass <ip> <port> [m]` | Bypass blocked firewall port via `knock`, `fragment`, or `tunnel` | Ingress filtering bypass & packet crafting |
| `av <ip>` / `edr` | Inspect active Antivirus/EDR engine, alert level, and daemon quarantine log | Endpoint detection & response intelligence |
| `evade <ip> [method]` | Blind host AV scanner via `rootkit` (hook) or `spoof` (morphing) | Active memory EDR evasion & daemon protection |
| `cve` / `exploits` | Catalog weaponized CVE exploits, requirements (RAM/CPU), and stealth ratings | Exploit payload arsenal & zero-day repertoire |
| `exploit <ip> <port> [cve]` | Weaponize a specific CVE or auto-match zero-day payload to breach open port | System penetration & root shell acquisition |
| `social <ip> [vec] [emp]` | Multi-vector social engineering (`spear_phish`, `pretext`, `bait`, `vishing`); success odds follow the in-game shift | Human factor exploitation & credential harvesting |
| `phish <ip>` | Legacy quick spear-phish credential lure against target staff | Social engineering & security downgrade |
| `ls [ip]` | List virtual directory contents on breached host (`/etc`, `/home`, `/data`) | Target file discovery & intel gathering |
| `steal <file>` / `download` | Exfiltrate data; payout tracks the live black-market index and archives a copy to rig `/loot/` | Data theft & primary heist objective |
| `keylogger [ip]` | Deploy passive background keylogger daemon on breached host (yield scales with host security tier) | In-game persistent background surveillance |
| `daemons` | Monitor all active background listener daemons and their credit yields | Passive income & risk telemetry |
| `workshop` | Inspect malware crafting lab recipes and synthesis requirements | In-game virus & exploit workshop |
| `craft <recipe>` | Synthesize custom virus chips (`keylogger_daemon`, `worm_replicator`, etc.) | Custom malware creation |
| `wipe_logs [ip]` | Clear access logs and sanitize intruder timestamps (drops active ICE trace by 20%) | Anti-forensics & trace mitigation |
| `move <ip>` / `ssh <ip>` | Transfer your active terminal session to an adjacent breached host | Network lateral movement |
| `scan` | Scan surrounding connected nodes to reveal topology and IP addresses | Information foraging & strategic autonomy |
| `spoof` | Burn 3 CPU cycles to bounce your proxy and reduce security trace by 25% | Risk mitigation & resource trade-offs |
| `overdrive` | Burn 2 CPU and 8% trace to stack +1 combo and +10 unbanked credits | Voluntary risk, combo priming & dopamine anticipation |
| `stance <mode>` / `proxy <ip>` / `quickhack <ip>` / `intel <reveal\|forge>` | Shift deck stance, route a proxy hop, instant-breach a tier 1-2 host, or spend threat intel | Tactical resource & risk modulation |
| `lay_low [1-3]` / `wait` | Ghost the connection for 1-3 turns: +1 CPU and up to -2% trace per turn while the grid keeps moving | Downtime recovery & shift-aware risk management |
| `forecast <action> [target]` / `preview` / `odds` | Preview CPU/trace/turn costs before committing (`scan`, `probe`, `overdrive`, `spoof`, `lay_low`, `quickhack`, `jackout`) | Risk transparency & informed push-your-luck |
| `world` / `city` / `grid` | Show the in-game clock, shift doctrine, grid alert, market index, daily modifier, and latest headlines | Living world awareness & consequence telemetry |
| `news` / `wire` | Read the generated grid news wire (`news 20` for a longer feed) | Diegetic feedback & attribution of events |
| `hunter` / `radar` | Display active NetWatch Hunter threat assessment, location, distance, and scent | Counter-surveillance & proximity telemetry |
| `counter [method]` | Deploy tactical countermeasures against hunter (`logic_bomb`, `ghost_protocol`, `cpu_burst`) | Active counter-defense & hunter neutralization |
| `story` | Show the current act, story log, and briefing | Narrative orientation & campaign immersion |
| `contract` / `bounty` | Open the job board: active job plus offers; `accept_job <id>` takes one, `drop_offer <id>` passes one for 30 CR or a one-turn cooldown, `decline_contract` abandons the active job | Job choice, clock & risk/reward |
| `reroll` | Spend 50 CR to replace the posted contract board with fresh offers | Board agency & credit sink |
| `hall [all\|easy\|normal\|hard]` | Show the career Hall of Fame, optionally filtered by difficulty | Difficulty-aware mastery tracking |
| `alias <name>` | Set the career dossier handle (trimmed, 24 characters max) | Identity & personalization |
| `reset_career CONFIRM` | Back up `career.backup.json`, clear the profile and all save slots, and start a fresh run | Safe restart |
| `tutorial` / `tips` | Show the first-run field manual with live scan, probe, breach, loot and extraction checkboxes | Onboarding & core-loop clarity |
| `rival` | Inspect the run's rival netrunner, stolen contract count, and next scheduled move | Peer-antagonist awareness |
| `counter_rival` | Burn 2 CPU to trace the rival and delay their next contract grab by 5 turns | Counterplay & tempo decision |
| `quests` / `missions` | Open the mission board with progress, rewards, and available jobs | Goal clarity & Zeigarnik completion pressure |
| `contacts` / `crew` | List channels, trust tiers, tier dialogue, and favors; Inner Circle unlocks a second favor | Relationship tracking & social capital |
| `contact <handle> [talk\|job\|favor\|ally\|defy]` | Talk to an operative, accept their job, spend a one-time favor, or make Agent Zero's Act III alliance choice | Character interaction & story branching |
| `accept <quest_id>` | Accept an available side quest from the mission board | Player-authored goals & autonomy |
| `cash_out` / `jackout` | Disconnect and bank all unbanked credits; trace 50%+ adds an ICE surge, and 85%+ can burn the run at the extraction point | Loss aversion & push-your-luck extraction |
| `shop` | Open the Black Market for permanent hardware, one-use consumables, Street standing and patron discounts | Anticipation of reward & meta-progression |
| `buy <item_id>` | Purchase permanent cyberdeck upgrades with banked career credits | Long-term investment & competence scaling |
| `career` | View lifetime operative dossier, breach stats, best neural combo, installed cyberware, milestone badges, faction ranks/standing, daily streak/bests, Hall of Fame, and the last five settled runs | Identity, pride & meta-game mastery |
| `status` | Display cyberdeck specs, unbanked credits, and active syndicate contract | HUD awareness & contract progress tracking |
| `save [1\|2\|3] [name]` | Atomically persist the live run to a manual slot with an optional run label (default slot 1) | Power-loss protection & parallel runs |
| `load [1\|2\|3\|auto]` | Restore a manual slot or the autosave checkpoint | Resumption fidelity |
| `saves` | List every checkpoint with label, turn, credits, trace, act and timestamp | Save-slot awareness & recovery choice |
| `rename <1\|2\|3> <name>` | Relabel an existing checkpoint without changing its progress or timestamp | Archive organization |
| `delete <1\|2\|3\|auto>` | Remove one checkpoint; the live run is untouched | Stale-run cleanup |
| `replay <1-5>` | Start a fresh run from the seed of a recent archived run (1 = newest) | Seed reuse & practice |
| `quit` | Sever connection and terminate terminal link | Clean exit |
