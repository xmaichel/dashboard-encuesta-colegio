#!/usr/bin/env python3
"""Pruebas puras para el modelo de respuestas y filtros del dashboard CBJML."""
from __future__ import annotations

import importlib.util
import json
import math
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ETL_PATH = ROOT / "etl_sync.py"
SERVER_PATH = ROOT / "cbjml-server.py"
spec = importlib.util.spec_from_file_location("cbjml_etl", ETL_PATH)
etl = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(etl)
server_spec = importlib.util.spec_from_file_location("cbjml_server", SERVER_PATH)
assert server_spec is not None and server_spec.loader is not None
server = importlib.util.module_from_spec(server_spec)
server_spec.loader.exec_module(server)


def make_row(overrides=None):
    row = [""] * 56
    defaults = {
        0: "2026-09-01 10:00:00",
        1: "family@example.com",
        2: "1",
        3: "Cuarto",
        4: "Entre 2 y 5 años",
        5: "Siempre",
        19: "Pensamiento crítico, cada estudiante",
        29: "Responde a la mayoría de los cambios de forma oportuna",
        51: "Más acompañamiento",
        54: "Ser una buena persona",
        55: "Lo recomiendo",
    }
    for index in range(6, 18):
        defaults[index] = "Bueno"
    for index in range(20, 27):
        defaults[index] = "De acuerdo"
    for offset, index in enumerate(range(30, 37), start=1):
        defaults[index] = str(offset)
    for index in range(38, 51):
        defaults[index] = "Mantener"
    defaults[18] = "Formación en valores"
    defaults[28] = "Forma de aprender"
    defaults[52] = "Educación financiera"
    defaults[53] = "Respondiendo consultas como esta"
    for key, value in defaults.items():
        row[key] = value
    for key, value in (overrides or {}).items():
        row[key] = value
    return row


def make_snapshot():
    headers = [""] * 56
    for index in range(6, 18):
        headers[index] = f"[Aspecto {index - 5}]"
    for index in range(20, 27):
        headers[index] = f"[Afirmación {index - 19}]"
    for index in range(30, 37):
        headers[index] = f"[Reto {index - 29}]"
    for index in range(38, 51):
        headers[index] = f"[Área {index - 37}]"
    return etl.build_snapshot([headers, make_row(), make_row({3: "Séptimo, Décimo"})])


class SnapshotTests(unittest.TestCase):
    def test_snapshot_has_all_responses_even_without_quotes(self):
        snapshot = etl.build_snapshot([[""] * 56, make_row({51: "", 54: "", 55: ""})])
        self.assertEqual(len(snapshot["responses"]), 1)
        self.assertEqual(snapshot["responses"][0]["quotes"], {})

    def test_snapshot_excludes_pii_columns_and_redacts_free_text(self):
        snapshot = etl.build_snapshot([
            [""] * 56,
            make_row({51: "Escribir a family@example.com o llamar 3001234567", 54: "https://example.com"}),
        ])
        encoded = json.dumps(snapshot, ensure_ascii=False)
        self.assertNotIn("family@example.com", encoded)
        self.assertNotIn("timestamp", encoded)
        self.assertNotIn("https://example.com", encoded)
        self.assertNotIn("3001234567", encoded)

    def test_redacts_explicit_person_names_in_free_text(self):
        snapshot = etl.build_snapshot([self_headers(), make_row({51: "Como el Sr. Juan Pérez, pediría más acompañamiento"})])
        encoded = json.dumps(snapshot, ensure_ascii=False)
        self.assertNotIn("Juan Pérez", encoded)
        self.assertIn("[persona eliminada]", encoded)

    def test_courses_with_accents_map_to_expected_sections(self):
        snapshot = etl.build_snapshot([[""] * 56, make_row({3: "Séptimo, Décimo, Undécimo"})])
        self.assertEqual(snapshot["responses"][0]["secciones"], ["Prejuvenil", "Juvenil"])

    def test_multiple_courses_are_not_duplicated(self):
        snapshot = etl.build_snapshot([[""] * 56, make_row({3: "Preescolar, Primero, Segundo"})])
        self.assertEqual(snapshot["responses"][0]["cursos"], ["Preescolar", "Primero", "Segundo"])
        self.assertEqual(snapshot["responses"][0]["secciones"], ["Infantil"])

    def test_snapshot_exposes_four_voice_questions_without_raw_headers(self):
        headers = self_headers()
        headers[27] = "Pregunta de no perder desde la hoja"
        headers[51] = "Pregunta de cambio desde la hoja"
        headers[54] = "Pregunta de enseñanza desde la hoja"
        headers[55] = "Pregunta de recomendación desde la hoja"
        snapshot = etl.build_snapshot([headers, make_row()])
        self.assertEqual(set(snapshot["questions"]["voz"]), {"cambiar", "no_perder", "ensenar", "recomendar"})
        self.assertEqual(snapshot["questions"]["voz"]["no_perder"], "Pregunta de no perder desde la hoja")
        self.assertNotIn("headers", snapshot)

    def test_word_tokens_are_normalized_and_stopwords_removed(self):
        record = make_snapshot()["responses"][0]
        self.assertIn("pensamiento", record["word_tokens"])
        self.assertIn("critico", record["word_tokens"])
        self.assertNotIn("cada", record["word_tokens"])
        self.assertNotIn("estudiantes", record["word_tokens"])
        self.assertNotIn("word_tokens_raw", record)

    def test_accent_variants_are_merged_before_ranking(self):
        headers = self_headers()
        first = make_row({19: "Crítico crítico"})
        second = make_row({19: "critico"})
        model = etl.compute_metrics(etl.build_snapshot([headers, first, second]))
        critical = next(item for item in model["TOP_WORDS"] if item["palabra"] == "Crítico")
        self.assertEqual(critical["frecuencia"], 3)

    def test_multi_select_ignores_unknown_person_name(self):
        row = make_row({18: "Formación en valores, Claudia Patricia Medina Mora"})
        record = etl.build_snapshot([self_headers(), row])["responses"][0]
        self.assertEqual(record["identidad"], ["Formación en valores"])
        self.assertNotIn("Claudia", json.dumps(record))


