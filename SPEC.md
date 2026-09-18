# SPEC — Dashboard Encuesta CBJML

## Objetivo

Construir y mantener un dashboard interactivo que visualice los resultados de la encuesta de familias del Colegio José Max León (CBJML), con datos sincronizados desde Google Sheets y deploy continuo en el VPS Contabo.

## Requirements

### R1 — Ingesta de datos
- Conectar a Google Sheets `1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY` vía OAuth2 (rclone refresh_token).
- Leer hoja `Respuestas de formulario 1` (todas las filas y columnas).
- Validar estructura: ~56 columnas, 1 fila = 1 respuesta.

### R2 — Procesamiento estadístico
- **Aspectos Formativos (12):** Calcular % Excelente + Bueno (satisfacción favorable). Clasificar semáforo.
- **Afirmaciones (7):** Calcular % Totalmente de acuerdo + De acuerdo.
- **Retos (7):** Calcular media de ranking (1-7) y % en puestos 1-2.
- **Matriz de Acción (13):** Determinar categoría predominante (Mantener/Mejorar/Transformar/No prioritario).
- **Multi-select:** Parsear con lista de opciones canónicas (no split por comas).
- **Testimonios:** Extraer textos de cols 27, 51, 54, 55 con metadata (curso, antigüedad).

### R3 — Dashboard web
- SPA HTML con Chart.js + Tailwind CSS.
- 5 módulos navegables por tabs.
- Datos inlined como JS constants (`var KPIS=...`, `var ASPECTOS=...`).
- Buscador de testimonios con filtro por categoría y texto libre.
- Nube de palabras basada en frecuencia de tokens en respuestas abiertas.

### R4 — Deploy
- Docker image `cbjml-dashboard:latest` basada en `python:3.12-slim`.
- Servidor estático con `Cache-Control: no-store` en HTML.
- Servicio Swarm en red `easypanel`.
- Traefik file provider con HTTPS Let's Encrypt.

### R5 — Privacidad
- No incluir emails ni datos personales en el dashboard público.
- `.gitignore` excluye archivos con datos crudos (`.xlsx`, `.csv`).
- No commitear secrets, tokens ni `.env`.

## Acceptance Criteria

- AC1: Dashboard accesible en https://cbjml-dashboard.ywzal8.easypanel.host/ con HTTP 200.
- AC2: Los 5 tabs funcionan al hacer click (resumen, calidad, matriz, retos, comunidad).
- AC3: Todos los gráficos se renderizan (Chart.js) con datos actualizados.
- AC4: El buscador de testimonios filtra correctamente.
- AC5: El conteo de familias refleja el número real de filas en el sheet.
- AC6: No hay datos personales (emails) visibles en el dashboard.
- AC7: `dashboard_data.json` se genera correctamente desde el sheet en vivo.

## Constraints

- Sin backend propio — todo es estático, datos se pre-calculan en build time.
- Actualización manual de datos (no hay webhook de Google Forms).
- VPS compartido con otros servicios (no monopolizar recursos).

## DoD

- [ ] Datos descargados y procesados desde Google Sheets
- [ ] `dashboard_data.json` generado con todas las métricas
- [ ] HTML actualizado con datos inlined (JS válido, sin errores de sintaxis)
- [ ] Docker build exitoso
- [ ] Deploy Swarm converged (1/1)
- [ ] Verificación curl al URL público (HTTP 200 + contenido correcto)
- [ ] Verificación browser (tabs funcionan, gráficos renderizan)

## ETL Pipeline

```
1. OAuth2 token refresh (rclone.conf)
2. GET /v4/spreadsheets/{id}/values/{sheet} → rows[][]
3. Parsear por columnas → estructuras tipadas
4. Calcular métricas → dashboard_data.json
5. Inyectar en Dashboard_CBJML.html (regex replace sección JS)
6. docker build → docker service update
```

## Opciones canónicas multi-select

### Identidad (col 18, máx 5)
Formación en valores, Excelencia académica, Proyección internacional, Programa SER/CARE, Cercanía y acompañamiento, Actividades artísticas/culturales/deportivas, Relación con familias, Escuela de argumentación, Competencias tecnológicas, Sentido de comunidad, Programa de emprendimiento, Tradiciones y celebraciones

### Diferencias generacionales (col 28, máx 5)
Relación con tecnología y redes sociales, Forma de aprender, Necesidades socioemocionales, Atención y concentración, Relación con autoridad y profesores, Expectativas frente al futuro, Relación con la información, Relación con compañeros

### Iniciativas (col 52, máx 5)
Educación financiera, Liderazgo/debate/oratoria, IA responsable/programación/robótica, Salud mental y bienestar, Emprendimiento con impacto social, Arte y deporte alto rendimiento, Orientación vocacional temprana, Voluntariado y servicio comunitario, Proyectos interdisciplinarios, Esquemas reconocimiento monetario, Mentoría profesional, Red de exalumnos

### Colaboración (col 53)
Charlas/talleres estudiantes, Talleres padres, Mentoría profesional, Voluntariado eventos, Respondiendo consultas, Por ahora no me es posible participar
