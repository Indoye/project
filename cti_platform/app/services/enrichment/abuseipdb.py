"""AbuseIPDB enrichment service (IP reputation)."""
import httpx
from typing import Optional
from app.core.config import get_settings

ABUSEIPDB_BASE = "https://api.abuseipdb.com/api/v2"


async def enrich_ip(ip: str) -> Optional[dict]:
    settings = get_settings()
    if not settings.abuseipdb_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ABUSEIPDB_BASE}/check",
            headers={
                "Key": settings.abuseipdb_api_key,
                "Accept": "application/json",
            },
            params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": True},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {})
        return {
            "source": "abuseipdb",
            "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
            "country_code": data.get("countryCode"),
            "isp": data.get("isp"),
            "domain": data.get("domain"),
            "total_reports": data.get("totalReports", 0),
            "num_distinct_users": data.get("numDistinctUsers", 0),
            "last_reported_at": data.get("lastReportedAt"),
            "is_tor": data.get("isTor", False),
            "usage_type": data.get("usageType"),
        }
