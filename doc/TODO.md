#TO DO LIST

## CREACIÓN DEL MAIN ENTRYPOINT

### ~~Crear connection manager~~
### ~~Crear validador~~
### ~~Crear report y report factory~~
### Crear output del connection manager

## CREACIÓN DEL POOL DE ENRIQUECIMIENTO

### Crear pool con Celery para procesamiento paralelo
### CUIDADO con la Queue: Aplicar lock para concurrencia segura
### Añadir funcionalidad de enriquecimiento (dia, hora, fecha, cuadrícula correspondiente, peligrosidad, momento del día)
### Crear objeto RichReport y Factory del mismo. 

## CREACIÓN DEL POOL DE PERSISTENCIA

### Crear pool de persistencia con la misma lógica que el pool de enriquecimiento
### Implementar Lock en la Queue.
### Implementar funcionalidad de guardado en base de datos y patrón repository para los workers.

## BASE DE DATOS

### Desplegar base Maria DB con docker
### Conectar la base al repository con variables de entorno

## CREACIÓN POOL DE ESTADÍSTICAS

### Crear pool de estadísticas con celery
### Implementar Lock en la Queue
### Implementar funcionalidad de análisis general de datos. Para esto primero hay que crear la base y el redis.
### Implementar salida al Connection Manager

## REDIS

### Implementar contenedor docker con REDIS
### Implementar broker y estado como dos bases del mismo REDIS que guarden cosas distintas.
### Los Worker de enriquecimiento deben dar sus reportes al REDIS Broker
### Implementar celery beat para empujar datos del broker a pool de estadísticas
### Implementar output del REDIS de estado hacia el output del connection manager

## Lado del cliente

### Implementar una forma de visualizar el mapa
### Implementar una forma de visualizar un grid sobre el mapa
### Implementar los hotspots en el grid
### Conectar con la aplicación de servidor