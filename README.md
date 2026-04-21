# Sistema 'Peer Guard' para precaución ciudadana

## Resúmen

'Peer Guard' es un software que permite evaluar los niveles de peligros a los que 
uno se expone en ciertas zonas de una ciudad en base a las experiencias reportadas
por otros usuarios. Se desplega un mapa de calor sobre el mapa, el cual está 
dividido en cuadriculas del mismo tamaño que se encienden según la cantidad
de reportes que encierran, la gravedad de los mismos y la hora del día.

Este sistema está destinado a incentivar la cooperación ciudadana con el motivo
de evitar este tipo de crímenes, y que personas que muchas veces pueden no pertenecer
a un lugar sean capaces de evitar zonas peligrosas.

Este sistema está encarado a modo de examen final integrador de la materia Computación II,
Ing. Informática en la Universidad de Mendoza.

Desarrollador: Nicolás Bartolomeo Koninckx

## Arquitectura del sistema

![arquitectura](https://ibb.co/yFLMqTrt)

La arquitectura consiste de una serie de componentes interconectados del lado del servidor,
cuyo objetivo es procesar los reportes, expandir la información que contienen, guardarlos
en la base de datos y luego enviarlos a demanda. Para conseguir esto, el sistema se divide
en las siguientes piezas clave:

### Main Entrypoint

#### Connection Manager

El connection manager maneja la conexión utilizando sockets. De esta forma, recibe los pedidos
de reporte en formato JSON y los sube a una Queue que utilizará el enriquecedor de información.

#### Verificador

El verificador es un objeto que toma el reporte y verifica que cumpla con la forma que debe tener
para ser procesado correctamente por el sistema. Además, cambia el formato de la fecha por un
objeto del tipo "datetime".

#### Report/Report Factory

El objeto de tipo Report es un DTO generado por un Report Factory. Este es el tipo de objetos que son
enviados a la primer Queue para ser consumidos por los siguientes componentes.

## Patrones de diseño aplicados al sistema

- Patrón Factory: Utilizado para independizar la creación de los objetos de los componentes particulares.
Se puede encontrar el patrón factory en la creación de objetos del tipo "Report" en el Connection Manager.