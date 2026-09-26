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

    def test_all_tabs_are_wired_and_nav_columns_match(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        names = ("resumen", "calidad", "matriz", "retos", "comunidad", "conclusiones", "hojaruta")
        for name in names:
            # switchTab whitelists tab names: a new tab that is not listed is ignored.
            self.assertIn(f"switchTab('{name}')", template)
            self.assertEqual(template.count(f'id="content-{name}"'), 1, name)
            self.assertEqual(template.count(f'id="tab-{name}"'), 1, name)
        body = runtime.split("function switchTab(tabName)", 1)[1].split("return;", 1)[0]
        for name in names:
            self.assertIn(f"'{name}'", body)
        # The nav grid must match the number of buttons or the last tab wraps.
        nav = template.split("<nav", 1)[1].split("</nav>", 1)[0]
        buttons = nav.count('class="tab-btn')
        self.assertEqual(buttons, len(names))
        self.assertIn(f"repeat({buttons}, minmax(0, 1fr))", template)

    def test_insights_tab_figures_are_live_not_hardcoded(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        block = template.split('id="content-conclusiones"', 1)[1].split('id="content-hojaruta"', 1)[0]
        # No fixed percentages: this tab used to ship figures from a 77-row cut
        # while the dashboard was showing 226 rows, which read as live data.
        # "0%" is the placeholder every live field starts from, so only a
        # non-zero literal counts as a hardcoded figure.
        found = re.findall(r">\s*(\d{1,3}(?:\.\d)?)%\s*<", block)
        hardcoded = [v for v in found if float(v) != 0]
        self.assertEqual(hardcoded, [], f"hardcoded percentage in Insights tab: {hardcoded}")
        # Every figure is written by the renderer from model.INSIGHTS.
        for anchor in (
            "insightsIndex", "ejeAdnPct", "ejeAlertaPct", "ejeDemandaPct", "ejePotencialPct",
            "paradoja1Reto", "paradoja2Pct", "paradoja3Top", "paradoja4Top",
        ):
            self.assertIn(f'id="{anchor}"', block, anchor)
            self.assertIn(f"'{anchor}'", runtime, anchor)
        self.assertIn("INSIGHTS: insights", runtime)
        self.assertIn("function renderInsights", runtime)
        # The tab must declare that it follows the filters.
        self.assertIn("Vista filtrada", runtime)

    def test_roadmap_tab_is_a_static_decision_document(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        block = template.split('id="content-hojaruta"', 1)[1]
        self.assertIn("Documento de Decisión", block)
        self.assertIn("No depende de los filtros", block)
        self.assertIn("6. Insights &amp; Conclusiones", block)
        self.assertIn('id="roadmapSampleSize"', block)
        for horizon in ("Horizonte 1", "Horizonte 2", "Horizonte 3"):
            self.assertIn(horizon, block)

    def test_tab_nav_keeps_all_tabs_on_one_row(self):
        template = (ROOT / "Dashboard_CBJML.html").read_text(encoding="utf-8")
        # A fixed column count with more buttons than columns wraps the last tab
        # onto a second row: the bar changes height and pushes content down.
        self.assertNotIn("grid-cols-5", template.split("</nav>")[0])
        # Tabs need a responsive container: grid at >=sm, scroll at <sm.
        self.assertIn('id="tabNav"', template)
        self.assertIn("grid-template-columns: repeat(7, minmax(0, 1fr))", template)
        self.assertIn("overflow-x: auto", template)
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # The active tab must be scrolled into view when the bar scrolls.
        self.assertIn("nav.scrollLeft = target", runtime)
        self.assertIn("nav.scrollWidth > nav.clientWidth", runtime)
        # offsetLeft is relative to the nearest positioned ancestor, so the
        # scroll math must use getBoundingClientRect deltas.
        self.assertNotIn("active.offsetLeft", runtime)

    def test_no_identifier_is_used_before_its_declaration(self):
        # A const/let declared after its use inside a closure throws only at
        # paint time ("Cannot access X before initialization"), which a source
        # scan must catch: it took down every pie percentage once already.
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        declared = set(re.findall(r"\b(?:const|let|function)\s+([A-Za-z_$][\w$]*)", runtime))
        for name in ("roundText", "isDarkColor", "size", "palette", "usable", "text"):
            self.assertIn(name, declared, f"{name} must be declared")
        # roundText is used inside the draw hook, so it has to live above it.
        self.assertLess(
            runtime.index("const roundText"),
            runtime.index("const rounded = roundText(share)"),
            "roundText must be declared before the draw hook uses it",
        )
        # The helper must not be redeclared inside the hook, which would hoist
        # a second binding in the wrong order.
        hook = runtime.split("afterDatasetsDraw(chart)", 1)[1]
        self.assertNotIn("const roundText", hook)

    def test_inline_label_uses_both_geometric_limits(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        inline = runtime.split("if (share >= MIN_SHARE)", 1)[1].split("// Small slice", 1)[0]
        # A horizontal label must fit both the wedge and the disc. Checking only
        # the wedge gave a 250-degree slice zero room and left it unreadable.
        self.assertIn("r * Math.tan(halfAngle)", inline)
        self.assertIn("Math.sqrt(Math.max(0, (R * R) - (r * r)))", inline)
        self.assertIn("Math.min(tangential, radial)", inline)
        # A slice wider than a half-turn has no tangential limit.
        self.assertIn("halfAngle >= (Math.PI / 2) - 0.05", inline)
        self.assertIn("? Infinity", inline)

    def test_outside_labels_clamp_to_the_canvas_not_only_the_chart_area(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # chartArea.left can be negative on narrow charts; clamping against it
        # alone left labels at x<0, which the canvas silently cut off.
        self.assertIn("const boundLeft = Math.max(0, area.left)", runtime)
        self.assertIn("const boundRight = Math.min(context.canvas.width, area.right)", runtime)
        self.assertIn("const limitLeft = Math.max(0, area ? area.left : 0)", runtime)
        self.assertIn("const limitRight = Math.min(context.canvas.width, area ? area.right : context.canvas.width)", runtime)

    def test_outside_column_bounds_apply_to_single_labels_too(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        block = runtime.split("const side = (item) =>", 1)[1].split("// Horizontal clamp", 1)[0]
        # The underflow correction used to live inside `if (group.length > 1)`,
        # so a lone label near the top was drawn half off-canvas.
        self.assertNotIn("if (group.length > 1) {", block)
        # Spreading, fitting and the underflow push must all run unconditionally.
        self.assertIn("if (gap < OUTSIDE_MIN_GAP) group[i].y = group[i - 1].y + OUTSIDE_MIN_GAP", block)
        self.assertIn("const span = group[group.length - 1].y - group[0].y", block)
        self.assertIn("const room = Math.max(0, bottom - top)", block)
        self.assertIn("const underflow = top - group[0].y", block)
        self.assertIn("if (underflow > 0) group.forEach((item) => { item.y += underflow; });", block)
        # When the column is taller than the space, centre it rather than
        # clamping every item to the same edge (which re-introduces overlaps).
        self.assertIn("if (span > room && span > 0)", block)
        self.assertIn("const shift = (room - span) / 2", block)

    def test_pie_plugin_measures_text_after_setting_the_font(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # The original bug: measureText ran before ctx.font was set, so every
        # label measured ~10px wide and the separation loop saw no collision.
        # Assert the font is set before every measureText in the inline path.
        inline = runtime.split("if (share >= MIN_SHARE)", 1)[1].split("// Small slice", 1)[0]
        first_font = inline.find("context.font = `600 ${candidate}px")
        first_measure = inline.find("context.measureText")
        self.assertNotEqual(first_font, -1, "inline path must set a per-label font")
        self.assertLess(first_font, first_measure, "font must be set before measuring")
        self.assertIn("w: context.measureText(rounded).width", inline)
        # And the size must be honoured at draw time, not only measured.
        self.assertIn("context.font = `600 ${item.size}px ${LABEL_FONT}`", runtime)

    def test_pie_plugin_rounds_inline_percentages_and_keeps_decimal_in_legend(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # "8.0%" inside a wedge is noise; the decimal stays in the legend.
        self.assertIn("const roundText = (share) => `${Math.round(share)}%`", runtime)
        self.assertIn("text: `${label} (${shares[index] ?? 0}%)`", runtime)
        # Font sizing must adapt to the arc, not be a hardcoded 11px.
        self.assertIn("const SIZE_LARGE = 13", runtime)
        self.assertIn("const SIZE_MID = 12", runtime)
        self.assertIn("const SIZE_SMALL = 11", runtime)
        # When even the small size does not fit, the slice goes OUTSIDE; the
        # exact decimal must never reappear inside a wedge.
        inline = runtime.split("if (share >= MIN_SHARE)", 1)[1].split("// Small slice", 1)[0]
        self.assertIn("if (size === null) {", inline)
        self.assertIn("outsideCandidates.push({", inline)
        self.assertNotIn("let text = label", inline)
        self.assertNotIn("text: label,", inline)

    def test_outside_label_bounds_use_the_real_font_height(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        # A fixed 6px top margin cut the top half of an 11px label off canvas.
        self.assertIn("const halfLine = Math.ceil(SIZE_SMALL * 0.82)", runtime)
        self.assertIn("const top = Math.max(area ? area.top : 0, 0) + halfLine", runtime)
        self.assertIn("const bottom = Math.min(area ? area.bottom : context.canvas.height, context.canvas.height) - halfLine", runtime)
        self.assertNotIn("area.top + 6", runtime)
        self.assertNotIn("area.bottom - 6", runtime)

    def test_pie_label_contrast_follows_the_slice_color(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        self.assertIn("function isDarkColor(color)", runtime)
        self.assertIn("tone: palette[index]", runtime)
        # White on amber/orange reads as a smudge: pick the pair by luminance.
        self.assertIn("context.strokeStyle = dark ? 'rgba(15, 23, 42, 0.55)' : 'rgba(255, 255, 255, 0.85)'", runtime)
        self.assertIn("context.fillStyle = dark ? '#ffffff' : '#0f172a'", runtime)

    def test_is_dark_color_uses_relative_luminance(self):
        runtime = (ROOT / "dashboard_runtime.js").read_text(encoding="utf-8")
        body = runtime.split("function isDarkColor(color)", 1)[1].split("function registerPercentageLabels", 1)[0]
        self.assertIn("0.2126", body)
        self.assertIn("0.7152", body)
        self.assertIn("0.0722", body)
        self.assertIn("luminance < 0.45", body)
        # Shorthand hex must be expanded before parsing.
        self.assertIn("color.slice(1).split('').map((c) => c + c).join('')", body)

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
