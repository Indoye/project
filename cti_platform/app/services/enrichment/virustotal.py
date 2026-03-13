"""VirusTotal v3 enrichment service."""
import httpx
from typing import Optional
from app.core.config import get_settings


VT_BASE = "https://www.virustotal.com/api/v3"


async def enrich_ip(ip: str) -> Optional[dict]:
    settings = get_settings()
    if not settings.virustotal_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{VT_BASE}/ip_addresses/{ip}",
            headers={"x-apikey": settings.virustotal_api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        return {
            "source": "virustotal",
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "country": data.get("country"),
            "asn": data.get("asn"),
            "as_owner": data.get("as_owner"),
            "reputation": data.get("reputation", 0),
        }


async def enrich_domain(domain: str) -> Optional[dict]:
    settings = get_settings()
    if not settings.virustotal_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{VT_BASE}/domains/{domain}",
            headers={"x-apikey": settings.virustotal_api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        return {
            "source": "virustotal",
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "categories": data.get("categories", {}),
            "reputation": data.get("reputation", 0),
            "creation_date": data.get("creation_date"),
        }


async def enrich_hash(file_hash: str) -> Optional[dict]:
    settings = get_settings()
    if not settings.virustotal_api_key:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{VT_BASE}/files/{file_hash}",
            headers={"x-apikey": settings.virustotal_api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        return {
            "source": "virustotal",
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "file_type": data.get("type_description"),
            "file_size": data.get("size"),
            "names": data.get("names", [])[:5],
            "tags": data.get("tags", []),
        }


async def enrich_url(url: str) -> Optional[dict]:
    """Encode URL in base64 (no padding) as required by VT API."""
    import base64
    settings = get_settings()
    if not settings.virustotal_api_key:
        return None
    url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{VT_BASE}/urls/{url_id}",
            headers={"x-apikey": settings.virustotal_api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        return {
            "source": "virustotal",
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "final_url": data.get("last_final_url"),
            "title": data.get("title"),
        }
