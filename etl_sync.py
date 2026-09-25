#!/usr/bin/env python3
"""ETL transaccional para respuestas anonimizadas del dashboard CBJML."""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

SHEET_ID = "1D1iZsRERzoFedD01_uYTy7-72vLssuEGnOmHSlPVNTY"
SHEET_RANGE = "Respuestas de formulario 1"
DASHBOARD_DIR = Path(os.environ.get("CBJML_ROOT", "/app"))
HTML_PATH = DASHBOARD_DIR / "Dashboard_CBJML.html"
JSON_PATH = DASHBOARD_DIR / "dashboard_data.json"
SCHEMA_VERSION = 2
EXPECTED_COLUMNS = 56

DATA_START = "/* CBJML_DATA_START */"
DATA_END = "/* CBJML_DATA_END */"
DATA_RE = re.compile(re.escape(DATA_START) + r".*?" + re.escape(DATA_END), re.DOTALL)

SCALE_OPTIONS = ["Excelente", "Bueno", "Aceptable", "Deficiente", "No conozco lo suficiente"]
AGREEMENT_OPTIONS = ["Totalmente de acuerdo", "De acuerdo", "Ni de acuerdo ni en desacuerdo", "En desacuerdo", "Totalmente en desacuerdo"]
MATRIX_ACTIONS = ["Mantener", "Mejorar", "Transformar", "No prioritario"]
PARTICIPATION_ORDER = ["Siempre", "Frecuentemente", "Algunas veces", "Rara vez", "Casi nunca", "Nunca"]
ANTIGUEDAD_ORDER = ["Menos de 2 años", "Entre 2 y 5 años", "Entre 6 y 10 años", "Más de 10 años"]
CHANGE_RESPONSE_ORDER = [
    "Se anticipa y responde de manera integral a estos cambios",
    "Responde a la mayoría de los cambios de forma oportuna",
    "Responde a algunos cambios, pero no a otros",
    "Hay esfuerzos aislados, pero insuficientes",
    "El Colegio no está atendiendo estos cambios",
]
IDENTITY_OPTIONS = [
    "Tradiciones y celebraciones", "Sentido de comunidad", "Programa de emprendimiento",
    "Desarrollo de competencias tecnológicas", "Escuela de argumentación",
    "Relación entre el Colegio y las familias", "Actividades artísticas, culturales y deportivas",
    "Cercanía y acompañamiento a los estudiantes", "Programa SER / Programa CARE",
    "Proyección internacional de los estudiantes", "Excelencia académica", "Formación en valores",
]
DIFFERENCE_OPTIONS = [
    "Relación con la tecnología y las redes sociales", "Forma de aprender", "Necesidades socioemocionales",
    "Atención y concentración", "Relación con la autoridad y los profesores", "Expectativas frente al futuro",
    "Relación con la información", "Relación con sus compañeros",
]
INITIATIVE_OPTIONS = [
    "Esquemas de reconocimiento monetario a estudiantes destacados",
    "Inteligencia artificial responsable, programación y robótica", "Liderazgo, debate y oratoria",
    "Emprendimiento y proyectos con impacto social", "Voluntariado y servicio comunitario",
    "Mentoría profesional o de emprendimiento", "Mentoría entre estudiantes mayores y menores",
    "Orientación vocacional desde grados tempranos",
    "Programa de salud mental y bienestar", "Arte y deporte de alto rendimiento", "Proyectos interdisciplinarios",
    "Educación financiera", "Red de exalumnos y familias",
]
CONTRIBUTION_OPTIONS = [
    "Respondiendo consultas como esta", "Voluntariado en eventos, proyectos sociales, culturales o deportivos",
    "Talleres o espacios para padres", "Charlas o talleres para estudiantes",
    "Mentoría profesional o de emprendimiento", "Por ahora no me es posible participar",
]
VOZ_QUESTION_FALLBACKS = {
    "no_perder": (27, "¿Qué sería especialmente importante NO perder, aunque el Colegio atraviese procesos de cambio?"),
    "cambiar": (51, "Si pudiera cambiar o mejorar UNA sola cosa del Colegio, ¿Cuál sería y cómo lo haría?"),
    "ensenar": (54, "Complete la frase: «Quisiera que cuando mi hijo(a) termine el Colegio pudiera decir que el Colegio le enseñó principalmente a..."),
    "recomendar": (55, "Si recomendara el Colegio, ¿qué sería lo principal que le diría a esa familia que encontrará aquí?"),
}
COURSE_ORDER = ["Preescolar", "Primero", "Segundo", "Tercero", "Cuarto", "Quinto", "Sexto", "Séptimo", "Octavo", "Noveno", "Décimo", "Undécimo"]
COURSE_TO_SECTION = {
    "preescolar": "Infantil", "primero": "Infantil", "segundo": "Infantil", "tercero": "Infantil",
    "cuarto": "Prejuvenil", "quinto": "Prejuvenil", "sexto": "Prejuvenil", "septimo": "Prejuvenil",
    "octavo": "Juvenil", "noveno": "Juvenil", "decimo": "Juvenil", "undecimo": "Juvenil",
}
WORD_PRESENTATION = {
    "critico": "Crítico", "formacion": "Formación", "participacion": "Participación", "comunicacion": "Comunicación",
    "educacion": "Educación", "etica": "Ética", "tecnologia": "Tecnología", "ingles": "Inglés", "practica": "Práctica",
    'matematica': 'Matemática', 'matematicas': 'Matemáticas', 'cercania': 'Cercanía', 'academica': 'Académica',
    'empatia': 'Empatía', 'critica': 'Crítica', 'autonomia': 'Autonomía', 'acompanamiento': 'Acompañamiento',
    'bilinguismo': 'Bilingüismo', 'empatico': 'Empático', 'etico': 'Ético', 'ninos': 'Niños', 'chicos': 'Chicos',
}
WORD_STOP_KEYS = {
    "cada", "estudiantes", "estudiante", "el", "la", "los", "las", "de", "del", "que", "en", "un", "una", "uno",
    "unos", "unas", "por", "con", "para", "se", "sus", "su", "al", "y", "es", "son", "mas", "muy", "como", "todo",
    "todos", "toda", "todas", "lo", "mi", "mis", "hijo", "hija", "hijos", "hijas", "no", "le", "les", "ni", "si",
    "hay", "ha", "he", "tienen", "tiene", "tener", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "sino", "sobre", "entre", "desde", "hasta", "sin", "tras", "durante", "mediante", "segun", "excepto", "hacia",
    "a", "ante", "bajo", "contra", "o", "u", "e", "pues", "porque", "cuando", "donde", "quien", "cual", "cuyo",
    "cuya", "cuyos", "cuyas", "cuanto", "cuanta", "cuantos", "cuantas", "familias", "colegio",
}


