# Sistema 'Peer Guard' para precaución ciudadana

## Resumen

'Peer Guard' es un software que permite evaluar los niveles de peligrosidad a los que
uno se expone en ciertas zonas de una ciudad, en base a las experiencias reportadas
por otros usuarios. Se despliega un mapa de calor sobre el mapa, el cual está
dividido en cuadrículas del mismo tamaño que se encienden según la cantidad
de reportes que encierran, la gravedad de los mismos y la hora del día.

Este sistema está destinado a incentivar la cooperación ciudadana con el motivo
de evitar este tipo de crímenes, y que personas que muchas veces pueden no pertenecer
a un lugar sean capaces de evitar zonas peligrosas.

Este sistema está encarado a modo de examen final integrador de la materia Computación II,
Ingeniería Informática en la Universidad de Mendoza.

**Desarrollador:** Nicolás Bartolomeo Koninckx

---

## Arquitectura del sistema

![arquitectura](https://ibb.co/yFLMqTrt)

La arquitectura consiste de una serie de componentes interconectados del lado del servidor,
cuyo objetivo es procesar los reportes, expandir la información que contienen, guardarlos
en la base de datos y luego enviarlos a demanda. El sistema se divide en las siguientes
piezas clave:

---

### Main Entrypoint

#### Connection Manager (`server/connection/conn_manager.py`)

El Connection Manager maneja las conexiones entrantes utilizando sockets TCP asíncronos
(Python `asyncio`). Recibe los reportes de los clientes en formato JSON, los pasa al
Validador, y si son válidos los encola en Celery para su procesamiento. Devuelve al
cliente un ACK inmediato indicando si el reporte fue aceptado o rechazado.

#### Validador (`server/validator/validator.py`)

El Validador verifica que cada reporte cumpla con la estructura esperada antes de ser
procesado. Valida:

- Que los campos presentes sean los correctos.
- Que el tipo de crimen sea uno de los tipos válidos definidos en `types_severity.json`.
- Que la fecha tenga el formato `YYYY-MM-DD HH:MM:SS` y valores coherentes.
- Que la latitud esté en el rango [-90, 90] y la longitud en [-180, 180].
- Que el detalle no supere los 300 caracteres.

Los tipos de crimen válidos y su nivel de severidad se cargan desde
`server/validator/types_severity.json` al importar el módulo, sin leer el archivo
en cada validación.

---

### Pipeline de Enriquecimiento (`server/enrichment/`)

Los reportes validados son procesados por un pipeline de enriquecimiento implementado
con el **patrón Strategy**, donde cada enriquecedor es intercambiable e independiente.
El pipeline se ejecuta de forma asíncrona mediante **Celery** (queue `enriquecimiento`).

Cada enriquecedor hereda de `BaseEnricher` e implementa el método `enrich(reporte: dict) -> dict`.
El pipeline los ejecuta en orden, pasando el reporte de uno a otro:

| Enriquecedor | Campos que agrega |
|---|---|
| `TimeEnricher` | `dia_semana`, `hora`, `franja_horaria` |
| `SeverityEnricher` | `severidad` |
| `GeoEnricher` | `barrio`, `ciudad`, `provincia` (via Nominatim/OSM) |
| `WeatherEnricher` | `temperatura`, `precipitacion` (via Open-Meteo) |

El reporte resultante es un diccionario plano con 14 campos, todos tipos primitivos,
directamente persistible en la base de datos.

---

### Persistencia (`server/repository/` + `server/tasks/persistence.py`)

Los reportes enriquecidos son persistidos en **PostgreSQL** mediante el **patrón Repository**.

#### Repository (`server/repository/`)

- `BaseRepository`: interfaz abstracta con el método `save(reporte: dict)`.
- `ReportRepository`: implementación concreta usando **SQLAlchemy** como ORM.
- `models.py`: define el modelo `Report` con todos los campos de la tabla `reports`.
- `db.py`: centraliza el engine, la sesión y la inicialización de la base de datos.
  Al arrancar el worker, se ejecuta `init_db()` que crea la tabla `reports` si no existe
  (`CREATE TABLE IF NOT EXISTS`), y la reutiliza con los datos existentes si ya fue creada.

#### Task de persistencia

La task `persistir` corre en la queue `persistencia` de Celery. Incluye reintentos
automáticos con backoff exponencial ante fallos de conexión a la base de datos.

---

### Infraestructura (`docker-compose.yaml`)

Todos los servicios de infraestructura se levantan con Docker Compose:

| Servicio | Imagen | Uso |
|---|---|---|
| `redis` | `redis:7-alpine` | Broker de mensajes y backend de resultados de Celery |
| `postgres` | `postgres:16-alpine` | Base de datos principal |

La base de datos persiste sus datos en un volumen Docker (`postgres_data`), por lo que
sobrevive reinicios del contenedor.

---

### Celery (`server/celery/celery_app.py`)

Celery gestiona el procesamiento distribuido y asíncrono. Está configurado con tres queues:

- `enriquecimiento`: procesamiento del pipeline de enrichers.
- `persistencia`: guardado en base de datos.
- `estadistica`: (pendiente) cálculo de métricas para el mapa de calor.

**Celery Beat** está disponible para disparar tareas periódicas (recálculo del heatmap).

---

### Scripts

#### `run.sh`

Script de inicio del sistema. Al ejecutarlo:

1. Verifica que Redis y PostgreSQL estén escuchando en los puertos configurados.
2. Si no están corriendo, ejecuta `docker compose up -d` y espera a que ambos servicios estén listos.
3. Abre el Connection Manager y el worker de Celery en terminales separadas (compatible con Hyprland/kitty, tmux, y terminales estándar).

---

## Estructura del proyecto

```
server/
├── celery/
│   └── celery_app.py         # Configuración de Celery (broker, queues, routing)
├── connection/
│   ├── conn_manager.py       # Main entrypoint (sockets TCP async)
│   └── client_sim.py         # Simulador de cliente para testing
├── enrichment/
│   ├── base.py               # Interfaz BaseEnricher
│   ├── pipeline.py           # EnrichmentPipeline (orquestador)
│   ├── time_enricher.py
│   ├── severity_enricher.py
│   ├── geo_enricher.py
│   └── weather_enricher.py
├── repository/
│   ├── base.py               # Interfaz BaseRepository
│   ├── models.py             # Modelo SQLAlchemy (tabla reports)
│   ├── db.py                 # Engine, sesión, init_db()
│   └── report_repository.py  # Implementación concreta
├── tasks/
│   ├── enrichment.py         # Task Celery: enriquecer()
│   └── persistence.py        # Task Celery: persistir()
└── validator/
    ├── validator.py
    └── types_severity.json
```

---

## Patrones de diseño aplicados

- **Strategy / Pipeline**: pipeline de enriquecimiento con enriquecedores intercambiables (`BaseEnricher`).
- **Repository**: capa de persistencia desacoplada del motor de base de datos concreto (`BaseRepository` / `ReportRepository`).
- **Template Method**: interfaz abstracta compartida entre enrichers y entre repositories.

---

## Variables de entorno (`.env`)

```env
SERVER_IP=127.0.0.1
SERVER_PORT=5000

REDIS_HOST=127.0.0.1
REDIS_PORT=6379

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=peerguard
DB_USER=peerguard
DB_PASSWORD=peerguard
```

---

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/nicobartok0/peer-guard-compII.git
cd peer-guard-compII

# 2. Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env  # editar con tus valores

# 5. Levantar el sistema
./run.sh
```

---

## Estado del proyecto

| Componente | Estado |
|---|---|
| Connection Manager (sockets TCP) | ✅ Completo |
| Validador | ✅ Completo |
| Pipeline de enriquecimiento | ✅ Completo |
| Persistencia en PostgreSQL | ✅ Completo |
| Workers de estadística | 🔲 Pendiente |
| Broadcast del heatmap (socket output) | 🔲 Pendiente |
| Celery Beat (recálculo periódico) | 🔲 Pendiente |
| Cliente (visualización del mapa) | 🔲 Pendiente |
