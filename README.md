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

## Privacidad

El snapshot no incluye timestamp, correo ni columnas personales. Los textos libres se limpian y se redactan correos, enlaces, teléfonos y nombres explícitos cuando aparecen con títulos como “Sr.” o “profesor” antes de publicarse. `.gitignore` excluye credenciales, archivos crudos, snapshots locales y artefactos de QA.

## Verificación realizada

- `py_compile`: correcto.
- `node --check dashboard_runtime.js`: correcto.
- `python3 -m unittest -v test_dashboard_metrics.py`: 18 pruebas OK.
- QA local con 149 respuestas: filtros cambian KPIs, tablas, Matriz, nube y citas; no hay áreas duplicadas.
- QA responsive: sin overflow horizontal a 375 px ni 320 px; una sola barra sticky de pregunta; logo carga con fallback.
- QA de producción: `213` familias, snapshot v2, cinco pestañas, filtros persistentes, `/api/update` exitoso y assets runtime bloqueados (`404`).