def clean_text(value: Any) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def normalize_key(value: Any) -> str:
    value = clean_text(value).casefold()
    return "".join(ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn")


def normalize_word(value: Any) -> str:
    key = normalize_key(value)
    return "" if key in WORD_STOP_KEYS else key


def extract_question_label(header: str, fallback: str) -> str:
    match = re.search(r"\[(.*?)\]", clean_text(header))
    return clean_text(match.group(1)) if match else fallback


def build_voice_questions(headers: list[str]) -> dict[str, str]:
    questions: dict[str, str] = {}
    for key, (index, fallback) in VOZ_QUESTION_FALLBACKS.items():
        raw = clean_text(headers[index]) if index < len(headers) else ""
        bracketed = extract_question_label(raw, "")
        # The first question has a product-approved wording; the other three
        # retain the current Sheet wording so the selector and data stay aligned.
        questions[key] = fallback if key == "cambiar" else bracketed or raw or fallback
    return questions


def build_questions(headers: list[str]) -> dict[str, dict[str, str]]:
    return {
        "aspectos": {f"aspecto_{i + 1:02d}": extract_question_label(headers[6 + i] if 6 + i < len(headers) else "", f"Aspecto {i + 1}") for i in range(12)},
        "afirmaciones": {f"afirmacion_{i + 1:02d}": extract_question_label(headers[20 + i] if 20 + i < len(headers) else "", f"Afirmación {i + 1}") for i in range(7)},
        "retos": {f"reto_{i + 1:02d}": extract_question_label(headers[30 + i] if 30 + i < len(headers) else "", f"Reto {i + 1}") for i in range(7)},
        "matriz": {f"area_{i + 1:02d}": extract_question_label(headers[38 + i] if 38 + i < len(headers) else "", f"Área {i + 1}") for i in range(13)},
        "voz": build_voice_questions(headers),
    }


def redact_free_text(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[correo eliminado]", text)
    text = re.sub(r"https?://\S+|www\.\S+", "[enlace eliminado]", text)
    # Remove phone-like numbers to reduce accidental personal data exposure.
    text = re.sub(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", "[teléfono eliminado]", text)
    # Names are not PII-safe by themselves; redact only explicit person-title
    # contexts so ordinary capitalized concepts remain readable.
    name_token = r"[A-ZÁÉÍÓÚÜÑ][\wÁÉÍÓÚÜáéíóúüñ]+"
    person_name = rf"{name_token}(?:\s+{name_token}){{0,3}}"
    text = re.sub(rf"\b(Sr|Sra|Srta|Dr|Dra)\.?\s+{person_name}", r"\1. [persona eliminada]", text)
    text = re.sub(
        rf"\b(profesor|profesora|maestro|maestra|director|directora|coordinador|coordinadora)\s+{person_name}",
        r"\1 [persona eliminada]",
        text,
    )
    return text


def match_options(value: str, options: list[str]) -> list[str]:
    normalized = normalize_key(value)
    return [option for option in options if normalize_key(option) in normalized]


def parse_courses(value: str) -> list[str]:
    parts = [normalize_key(part) for part in clean_text(value).split(",")]
    return [course for course in COURSE_ORDER if normalize_key(course) in parts]


def section_for_course(course: str) -> str | None:
    return COURSE_TO_SECTION.get(normalize_key(course))


def pct(count: int, total: int) -> float:
    return round((count / total) * 100, 1) if total else 0.0


def modal_label(counter: Counter[str], options: list[str]) -> str | None:
    if not counter:
        return None
    max_count = max(counter.values())
    winners = [label for label in options if counter.get(label, 0) == max_count]
    return winners[0] if len(winners) == 1 else "Empate"


def _to_rank(value: str) -> int | None:
    try:
        rank = int(clean_text(value))
        return rank if 1 <= rank <= 7 else None
    except (TypeError, ValueError):
        return None


def build_response_record(headers: list[str], row: list[str], index: int) -> dict[str, Any]:
    get = lambda idx: clean_text(row[idx]) if idx < len(row) else ""
    courses = parse_courses(get(3))
    sections = list(dict.fromkeys(section_for_course(course) for course in courses if section_for_course(course)))
    aspect_keys = [f"aspecto_{i + 1:02d}" for i in range(12)]
    afirmacion_keys = [f"afirmacion_{i + 1:02d}" for i in range(7)]
    reto_keys = [f"reto_{i + 1:02d}" for i in range(7)]
    matriz_keys = [f"area_{i + 1:02d}" for i in range(13)]
    raw_words = re.findall(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+", get(19))
    return {
        "id": f"response-{index + 1}", "hijos": get(2), "cursos": courses, "cursos_texto": get(3),
        "secciones": sections, "antiguedad": get(4), "participacion": get(5),
        "aspectos": {key: get(6 + i) for i, key in enumerate(aspect_keys)},
        "afirmaciones": {key: get(20 + i) for i, key in enumerate(afirmacion_keys)},
        "retos": {key: _to_rank(get(30 + i)) for i, key in enumerate(reto_keys)},
        "matriz": {key: get(38 + i) for i, key in enumerate(matriz_keys)},
        "identidad": match_options(get(18), IDENTITY_OPTIONS),
        "diferencias": match_options(get(28), DIFFERENCE_OPTIONS),
        "respuesta_cambio": get(29), "iniciativas": match_options(get(52), INITIATIVE_OPTIONS),
        "aporte": match_options(get(53), CONTRIBUTION_OPTIONS),
        "quotes": {key: text for key, text in {
            "no_perder": redact_free_text(get(27)), "cambiar": redact_free_text(get(51)),
            "ensenar": redact_free_text(get(54)), "recomendar": redact_free_text(get(55)),
        }.items() if text},
        "word_tokens": [normalized for normalized in (normalize_word(token) for token in raw_words) if len(normalized) > 3],
    }


def build_snapshot(data: list[list[str]]) -> dict[str, Any]:
    if not data or len(data[0]) < EXPECTED_COLUMNS:
        raise ValueError(f"Sheet inválido: se esperaban {EXPECTED_COLUMNS} columnas")
    headers = data[0]
    responses = [build_response_record(headers, row, index) for index, row in enumerate(data[1:]) if any(clean_text(value) for value in row)]
    return {
        "schema_version": SCHEMA_VERSION,
        "questions": build_questions(headers),
        "responses": responses,
    }


def _count_option(records: list[dict[str, Any]], getter: Any, options: list[str]) -> list[dict[str, Any]]:
    valid = [record for record in records if getter(record)]
    total = len(valid)
    result = [{"label": option, "opcion": option, "count": sum(1 for record in valid if getter(record) == option), "pct": 0.0} for option in options]
    for item in result:
        item["pct"] = pct(item["count"], total)
    return [item for item in result if item["count"] > 0]


def _count_multi(records: list[dict[str, Any]], getter: Any, options: list[str]) -> list[dict[str, Any]]:
    # Rank multiselect answers by support so "Iniciativa Top" reports the most
    # relevant option instead of the first canonical label. Ties break
    # alphabetically to keep repeated runs identical.
    valid = [record for record in records if getter(record)]
    total = len(valid)
    result = [{"opcion": option, "count": sum(1 for record in valid if option in getter(record)), "pct": 0.0} for option in options]
    for item in result:
        item["pct"] = pct(item["count"], total)
    ranked = [item for item in result if item["count"] > 0]
    return sorted(ranked, key=lambda item: (-item["count"], item["opcion"]))


def compute_metrics(payload: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        records = list(payload.get("responses", []))
        questions = payload.get("questions", {}) if isinstance(payload.get("questions", {}), dict) else {}
    else:
        records = list(payload)
        first = records[0] if records else {}
        questions = first.get("questions", {}) if isinstance(first, dict) else {}
    N = len(records)
    first = records[0] if records else None
    aspect_keys = list((first or {}).get("aspectos", {}).keys()) or [f"aspecto_{i:02d}" for i in range(1, 13)]
    affirmation_keys = list((first or {}).get("afirmaciones", {}).keys()) or [f"afirmacion_{i:02d}" for i in range(1, 8)]
    reto_keys = list((first or {}).get("retos", {}).keys()) or [f"reto_{i:02d}" for i in range(1, 8)]
    matriz_keys = list((first or {}).get("matriz", {}).keys()) or [f"area_{i:02d}" for i in range(1, 14)]
    question_labels = questions.get("aspectos", {})
    affirmation_labels = questions.get("afirmaciones", {})
    reto_labels = questions.get("retos", {})
    matrix_labels = questions.get("matriz", {})
    aspectos = []
    for key in aspect_keys:
        values = [record["aspectos"].get(key, "") for record in records]
        valid = [value for value in values if value]
        total = len(valid)
        item = {"aspecto": question_labels.get(key, key), "key": key}
        for option in SCALE_OPTIONS:
            count = valid.count(option)
            item[option] = {"count": count, "pct": pct(count, total)}
        item["satisfaccion_positiva_pct"] = round(item["Excelente"]["pct"] + item["Bueno"]["pct"], 1)
        aspectos.append(item)
    afirmaciones = []
    for key in affirmation_keys:
        values = [record["afirmaciones"].get(key, "") for record in records]
        valid = [value for value in values if value]
        total = len(valid)
        item = {"afirmacion": affirmation_labels.get(key, key), "key": key}
        for option in AGREEMENT_OPTIONS:
            count = valid.count(option)
            item[option] = {"count": count, "pct": pct(count, total)}
        item["acuerdo_total_pct"] = round(item["Totalmente de acuerdo"]["pct"] + item["De acuerdo"]["pct"], 1)
        afirmaciones.append(item)
    retos = []
    for key in reto_keys:
        values = [record["retos"].get(key) for record in records]
        valid = [value for value in values if isinstance(value, int)]
        retos.append({"reto": reto_labels.get(key, key), "key": key, "media_urgencia": round(sum(valid) / len(valid), 2) if valid else 0, "top2_pct": pct(sum(1 for value in valid if value <= 2), len(valid)), "valid": len(valid)})
    matrix = []
    matrix_groups = {action: [] for action in [*MATRIX_ACTIONS, "Sin respuesta", "Empate"]}
    matrix_by_area: dict[str, dict[str, Any]] = {}
    for key in matriz_keys:
        label = matrix_labels.get(key, key)
        area_key = normalize_key(label)
        values = [record["matriz"].get(key, "") for record in records]
        valid = [value for value in values if value in MATRIX_ACTIONS]
        counter = Counter(valid)
        if area_key not in matrix_by_area:
            matrix_by_area[area_key] = {"area": label, "key": key, "counts": {option: 0 for option in MATRIX_ACTIONS}}
        entry = matrix_by_area[area_key]
        for option in MATRIX_ACTIONS:
            entry["counts"][option] += counter.get(option, 0)
    for entry in matrix_by_area.values():
        counter = Counter({option: count for option, count in entry["counts"].items() if count})
        action = modal_label(counter, MATRIX_ACTIONS) or "Sin respuesta"
        total = sum(entry["counts"].values())
        entry["action"] = action
        entry["pcts"] = {option: pct(entry["counts"][option], total) for option in MATRIX_ACTIONS}
        entry.update({option: {"count": entry["counts"][option], "pct": entry["pcts"][option]} for option in MATRIX_ACTIONS})
        matrix.append(entry)
        matrix_groups.setdefault(action, []).append(entry)
    for group in matrix_groups.values():
        group.sort(key=lambda item: item["pcts"].get(item["action"] if item["action"] in MATRIX_ACTIONS else "", 0), reverse=True)
    identity = _count_multi(records, lambda record: record["identidad"], IDENTITY_OPTIONS)
    differences = _count_multi(records, lambda record: record["diferencias"], DIFFERENCE_OPTIONS)
    initiatives = _count_multi(records, lambda record: record["iniciativas"], INITIATIVE_OPTIONS)
    contribution = _count_multi(records, lambda record: record["aporte"], CONTRIBUTION_OPTIONS)
    change = _count_option(records, lambda record: record["respuesta_cambio"], CHANGE_RESPONSE_ORDER)
    participation = _count_option(records, lambda record: record["participacion"], PARTICIPATION_ORDER)
    antiguedad = _count_option(records, lambda record: record["antiguedad"], ANTIGUEDAD_ORDER)
    words = Counter()
    for record in records:
        words.update(record.get("word_tokens", []))
    top_words = [{"palabra": WORD_PRESENTATION.get(word, word[:1].upper() + word[1:]), "frecuencia": count} for word, count in words.most_common(20)]
    demo = {"total_respuestas": N, "hijos": _count_option(records, lambda record: record["hijos"], ["1", "2", "3", "4", "5"]), "antiguedad": antiguedad, "participacion": participation, "secciones": [{"label": section, "count": sum(1 for record in records if section in record["secciones"]), "pct": pct(sum(1 for record in records if section in record["secciones"]), N)} for section in ["Infantil", "Prejuvenil", "Juvenil"]]}
    urgent = sorted([item for item in retos if item["valid"]], key=lambda item: item["media_urgencia"])
    kpis = {
        "bienestar_hijos_pct": afirmaciones[5]["acuerdo_total_pct"] if len(afirmaciones) >= 6 else 0.0,
        "comunidad_leonista_pct": afirmaciones[6]["acuerdo_total_pct"] if len(afirmaciones) >= 7 else 0.0,
        "coincidencia_valores_pct": afirmaciones[1]["acuerdo_total_pct"] if len(afirmaciones) >= 2 else 0.0,
        "identidad_diferenciada_pct": afirmaciones[0]["acuerdo_total_pct"] if afirmaciones else 0.0,
        "participacion_activa_pct": pct(sum(item["count"] for item in participation if item["label"] in PARTICIPATION_ORDER[:2]), len(records)),
        "reto_urgente_1": urgent[0]["reto"] if urgent else "Sin respuesta", "reto_urgente_1_pct": urgent[0]["top2_pct"] if urgent else 0.0,
        "reto_urgente_2": urgent[1]["reto"] if len(urgent) >= 2 else "Sin respuesta", "reto_urgente_2_pct": urgent[1]["top2_pct"] if len(urgent) >= 2 else 0.0,
        "iniciativa_top_1": initiatives[0]["opcion"] if initiatives else "Sin respuesta", "iniciativa_top_1_pct": initiatives[0]["pct"] if initiatives else 0.0,
        "disposicion_aporte_pct": pct(sum(1 for record in records if any(option != "Por ahora no me es posible participar" for option in record["aporte"])), len(records)),
    }
    quotes = []
    for record in records:
        if any(record["quotes"].values()):
            quote = dict(record["quotes"])
            quote.update({"id": record["id"], "curso": record["cursos_texto"], "nivel": ", ".join(record["secciones"]), "antiguedad": record["antiguedad"]})
            quotes.append(quote)
    return {"KPIS": kpis, "ASPECTOS": aspectos, "AFIRMACIONES": afirmaciones, "RETOS": retos, "MATRIZ": matrix, "matrix_groups": matrix_groups, "IDENTIDAD": identity, "DIFERENCIAS": differences, "INICIATIVAS": initiatives, "APORTE": contribution, "DEMO": demo, "RESP_CAMBIOS": change, "TOP_WORDS": top_words, "QUOTES": quotes, "N": N}


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def inject_snapshot(html_text: str, snapshot: dict[str, Any]) -> str:
    # Escape only the script-closing sequence; JSON strings remain valid JavaScript
    # and free-text content cannot terminate the surrounding script element.
    encoded = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("</", "<\\/")
    block = f"{DATA_START}\nvar CBJML_SNAPSHOT={encoded};\n{DATA_END}"
    if DATA_RE.search(html_text):
        return DATA_RE.sub(lambda _: block, html_text, count=1)
    marker = "  <script id=\"cbjml-data\">\n"
    if marker not in html_text:
        raise ValueError("Plantilla HTML sin bloque de datos estable")
    return html_text.replace(marker, f"{marker}{block}\n", 1)


def validate_rendered_html(rendered: str) -> None:
    required_ids = ["sampleTotal", "filterPanel", "filterSeccion", "filterAntiguedad", "filterCurso", "matrixGroups", "vozQuestionBar", "vozQuestionText", "wordCloudContainer", "quotesList"]
    missing = [element_id for element_id in required_ids if rendered.count(f'id="{element_id}"') != 1]
    if missing:
        raise ValueError(f"HTML inválido: IDs ausentes o duplicados: {missing}")
    if rendered.count(DATA_START) != 1 or rendered.count(DATA_END) != 1:
        raise ValueError("HTML inválido: marcadores de datos no son únicos")


def refresh_access_token() -> str:
    payload = urllib.parse.urlencode({"client_id": os.environ.get("GOOGLE_CLIENT_ID", ""), "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""), "refresh_token": os.environ.get("GOOGLE_REFRESH_TOKEN", ""), "grant_type": "refresh_token"}).encode()
    request = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())["access_token"]


def fetch_sheet() -> list[list[str]]:
    token = refresh_access_token()
    quoted_range = urllib.parse.quote(SHEET_RANGE, safe="")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{quoted_range}?majorDimension=ROWS&valueRenderOption=FORMATTED_VALUE"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read()).get("values", [])


def run_pipeline() -> tuple[int, str]:
    data = fetch_sheet()
    snapshot = build_snapshot(data)
    metrics = compute_metrics(snapshot)
    if metrics["N"] != len(snapshot["responses"]):
        raise ValueError("El modelo agregado no coincide con el snapshot")
    rendered = inject_snapshot(HTML_PATH.read_text(encoding="utf-8"), snapshot)
    validate_rendered_html(rendered)
    write_json_atomic(JSON_PATH, snapshot)
    fd, temp_name = tempfile.mkstemp(prefix=f".{HTML_PATH.name}.", dir=str(HTML_PATH.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, HTML_PATH)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return len(snapshot["responses"]), "OK"


if __name__ == "__main__":
    try:
        count, status = run_pipeline()
        print(f"N={count} families")
        print(status)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
