"""Procedural cyberspace network generator with deterministic topology."""

import random
from typing import Any, Dict, List

from cyberpulse.models import (
    EmployeeProfile,
    FirewallPolicy,
    FirewallRule,
    HostAntivirus,
    HostFirewall,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    SecurityAwarenessLevel,
    VirtualFile,
)

# Side-subnet hosts sit beside the fixed campaign spine. The seed chooses which
# templates appear, their security, puzzle, payout and which spine hosts they hang
# from, so two runs scan different routes and the contract board draws from a
# wider pool without disturbing the story targets.
SIDE_HOST_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Cold Storage Depository",
        "hostname": "coldstore.sprawl.internal",
        "payload": "Escrowed corporate bearer bonds",
        "file_path": "/data/escrow_ledger.dat",
        "file_size_kb": 48,
        "content": "ESCROW_ID,BOND_OWNER,AMOUNT\nESC-7712,OmniCorp Holdings,$880000",
        "port": 445,
        "service": "smb",
        "version": "Samba 4.6",
        "exploit_tool": "smb_relay",
        "employee": ("Nadia Rho", "Vault Custodian", "nrho@coldstore.sprawl", "smb_share_token=COLD-7712"),
        "antivirus": ("DefenderBasic", "v1.4", 10, 2),
    },
    {
        "name": "Clinic Records Node",
        "hostname": "clinic.sprawl.internal",
        "payload": "Cortex-implant patient index",
        "file_path": "/records/neural_patient_index.db",
        "file_size_kb": 72,
        "content": "PATIENT_ID,IMPLANT,INSURER\nPX-118,Chimera-Cortex,OmniHealth",
        "port": 5432,
        "service": "postgres",
        "version": "PostgreSQL 13",
        "exploit_tool": "sql_inject",
        "employee": ("Dr. Ilya Sen", "Clinic Administrator", "isen@clinic.sprawl", "db_ro_token=CLINIC-418"),
        "antivirus": ("SentinelCore EDR", "v3.1", 15, 3),
    },
    {
        "name": "Media Archive Relay",
        "hostname": "relay.sprawl.internal",
        "payload": "Unreleased blackmail footage",
        "file_path": "/archive/blackmail_reel.mkv",
        "file_size_kb": 256,
        "content": "REEL 09: OmniCorp board meeting, off-record transfer.",
        "port": 80,
        "service": "http",
        "version": "StreamServe 2.0",
        "exploit_tool": "web_shell",
        "employee": ("Tomas Vale", "Broadcast Engineer", "tvale@relay.sprawl", "relay_admin=MEDIA-902"),
        "antivirus": None,
    },
    {
        "name": "Logistics Dispatch Hub",
        "hostname": "dispatch.sprawl.internal",
        "payload": "Encrypted freight manifests",
        "file_path": "/shipping/manifest_encrypted.csv",
        "file_size_kb": 36,
        "content": "LANE,CARGO,DEST\nL-17,Unmarked crates,Dockside 4",
        "port": 22,
        "service": "ssh",
        "version": "OpenSSH 8.2",
        "exploit_tool": "ssh_overflow",
        "employee": ("Greta Moss", "Dispatch Lead", "gmoss@dispatch.sprawl", "ssh_dispatch_key=DISPATCH-55"),
        "antivirus": ("AegisAI Sentinel", "v5.0", 20, 3),
    },
    {
        "name": "Orbital Telemetry Cache",
        "hostname": "telemetry.sprawl.internal",
        "payload": "Orbital mirror sync telemetry",
        "file_path": "/telemetry/orbital_sync.bin",
        "file_size_kb": 160,
        "content": "SYNC WINDOW 04:00-04:12 // mirror array drift 0.003deg",
        "port": 8080,
        "service": "http",
        "version": "Telemetry API v1.3",
        "exploit_tool": "web_shell",
        "employee": ("Rune Okafor", "Orbital Analyst", "rokafor@telemetry.sprawl", "orbit_api_token=SKY-3301"),
        "antivirus": ("CyberShield Corp", "v4.2", 15, 4),
    },
    {
        "name": "Courier Dead-Drop Node",
        "hostname": "drop.sprawl.internal",
        "payload": "Dead courier's final message",
        "file_path": "/drops/dead_courier.msg",
        "file_size_kb": 8,
        "content": "If you are reading this, the name is NEXUS. Trust the Archivist.",
        "port": 21,
        "service": "ftp",
        "version": "vsftpd 3.0",
        "exploit_tool": "ftp_bounce",
        "employee": ("Sal Kore", "Drop Warden", "skore@drop.sprawl", "ftp_drop_pass=COURIER-13"),
        "antivirus": None,
    },
    {
        "name": "Ledger Replica Vault",
        "hostname": "replica.sprawl.internal",
        "payload": "Mirrored escrow ledger shard",
        "file_path": "/replica/escrow_shard.dat",
        "file_size_kb": 64,
        "content": "ESCROW_SHARD,OWNER,AMOUNT\nESC-7713,Mirror Holdings,$440000",
        "port": 5433,
        "service": "postgres",
        "version": "PostgreSQL 14",
        "exploit_tool": "sql_inject",
        "employee": ("Petra Lind", "Replica Keeper", "plind@replica.sprawl", "db_replica_token=REPLICA-209"),
        "antivirus": ("SentinelCore EDR", "v3.4", 15, 3),
    },
    {
        "name": "Print Shop Front",
        "hostname": "print.sprawl.internal",
        "payload": "Forged transit credentials",
        "file_path": "/spool/forged_passes.csv",
        "file_size_kb": 12,
        "content": "PASS_ID,BEARER,GATE\nPX-77,J. Doe,Dockside 4",
        "port": 139,
        "service": "smb",
        "version": "Samba 4.15",
        "exploit_tool": "smb_relay",
        "employee": ("Otto Fix", "Press Operator", "ofix@print.sprawl", "smb_spool_token=PRESS-081"),
        "antivirus": ("DefenderBasic", "v1.6", 10, 2),
    },
    {
        "name": "Skyline Admin Console",
        "hostname": "admin.skyline.internal",
        "payload": "Rooftop relay access codes",
        "file_path": "/admin/relay_codes.json",
        "file_size_kb": 20,
        "content": "{\"relay\": \"SKY-7\", \"code\": \"ROOFTOP-556\"}",
        "port": 8443,
        "service": "https",
        "version": "Skyline Admin TLS v2.2",
        "exploit_tool": "tls_downgrade",
        "employee": ("Vera Skye", "Console Administrator", "vskye@admin.skyline", "admin_console_pin=SKY-556"),
        "antivirus": ("AegisAI Sentinel", "v4.6", 20, 4),
    },
]

