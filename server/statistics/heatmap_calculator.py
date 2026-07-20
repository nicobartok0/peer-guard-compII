import os
import json
from pathlib import Path
from dotenv import load_dotenv
import redis
from sqlalchemy import text
from server.repository.db import engine

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_redis = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=2,
    decode_responses=True,  
)

FRANJAS = ("mañana", "tarde", "noche", "madrugada")
ZONA_SIN_BARRIO = "Sin barrio"


class HeatmapCalculator:

    def calcular(self) -> None:
        """
        Recalcula el heatmap completo desde PostgreSQL y lo escribe en Redis estado.
        Lee todos los reportes, agrupa por (barrio, franja_horaria), calcula el
        promedio de severidad y el total de reportes, y persiste en Redis.
        """
        agregados = self._agregar_desde_db()
        self._escribir_en_redis(agregados)

    def _agregar_desde_db(self) -> dict:
        """
        Consulta PostgreSQL y devuelve un dict con la estructura:
        {
            "barrio": {
                "franja_horaria": {"suma_severidad": X, "total": N},
                ...
            },
            ...
        }
        """
        query = text("""
            SELECT
                COALESCE(barrio, :sin_barrio)  AS zona,
                franja_horaria,
                SUM(severidad)                 AS suma_severidad,
                COUNT(*)                       AS total
            FROM reports
            GROUP BY zona, franja_horaria
        """)

        agregados = {}

        with engine.connect() as conn:
            filas = conn.execute(query, {"sin_barrio": ZONA_SIN_BARRIO}).fetchall()

        for fila in filas:
            zona = fila.zona
            franja = fila.franja_horaria

            if zona not in agregados:
                agregados[zona] = {}

            agregados[zona][franja] = {
                "suma_severidad": float(fila.suma_severidad),
                "total":          int(fila.total),
            }

        return agregados

    def _escribir_en_redis(self, agregados: dict) -> None:
        """
        Escribe el heatmap calculado en Redis estado.
        Cada zona es un hash con una key por franja horaria + una key 'total'.

        Estructura en Redis:
            heatmap:barrio:<zona>  →  {
                "mañana":    2.3,
                "tarde":     1.1,
                "noche":     4.7,
                "madrugada": 3.2,
                "total":     87
            }
        """
        pipe = _redis.pipeline()

        for zona, franjas in agregados.items():
            key = f"heatmap:barrio:{zona}"

            # Calculamos intensidad (promedio de severidad) por franja
            datos = {}
            total_zona = 0

            for franja in FRANJAS:
                if franja in franjas:
                    d = franjas[franja]
                    intensidad = round(d["suma_severidad"] / d["total"], 2)
                    datos[franja] = intensidad
                    total_zona += d["total"]
                else:
                    # Franja sin reportes en esta zona → intensidad 0
                    datos[franja] = 0.0

            datos["total"] = total_zona

            # Sobreescribimos el hash completo de esta zona
            pipe.delete(key)
            pipe.hset(key, mapping={k: json.dumps(v) for k, v in datos.items()})

        pipe.execute()