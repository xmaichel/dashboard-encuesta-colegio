# Dashboard Encuesta CBJML — Colegio José Max León

> Diagnóstico Estratégico Leonista 2026 — datos sincronizados desde Google Sheets en modo de solo consulta.

[🌐 Dashboard live](https://cbjml-dashboard.ywzal8.easypanel.host/)

## Arquitectura

```text
Google Sheets (solo lectura)
    ↓ OAuth2
etl_sync.py
    ├─ dashboard_data.json (snapshot v2 anonimizado)
    └─ Dashboard_CBJML.html (plantilla + CBJML_SNAPSHOT)
    ↓
cbjml-server.py
    ├─ ETL al arrancar
    └─ /api/update ETL serializado
    ↓
Docker Swarm → Traefik → HTTPS
```

El servidor entrega una plantilla estable y un runtime externo (`dashboard_runtime.js`). El navegador calcula cada módulo a partir del snapshot de respuestas anonimizadas, por lo que los filtros recalculan KPIs, tablas, gráficos, Matriz, nube y citas.

## Archivos

- `Dashboard_CBJML.html`: plantilla estable, logo, filtros, cinco pestañas y contenedores de render.
- `dashboard_runtime.js`: render, filtros, persistencia UI, gráficos y accesibilidad.
- `etl_sync.py`: lectura de Sheets, normalización, snapshot atómico e inyección segura.
- `cbjml-server.py`: servidor estático con allowlist pública, healthcheck y actualización serializada.
- `test_dashboard_metrics.py`: pruebas sintéticas de datos, filtros conceptuales, matriz, nube, privacidad e idempotencia.
- `Dockerfile`: imagen mínima de producción.

La plantilla vive en Git; el snapshot generado en runtime (`dashboard_data.json` y `CBJML_SNAPSHOT`) no se versiona.


## Actualización

El botón **Actualizar datos** llama `GET /api/update`. La respuesta ejecuta exactamente el mismo ETL que corre al arrancar. Google Sheets nunca se escribe. El servidor solo publica la plantilla, el runtime y sus dos endpoints de operación; el snapshot y el código fuente responden `404`.

```bash
cd /root/projects/dashboard-encuesta-colegio
python3 -m unittest -v test_dashboard_metrics.py
node --check dashboard_runtime.js
docker build --no-cache -t cbjml-dashboard:latest .
docker service update --image cbjml-dashboard:latest --force cbjml-dashboard
curl -sk https://cbjml-dashboard.ywzal8.easypanel.host/api/health
```

## Filtros y persistencia

Filtros disponibles: colegio total, sección, antigüedad y curso. Se guardan en `localStorage` junto con la pestaña activa y el estado del panel. La selección se conserva al cambiar de pestaña y al recargar.

La nube de palabras normaliza tildes, elimina términos sin contexto como `cada` y `estudiantes`, y combina variantes. Las respuestas de la Matriz usan la opción predominante; los empates se muestran explícitamente y cada área aparece una sola vez.

Las multiselecciones (iniciativas, identidad, diferencias y aportación) se ordenan por relevancia, es decir, por número de respaldos, con desempate alfabético para que el resultado sea estable. El KPI **Iniciativa Top** muestra siempre la iniciativa más apoyada por las familias del filtro activo.

## Privacidad

El snapshot no incluye timestamp, correo ni columnas personales. Los textos libres se limpian y se redactan correos, enlaces, teléfonos y nombres explícitos cuando aparecen con títulos como “Sr.” o “profesor” antes de publicarse. `.gitignore` excluye credenciales, archivos crudos, snapshots locales y artefactos de QA.

## Verificación realizada

- `py_compile`: correcto.
- `node --check dashboard_runtime.js`: correcto.
- `python3 -m unittest -v test_dashboard_metrics.py`: 21 pruebas OK.
- QA local y producción: `219` familias tras ETL en vivo; filtros/persistencia, pestañas, Matriz deduplicada y pregunta sticky única.
- QA de Voz Directa: las cuatro preguntas actualizan el recuadro azul y muestran únicamente sus citas; el recuadro conserva `position: sticky`.
- QA de Iniciativa Top: sin filtros muestra `Educación financiera` (la más apoyada) y con filtro de curso cambia a la más apoyada de ese grupo.
- QA responsive: sin overflow horizontal a 375 px ni 320 px; logo con fallback.
- `dashboard_runtime.js?v=5` desplegado; allowlist pública verificada (snapshot, ETL, servidor, `.env` y `data_*.js` responden `404`).
- Commit `ebdb35d` publicado en `origin/main`.