SIDE_HOST_ANCHORS = ("node_proxy_a", "node_proxy_b", "node_ice_perimeter")
SIDE_HOST_PUZZLES = ("frequency", "buffer", "hash")


OS_BY_TYPE: Dict[str, str] = {
    NodeType.GATEWAY: "OmniOS 12.4 (edge router)",
    NodeType.FIREWALL: "HardenedBSD 14 (packet filter)",
    NodeType.DATA_VAULT: "CorpLinux 6.8 LTS (vault)",
    NodeType.ICE_DEFENSE: "BlackICE RTOS 9 (countermeasure)",
    NodeType.CENTRAL_CORE: "Omega Hypervisor 10 (AI core)",
}


def host_fingerprint_fields(rng: random.Random, node_type: str, security: int) -> Dict[str, Any]:
    """Derive deterministic host identity: OS, uptime, and patch train."""
    uptime = rng.randint(48, 5200)
    patch = f"2026.{min(12, max(1, security + rng.randint(0, 3))):02d}-stable"
    return {"os_name": OS_BY_TYPE.get(node_type, "Unknown OS"),
            "uptime_hours": uptime, "patch_level": patch}


def generate_network(seed: int) -> Dict[str, Node]:
    """Generate a deterministic cyberspace infiltration network grid from seed."""
    rng = random.Random(seed)

    nodes: Dict[str, Node] = {
        "node_gateway": Node(
            node_id="node_gateway",
            name="External Border Gateway",
            node_type=NodeType.GATEWAY,
            security_level=1,
            status=NodeStatus.BREACHED,  # Player starts here
            connected_ids=["node_proxy_a", "node_proxy_b"],
            trace_rate=5,
            credits_reward=0,
            puzzle_type=None,
            os_name="OmniOS 12.4 (edge router)",
            uptime_hours=744,
            patch_level="2026.04-stable",
            ip_address="192.168.1.1",
            hostname="gw.omninet.internal",
            ports=[
                PortService(port=80, service="http", version="OmniWeb Portal v2.1", vulnerable=False, breached=True),
            ],
            filesystem=[
                VirtualFile(path="/etc/hosts", size_kb=1, content="192.168.1.1 gw.omninet\n192.168.1.10 alpha.internal\n192.168.1.20 beta.internal"),
                VirtualFile(path="/var/log/syslog", size_kb=4, content="[INFO] Border gateway routing active"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_gw_1", port=80, action="ALLOW")]),
            antivirus=None,
            employees=[
                EmployeeProfile(name="Leo Gates", role="Gate Operator", email="lgates@omninet.internal", awareness_level=SecurityAwarenessLevel.NAIVE, leaked_credential="gw_bypass_token=GW-991", work_shift="swing"),
            ],
        ),
        "node_proxy_a": Node(
            node_id="node_proxy_a",
            name="Subnet Router Alpha",
            node_type=NodeType.FIREWALL,
            security_level=1,
            status=NodeStatus.DISCOVERED,
            connected_ids=["node_gateway", "node_vault_1", "node_ice_perimeter"],
            trace_rate=10,
            credits_reward=50,
            data_payload="System architecture specs",
            puzzle_type="frequency",
            os_name="HardenedBSD 14 (packet filter)",
            uptime_hours=1310,
            patch_level="2026.02-stable",
            ip_address="192.168.1.10",
            hostname="alpha.internal",
            ports=[
                PortService(port=21, service="ftp", version="vsftpd 2.3.4", vulnerable=True, exploit_tool="ftp_bounce"),
            ],
            filesystem=[
                VirtualFile(path="/home/admin/network_map.txt", size_kb=12, content="Subnet topology routing table:\n10.0.4.15 vault.corp.finance\n172.16.1.99 blackice.defense.core", value_creds=50, is_target_data=True),
                VirtualFile(path="/var/log/auth.log", size_kb=3, content="Accepted publickey for admin from 192.168.1.1"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_a_1", port=21, action="ALLOW")]),
            antivirus=HostAntivirus(name="DefenderBasic", version="v1.2", alert_level=0, heuristic_sensitivity=2),
            employees=[
                EmployeeProfile(name="Alice Vance", role="Junior SysAdmin", email="avance@alpha.internal", awareness_level=SecurityAwarenessLevel.STANDARD, leaked_credential="ftp_admin_pass=V4nce_2026", work_shift="day"),
            ],
        ),
        "node_proxy_b": Node(
            node_id="node_proxy_b",
            name="Subnet Router Beta",
            node_type=NodeType.FIREWALL,
            security_level=2,
            status=NodeStatus.DISCOVERED,
            connected_ids=["node_gateway", "node_vault_2", "node_ice_perimeter"],
            trace_rate=15,
            credits_reward=75,
            data_payload="Admin credential fragment",
            puzzle_type="buffer",
            os_name="HardenedBSD 14 (packet filter)",
            uptime_hours=2890,
            patch_level="2026.03-stable",
            ip_address="192.168.1.20",
            hostname="beta.internal",
            ports=[
                PortService(port=22, service="ssh", version="OpenSSH 7.2p2", vulnerable=True, exploit_tool="ssh_overflow"),
            ],
            filesystem=[
                VirtualFile(path="/home/secops/credentials.bak", size_kb=8, content="vault_access_token=VAULT-8842-X\nrnd_token=RND-9921-Z", value_creds=75, is_target_data=True),
                VirtualFile(path="/var/log/secure", size_kb=5, content="Failed password for invalid user root"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_b_1", port=22, action="BLOCK")]),
            antivirus=HostAntivirus(name="SentinelCore EDR", version="v3.0", alert_level=10, heuristic_sensitivity=3),
            employees=[
                EmployeeProfile(name="Marcus Cole", role="SecOps Analyst", email="mcole@beta.internal", awareness_level=SecurityAwarenessLevel.STANDARD, leaked_credential="ssh_firewall_rule_override=RULE_ALLOW_22", work_shift="night"),
            ],
        ),
        "node_vault_1": Node(
            node_id="node_vault_1",
            name="Financial Ledger Vault",
            node_type=NodeType.DATA_VAULT,
            security_level=2,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_a"],
            trace_rate=15,
            credits_reward=250,
            data_payload="Corporate slush fund transaction logs",
            puzzle_type="hash",
            os_name="CorpLinux 6.8 LTS (vault)",
            uptime_hours=4120,
            patch_level="2026.03-stable",
            ip_address="10.0.4.15",
            hostname="vault.corp.finance",
            ports=[
                PortService(port=3306, service="mysql", version="MariaDB 10.3", vulnerable=True, exploit_tool="sql_inject"),
            ],
            filesystem=[
                VirtualFile(path="/data/corporate_slush_fund.csv", size_kb=64, content="EXEC_ID,AMOUNT,ROUTING\nCEO_OFFSHORE,$4200000,CAYMAN_SUB_99\nCFO_RESERVE,$1850000,ZURICH_NODE_12", value_creds=250, is_target_data=True),
                VirtualFile(path="/var/log/mysql.log", size_kb=16, content="Query: SELECT * FROM offshore_accounts"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_v1_1", port=3306, action="BLOCK")]),
            antivirus=HostAntivirus(name="CyberShield Corp", version="v4.0", alert_level=15, heuristic_sensitivity=4),
            employees=[
                EmployeeProfile(name="Diana Prince", role="Chief Financial Officer", email="dprince@corp.finance", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="vault_db_root_auth=CFO_PRINCE_SECRET", work_shift="day"),
            ],
        ),
        "node_vault_2": Node(
            node_id="node_vault_2",
            name="Research & Prototype Archive",
            node_type=NodeType.DATA_VAULT,
            security_level=3,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_b"],
            trace_rate=20,
            credits_reward=350,
            data_payload="Classified Neural Interface schematic",
            puzzle_type="buffer",
            os_name="CorpLinux 6.8 LTS (vault)",
            uptime_hours=980,
            patch_level="2026.04-stable",
            ip_address="10.0.4.50",
            hostname="rnd.prototype.archive",
            ports=[
                PortService(port=8080, service="http", version="Prototype Dev API v1.0", vulnerable=True, exploit_tool="web_shell"),
            ],
            filesystem=[
                VirtualFile(path="/research/neural_interface.blueprint", size_kb=128, content="PROJECT CHIMERA: Direct cortex neural override matrix firmware specifications", value_creds=350, is_target_data=True),
                VirtualFile(path="/var/log/audit.log", size_kb=8, content="Checkout: Neural schematic rev 4.2"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_v2_1", port=8080, action="BLOCK")]),
            antivirus=HostAntivirus(name="AegisAI Sentinel", version="v5.1", alert_level=20, heuristic_sensitivity=4),
            employees=[
                EmployeeProfile(name="Dr. Victor Stone", role="Lead AI Architect", email="vstone@rnd.prototype", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="chimera_debug_key=NEURAL_OVERRIDE_42", work_shift="night"),
            ],
        ),
        "node_ice_perimeter": Node(
            node_id="node_ice_perimeter",
            name="Black ICE Defense Cluster",
            node_type=NodeType.ICE_DEFENSE,
            security_level=4,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_a", "node_proxy_b", "node_central_core"],
            trace_rate=30,
            credits_reward=150,
            data_payload="Root clearance security token",
            puzzle_type="frequency",
            os_name="BlackICE RTOS 9 (countermeasure)",
            uptime_hours=5010,
            patch_level="2026.05-stable",
            ip_address="172.16.1.99",
            hostname="blackice.defense.core",
            ports=[
                PortService(port=443, service="https", version="Sentinel ICE Gateway v4", vulnerable=True, exploit_tool="zero_day_ice"),
            ],
            filesystem=[
                VirtualFile(path="/sys/root_clearance.key", size_kb=2, content="ROOT_CLEARANCE_KEY: OMEGA-ACCESS-CLEARANCE-LEVEL-5", value_creds=150, is_target_data=True),
                VirtualFile(path="/var/log/ice_trace.log", size_kb=12, content="Intruder signature detected on perimeter"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_ice_1", port=443, action="BLOCK")]),
            antivirus=HostAntivirus(name="BlackICE Autonomous Hunter", version="v9.0", alert_level=30, heuristic_sensitivity=5),
            employees=[
                EmployeeProfile(name="Agent Smith", role="ICE Commander", email="smith@blackice.defense", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="ice_core_override=OMEGA_ZERO_CLEAR", work_shift="night"),
            ],
        ),
        "node_central_core": Node(
            node_id="node_central_core",
            name="Nexus Central Supercore",
            node_type=NodeType.CENTRAL_CORE,
            security_level=5,
            status=NodeStatus.LOCKED,
            connected_ids=["node_ice_perimeter"],
            trace_rate=40,
            credits_reward=1000,
            data_payload="PROJECT OMEGA: Master AI Decryption Keys",
            puzzle_type="hash",
            os_name="Omega Hypervisor 10 (AI core)",
            uptime_hours=8760,
            patch_level="2026.06-stable",
            ip_address="172.16.80.1",
            hostname="nexus.master.supercore",
            ports=[
                PortService(port=8888, service="tcp", version="Project Omega AI Core v1.0", vulnerable=True, exploit_tool="neural_exploit"),
            ],
            filesystem=[
                VirtualFile(path="/core/master_ai_keys.enc", size_kb=256, content="PROJECT OMEGA: Master AI Decryption Keys & Autonomous Model Weights", value_creds=1000, is_target_data=True),
                VirtualFile(path="/var/log/kernel.log", size_kb=32, content="Supercore kernel online. Decryption matrix active."),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_core_1", port=8888, action="BLOCK")]),
            antivirus=HostAntivirus(name="Omega Sentinel AI", version="v10.0", alert_level=40, heuristic_sensitivity=5),
            employees=[
                EmployeeProfile(name="Root Executive", role="Master AI Controller", email="nexus@omega.supercore", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="root_master_key=SUPERCORE_DECRYPT_ALL", work_shift="night"),
            ],
        ),
    }

    _generate_side_hosts(rng, nodes)
    return nodes


def _generate_side_hosts(rng: random.Random, nodes: Dict[str, Node]) -> None:
    """Attach 2-3 seeded side hosts to the fixed campaign spine.

    The campaign hosts, their IDs, IPs and story files stay untouched. Side hosts
    are ordinary LOCKED nodes wired to early anchors, so breaching an anchor
    reveals them for exploration, contracts and loot.
    """
    count = rng.randint(2, 3)
    templates = rng.sample(SIDE_HOST_TEMPLATES, count)
    for index, template in enumerate(templates, start=1):
        security = rng.randint(1, 3)
        reward = 60 + security * 20 + rng.randrange(0, 31)
        trace_rate = 10 + security * 5 + rng.randrange(0, 6)
        puzzle_type = rng.choice(SIDE_HOST_PUZZLES)
        node_id = f"node_side_{index:02d}"

        anchors = [rng.choice(("node_proxy_a", "node_proxy_b"))]
        extra_anchor = rng.choice(SIDE_HOST_ANCHORS)
        if extra_anchor not in anchors:
            anchors.append(extra_anchor)

        employee_name, role, email, leaked_credential = template["employee"]
        firewall = HostFirewall(
            rules=[FirewallRule(rule_id=f"fw_{node_id}_1", port=template["port"], action="BLOCK")]
        )
        antivirus = None
        if template["antivirus"]:
            av_name, av_version, alert_level, sensitivity = template["antivirus"]
            antivirus = HostAntivirus(
                name=av_name,
                version=av_version,
                alert_level=alert_level,
                heuristic_sensitivity=sensitivity,
            )

        fp = host_fingerprint_fields(rng, NodeType.DATA_VAULT, security)
        shift = rng.choice(("day", "day", "day", "night", "swing"))
        node = Node(
            node_id=node_id,
            name=template["name"],
            node_type=NodeType.DATA_VAULT,
            security_level=security,
            status=NodeStatus.LOCKED,
            connected_ids=list(anchors),
            trace_rate=trace_rate,
            credits_reward=reward,
            data_payload=template["payload"],
            puzzle_type=puzzle_type,
            os_name=fp["os_name"],
            uptime_hours=fp["uptime_hours"],
            patch_level=fp["patch_level"],
            ip_address=f"10.0.9.{20 + index}",
            hostname=template["hostname"],
            ports=[
                PortService(
                    port=template["port"],
                    service=template["service"],
                    version=template["version"],
                    vulnerable=True,
                    exploit_tool=template["exploit_tool"],
                )
            ],
            filesystem=[
                VirtualFile(
                    path=template["file_path"],
                    size_kb=template["file_size_kb"],
                    content=template["content"],
                    is_target_data=True,
                    value_creds=reward,
                ),
                VirtualFile(
                    path="/var/log/access.log",
                    size_kb=2,
                    content="[INFO] Remote session opened by unknown operator.",
                ),
            ],
            firewall=firewall,
            antivirus=antivirus,
            employees=[
                EmployeeProfile(
                    name=employee_name,
                    role=role,
                    email=email,
                    awareness_level=SecurityAwarenessLevel.STANDARD,
                    leaked_credential=leaked_credential,
                    work_shift=shift,
                )
            ],
        )
        nodes[node_id] = node
        for anchor in anchors:
            nodes[anchor].connected_ids.append(node_id)
