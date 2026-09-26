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
- `python3 -m unittest -v test_dashboard_metrics.py`: 45 pruebas OK.
- QA local y producción: `227` familias tras ETL en vivo; filtros/persistencia, pestañas, Matriz deduplicada y pregunta sticky única.
- QA de las 7 pestañas: las 6 y 7 son documentos de decisión sobre el corte completo (227 familias) — no cambian al filtrar, ocultan la fila de KPIs y el panel de filtros, y el `mainContent` no se mueve al cambiar de pestaña. El nav ocupa una sola fila a 1440, 768, 375 y 320 px, sin desbordes.
- QA de tortas: 60 combinaciones de filtros medidas interceptando el dibujado real — 0 colisiones, 0 recortes, tamaños 11/12/13 px según el espacio del arco y decimales conservados en la leyenda.
- QA de barras: las 7 gráficas de barras horizontales usan 10px (la tipografía de la Matriz) y ninguna etiqueta se sale de su margen; las que no caben se abrevian con puntos suspensivos y conservan el texto completo en el tooltip.
- QA de Voz Directa: las cuatro preguntas actualizan el recuadro azul y muestran únicamente sus citas; el recuadro conserva `position: sticky`.
- QA de Iniciativa Top: sin filtros muestra `Educación financiera` (la más apoyada) y con filtro de curso cambia a la más apoyada de ese grupo.
- QA responsive: sin overflow horizontal a 375 px ni 320 px; logo con fallback.
- `dashboard_runtime.js?v=21` desplegado; porcentajes numéricos redondeados dentro de las porciones, contraste automático según el color, etiquetas externas cuando el arco no tiene espacio, leyenda única con color en "Respuesta al Cambio", siete pestañas en una sola fila con la 6 en vivo y la 7 como documento de decisión, y las 7 gráficas de barras con la tipografía de la Matriz y etiquetas abreviadas cuando no caben; allowlist pública verificada (snapshot, ETL, servidor, `.env` y `data_*.js` responden `404`).
- Commit `6e3df2d` publicado en `origin/main`.
