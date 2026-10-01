# Frontend

Este directorio está reservado para la interfaz administrativa del sistema de gestión de PQRS.

## Estado actual

La carpeta está vacía en esta iteración. No existe todavía una aplicación web, framework, gestor de paquetes ni comandos de desarrollo configurados.

## Integración prevista

La futura interfaz deberá consumir la API del backend, inicialmente:

- `GET /` para comprobar disponibilidad.
- `POST /api/v1/pqrs/` para registrar una PQRS.
- `POST /api/v1/pqrs/classify-poc` para pruebas aisladas de clasificación.

La implementación del frontend debe definirse junto con los requisitos de autenticación, consulta de tickets, gestión de estados, asignación de áreas y visualización de auditoría.