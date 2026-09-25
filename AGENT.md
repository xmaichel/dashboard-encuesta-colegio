# AGENT.md — CBJML Survey Dashboard

## Propósito

Dashboard ejecutivo de la encuesta de familias del Colegio José Max León (CBJML). El agente mantiene el pipeline de solo lectura, la anonimización, los cálculos y el deploy.

## Fuente de datos

- Google Drive: `1gCNTNLva5Orc2NYEZEQop7f1iC2727Ir` (`FormEcuestaCol_JML`).
- Google Sheets: `1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY`.
- Hoja: `Respuestas de formulario 1`.
- Dashboard: `https://cbjml-dashboard.ywzal8.easypanel.host/`.
- Proyecto: `/root/projects/dashboard-encuesta-colegio/`.
- Sheet es estrictamente **solo lectura**.

La autenticación se configura en el servicio con `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `GOOGLE_REFRESH_TOKEN`. Nunca copiar valores a Git ni logs. La plantilla vive en Git; el snapshot generado en runtime (`dashboard_data.json` y `CBJML_SNAPSHOT`) no se versiona.

## Estructura del Sheet

- 0–1: marca temporal y correo; se descartan.
- 2–5: número de hijos, cursos, antigüedad y participación.
- 6–17: 12 aspectos (escala de cinco opciones).
- 18–19: identidad y tres palabras.
- 20–26: 7 afirmaciones.
- 27: texto libre “qué no perder”.
- 28: diferencias generacionales.
- 29: respuesta a cambios.
- 30–36: ranking de 7 retos.
- 37: texto libre complementario.
- 38–50: 13 áreas de acción.
- 51: texto libre “qué cambiar/mejorar”.
- 52: iniciativas.
- 53: disposición a colaborar.
- 54–55: textos finales.

## Pipeline vigente

```text
OAuth2 → Sheets values.get → build_snapshot()
→ inject_snapshot() → validate_rendered_html()
→ dashboard_data.json + Dashboard_CBJML.html
→ cbjml-server.py + dashboard_runtime.js
```

`etl_sync.py` corre al arrancar y en `GET /api/update`; un lock serializa actualizaciones. La inyección reemplaza un bloque delimitado, no concatena ni ejecuta parches HTML. `dashboard_data.json` se genera en runtime y no se versiona.

## Cálculos

- Aspectos: `Excelente + Bueno` sobre respuestas válidas.
- Afirmaciones: `Totalmente de acuerdo + De acuerdo`.
- Retos: media de ranking; menor es más urgente; también `%` top 1–2.
- Matriz: cada clave aparece una vez; se asigna al modal de la respuesta; empate explícito.
- Multiselección: match contra opciones canónicas; nunca separar internamente por comas.
- Ranking de multiselección: ordenar por número de respaldos, no por el orden de la lista canónica; desempate alfabético estable.
- Nube: normalizar Unicode, combinar tildes y eliminar stop words/contexto.
- KPIs y filtros: se recalculan en `dashboard_runtime.js` desde el snapshot v2.
- Voz Directa: `questions.voz` conserva los cuatro textos canónicos; el selector actualiza la barra sticky y las citas sin mover la barra.

## Privacidad

El snapshot público excluye timestamp, correo y columnas personales. Los textos libres se limpian y redaccionan emails, URLs, teléfonos y nombres explícitos cuando aparecen con títulos de persona antes de inyectarse. La palabra cruda no se persiste. `.gitignore` excluye datos, CSV/XLSX, `.env` y artefactos de QA.

## Verificación y deploy

```bash
cd /root/projects/dashboard-encuesta-colegio
python3 -m unittest -v test_dashboard_metrics.py
node --check dashboard_runtime.js
docker build --no-cache -t cbjml-dashboard:latest .
docker service update --image cbjml-dashboard:latest --force cbjml-dashboard
curl -sk https://cbjml-dashboard.ywzal8.easypanel.host/api/health
# Verificar que /dashboard_data.json, /etl_sync.py y /.env devuelven 404.
```

Verificar siempre el contenedor nuevo, la URL pública y el navegador; no confiar solo en `HTTP 200` o en el estado `1/1` de Swarm. El servidor solo expone `/`, `/Dashboard_CBJML.html` y `/dashboard_runtime.js`; los artefactos de runtime y el código fuente deben responder `404`.

## Pitfalls

- No reusar el texto fijo original en `vozQuestionText`; el texto depende de `quoteCategory` y de `questions.voz`.
- No usar el orden de la lista canónica como criterio de "top"; ordenar por número de respaldos.
- No separar multiselección por comas.
- No buscar `septimo`/`decimo` sin normalizar tildes primero.
- No usar el snapshot agregado antiguo para filtros por familia.
- No ejecutar scripts legacy de postprocesado.
- No incluir `Google Sheets` como enlace de escritura o como fuente modificable.
- No reutilizar puertos ni dominios; leer `/root/projects/INDEX.md`.
- No usar `web`/`websecure` como entrypoints: en este VPS son `http`/`https`.
