# Dashboard Encuesta CBJML — Colegio José Max León

> Diagnóstico Estratégico Leonista 2026 — Datos en vivo desde Google Sheets

[🌐 Dashboard Live](https://cbjml-dashboard.ywzal8.easypanel.host/) · [📊 Google Sheets](https://docs.google.com/spreadsheets/d/1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY/edit)

---

## Descripción

Dashboard interactivo SPA (Single Page Application) que visualiza los resultados de la encuesta aplicada a las familias del Colegio José Max León (CBJML). Los datos se sincronizan desde Google Sheets mediante OAuth2 (rclone).

**Muestra actual:** 96 familias  
**Última actualización:** Septiembre 2026

---

## Arquitectura

```
Google Sheets (Form Responses)
    ↓ (OAuth2 via rclone refresh_token)
Python ETL → dashboard_data.json
    ↓
Docker (python:3.12-slim) → http.server con Cache-Control no-store
    ↓
Docker Swarm → Traefik file provider → HTTPS (Let's Encrypt)
    ↓
https://cbjml-dashboard.ywzal8.easypanel.host/
```

---

## Componentes

| Archivo | Descripción |
|---------|-------------|
| `Dashboard_CBJML.html` | Dashboard SPA con Chart.js + Tailwind CSS, datos inlined |
| `dashboard_data.json` | Datos procesados desde Google Sheets (fuente de verdad) |
| `cbjml-server.py` | Servidor estático Python con Cache-Control no-store |
| `Dockerfile` | Imagen Docker para el dashboard |
| `ops/traefik/cbjml-dashboard.yml` | Configuración Traefik (file provider) |

**Datos excluidos de Git:** `.xlsx`, `.csv`, `data_*.js`, `analisis.json` (contienen emails y datos personales).

---

## Módulos del Dashboard

1. **Resumen Ejecutivo & KPIs** — Síntesis estratégica, demografía, respuesta al cambio
2. **Calidad de Aspectos (12 Dimensiones)** — Gráfico stacked + tabla de desempeño
3. **Matriz de Acción** — Mantener / Mejorar / Transformar (13 frentes)
4. **Retos Actuales & Futuro** — Ranking de urgencia, diferencias generacionales, iniciativas
5. **Identidad & Voz de Familias** — Nube de palabras, buscador de testimonios

---

## KPIs actuales (96 familias)

| KPI | Valor |
|-----|-------|
| Bienestar Hijo(a) | 90.6% |
| Coincidencia Valores | 92.8% |
| Comunidad Leonista | 91.6% |
| Participación Activa | 93.8% |
| Disposición Aporte | 95.8% |
| Iniciativa Top | Educación financiera 78.1% |

### Retos urgentes
1. **Salud mental, ansiedad y bienestar emocional** — media 2.46, 63.5% top1-2
2. **Uso excesivo de pantallas y redes sociales** — media 2.69, 61.5% top1-2
3. **Inteligencia artificial y nuevas formas de aprender** — media 2.92, 50.0% top1-2

---

## Deploy

### Requisitos
- VPS Contabo con Docker Swarm + Easypanel + Traefik
- rclone configurado con Google Drive OAuth2

### Actualizar datos + redeploy
```bash
cd /root/projects/dashboard-encuesta-colegio
# 1. Sync datos desde Google Sheets (script ETL)
python3 -c "..."  # Ver SPEC.md §ETL
# 2. Build + deploy
docker build --no-cache -t cbjml-dashboard:latest .
docker service update --image cbjml-dashboard:latest --force cbjml-dashboard
```

### Actualizar ruta Traefik
```bash
TRAEFIK_CID=$(docker ps --format '{{.Names}}' | grep '^easypanel-traefik\.' | head -1)
docker cp ops/traefik/cbjml-dashboard.yml "$TRAEFIK_CID:/data/config/cbjml-dashboard.yml"
TRAF_PID=$(docker exec "$TRAEFIK_CID" pidof traefik)
docker exec "$TRAEFIK_CID" kill -HUP "$TRAF_PID"
```

---

## Privacidad

- **Fuente:** Google Sheets (Form Responses del formulario CBJML)
- **Sheet ID:** `1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY`
- **Autenticación:** OAuth2 via rclone (`~/.config/rclone/rclone.conf`)
- **Git:** `.gitignore` excluye `.xlsx`, `.csv` y archivos con datos crudos
