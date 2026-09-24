# SPEC — Dashboard CBJML

## Objetivo

Mantener un dashboard ejecutivo de la encuesta de familias del Colegio José Max León, sincronizado desde Google Sheets en modo de solo lectura, con filtros que recalculan todos los módulos y una UI persistente/idempotente frente al ETL.

## Requirements

### R1 — Ingesta
- Leer Google Sheets `1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY`, hoja `Respuestas de formulario 1`.
- No escribir, editar ni reordenar la hoja.
- Validar al menos 56 columnas y tratar cada fila no vacía como una familia.
- Ejecutar el ETL al arrancar y en `/api/update`.

### R2 — Modelo anonimizado
- Producir `dashboard_data.json` y `CBJML_SNAPSHOT` con respuestas anonimizadas; no versionar esos artefactos.
- Excluir timestamp, correo y columnas personales.
- Redactar correo, URL, teléfono y nombres explícitos en contextos de persona dentro de textos libres.
- Normalizar Unicode antes de mapear cursos con tildes.
- Parsear multiselección contra opciones canónicas, sin dividir internamente por comas.

### R3 — Métricas
- Aspectos: Excelente + Bueno, denominador de respuestas válidas.
- Afirmaciones: Totalmente de acuerdo + De acuerdo.
- Retos: media de urgencia (1 más urgente) y % top 1–2.
- Matriz: cada área una sola vez, asignada por respuesta predominante; empate explícito.
- Nube: normalizar variantes y excluir términos sin contexto como `cada` y `estudiantes`.
- Citas: texto público anonimizado, con curso, sección y antigüedad.

### R4 — UI
- Mantener exactamente cinco pestañas con los títulos executive definidos en el encargo.
- Grid responsive de cinco botones sin overflow horizontal.
- Panel de filtros ocultable: total colegio, sección, antigüedad y curso.
- Persistir filtros, collapsed state y pestaña en `localStorage`.
- Recalcular KPIs, gráficos, tablas, matriz, nube y citas al cambiar cualquier filtro.
- Mostrar una sola vez la pregunta de Voz Directa en barra sticky.
- El selector de las cuatro preguntas de Voz Directa cambia simultáneamente el texto de la barra y las citas; la barra conserva su comportamiento sticky.
- Logo oficial CBJML con fallback textual.

### R5 — Ship y privacidad
- Build Docker desde `Dockerfile` mínimo.
- Deploy con `docker service update --image ... --force`.
- Verificar URL pública, healthcheck, contenido/versionado y navegador.
- No versionar secretos ni datos crudos.

## Acceptance Criteria

- AC1: `GET /` responde el dashboard y `/api/health` devuelve estado con conteo actual.
- AC2: ETL idempotente: dos ejecuciones del mismo snapshot producen el mismo HTML.
- AC3: Los cinco tabs cambian de estado correctamente.
- AC4: A 375 px y 320 px, `scrollWidth <= innerWidth`.
- AC5: Cambiar sección/curso modifica el modelo renderizado, no solo el contador.
- AC6: La Matriz contiene 13 áreas únicas y los empates no se reparten.
- AC7: La nube no contiene `cada`, `estudiantes` ni duplicados por tildes.
- AC8: Hay exactamente un `#vozQuestionBar` y un `#vozQuestionText`; cambiar cualquiera de las cuatro preguntas actualiza ambos el texto y las citas.
- AC9: El snapshot no contiene email, URL, teléfono, timestamp ni secretos.
- AC10: Pruebas Python y `node --check` terminan correctamente antes del deploy.

## Constraints

- Google Sheets es solo consulta.
- El HTML debe ser una plantilla estable; no se parcheará con scripts de postprocesado.
- snapshot v2 debe ser suficiente para que el navegador calcule todos los filtros; por eso se entrega por respuesta anonimizada.
- No guardar valores de OAuth, rclone o `.env` en Git, logs o respuestas.
- No servir el snapshot (`dashboard_data.json`) ni el código fuente desde HTTP; deben quedar fuera de la allowlist pública.
- El deploy es irreversible en producción; se ejecuta solo después de pruebas y revisión de diff.

## DoD

- [x] Modelo ETL con snapshot v2 e idempotencia.
- [x] Runtime externo conectado al snapshot.
- [x] Filtros, persistencia, Matriz, nube, logo y responsive implementados.
- [x] Pruebas sintéticas y QA local en navegador.
- [x] Build Docker y deploy Swarm.
- [x] Verificación post-deploy en URL pública.
- [x] Commit y push revisados (`6f18ca6` + `b89420b`).
- [x] Selector de las cuatro preguntas de Voz Directa dinámico y verificado en producción.

## Pipeline

```text
refresh_access_token()
→ sheets.values.get(majorDimension=ROWS, valueRenderOption=FORMATTED_VALUE)
→ build_snapshot()
→ compute_metrics() (validación y salida agregada)
→ inject_snapshot() con reemplazo de bloque delimitado
→ validate_rendered_html()
→ write_json_atomic() + os.replace()
→ servidor sirve HTML con no-store
```
