# TASKs — Dashboard CBJML

| ID | Prioridad | Estado | Verificación |
|---|---|---|---|
| TASK-001 — Nube limpia y normalizada | Alta | Completada | Tests + QA navegador; `cada`, `estudiantes` y variantes tilde controlados |
| TASK-002 — Cinco pestañas sin overflow | Alta | Completada | 320 px y 375 px sin `scrollWidth > innerWidth` |
| TASK-003 — Filtros reales y persistentes | Crítica | Completada | Sección/curso recalculan KPIs, tablas, gráficos, matriz, nube y citas; `localStorage` |
| TASK-004 — Matriz sin duplicados | Crítica | Completada | 13 áreas únicas; predominio y empates explícitos |
| TASK-005 — Logo CBJML | Media | Completada | Imagen oficial cargada; fallback oculto mientras funciona |
| QA-001 — Browser, privacidad y accesibilidad | Crítica | Completada | QA local + producción: `214` familias, filtros/persistencia, responsive y pregunta sticky |
| SHIP-001 — Documentación, diff, commit y push | Alta | Completada | Commit `6f18ca6` y `origin/main` verificados; sin datos crudos en HEAD |
| DEPLOY-001 — Rebuild y actualización del servicio | Crítica | Completada | `docker build --no-cache`, Swarm `1/1`, health `200`, ETL en vivo |
| TASK-006 — Voz Directa: cuatro preguntas dinámicas | Crítica | Completada | El recuadro sticky cambia de texto y las citas cambian con la pregunta seleccionada |
| QA-002 — Regresión de Voz Directa | Alta | Completada | 19 pruebas Python, sintaxis JS, navegador local/producción y responsive |
| DEPLOY-002 — Rebuild con pregunta dinámica | Crítica | Completada | `dashboard_runtime.js?v=4`, ETL en vivo y rutas internas `404` |
| SHIP-002 — Commit y push de la corrección | Alta | Completada | Commit `bba369f` publicado en `origin/main`; sin datos crudos en HEAD |
| TASK-007 — KPI Iniciativa Top por relevancia | Crítica | Completada | Multiselección ordenada por respaldos; sin filtros muestra `Educación financiera` |
| QA-003 — Regresión del KPI Iniciativa Top | Alta | Completada | 21 pruebas Python, navegador local/producción y filtros por sección, antigüedad y curso |
| DEPLOY-003 — Rebuild del KPI por relevancia | Crítica | Completada | `dashboard_runtime.js?v=5`, Swarm `1/1`, allowlist `404`, ETL en vivo |
| SHIP-003 — Commit y push del KPI | Alta | Completada | Commit `ebdb35d` publicado en `origin/main`; sin datos crudos en HEAD |
| TASK-008 — Porcentajes numéricos en tortas | Crítica | Completada | Porción con `MIN_SHARE` y leyenda con % en las 3 tortas; barras intactas |
| QA-004 — Regresión de porcentajes en tortas | Alta | Completada | 22 pruebas Python, evidencia visual y QA en producción con y sin filtros |
| DEPLOY-004 — Rebuild con porcentajes en tortas | Crítica | Completada | `dashboard_runtime.js?v=6`, Swarm `1/1`, allowlist `404` |
| SHIP-004 — Commit y push de porcentajes | Alta | Completada | Commit `e951676` publicado en `origin/main`; sin datos crudos en HEAD |
| TASK-009 — Leyenda única con color en Respuesta al Cambio | Crítica | Completada | Lista HTML `#respCambioLegend` con swatch; fuera la leyenda de Chart.js y el bloque duplicado |
| QA-005 — Regresión de leyenda y porcentajes | Alta | Completada | 24 pruebas Python, 17 escenarios de filtro, móvil 375/320 y evidencia visual |
| DEPLOY-005 — Rebuild de leyenda | Crítica | Completada | `dashboard_runtime.js?v=8`, Swarm `1/1`, allowlist `404` |
| SHIP-005 — Commit y push de leyenda | Alta | Completada | Commit `f120843` publicado en `origin/main`; sin datos crudos en HEAD |

## Orden de cierre

1. Ejecutar tests y build local.
2. Rebuild Docker sin cache y actualizar `cbjml-dashboard` en Swarm.
3. Verificar `/api/health`, `/`, runtime, snapshot y navegador público.
4. Actualizar esta tabla, revisar secretos/diff, commit y push.
