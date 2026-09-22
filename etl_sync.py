#!/usr/bin/env python3
"""ETL: Download latest data from Google Sheets and regenerate dashboard HTML."""
import json, os, sys, re
import urllib.request
import urllib.parse
import csv
import io
from collections import Counter

# Google OAuth config from env vars
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
SHEET_ID = "1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY"
DASHBOARD_DIR = "/app"

def refresh_token():
    """Refresh OAuth2 access token."""
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]

def fetch_sheet():
    """Fetch all rows from Google Sheets."""
    token = refresh_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Respuestas%20de%20formulario%201?majorDimension=ROWS&valueRenderOption=FORMATTED_VALUE"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return data.get("values", [])

def compute_metrics(data):
    """Compute all metrics from raw sheet data."""
    headers = data[0]
    rows = data[1:]
    N = len(rows)
    
    # ASPECTOS (cols 6-17)
    ASPECTOS = []
    for i in range(6, 18):
        col_header = headers[i]
        match = re.search(r"\[(.*?)\]", col_header)
        nombre = match.group(1) if match else col_header
        counter = Counter()
        for row in rows:
            val = row[i].strip() if i < len(row) else ""
            if val: counter[val] += 1
        total = sum(counter.values())
        def pct(k, t=total): return round(counter.get(k, 0) / t * 100, 1) if t > 0 else 0.0
        ASPECTOS.append({
            "aspecto": nombre,
            "Excelente": {"count": counter.get("Excelente", 0), "pct": pct("Excelente")},
            "Bueno": {"count": counter.get("Bueno", 0), "pct": pct("Bueno")},
            "Aceptable": {"count": counter.get("Aceptable", 0), "pct": pct("Aceptable")},
            "Deficiente": {"count": counter.get("Deficiente", 0), "pct": pct("Deficiente")},
            "No conozco lo suficiente": {"count": counter.get("No conozco lo suficiente", 0), "pct": pct("No conozco lo suficiente")},
            "satisfaccion_positiva_pct": round(pct("Excelente") + pct("Bueno"), 1)
        })
    
    # AFIRMACIONES (cols 20-26)
    AFIRMACIONES = []
    for i in range(20, 27):
        col_header = headers[i]
        match = re.search(r"\[(.*?)\]", col_header)
        afirmacion = match.group(1) if match else col_header
        counter = Counter()
        for row in rows:
            val = row[i].strip() if i < len(row) else ""
            if val: counter[val] += 1
        total = sum(counter.values())
        def pct(k, t=total): return round(counter.get(k, 0) / t * 100, 1) if t > 0 else 0.0
        AFIRMACIONES.append({
            "afirmacion": afirmacion,
            "Totalmente de acuerdo": {"count": counter.get("Totalmente de acuerdo", 0), "pct": pct("Totalmente de acuerdo")},
            "De acuerdo": {"count": counter.get("De acuerdo", 0), "pct": pct("De acuerdo")},
            "Ni de acuerdo ni en desacuerdo": {"count": counter.get("Ni de acuerdo ni en desacuerdo", 0), "pct": pct("Ni de acuerdo ni en desacuerdo")},
            "En desacuerdo": {"count": counter.get("En desacuerdo", 0), "pct": pct("En desacuerdo")},
            "Totalmente en desacuerdo": {"count": counter.get("Totalmente en desacuerdo", 0), "pct": pct("Totalmente en desacuerdo")},
            "acuerdo_total_pct": round(pct("Totalmente de acuerdo") + pct("De acuerdo"), 1)
        })
    
    # RETOS (cols 30-36)
    RETOS = []
    for i in range(30, 37):
        col_header = headers[i]
        match = re.search(r"\[(.*?)\]", col_header)
        nombre = match.group(1) if match else col_header
        values = []
        dist = Counter()
        for row in rows:
            val = row[i].strip() if i < len(row) else ""
            if val:
                try:
                    v = int(val); values.append(v); dist[f"Rank {v}"] += 1
                except: pass
        if values:
            media = round(sum(values)/len(values), 2)
            mediana = sorted(values)[len(values)//2]
            top2 = sum(1 for v in values if v <= 2)
            top2_pct = round(top2/len(values)*100, 1)
        else: media = 0; mediana = 0; top2_pct = 0
        RETOS.append({"reto": nombre, "media_urgencia": media, "mediana": mediana, "top2_pct": top2_pct, "distribucion": dict(sorted(dist.items()))})
    
    # MATRIZ (cols 38-50)
    MATRIZ = []
    for i in range(38, 51):
        col_header = headers[i]
        match = re.search(r"\[(.*?)\]", col_header)
        nombre = match.group(1) if match else col_header
        counter = Counter()
        for row in rows:
            val = row[i].strip() if i < len(row) else ""
            if val: counter[val] += 1
        total = sum(counter.values())
        def pct(k, t=total): return round(counter.get(k, 0) / t * 100, 1) if t > 0 else 0.0
        MATRIZ.append({
            "area": nombre,
            "Mantener": {"count": counter.get("Mantener", 0), "pct": pct("Mantener")},
            "Mejorar": {"count": counter.get("Mejorar", 0), "pct": pct("Mejorar")},
            "Transformar": {"count": counter.get("Transformar", 0), "pct": pct("Transformar")},
            "No prioritario": {"count": counter.get("No prioritario", 0), "pct": pct("No prioritario")}
        })
    
    # Multi-select helpers
    def match_options(col_idx, options):
        counter = Counter()
        for row in rows:
            val = row[col_idx].strip() if col_idx < len(row) else ""
            if val:
                for opcion in options:
                    if opcion.lower() in val.lower():
                        counter[opcion] += 1
        return [{"opcion": k, "count": v, "pct": round(v/N*100, 1)} for k, v in counter.most_common()]
    
    ID_OPCIONES = [
        "Tradiciones y celebraciones", "Sentido de comunidad", "Programa de emprendimiento",
        "Desarrollo de competencias tecnológicas", "Escuela de argumentación",
        "Relación entre el Colegio y las familias", "Actividades artísticas, culturales y deportivas",
        "Cercanía y acompañamiento a los estudiantes", "Programa SER / Programa CARE",
        "Proyección internacional de los estudiantes", "Excelencia académica", "Formación en valores",
    ]
    IDENTIDAD = match_options(18, ID_OPCIONES)
    
    DIF_OPCIONES = [
        "Relación con la tecnología y las redes sociales", "Forma de aprender",
        "Necesidades socioemocionales", "Atención y concentración",
        "Relación con la autoridad y los profesores", "Expectativas frente al futuro",
        "Relación con la información", "Relación con sus compañeros",
    ]
    DIFERENCIAS = match_options(28, DIF_OPCIONES)
    
    IN_OPCIONES = [
        "Esquemas de reconocimiento monetario a estudiantes destacados",
        "Inteligencia artificial responsable, programación y robótica",
        "Liderazgo, debate y oratoria", "Emprendimiento y proyectos con impacto social",
        "Voluntariado y servicio comunitario", "Mentoría profesional o de emprendimiento",
        "Orientación vocacional desde grados tempranos", "Programa de salud mental y bienestar",
        "Arte y deporte de alto rendimiento", "Proyectos interdisciplinarios",
        "Educación financiera", "Red de exalumnos y familias",
    ]
    INICIATIVAS = match_options(52, IN_OPCIONES)
    
    colab_opciones = [
        "Respondiendo consultas como esta", "Voluntariado en eventos, proyectos sociales, culturales o deportivos",
        "Talleres o espacios para padres", "Charlas o talleres para estudiantes",
        "Mentoría profesional o de emprendimiento", "Por ahora no me es posible participar"
    ]
    colab_counter = Counter()
    for row in rows:
        val = row[53].strip() if 53 < len(row) else ""
        if val:
            for opcion in colab_opciones:
                if opcion.lower() in val.lower(): colab_counter[opcion] += 1
    APORTE = [{"opcion": k, "count": v, "pct": round(v/N*100, 1)} for k, v in colab_counter.most_common()]
    
    # DEMO
    hijos_counter = Counter(row[2].strip() for row in rows if 2 < len(row) and row[2].strip())
    tiempo_counter = Counter(row[4].strip() for row in rows if 4 < len(row) and row[4].strip())
    freq_counter = Counter(row[5].strip() for row in rows if 5 < len(row) and row[5].strip())
    orden_tiempo = ["Menos de 2 anos", "Entre 2 y 5 anos", "Entre 6 y 10 anos", "Mas de 10 anos"]
    orden_freq = ["Siempre", "Frecuentemente", "Algunas veces", "Casi nunca", "Nunca"]
    DEMO = {
        "total_respuestas": N,
        "hijos": [{"label": k, "count": v, "pct": round(v/N*100, 1)} for k, v in sorted(hijos_counter.items(), key=lambda x: -x[1])],
        "antiguedad": [{"label": k, "count": tiempo_counter.get(k, 0), "pct": round(tiempo_counter.get(k, 0)/N*100, 1)} for k in orden_tiempo if tiempo_counter.get(k, 0) > 0],
        "participacion": [{"label": k, "count": freq_counter.get(k, 0), "pct": round(freq_counter.get(k, 0)/N*100, 1)} for k in orden_freq if freq_counter.get(k, 0) > 0]
    }
    
    # RESP_CAMBIOS
    resp_counter = Counter(row[29].strip() for row in rows if 29 < len(row) and row[29].strip())
    orden_resp = [
        "Se anticipa y responde de manera integral a estos cambios",
        "Responde a la mayoria de los cambios de forma oportuna",
        "Responde a algunos cambios, pero no a otros",
        "Hay esfuerzos aislados, pero insuficientes",
        "El Colegio no esta atendiendo estos cambios"
    ]
    RESP_CAMBIOS = [{"label": k, "count": resp_counter.get(k, 0), "pct": round(resp_counter.get(k, 0)/N*100, 1)} for k in orden_resp if resp_counter.get(k, 0) > 0]
    
    # KPIS
    retos_sorted = sorted(RETOS, key=lambda x: x["media_urgencia"])
    KPIS = {
        "bienestar_hijos_pct": AFIRMACIONES[5]["acuerdo_total_pct"],
        "comunidad_leonista_pct": AFIRMACIONES[6]["acuerdo_total_pct"],
        "coincidencia_valores_pct": AFIRMACIONES[1]["acuerdo_total_pct"],
        "identidad_diferenciada_pct": AFIRMACIONES[0]["acuerdo_total_pct"],
        "participacion_activa_pct": round((freq_counter.get("Siempre", 0) + freq_counter.get("Frecuentemente", 0)) / N * 100, 1),
        "reto_urgente_1": retos_sorted[0]["reto"], "reto_urgente_1_pct": retos_sorted[0]["top2_pct"],
        "reto_urgente_2": retos_sorted[1]["reto"], "reto_urgente_2_pct": retos_sorted[1]["top2_pct"],
        "iniciativa_top_1": INICIATIVAS[0]["opcion"] if INICIATIVAS else "", "iniciativa_top_1_pct": INICIATIVAS[0]["pct"] if INICIATIVAS else 0,
        "disposicion_aporte_pct": round((N - colab_counter.get("Por ahora no me es posible participar", 0)) / N * 100, 1)
    }
    
    # TOP_WORDS
    palabras = []
    for row in rows:
        val = row[19].strip() if 19 < len(row) else ""
        if val:
            for w in val.split():
                w = w.strip(".,;:()[]{}\"\'").capitalize()
                if len(w) > 3: palabras.append(w)
    palabras_counter = Counter(palabras)
    TOP_WORDS = [{"palabra": k, "frecuencia": v} for k, v in palabras_counter.most_common(20) if v >= 2]
    
    # QUOTES
    QUOTES = []
    for idx, row in enumerate(rows):
        t = {}
        curso = row[3].strip() if 3 < len(row) else ""
        antiguedad = row[4].strip() if 4 < len(row) else ""
        nivel = ""
        cl = curso.lower()
        if "preescolar" in cl: nivel = "Preescolar"
        if any(c in cl for c in ["primero", "segundo", "tercero", "cuarto", "quinto", "sexto"]):
            nivel = "Primaria" if not nivel else "Preescolar, Primaria"
        if any(c in cl for c in ["septimo", "octavo", "noveno", "decimo", "once", "undecimo"]):
            nivel = "Bachillerato" if not nivel else ("Primaria, Bachillerato" if "Primaria" in nivel else "Preescolar, Bachillerato")
        if not nivel: nivel = "General"
        if 51 < len(row) and row[51].strip(): t["cambiar"] = row[51].strip()
        if 27 < len(row) and row[27].strip(): t["no_perder"] = row[27].strip()
        if 54 < len(row) and row[54].strip(): t["ensenar"] = row[54].strip()
        if 55 < len(row) and row[55].strip(): t["recomendar"] = row[55].strip()
        if t:
            for key in ["cambiar", "no_perder", "ensenar", "recomendar"]:
                if key in t: t[key] = t[key].replace("\n", " ")
            t["id"] = idx + 1; t["curso"] = curso; t["nivel"] = nivel; t["antiguedad"] = antiguedad
            QUOTES.append(t)
    
    return {
        "KPIS": KPIS, "ASPECTOS": ASPECTOS, "AFIRMACIONES": AFIRMACIONES, "RETOS": RETOS,
        "MATRIZ": MATRIZ, "IDENTIDAD": IDENTIDAD, "DIFERENCIAS": DIFERENCIAS,
        "INICIATIVAS": INICIATIVAS, "APORTE": APORTE, "DEMO": DEMO,
        "RESP_CAMBIOS": RESP_CAMBIOS, "TOP_WORDS": TOP_WORDS, "QUOTES": QUOTES, "N": N
    }

def update_html(metrics, html_path):
    """Update HTML file with new metrics."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    N = metrics["N"]
    
    # Generate JS data block
    def js_var(name, value):
        return f"var {name}={json.dumps(value, ensure_ascii=False, separators=(',',':'))};"
    
    js_vars = [js_var(k, metrics[k]) for k in ["KPIS","ASPECTOS","AFIRMACIONES","RETOS","MATRIZ","IDENTIDAD","DIFERENCIAS","INICIATIVAS","APORTE","DEMO","RESP_CAMBIOS","TOP_WORDS","QUOTES"]]
    js_data_block = "\n".join(js_vars)
    
    # Find and replace data section
    start_marker = "// Datos cargados"
    end_marker = "// Navegacion por pestanas"
    
    # Try with accents first, then without
    start_idx = html.find("// Datos cargados")
    end_idx = html.find("// Navegaci")
    
    if start_idx == -1:
        # Try finding by script content
        start_idx = html.find("var KPIS=")
        if start_idx > 0:
            # Go back to find the comment
            comment_idx = html.rfind("//", 0, start_idx)
            if comment_idx > 0 and "Datos" in html[comment_idx:start_idx]:
                start_idx = comment_idx
    
    if end_idx == -1:
        end_idx = html.find("function switchTab")
        if end_idx > 0:
            # Go back to find the comment
            comment_idx = html.rfind("//", 0, end_idx)
            if comment_idx > 0:
                end_idx = comment_idx
    
    if start_idx > 0 and end_idx > start_idx:
        new_section = f"// Datos cargados - {N} familias\n{js_data_block}\n\n    // Navegacion por pestanas"
        html = html[:start_idx] + new_section + html[end_idx + len("// Navegacion por pestanas"):]
        
        # Update family count in header
        html = re.sub(r"(\d+) familias", f"{N} familias", html)
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True, N
    else:
        return False, f"Markers not found: start={start_idx}, end={end_idx}"

if __name__ == "__main__":
    print("Fetching data from Google Sheets...")
    data = fetch_sheet()
    print(f"Got {len(data)} rows (including header)")
    
    print("Computing metrics...")
    metrics = compute_metrics(data)
    print(f"N={metrics['N']} families")
    
    print("Updating dashboard HTML...")
    html_path = os.path.join(DASHBOARD_DIR, "Dashboard_CBJML.html")
    success, result = update_html(metrics, html_path)
    
    if success:
        print(f"Dashboard updated with {result} families")
        print("OK")
    else:
        print(f"Error: {result}")
        sys.exit(1)
