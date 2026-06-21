from datetime import datetime
from server.enrichment.base import BaseEnricher

class TimeEnricher(BaseEnricher):
    def enrich(self, reporte: dict) -> dict:
        fecha = datetime.strptime(reporte["datetime"], "%Y-%m-%d %H:%M:%S")
        reporte["dia_semana"] = fecha.weekday()
        reporte["hora"] = fecha.hour
        reporte["franja_horaria"] = self._franja(fecha.hour)
        return reporte

    @staticmethod
    def _franja(hora: int) -> str:
        if 6 <= hora < 12: return "mañana"
        if 12 <= hora < 19: return "tarde"
        if 19 <= hora < 24: return "noche"
        return "madrugada"