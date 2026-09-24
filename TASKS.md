# TASKs — Dashboard CBJML

| ID | Prioridad | Estado | Verificación |
|---|---|---|---|
| TASK-001 — Nube limpia y normalizada | Alta | Completada | Tests + QA navegador; `cada`, `estudiantes` y variantes tilde controlados |
| TASK-002 — Cinco pestañas sin overflow | Alta | Completada | 320 px y 375 px sin `scrollWidth > innerWidth` |
| TASK-003 — Filtros reales y persistentes | Crítica | Completada | Sección/curso recalculan KPIs, tablas, gráficos, matriz, nube y citas; `localStorage` |
| TASK-004 — Matriz sin duplicados | Crítica | Completada | 13 áreas únicas; predominio y empates explícitos |
| TASK-005 — Logo CBJML | Media | Completada | Imagen oficial cargada; fallback oculto mientras funciona |
| QA-001 — Browser, privacidad y accesibilidad | Crítica | Completada | QA local + producción: `213` familias, filtros/persistencia, responsive y pregunta sticky |
| SHIP-001 — Documentación, diff, commit y push | Alta | En curso | Revisión de privacidad y secretos; faltan commits/push |
| DEPLOY-001 — Rebuild y actualización del servicio | Crítica | Completada | `docker build --no-cache`, Swarm `1/1`, health `200`, ETL en vivo |

## Orden de cierre

1. Ejecutar tests y build local.
2. Rebuild Docker sin cache y actualizar `cbjml-dashboard` en Swarm.
3. Verificar `/api/health`, `/`, runtime, snapshot y navegador público.
4. Actualizar esta tabla, revisar secretos/diff, commit y push.