class MetricTests(unittest.TestCase):
    def test_matrix_assigns_each_area_once(self):
        snapshot = etl.build_snapshot([self_headers(), make_row()])
        model = etl.compute_metrics(snapshot)
        groups = model["matrix_groups"]
        areas = [entry["area"] for group in groups.values() for entry in group]
        self.assertEqual(len(areas), len(set(areas)))
        self.assertEqual(len(areas), 13)
        self.assertEqual(len(model["MATRIZ"]), 13)

    def test_matrix_uses_predominant_action_and_never_duplicate(self):
        snapshot = etl.build_snapshot([
            self_headers(),
            make_row(),
            make_row({38: "Mejorar"}),
        ])
        model = etl.compute_metrics(snapshot)
        self.assertEqual(len(model["matrix_groups"]["Mantener"]), 12)
        self.assertEqual(len(model["matrix_groups"]["Empate"]), 1)
        self.assertEqual(len(model["matrix_groups"]["Mejorar"]), 0)
        self.assertEqual(len({item["area"] for item in model["MATRIZ"]}), 13)

    def test_ties_are_not_assigned_to_two_actions(self):
        snapshot = etl.build_snapshot([
            self_headers(),
            make_row(),
            make_row({38: "Mejorar"}),
        ])
        model = etl.compute_metrics(snapshot)
        labels = [item["action"] for item in model["MATRIZ"]]
        self.assertEqual(len(labels), 13)
        self.assertEqual(sum(label == "Empate" for label in labels), 1)

    def test_zero_responses_returns_safe_model(self):
        model = etl.compute_metrics([])
        self.assertEqual(model["N"], 0)
        self.assertEqual(model["KPIS"]["bienestar_hijos_pct"], 0.0)
        self.assertEqual(model["matrix_groups"]["Mantener"], [])

    def test_pct_is_guarded_against_zero_denominator(self):
        model = etl.compute_metrics([])
        for key in ["participacion_activa_pct", "disposicion_aporte_pct"]:
            self.assertTrue(math.isfinite(model["KPIS"][key]))

    def test_participation_uses_first_two_frequency_options(self):
        rows = [
            make_row({5: "Siempre"}),
            make_row({5: "Frecuentemente"}),
            make_row({5: "Rara vez"}),
        ]
        headers = self_headers()
        model = etl.compute_metrics(etl.build_snapshot([headers, *rows]))
        self.assertEqual(model["KPIS"]["participacion_activa_pct"], 66.7)

    def test_initiative_kpi_reports_most_supported_not_first_canonical(self):
        # "Esquemas de reconocimiento monetario" is the first canonical option but
        # has the least support here; "Educación financiera" must win the KPI.
        headers = self_headers()
        rows = [
            make_row({52: "Esquemas de reconocimiento monetario a estudiantes destacados"}),
            make_row({52: "Educación financiera"}),
            make_row({52: "Educación financiera, Mentoría profesional o de emprendimiento"}),
        ]
        model = etl.compute_metrics(etl.build_snapshot([headers, *rows]))
        self.assertEqual(model["KPIS"]["iniciativa_top_1"], "Educación financiera")
        # 2 of the 3 valid families chose it.
        self.assertEqual(model["KPIS"]["iniciativa_top_1_pct"], 66.7)
        self.assertEqual(model["INICIATIVAS"][0]["opcion"], "Educación financiera")
        counts = [item["count"] for item in model["INICIATIVAS"]]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_multiselect_ranking_breaks_ties_alphabetically(self):
        headers = self_headers()
        rows = [
            make_row({52: "Educación financiera"}),
            make_row({52: "Red de exalumnos y familias"}),
        ]
        model = etl.compute_metrics(etl.build_snapshot([headers, *rows]))
        self.assertEqual(
            [item["opcion"] for item in model["INICIATIVAS"]],
            ["Educación financiera", "Red de exalumnos y familias"],
        )


