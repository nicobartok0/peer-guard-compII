import requests
from server.enrichment.base import BaseEnricher

class WeatherEnricher(BaseEnricher):
    def enrich(self, reporte: dict) -> dict:
        try:
            fecha = reporte["datetime"].split(" ")[0]
            hora = reporte["hora"]
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": reporte["lat"], "longitude": reporte["long"],
                "start_date": fecha, "end_date": fecha,
                "hourly": "temperature_2m,precipitation"
            }
            resp = requests.get(url, params=params, timeout=5)
            hourly = resp.json().get("hourly", {})
            reporte["temperatura"] = hourly.get("temperature_2m", [])[hora]
            reporte["precipitacion"] = hourly.get("precipitation", [])[hora]
        except (requests.RequestException, IndexError, TypeError):
            reporte["temperatura"] = None
            reporte["precipitacion"] = None
        return reporte