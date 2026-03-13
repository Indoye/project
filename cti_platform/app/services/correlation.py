"""
MITRE ATT&CK correlation engine.

Maps IoC characteristics and enrichment signals to ATT&CK techniques.
Seed data for common techniques is provided; can be extended via the /ttps API.
"""
from typing import List
from sqlalchemy.orm import Session
from app.models.ioc import IoC, IoCType, TTP


# Heuristic rules: (condition_fn, technique_id) → auto-link TTP
RULES: List[dict] = [
    # Phishing / Initial Access
    {
        "technique_id": "T1566",
        "name": "Phishing",
        "tactic": "Initial Access",
        "match": lambda ioc, enrichment: (
            ioc.ioc_type == IoCType.EMAIL
            or (ioc.ioc_type == IoCType.URL and any(
                kw in ioc.value for kw in ["login", "verify", "account", "secure", "update"]
            ))
        ),
    },
    # Drive-by Compromise
    {
        "technique_id": "T1189",
        "name": "Drive-by Compromise",
        "tactic": "Initial Access",
        "match": lambda ioc, enrichment: (
            ioc.ioc_type == IoCType.URL
            and enrichment.get("virustotal", {}).get("malicious", 0) > 3
        ),
    },
    # Malicious File / User Execution
    {
        "technique_id": "T1204",
        "name": "User Execution",
        "tactic": "Execution",
        "match": lambda ioc, enrichment: ioc.ioc_type == IoCType.FILE_HASH,
    },
    # Command and Control - commonly malicious IPs with open ports
    {
        "technique_id": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
        "match": lambda ioc, enrichment: (
            ioc.ioc_type == IoCType.IP
            and len(enrichment.get("shodan", {}).get("open_ports", [])) > 5
        ),
    },
    # Exploit Public-Facing Application (CVEs on host)
    {
        "technique_id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "match": lambda ioc, enrichment: (
            len(enrichment.get("shodan", {}).get("vulns", [])) > 0
        ),
    },
    # Tor / Proxy
    {
        "technique_id": "T1090",
        "name": "Proxy",
        "tactic": "Command and Control",
        "match": lambda ioc, enrichment: (
            enrichment.get("abuseipdb", {}).get("is_tor", False)
        ),
    },
    # High AbuseIPDB score → Brute Force
    {
        "technique_id": "T1110",
        "name": "Brute Force",
        "tactic": "Credential Access",
        "match": lambda ioc, enrichment: (
            ioc.ioc_type == IoCType.IP
            and enrichment.get("abuseipdb", {}).get("abuse_confidence_score", 0) >= 70
        ),
    },
    # Domain → DNS-based C2
    {
        "technique_id": "T1568",
        "name": "Dynamic Resolution",
        "tactic": "Command and Control",
        "match": lambda ioc, enrichment: (
            ioc.ioc_type == IoCType.DOMAIN
            and enrichment.get("virustotal", {}).get("malicious", 0) > 2
        ),
    },
]


def _get_or_create_ttp(db: Session, rule: dict) -> TTP:
    ttp = db.query(TTP).filter(TTP.technique_id == rule["technique_id"]).first()
    if not ttp:
        ttp = TTP(
            technique_id=rule["technique_id"],
            name=rule["name"],
            tactic=rule["tactic"],
            url=f"https://attack.mitre.org/techniques/{rule['technique_id']}/",
        )
        db.add(ttp)
        db.flush()
    return ttp


def correlate_ioc(db: Session, ioc: IoC) -> List[TTP]:
    """Apply heuristic rules and link matching TTPs to the IoC."""
    import json
    enrichment = {}
    if ioc.enrichment_data:
        try:
            enrichment = json.loads(ioc.enrichment_data)
        except Exception:
            pass

    matched_ttps = []
    for rule in RULES:
        try:
            if rule["match"](ioc, enrichment):
                ttp = _get_or_create_ttp(db, rule)
                if ttp not in ioc.ttps:
                    ioc.ttps.append(ttp)
                matched_ttps.append(ttp)
        except Exception:
            continue

    db.commit()
    return matched_ttps
