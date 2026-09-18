# AGENT.md — CBJML Survey Dashboard

## 1. Identidad y Propósito

Dashboard interactivo de la encuesta de familias del **Colegio José Max León (CBJML)** — Diagnóstico Estratégico Leonista 2026. El agente actúa como analista de datos educativos: procesa respuestas, calcula métricas, actualiza el dashboard y mantiene la coherencia estadística.

## 2. Fuentes de Datos

| Recurso | ID / URL | Uso |
|---------|----------|-----|
| Google Drive Folder | `1gCNTNLva5Orc2NYEZEQop7f1iC2727Ir` (FormEcuestaCol_JML) | Archivos del proyecto |
| Google Sheets | `1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY` | Respuestas en vivo |
| Dashboard URL | https://cbjml-dashboard.ywzal8.easypanel.host/ | Producción |

**Autenticación:** rclone con Google Drive OAuth2. Token en `~/.config/rclone/rclone.conf`. El refresh_token se renueva automáticamente.

## 3. Estructura del Sheet

Hoja: `Respuestas de formulario 1` — ~56 columnas, 1 fila por respuesta.

### Columnas clave
| Rango | Descripción |
|-------|-------------|
| 0-1 | Timestamp, Email |
| 2-5 | Demografía (hijos, cursos, antigüedad, participación) |
| 6-17 | 12 Aspectos Formativos (Escala: Excelente/Bueno/Aceptable/Deficiente/No conozco) |
| 18-19 | Identidad (multi-select máx 5), 3 palabras únicas |
| 20-26 | Afirmaciones (Totalmente de acuerdo / De acuerdo / Ni acuerdo ni desacuerdo / En desacuerdo / Totalmente en desacuerdo) |
| 27 | Texto libre: qué no perder |
| 28 | Diferencias generacionales (multi-select máx 5) |
| 29 | Respuesta al cambio (categoría única) |
| 30-36 | 7 Retos (Ranking 1-7, 1=más urgente) |
| 37 | Texto libre: qué no se aborda |
| 38-50 | 13 Áreas de acción (Mantener / Mejorar / Transformar / No prioritario) |
| 51 | Texto libre: un cambio |
| 52 | Iniciativas (multi-select máx 5) |
| 53 | Disposición a colaborar (multi-select) |
| 54-55 | Texto libre: frase final, recomendación |

## 4. Reglas de Procesamiento

### Escalas
- **Aspectos Formativos (cols 6-17):** `Excelente`(4) + `Bueno`(3) = Satisfacción Favorable. Semáforo: ≥90% Verde, 80-89.9% Azul, <80% Ámbar.
- **Afirmaciones (cols 20-26):** `Totalmente de acuerdo` + `De acuerdo` = Acuerdo Total.
- **Retos (cols 30-36):** Media aritmética (menor = más urgente) + % en Rank 1-2.
- **Matriz (cols 38-50):** Categoría predominante define acción. `Transformar` >20% = alerta.

### Multi-select con comas internas
⚠️ Opciones como `"Actividades artísticas, culturales y deportivas"` contienen comas. **NO separar por comas** — matchear contra lista de opciones canónicas exactas.

### Privacidad
- Anonimizar emails en cualquier output público.
- No commitear `.xlsx`, `.csv` ni archivos con datos crudos.

## 5. Workflow de Actualización

1. **Descargar datos** desde Google Sheets via Google Sheets API (OAuth2 rclone)
2. **Calcular métricas** → generar `dashboard_data.json`
3. **Inyectar datos** en `Dashboard_CBJML.html` (reemplazar sección JS entre `// Datos cargados` y `// Navegación por pestañas`)
4. **Build Docker** → `docker build --no-cache -t cbjml-dashboard:latest .`
5. **Deploy Swarm** → `docker service update --image cbjml-dashboard:latest --force cbjml-dashboard`
6. **Verificar** → `curl -sk https://cbjml-dashboard.ywzal8.easypanel.host/ | grep "96 familias"`

## 6. Infraestructura

- **VPS:** Contabo 194.34.232.193 (Ubuntu 22.04, Docker Swarm)
- **Traefik:** file provider en `/etc/easypanel/traefik/config/cbjml-dashboard.yml`
- **Puerto servicio:** 8102
- **Red:** easypanel (overlay)

### Traefik config
```yaml
http:
  routers:
    cbjml-dashboard-http:
      rule: "Host(`cbjml-dashboard.ywzal8.easypanel.host`)"
      entrypoints: [http]
      middlewares: [redirect-to-https]
      service: cbjml-dashboard
    cbjml-dashboard-https:
      rule: "Host(`cbjml-dashboard.ywzal8.easypanel.host`)"
      entrypoints: [https]
      tls: { certResolver: letsencrypt, domains: [{ main: cbjml-dashboard.ywzal8.easypanel.host }] }
      service: cbjml-dashboard
  services:
    cbjml-dashboard:
      loadBalancer:
        passHostHeader: true
        servers: [{ url: "http://cbjml-dashboard:8102" }]
```

## 7. Pitfalls

- ❌ **No usar `python -m http.server`** — no envía Cache-Control → navegador cachea HTML stale. Usar `cbjml-server.py` con no-store.
- ❌ **No separar multi-select por comas** — las opciones canónicas contienen comas internas.
- ❌ **No commitear datos crudos** — `.xlsx`, `.csv` están en `.gitignore`.
- ❌ **No usar `write_file` en `/etc/systemd`** — usar terminal con heredoc.
- ✅ **Siempre verificar post-deploy** con curl al URL público, no solo local.