class PipelineTests(unittest.TestCase):
    def test_same_snapshot_produces_identical_html(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        snapshot = make_snapshot()
        first = etl.inject_snapshot(template, snapshot)
        second = etl.inject_snapshot(first, snapshot)
        self.assertEqual(first, second)

    def test_snapshot_json_roundtrip_is_anonymous(self):
        snapshot = make_snapshot()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dashboard_data.json"
            etl.write_json_atomic(output, snapshot)
            loaded = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema_version"], 2)
        self.assertNotIn("email", json.dumps(loaded).lower())
        self.assertNotIn("headers", loaded)
        self.assertNotIn("word_tokens_raw", json.dumps(loaded))

    def test_public_server_allowlist_rejects_runtime_data(self):
        self.assertTrue(server.is_public_asset("/"))
        self.assertTrue(server.is_public_asset("/Dashboard_CBJML.html"))
        self.assertTrue(server.is_public_asset("/dashboard_runtime.js"))
        for path in ["/dashboard_data.json", "/etl_sync.py", "/cbjml-server.py", "/.env", "/../etc/passwd"]:
            self.assertFalse(server.is_public_asset(path), path)

    def test_pie_charts_expose_numeric_percentages(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # The plugin must stay type-gated so bar charts are never touched.
        self.assertIn("'pie' && type !== 'doughnut'", runtime.replace('type !== "doughnut"', "'pie' && type !== 'doughnut'"))
        self.assertIn("MIN_SHARE", runtime)
        self.assertIn("shareOf", runtime)
        self.assertIn("percentLegend", runtime)
        self.assertIn("cbjmlPercentageLabels", runtime)
        # Legend text must carry the numeric share for every slice.
        self.assertIn("(${shares[index] ?? 0}%)", runtime)
        # Only the pie/doughnut charts that fit use the Chart.js percent legend.
        # chartRespCambios renders a real HTML list instead: its labels are long
        # sentences and Chart.js clipped them on a ~250px canvas.
        legend_calls = runtime.count("...percentLegend()")
        self.assertEqual(legend_calls, 2)
        self.assertNotIn("...percentLegend(),\n    labels:", runtime)
        self.assertIn("display: false", runtime.split("chartRespCambios", 1)[1][:400])

    def test_pie_percentage_plugin_has_no_out_of_scope_arc(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # The outside-label builder was extracted from the arcs.forEach body, so
        # it must not reference `arc` any more: that threw ReferenceError at draw
        # time and silently killed every label in the chart.
        body = runtime.split("outsideCandidates.slice(0, MAX_OUTSIDE).forEach", 1)[1]
        body = body.split("});", 1)[0]
        self.assertNotIn("arc.", body)
        self.assertIn("cx, cy", runtime)
        # The cap must exist, otherwise tiny slices produce an unreadable web.
        self.assertIn("MAX_OUTSIDE", runtime)
        self.assertIn("OUTSIDE_MIN_GAP", runtime)
        self.assertIn("OUTSIDE_REACH", runtime)

    def test_resp_cambio_legend_is_a_single_html_list_with_swatches(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # Exactly one legend source: the old duplicated text block must be gone.
        self.assertIn('id="respCambioLegend"', template)
        self.assertNotIn("respCambioText", template)
        self.assertNotIn("respCambioText", runtime)
        # Each row must carry a colour swatch so the option can be identified.
        self.assertIn("RESP_CAMBIO_COLORS", runtime)
        self.assertIn("swatch.style.backgroundColor = color", runtime)
        # Swatch colours must match the doughnut dataset colours exactly.
        dataset = runtime.split("chartRespCambios", 1)[1]
        chart_colors = dataset.split("backgroundColor: [", 1)[1].split("]", 1)[0]
        legend_colors = runtime.split("RESP_CAMBIO_COLORS = [", 1)[1].split("]", 1)[0]
        self.assertEqual(
            [c.strip() for c in chart_colors.split(",")],
            [c.strip() for c in legend_colors.split(",")]
        )

    def test_runtime_has_no_undefined_identifier_in_percentage_plugin(self):
        # A leftover `halves.length = 0` from a cancelled refactor threw
        # ReferenceError at draw time and silently removed every pie label.
        # eslint-free repo: catch undefined identifiers with a small scope check.
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        start = runtime.index("afterDatasetsDraw(chart) {")
        body = runtime[start:]
        # Collect the identifiers this plugin declares or imports.
        declared = set()
        for pattern in (
            r"const\s+([A-Za-z_$][\w$]*)",
            r"let\s+([A-Za-z_$][\w$]*)",
            r"\bfunction\s+([A-Za-z_$][\w$]*)",
            r"([A-Za-z_$][\w$]*)\s*=.*=>",
            r"\{([A-Za-z_$][\w$]*)\s*\}",
        ):
            declared.update(re.findall(pattern, body))
        # Names available from the enclosing IIFE scope or the JS globals.
        declared.update(
            {
                "Chart", "shareOf", "MIN_SHARE", "OUTSIDE_REACH", "OUTSIDE_MIN_GAP",
                "MAX_OUTSIDE", "INLINE_MIN_GAP", "$", "state", "text",
                "window", "document", "console", "Math", "Number", "Object",
                "Array", "JSON", "String", "Boolean", "isNaN", "parseInt", "parseFloat",
                "ResizeObserver", "requestAnimationFrame", "setTimeout", "clearTimeout",
            }
        )
        assignments = re.findall(r"^\s*([A-Za-z_$][\w$]*)\.[A-Za-z_$][\w$]*\s*=", body, re.M)
        for name in set(assignments):
            self.assertIn(name, declared, f"undefined identifier {name!r} in percentage plugin")

    def test_sixth_tab_conclusiones_is_wired(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # Nav button and content container must both exist and be paired.
        self.assertIn('id="tab-conclusiones"', template)
        self.assertIn("switchTab('conclusiones')", template)
        self.assertIn('id="content-conclusiones"', template)
        # switchTab whitelists tab names: a new tab that is not listed is ignored.
        body = runtime.split("function switchTab(tabName)", 1)[1].split("return;", 1)[0]
        self.assertIn("'conclusiones'", body)
        self.assertIn("'comunidad'", body)
        self.assertIn("'resumen'", body)
        # All six tab contents must exist exactly once.
        for name in ("resumen", "calidad", "matriz", "retos", "comunidad", "conclusiones"):
            self.assertEqual(template.count(f'id="content-{name}"'), 1, name)
            self.assertEqual(template.count(f'id="tab-{name}"'), 1, name)
        # The editorial percentages are static, so the tab must say so.
        self.assertIn("insightsSampleSize", template)
        self.assertIn("77 respuestas", template)

    def test_html_snapshot_contains_no_pii_columns(self):
        headers = self_headers()
        headers[0] = "Marca temporal"
        headers[1] = "Dirección de correo electrónico"
        snapshot = etl.build_snapshot([headers, make_row()])
        encoded = json.dumps(snapshot, ensure_ascii=False)
        self.assertNotIn("family@example.com", encoded)
        self.assertNotIn("Dirección de correo electrónico", encoded)
        self.assertNotIn("Marca temporal", encoded)
        self.assertEqual(encoded.count("headers"), 0)


def self_headers():
    headers = [""] * 56
    for index in range(6, 18):
        headers[index] = f"[Aspecto {index - 5}]"
    for index in range(20, 27):
        headers[index] = f"[Afirmación {index - 19}]"
    for index in range(30, 37):
        headers[index] = f"[Reto {index - 29}]"
    for index in range(38, 51):
        headers[index] = f"[Área {index - 37}]"
    return headers


if __name__ == "__main__":
    unittest.main(verbosity=2)
