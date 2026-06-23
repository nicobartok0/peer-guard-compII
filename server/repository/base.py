from abc import ABC, abstractmethod

class BaseRepository(ABC):

    @abstractmethod
    def save(self, reporte: dict) -> None:
        pass