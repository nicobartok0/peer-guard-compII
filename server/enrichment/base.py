from abc import ABC, abstractmethod

class BaseEnricher(ABC):
    @abstractmethod
    def enrich(self, reporte: dict) -> dict:
        """Recibe el reporte, devuelve el reporte con campos nuevos agregados."""
        pass