import requests
from server.enrichment.base import BaseEnricher

class GeoEnricher(BaseEnricher):
    def enrich(self, reporte: dict) -> dict:
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {"lat": reporte["lat"], "lon": reporte["long"], "format": "json"}
            headers = {"User-Agent": "PeerGuard/1.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            address = resp.json().get("address", {})
            reporte["barrio"] = address.get("suburb") or address.get("neighbourhood")
            reporte["ciudad"] = address.get("city") or address.get("town")
        except requests.RequestException:
            reporte["barrio"] = None
            reporte["ciudad"] = None
        return reporte