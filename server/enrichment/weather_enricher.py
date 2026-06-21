import requests
from server.enrichment.base import BaseEnricher

class WeatherEnricher(BaseEnricher):
    def enrich(self, reporte: dict) -> dict:
        try:
            fecha = reporte["datetime"].split(" ")[0]
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": reporte["lat"], "longitude": reporte["long"],
                "start_date": fecha, "end_date": fecha,
                "hourly": "temperature_2m,precipitation"
            }
            resp = requests.get(url, params=params, timeout=5)
            reporte["clima"] = resp.json().get("hourly")
        except requests.RequestException:
            reporte["clima"] = None
        return reporte