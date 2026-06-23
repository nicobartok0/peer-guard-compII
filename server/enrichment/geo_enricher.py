import requests
from server.enrichment.base import BaseEnricher

class GeoEnricher(BaseEnricher):


    _BARRIO_KEYS = ["neighbourhood", "suburb", "quarter", "city_district"]
    _CIUDAD_KEYS = ["city", "town", "municipality", "county"]
    _PROVINCIA_KEYS = ["state"]

    def enrich(self, reporte: dict) -> dict:
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": reporte["lat"],
                "lon": reporte["long"],
                "format": "json",
                "addressdetails": 1,  
            }
            headers = {"User-Agent": "PeerGuard/1.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            address = resp.json().get("address", {})

            reporte["barrio"]   = self._primero(address, self._BARRIO_KEYS)
            reporte["ciudad"]   = self._primero(address, self._CIUDAD_KEYS)
            reporte["provincia"] = self._primero(address, self._PROVINCIA_KEYS)

        except requests.RequestException:
            reporte["barrio"]    = None
            reporte["ciudad"]    = None
            reporte["provincia"] = None

        return reporte

    @staticmethod
    def _primero(address: dict, keys: list) -> str | None:
        for key in keys:
            valor = address.get(key)
            if valor:
                return valor
        return None