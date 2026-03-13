"""Shodan enrichment service (open ports, banners, vulns)."""
import httpx
from typing import Optional
from app.core.config import get_settings

SHODAN_BASE = "https://api.shodan.io"


async def enrich_ip(ip: str) -> Optional[dict]:
    settings = get_settings()
    if not settings.shodan_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SHODAN_BASE}/shodan/host/{ip}",
            params={"key": settings.shodan_api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "source": "shodan",
            "org": data.get("org"),
            "isp": data.get("isp"),
            "country_name": data.get("country_name"),
            "open_ports": data.get("ports", []),
            "hostnames": data.get("hostnames", []),
            "os": data.get("os"),
            "vulns": list(data.get("vulns", {}).keys()),
            "tags": data.get("tags", []),
        }
