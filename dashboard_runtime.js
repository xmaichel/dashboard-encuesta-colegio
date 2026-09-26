/* CBJML dashboard runtime: snapshot-driven metrics, filters and rendering. */
(function () {
  'use strict';

  const VOZ_QUESTION_FALLBACKS = {
    no_perder: '¿Qué sería especialmente importante NO perder, aunque el Colegio atraviese procesos de cambio?',
    cambiar: 'Si pudiera cambiar o mejorar UNA sola cosa del Colegio, ¿Cuál sería y cómo lo haría?',
    ensenar: 'Complete la frase: «Quisiera que cuando mi hijo(a) termine el Colegio pudiera decir que el Colegio le enseñó principalmente a...',
    recomendar: 'Si recomendara el Colegio, ¿qué sería lo principal que le diría a esa familia que encontrará aquí?'
  };
  const STORAGE_KEY = 'cbjml.dashboard.ui.v1';
  const ACTIONS = ['Mantener', 'Mejorar', 'Transformar', 'No prioritario'];
  const NO_DATA = 'Sin respuesta';
  const SECTIONS = ['Infantil', 'Prejuvenil', 'Juvenil'];
  const COURSES = ['Preescolar', 'Primero', 'Segundo', 'Tercero', 'Cuarto', 'Quinto', 'Sexto', 'Séptimo', 'Octavo', 'Noveno', 'Décimo', 'Undécimo'];
  const COURSE_SECTION = {
    Preescolar: 'Infantil', Primero: 'Infantil', Segundo: 'Infantil', Tercero: 'Infantil',
    Cuarto: 'Prejuvenil', Quinto: 'Prejuvenil', Sexto: 'Prejuvenil', 'Séptimo': 'Prejuvenil',
    Octavo: 'Juvenil', Noveno: 'Juvenil', 'Décimo': 'Juvenil', 'Undécimo': 'Juvenil'
  };
  const PARTICIPATION = ['Siempre', 'Frecuentemente', 'Algunas veces', 'Rara vez', 'Casi nunca', 'Nunca'];
  const ANTIGUEDAD = ['Menos de 2 años', 'Entre 2 y 5 años', 'Entre 6 y 10 años', 'Más de 10 años'];
  const CHANGE = [
    'Se anticipa y responde de manera integral a estos cambios',
    'Responde a la mayoría de los cambios de forma oportuna',
    'Responde a algunos cambios, pero no a otros',
    'Hay esfuerzos aislados, pero insuficientes',
    'El Colegio no está atendiendo estos cambios'
  ];
  const SCALE = ['Excelente', 'Bueno', 'Aceptable', 'Deficiente', 'No conozco lo suficiente'];
  const AGREEMENT = ['Totalmente de acuerdo', 'De acuerdo', 'Ni de acuerdo ni en desacuerdo', 'En desacuerdo', 'Totalmente en desacuerdo'];
  const IDENTITY = [
    'Tradiciones y celebraciones', 'Sentido de comunidad', 'Programa de emprendimiento',
    'Desarrollo de competencias tecnológicas', 'Escuela de argumentación',
    'Relación entre el Colegio y las familias', 'Actividades artísticas, culturales y deportivas',
    'Cercanía y acompañamiento a los estudiantes', 'Programa SER / Programa CARE',
    'Proyección internacional de los estudiantes', 'Excelencia académica', 'Formación en valores'
  ];
  const DIFFERENCES = [
    'Relación con la tecnología y las redes sociales', 'Forma de aprender', 'Necesidades socioemocionales',
    'Atención y concentración', 'Relación con la autoridad y los profesores',
    'Expectativas frente al futuro', 'Relación con la información', 'Relación con sus compañeros'
  ];
  const INITIATIVES = [
    'Esquemas de reconocimiento monetario a estudiantes destacados',
    'Inteligencia artificial responsable, programación y robótica', 'Liderazgo, debate y oratoria',
    'Emprendimiento y proyectos con impacto social', 'Voluntariado y servicio comunitario',
    'Mentoría profesional o de emprendimiento', 'Mentoría entre estudiantes mayores y menores',
    'Orientación vocacional desde grados tempranos',
    'Programa de salud mental y bienestar', 'Arte y deporte de alto rendimiento',
    'Proyectos interdisciplinarios', 'Educación financiera', 'Red de exalumnos y familias'
  ];
  const CONTRIBUTION = [
    'Respondiendo consultas como esta',
    'Voluntariado en eventos, proyectos sociales, culturales o deportivos',
    'Talleres o espacios para padres', 'Charlas o talleres para estudiantes',
    'Mentoría profesional o de emprendimiento', 'Por ahora no me es posible participar'
  ];
  const STOP_WORDS = new Set([
    'cada', 'estudiantes', 'estudiante', 'el', 'la', 'los', 'las', 'de', 'del', 'que', 'en',
    'un', 'una', 'uno', 'unos', 'unas', 'por', 'con', 'para', 'se', 'sus', 'su', 'al', 'y',
    'es', 'son', 'mas', 'más', 'muy', 'como', 'todo', 'todos', 'toda', 'todas', 'lo', 'mi', 'mis',
    'hijo', 'hija', 'hijos', 'hijas', 'no', 'le', 'les', 'ni', 'si', 'hay', 'ha', 'he', 'tienen',
    'tiene', 'tener', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'sino',
    'sobre', 'entre', 'desde', 'hasta', 'sin', 'tras', 'durante', 'mediante', 'segun', 'según',
    'excepto', 'hacia', 'a', 'ante', 'bajo', 'contra', 'o', 'u', 'e', 'pues', 'porque', 'cuando',
    'donde', 'dónde', 'quien', 'quién', 'cual', 'cuál', 'cuyo', 'cuya', 'cuyos', 'cuyas',
    'cuanto', 'cuanta', 'cuantos', 'cuantas', 'familias', 'colegio', 'qué', 'cómo', 'dónde'
  ]);
  const WORD_DISPLAY = {
    critico: 'Crítico', formacion: 'Formación', participacion: 'Participación',
    comunicacion: 'Comunicación', educacion: 'Educación', etica: 'Ética', tecnologia: 'Tecnología',
    'practica': 'Práctica', matematica: 'Matemática', matematicas: 'Matemáticas',
    convivencia: 'Convivencia', ciencia: 'Ciencia', historia: 'Historia', literatura: 'Literatura',
    cercania: 'Cercanía', academica: 'Académica', empatia: 'Empatía', critica: 'Crítica',
    autonomia: 'Autonomía', acompanamiento: 'Acompañamiento', bilinguismo: 'Bilingüismo',
    empatico: 'Empático', etico: 'Ético', ninos: 'Niños', chicos: 'Chicos',
  };

  const state = {
    filters: { seccion: '', antiguedad: '', curso: '' },
    panelCollapsed: false,
    activeTab: 'resumen',
    quoteCategory: 'cambiar',
    quoteSearch: '',
    currentModel: null,
    charts: {},
    ready: false
  };

  const $ = (id) => document.getElementById(id);
  const text = (value) => value == null ? '' : String(value);
  const pct = (count, total) => total ? Math.round((count / total) * 1000) / 10 : 0;
  const validArray = (value) => Array.isArray(value) ? value : [];
  const snapshot = () => (window.CBJML_SNAPSHOT && Array.isArray(window.CBJML_SNAPSHOT.responses)) ? window.CBJML_SNAPSHOT : { responses: [], questions: {} };
  const responses = () => snapshot().responses;
  const questions = () => (snapshot().questions && typeof snapshot().questions === 'object') ? snapshot().questions : {};

  function normalize(value) {
    return text(value).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function normalizeWord(value) {
    const key = normalize(value);
    return STOP_WORDS.has(key) ? '' : key;
  }

  function getQuestion(group, key, fallback) {
    const values = questions()[group] || {};
    return text(values[key] || fallback);
  }

  function optionCount(records, getter, options) {
    const valid = records.filter((record) => getter(record));
    return options.map((label) => {
      const count = valid.filter((record) => getter(record) === label).length;
      return { label, opcion: label, count, pct: pct(count, valid.length) };
    }).filter((item) => item.count > 0);
  }

  // Multiselect answers are ranked by relevance (support count) so KPIs such as
  // "Iniciativa Top" point at the most supported option, not the first canonical
  // label. Ties fall back to alphabetical order for a stable, reproducible view.
  function multiCount(records, getter, options) {
    const valid = records.filter((record) => validArray(getter(record)).length > 0);
    return options.map((label) => {
      const count = valid.filter((record) => validArray(getter(record)).includes(label)).length;
      return { opcion: label, count, pct: pct(count, valid.length) };
    }).filter((item) => item.count > 0)
      .sort((a, b) => b.count - a.count || a.opcion.localeCompare(b.opcion, 'es'));
  }

  function computeMatrix(records) {
    const first = records[0] || {};
    const rawMatrix = first.matriz || {};
    const keys = Object.keys(rawMatrix).length ? Object.keys(rawMatrix) : Array.from({ length: 13 }, (_, i) => `area_${String(i + 1).padStart(2, '0')}`);
    const groups = { Mantener: [], Mejorar: [], Transformar: [], 'No prioritario': [], 'Sin respuesta': [], Empate: [] };
    const byArea = new Map();
    keys.forEach((key) => {
      const rawArea = getQuestion('matriz', key, key);
      const areaKey = normalize(rawArea);
      if (!byArea.has(areaKey)) byArea.set(areaKey, { area: rawArea, key, counts: Object.fromEntries(ACTIONS.map((action) => [action, 0])) });
      const entry = byArea.get(areaKey);
      records.forEach((record) => {
        const value = record.matriz?.[key] || '';
        if (ACTIONS.includes(value)) entry.counts[value] += 1;
      });
    });
    const matrix = [...byArea.values()].map((entry) => {
      const max = Math.max(...Object.values(entry.counts));
      const winners = ACTIONS.filter((action) => entry.counts[action] === max && max > 0);
      const action = winners.length === 1 ? winners[0] : (max > 0 ? 'Empate' : 'Sin respuesta');
      const pcts = Object.fromEntries(ACTIONS.map((option) => [option, pct(entry.counts[option], Object.values(entry.counts).reduce((a, b) => a + b, 0))]));
      const result = { ...entry, action, pcts, Mantener: { count: entry.counts.Mantener, pct: pcts.Mantener }, Mejorar: { count: entry.counts.Mejorar, pct: pcts.Mejorar }, Transformar: { count: entry.counts.Transformar, pct: pcts.Transformar }, 'No prioritario': { count: entry.counts['No prioritario'], pct: pcts['No prioritario'] } };
      groups[action].push(result);
      return result;
    });
    return { matrix, groups };
  }

  function computeModel(filtered) {
    const N = filtered.length;
    const first = filtered[0] || {};
    const aspectKeys = Object.keys(first.aspectos || {}).length ? Object.keys(first.aspectos) : Array.from({ length: 12 }, (_, i) => `aspecto_${String(i + 1).padStart(2, '0')}`);
    const affirmationKeys = Object.keys(first.afirmaciones || {}).length ? Object.keys(first.afirmaciones) : Array.from({ length: 7 }, (_, i) => `afirmacion_${String(i + 1).padStart(2, '0')}`);
    const retoKeys = Object.keys(first.retos || {}).length ? Object.keys(first.retos) : Array.from({ length: 7 }, (_, i) => `reto_${String(i + 1).padStart(2, '0')}`);
    const matrixKeys = Object.keys(first.matriz || {}).length ? Object.keys(first.matriz) : Array.from({ length: 13 }, (_, i) => `area_${String(i + 1).padStart(2, '0')}`);

    const aspects = aspectKeys.map((key) => {
      const values = filtered.map((record) => record.aspectos?.[key] || '').filter(Boolean);
      const item = { key, aspecto: getQuestion('aspectos', key, key) };
      SCALE.forEach((option) => { item[option] = { count: values.filter((value) => value === option).length, pct: pct(values.filter((value) => value === option).length, values.length) }; });
      item.satisfaccion_positiva_pct = Math.round((item.Excelente.pct + item.Bueno.pct) * 10) / 10;
      return item;
    });
    const afirmaciones = affirmationKeys.map((key) => {
      const values = filtered.map((record) => record.afirmaciones?.[key] || '').filter(Boolean);
      const item = { key, afirmacion: getQuestion('afirmaciones', key, key) };
      AGREEMENT.forEach((option) => { item[option] = { count: values.filter((value) => value === option).length, pct: pct(values.filter((value) => value === option).length, values.length) }; });
      item.acuerdo_total_pct = Math.round((item['Totalmente de acuerdo'].pct + item['De acuerdo'].pct) * 10) / 10;
      return item;
    });
    const retos = retoKeys.map((key) => {
      const values = filtered.map((record) => Number(record.retos?.[key])).filter((value) => Number.isInteger(value) && value >= 1 && value <= 7);
      const media = values.length ? Math.round((values.reduce((sum, value) => sum + value, 0) / values.length) * 100) / 100 : 0;
      return { key, reto: getQuestion('retos', key, key), media_urgencia: media, top2_pct: pct(values.filter((value) => value <= 2).length, values.length), valid: values.length };
    }).sort((a, b) => a.media_urgencia - b.media_urgencia);
    const matrixData = computeMatrix(filtered);
    const identity = multiCount(filtered, (record) => record.identidad, IDENTITY);
    const differences = multiCount(filtered, (record) => record.diferencias, DIFFERENCES);
    const initiatives = multiCount(filtered, (record) => record.iniciativas, INITIATIVES);
    const contribution = multiCount(filtered, (record) => record.aporte, CONTRIBUTION);
    const change = optionCount(filtered, (record) => record.respuesta_cambio, CHANGE);
    const participation = optionCount(filtered, (record) => record.participacion, PARTICIPATION);
    const antiguedad = optionCount(filtered, (record) => record.antiguedad, ANTIGUEDAD);
    const words = {};
    filtered.forEach((record) => validArray(record.word_tokens).forEach((value) => {
      const key = normalizeWord(value);
      if (key && key.length > 3) words[key] = (words[key] || 0) + 1;
    }));
    const topWords = Object.entries(words).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 30)
      .map(([word, frequency]) => ({ palabra: WORD_DISPLAY[word] || word.charAt(0).toUpperCase() + word.slice(1), frecuencia: frequency }));
    const urgent = retos.filter((reto) => reto.valid > 0);
    const kpis = {
      bienestar_hijos_pct: afirmaciones[5]?.acuerdo_total_pct || 0,
      valores_familia_pct: afirmaciones[1]?.acuerdo_total_pct || 0,
      comunidad_leonista_pct: afirmaciones[6]?.acuerdo_total_pct || 0,
      participacion_activa_pct: pct(participation.filter((item) => PARTICIPATION.indexOf(item.label) < 2).reduce((sum, item) => sum + item.count, 0), filtered.length),
      disposicion_aporte_pct: pct(filtered.filter((record) => validArray(record.aporte).some((option) => option !== 'Por ahora no me es posible participar')).length, filtered.length),
      iniciativa_top_1_pct: initiatives[0]?.pct || 0,
      iniciativa_top_1: initiatives[0]?.opcion || NO_DATA,
      reto_urgente_1: urgent[0]?.reto || NO_DATA,
      reto_urgente_1_pct: urgent[0]?.top2_pct || 0,
      reto_urgente_2: urgent[1]?.reto || NO_DATA,
      reto_urgente_2_pct: urgent[1]?.top2_pct || 0
    };
    // Live figures for the Insights tab. Every number here is derived from the
    // current `filtered` set, so the tab reacts to the filters like the rest.
    // The previous version of this tab hardcoded percentages from an old 77-row
    // cut while the dashboard was showing 226 rows: that looked live and was not.
    const identityIndex = Math.round(((kpis.bienestar_hijos_pct + kpis.valores_familia_pct + kpis.comunidad_leonista_pct) / 3) * 10) / 10;
    const topInitiative = initiatives[0] || null;
    const techTransform = matrixData.matrix.find((row) => /tecnolog|digital|pantalla|dispositivo/i.test(row.area)) || null;
    const techPct = techTransform ? (techTransform.pcts.Transformar || 0) + (techTransform.pcts.Mejorar || 0) : 0;
    const topTwoInitiatives = initiatives.slice(0, 2);
    const insights = {
      identity_index_pct: identityIndex,
      // Share of families that want to keep the school's core values.
      adn_pct: kpis.valores_familia_pct,
      // Share ranking the leading risk among their two most urgent challenges.
      alerta_pct: kpis.reto_urgente_1_pct,
      alerta_label: kpis.reto_urgente_1,
      // Most-supported initiative plus the runner-up, both live.
      demanda_pct: topInitiative ? topInitiative.pct : 0,
      demanda_label: topInitiative ? topInitiative.opcion : NO_DATA,
      demanda_2_pct: topTwoInitiatives[1] ? topTwoInitiatives[1].pct : 0,
      demanda_2_label: topTwoInitiatives[1] ? topTwoInitiatives[1].opcion : NO_DATA,
      // Share asking to transform or improve technology use.
      paradoja_tec_pct: techPct,
      paradoja_tec_label: techTransform ? techTransform.area : NO_DATA,
      // Reto ranked #2 by urgency.
      paradoja_pantallas_media: urgent[1] ? urgent[1].media_urgencia : 0,
      paradoja_pantallas_label: kpis.reto_urgente_2,
      // Willingness to contribute and the two most chosen ways.
      potencial_pct: kpis.disposicion_aporte_pct,
      potencial_1: contribution[0] || null,
      potencial_2: contribution[1] || null,
      potencial_3: contribution[2] || null,
      N,
      has_data: N > 0
    };
    const quotes = filtered.filter((record) => Object.values(record.quotes || {}).some(Boolean)).map((record) => ({
      id: record.id, cambiar: record.quotes?.cambiar || '', no_perder: record.quotes?.no_perder || '',
      ensenar: record.quotes?.ensenar || '', recomendar: record.quotes?.recomendar || '',
      curso: text(record.cursos_texto), nivel: validArray(record.secciones).join(', '), antiguedad: text(record.antiguedad)
    }));
    return {
      N, aspects, afirmaciones, retos, MATRIZ: matrixData.matrix, matrix_groups: matrixData.groups,
      IDENTITY: identity, DIFERENCIAS: differences, INICIATIVAS: initiatives, APORTE: contribution,
      RESP_CAMBIOS: change, DEMO: { antiguedad, participacion: participation, secciones: SECTIONS.map((section) => ({ label: section, count: filtered.filter((record) => validArray(record.secciones).includes(section)).length, pct: pct(filtered.filter((record) => validArray(record.secciones).includes(section)).length, N) })) },
      TOP_WORDS: topWords, QUOTES: quotes, KPIS: kpis, INSIGHTS: insights
    };
  }

  function getFilteredResponses() {
    const f = state.filters;
    return responses().filter((record) => {
      if (f.seccion && !validArray(record.secciones).includes(f.seccion)) return false;
      if (f.antiguedad && text(record.antiguedad) !== f.antiguedad) return false;
      if (f.curso && !validArray(record.cursos).includes(f.curso)) return false;
      return true;
    });
  }

  function setText(id, value) { const node = $(id); if (node) node.textContent = text(value); }
  function setPct(id, value) { setText(id, `${Number(value || 0).toFixed(1).replace(/\.0$/, '')}%`); }
  function escapeHtml(value) { return text(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

  function updateStaticText(model) {
    setText('sampleTotal', `${model.N} familias`);
    setText('processedRecords', model.N);
    setText('insightsSampleSize', model.N);
    setText('roadmapSampleSize', model.N);
    renderInsights(model.INSIGHTS);
    setPct('kpiBienestar', model.KPIS.bienestar_hijos_pct);
    setPct('kpiValores', model.KPIS.valores_familia_pct);
    setPct('kpiPertenencia', model.KPIS.comunidad_leonista_pct);
    setPct('kpiParticipacion', model.KPIS.participacion_activa_pct);
    setPct('kpiDisposicion', model.KPIS.disposicion_aporte_pct);
    setPct('kpiIniciativa', model.KPIS.iniciativa_top_1_pct);
    setText('kpiIniciativaLabel', model.KPIS.iniciativa_top_1);
    setText('narrativeBienestar', `${model.KPIS.bienestar_hijos_pct}% de las familias afirma que su hijo se siente feliz, seguro y acompañado. La comunidad alcanza ${model.KPIS.comunidad_leonista_pct}%.`);
    setText('narrativeValores', `La formación bilingüe (${model.aspects[0]?.satisfaccion_positiva_pct || 0}%) y el pensamiento crítico (${model.aspects[1]?.satisfaccion_positiva_pct || 0}%) son los aspectos mejor calificados.`);
    setText('narrativeRetos', `${model.KPIS.reto_urgente_1} (${model.KPIS.reto_urgente_1_pct}%) y ${model.KPIS.reto_urgente_2} (${model.KPIS.reto_urgente_2_pct}%) lideran la urgencia generacional.`);
    setText('narrativeAccion', `El ${model.KPIS.iniciativa_top_1_pct}% prioriza ${model.KPIS.iniciativa_top_1}; la disposición a aportar es de ${model.KPIS.disposicion_aporte_pct}%.`);
    renderRespCambioLegend(model.RESP_CAMBIOS);
  }

  // Renders the live figures of the Insights tab. Every value comes from
  // model.INSIGHTS, which is recomputed from the filtered responses, so the
  // tab always describes the same slice of data as the other five tabs.
  function renderInsights(insights) {
    if (!insights) return;
    const filtered = state.filters && Object.values(state.filters).some(Boolean);
    setPct('insightsIndex', insights.identity_index_pct);
    const scope = $('insightsScope');
    if (scope) {
      scope.textContent = filtered
        ? `Vista filtrada · ${insights.N} respuestas`
        : `Corte completo · ${insights.N} respuestas`;
    }
    setPct('ejeAdnPct', insights.adn_pct);
    setPct('ejeAlertaPct', insights.alerta_pct);
    setText('ejeAlertaTitle', insights.alerta_label);
    setPct('ejeDemandaPct', insights.demanda_pct);
    setText('ejeDemandaTitle', insights.demanda_label);
    setPct('ejePotencialPct', insights.potencial_pct);
    setText('paradoja1Reto', insights.alerta_label);
    setText('paradoja2Area', insights.paradoja_tec_label);
    setPct('paradoja2Pct', insights.paradoja_tec_pct);
    setText('paradoja2Reto', insights.paradoja_pantallas_label);
    setText('paradoja2Media', insights.paradoja_pantallas_media);
    setText('paradoja3Top', insights.demanda_label);
    setPct('paradoja3Pct', insights.demanda_pct);
    setText('paradoja3Second', insights.demanda_2_label);
    setPct('paradoja3Pct2', insights.demanda_2_pct);
    setText('paradoja4Top', insights.potencial_1?.opcion || NO_DATA);
    setText('paradoja4Second', insights.potencial_2?.opcion || NO_DATA);
    setText('paradoja4Third', insights.potencial_3?.opcion || NO_DATA);
    setText('roadmapStamp', insights.has_data ? `Actualizado con el ETL · ${insights.N} respuestas` : 'Sin datos');
  }

  // Chart.js truncated this legend: the option labels are long sentences and the
  // canvas is only ~250px wide, so it clipped the text and dropped the colour
  // swatches. A real HTML list gives every option a full-width row with its
  // swatch, and it never clips.
  const RESP_CAMBIO_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ef4444'];

  function renderRespCambioLegend(items) {
    const list = $('respCambioLegend');
    if (!list) return;
    list.textContent = '';
    items.forEach((item, index) => {
      const color = RESP_CAMBIO_COLORS[index % RESP_CAMBIO_COLORS.length];
      const row = document.createElement('li');
      row.className = 'flex items-start gap-2';
      const swatch = document.createElement('span');
      swatch.className = 'inline-block w-3 h-3 rounded-sm shrink-0 mt-0.5';
      swatch.style.backgroundColor = color;
      swatch.setAttribute('aria-hidden', 'true');
      const text = document.createElement('span');
      text.className = 'flex-1 min-w-0';
      text.textContent = `${item.label}: ${item.pct}%`;
      row.appendChild(swatch);
      row.appendChild(text);
      list.appendChild(row);
    });
  }

  function chartConfig(type, data, options) { return { type, data, options: { responsive: true, maintainAspectRatio: false, ...options } }; }

  // One source of truth for the horizontal-bar category labels. The Matriz
  // chart was the only one declaring 10px, so every other bar chart silently
  // inherited Chart.js's 12px default and its long option labels overflowed
  // the card. This helper is the reference size, not a new constant.
  const AXIS_LABEL_SIZE = 10;
  const AXIS_LABEL_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif';
  // Share of the canvas the longest label may take before it is elided. Below
  // 0.5 the bars are starved of room; above it the labels eat the plot.
  const AXIS_LABEL_MAX_RATIO = 0.46;
  // A label needs at least 6 characters on screen or it becomes "In…".
  const AXIS_LABEL_MIN_CHARS = 6;
  // Breathing room between the label and the axis line.
  const PADDING = 8;

  function smallAxisTicks() {
    return {
      font: { size: AXIS_LABEL_SIZE, family: AXIS_LABEL_FONT },
      // Elide instead of overflowing: the full text stays in the tooltip.
      autoSkip: false,
      ...elideCategoryTicks()
    };
  }

  // Horizontal bars whose category labels are long sentences need a wider
  // gutter than Chart.js reserves by default. Two details make this work:
  //   - `afterFit` IS the right hook (not beforeLayout): it runs after
  //     Chart.js has measured the labels, so raising axis.width there makes
  //     the plot shrink accordingly. Setting it in beforeLayout had no effect
  //     because Chart.js recomputed the width right afterwards.
  //   - the floor matters: only grow the gutter, never shrink it, otherwise a
  //     long label made the bars narrower on one redraw and wider on the next.
  function wideCategoryAxis() {
    return {
      afterFit(axis) {
        const canvas = axis.chart && axis.chart.canvas;
        if (!canvas) return;
        const ctx = axis.ctx || (canvas.getContext && canvas.getContext('2d'));
        if (!ctx) return;
        ctx.save();
        ctx.font = `${AXIS_LABEL_SIZE}px ${AXIS_LABEL_FONT}`;
        const longest = (axis.ticks || []).reduce(
          (max, tick) => Math.max(max, ctx.measureText(String(tick.label)).width), 0
        );
        ctx.restore();
        if (!longest) return;
        // Cap the gutter: an unbounded one would eat the whole plot, leaving
        // no room for the bars themselves.
        const target = Math.min(longest + PADDING, canvas.width * AXIS_LABEL_MAX_RATIO);
        if (target > (axis.width || 0)) axis.width = target;
      }
    };
  }

  // Elides a category label that would not fit the gutter. This has to run
  // inside `ticks.callback`, not by mutating tick.label: Chart.js re-reads the
  // raw labels on every redraw and overwrites anything written before it.
  function elideCategoryTicks() {
    return {
      callback(value, index) {
        const chart = this.chart;
        const axis = this;
        const full = String(chart.data.labels[index] ?? value ?? '');
        const ctx = chart.ctx;
        if (!full || !ctx || !axis.width) return full;
        const room = axis.width - PADDING;
        ctx.save();
        ctx.font = `${AXIS_LABEL_SIZE}px ${AXIS_LABEL_FONT}`;
        if (ctx.measureText(full).width <= room) {
          ctx.restore();
          return full;
        }
        // Binary search for the longest prefix that still fits.
        let low = AXIS_LABEL_MIN_CHARS;
        let high = full.length;
        while (low < high) {
          const mid = Math.ceil((low + high) / 2);
          if (ctx.measureText(`${full.slice(0, mid)}…`).width <= room) low = mid;
          else high = mid - 1;
        }
        ctx.restore();
        return `${full.slice(0, low)}…`;
      }
    };
  }

  // Percentages are shown in two places on purpose: inside each pie/doughnut
  // slice when it is wide enough to read, and outside the pie with a leader
  // line when it is too small. The legend always carries every percentage.
  // MIN_SHARE is the inline threshold; OUTSIDE_* tune the leader-line labels.
  // INLINE_MIN_GAP keeps two inline labels from touching when both slices are
  // just above the threshold but sit close to each other.
  const MIN_SHARE = 4;
  const INLINE_MIN_GAP = 11;
  const OUTSIDE_REACH = 14;
  const OUTSIDE_MIN_GAP = 13;
  // Cap the leader-line labels: past this many tiny slices the lines cross so
  // much they read worse than the legend, so the rest stay legend-only.
  const MAX_OUTSIDE = 6;
  // Inline label sizes. The largest one that provably fits inside the arc is
  // used, so a big slice reads at a glance without bleeding into its neighbour.
  const SIZE_LARGE = 13;
  const SIZE_MID = 12;
  const SIZE_SMALL = 11;
  // Breathing room required between a label edge and the arc boundary.
  const INLINE_PAD = 3;
  const LABEL_FONT = 'Inter, system-ui, sans-serif';
  let percentageLabelsRegistered = false;

  function shareOf(counts) {
    const total = counts.reduce((sum, value) => sum + (Number(value) || 0), 0);
    return counts.map((value) => (total ? Math.round(((Number(value) || 0) / total) * 1000) / 10 : 0));
  }

  // Keeps `data.labels` clean for tooltips while the legend text carries "%".
  // Chart.js calls this with `{ chart }` in v4+ and with the chart itself in v3,
  // so both shapes are accepted to avoid breaking the legend.
  function percentLegend() {
    return {
      generateLabels: (context) => {
        const chart = context && context.data && context.datasets ? context : (context && context.chart) || context;
        const datasets = (chart && chart.data && chart.data.datasets) || [];
        const dataset = datasets[0] || {};
        const data = Array.isArray(dataset.data) ? dataset.data : [];
        const shares = shareOf(data);
        const colors = Array.isArray(dataset.backgroundColor) ? dataset.backgroundColor : [];
        const labels = (chart && chart.data && chart.data.labels) || [];
        return labels.map((label, index) => ({
          text: `${label} (${shares[index] ?? 0}%)`,
          fillStyle: colors[index] || '#94a3b8',
          strokeStyle: colors[index] || '#94a3b8',
          lineWidth: 0,
          hidden: false,
          fontColor: '#475569',
          index
        }));
      }
    };
  }

  // Relative luminance check, so a label picks black or white to match the
  // slice it sits on. Without it, white text on the amber/orange slices reads
  // as a smudge no matter how thick the halo is.
  function isDarkColor(color) {
    if (typeof color !== 'string' || color[0] !== '#') return true;
    const hex = color.length === 4
      ? color.slice(1).split('').map((c) => c + c).join('')
      : color.slice(1, 7);
    if (hex.length < 6) return true;
    const channels = [0, 2, 4].map((i) => {
      const channel = parseInt(hex.slice(i, i + 2), 16) / 255;
      return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    const luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    return luminance < 0.45;
  }

  // Rounded inside: a label that reads "8.0%" on a slice of 8% is noise. The
  // decimal is kept in the legend and tooltip, where there is room. Declared
  // here, not inside the draw hook: the hook is a closure and a const declared
  // after its use would throw on the very first paint.
  const roundText = (share) => `${Math.round(share)}%`;

  // Eliding axis labels has to happen after the axis has been laid out and
  // before anything is painted, on every draw (resize, filter change, hover).
  function registerPercentageLabels() {
    if (percentageLabelsRegistered || typeof Chart === 'undefined') return;
    Chart.register({
      id: 'cbjmlPercentageLabels',
      afterDatasetsDraw(chart) {
        const type = chart.config.type;
        if (type !== 'pie' && type !== 'doughnut') return;
        const dataset = (chart.data.datasets || [])[0];
        if (!dataset || !Array.isArray(dataset.data)) return;
        const shares = shareOf(dataset.data);
        const context = chart.ctx;
        const arcs = chart.getDatasetMeta(0).data || [];
        const palette = Array.isArray(dataset.backgroundColor) ? dataset.backgroundColor : [];
        const area = chart.chartArea;
        // Out-of-arc labels need horizontal room, otherwise they get clipped.
        const roomy = !!area && area.right - area.left > 40;
        const labels = [];
        const outsideCandidates = [];
        arcs.forEach((arc, index) => {
          const value = Number(dataset.data[index]) || 0;
          if (value <= 0) return;
          const share = shares[index] ?? 0;
          const label = `${share}%`;
          if (share >= MIN_SHARE) {
            const position = arc.tooltipPosition();
            if (!position || !Number.isFinite(position.x) || !Number.isFinite(position.y)) return;
            // Decide by the space the arc actually offers, not by the share
            // alone. Two geometric limits apply to a horizontal label of width
            // W centred at distance r inside a wedge of half-angle phi:
            //   tangential: the corner must stay inside the wedge, W <= r*tan(phi)
            //   radial:      the corner must stay inside the disc, W <= sqrt(R^2-r^2)
            // Both matter. Using only one of them was what let a 69.6% wedge
            // (250 degrees!) be treated as if it had no room at all.
            const R = Number(arc.outerRadius);
            const r = Math.hypot(position.x - arc.x, position.y - arc.y) || Math.max(18, R * 0.58);
            const halfAngle = Math.abs(Number(arc.endAngle) - Number(arc.startAngle)) / 2;
            // A wedge wider than a half-turn has no tangential limit.
            const tangential = halfAngle >= (Math.PI / 2) - 0.05
              ? Infinity
              : r * Math.tan(halfAngle);
            const radial = Math.sqrt(Math.max(0, (R * R) - (r * r)));
            const usable = Math.max(14, Math.min(tangential, radial));
            // Only the rounded form is ever drawn inside: "69.6%" inside a
            // wedge is both noisier and wider than "70%". If even the small
            // size cannot fit, the slice goes outside with a leader line
            // rather than shrinking the text or spilling a decimal back in.
            const rounded = roundText(share);
            let size = null;
            for (const candidate of [SIZE_LARGE, SIZE_MID, SIZE_SMALL]) {
              context.font = `600 ${candidate}px ${LABEL_FONT}`;
              if (context.measureText(rounded).width + INLINE_PAD * 2 <= usable) {
                size = candidate;
                break;
              }
            }
            if (size === null) {
              if (!roomy || arc.fullCircles) return;
              const start = Number(arc.startAngle);
              const end = Number(arc.endAngle);
              const radius = R;
              if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(radius) || radius <= 0) return;
              const mid = (start + end) / 2;
              outsideCandidates.push({
                share, label: rounded,
                x0: arc.x + Math.cos(mid) * radius,
                y0: arc.y + Math.sin(mid) * radius,
                right: Math.cos(mid) >= 0, mid, radius, cx: arc.x, cy: arc.y
              });
              return;
            }
            context.font = `600 ${size}px ${LABEL_FONT}`;
            labels.push({
              label: rounded, x: position.x, y: position.y,
              w: context.measureText(rounded).width, size,
              tone: palette[index], outside: false
            });
            return;
          }
          // Small slice: percentage goes outside the pie with a leader line.
          if (!roomy || arc.fullCircles) return;
          const start = Number(arc.startAngle);
          const end = Number(arc.endAngle);
          const radius = Number(arc.outerRadius);
          if (!Number.isFinite(start) || !Number.isFinite(end) || !Number.isFinite(radius) || radius <= 0) return;
          const mid = (start + end) / 2;
          const x0 = arc.x + Math.cos(mid) * radius;
          const y0 = arc.y + Math.sin(mid) * radius;
          const right = Math.cos(mid) >= 0;
          outsideCandidates.push({ share, label, x0, y0, right, mid, radius, cx: arc.x, cy: arc.y });
        });
        context.save();
        context.textBaseline = 'middle';
        // Give the leader lines to the biggest tiny slices; the rest are
        // legend-only so the fan of lines never becomes an unreadable web.
        outsideCandidates.sort((a, b) => b.share - a.share || a.mid - b.mid);
        outsideCandidates.slice(0, MAX_OUTSIDE).forEach((item) => {
          const { label, x0, y0, right, mid, radius: outRadius, cx, cy } = item;
          const elbowX = right
            ? Math.max(cx + outRadius + 8, cx + Math.cos(mid) * (outRadius + OUTSIDE_REACH))
            : Math.min(cx - outRadius - 8, cx + Math.cos(mid) * (outRadius + OUTSIDE_REACH));
          const elbowY = cy + Math.sin(mid) * (outRadius + OUTSIDE_REACH);
          const tailX = elbowX + (right ? OUTSIDE_REACH / 2 : -OUTSIDE_REACH / 2);
          labels.push({
            label, x0, y0, elbowX, elbowY, tailX,
            x: tailX + (right ? 4 : -4),
            y: elbowY,
            right,
            outside: true
          });
        });
        if (!labels.length) {
          context.restore();
          return;
        }
        // Two inline labels can still touch when both slices are just above the
        // threshold but neighbouring. Iterate until nothing overlaps: one pass is
        // not enough when three or more labels crowd the same arc of the pie.
        const inline = labels.filter((item) => !item.outside);
        for (let pass = 0; pass < 12 && inline.length > 1; pass += 1) {
          let moved = false;
          for (let i = 0; i < inline.length; i += 1) {
            for (let j = i + 1; j < inline.length; j += 1) {
              const a = inline[i];
              const b = inline[j];
              const ha = a.w / 2;
              const hb = b.w / 2;
              const overlapX = Math.min(a.x + ha, b.x + hb) - Math.max(a.x - ha, b.x - hb);
              const overlapY = Math.min(a.y, b.y) + (a.size + b.size) / 4 - (Math.max(a.y, b.y) - (a.size + b.size) / 4);
              if (overlapX <= 0 || overlapY <= 0) continue;
              moved = true;
              const midX = (a.x + b.x) / 2;
              const midY = (a.y + b.y) / 2;
              const dirX = a.x - midX;
              const dirY = a.y - midY;
              const len = Math.hypot(dirX, dirY) || 1;
              const push = (overlapY + INLINE_MIN_GAP) / 2;
              a.x += (dirX / len) * push;
              a.y += (dirY / len) * push;
              b.x -= (dirX / len) * push;
              b.y -= (dirY / len) * push;
            }
          }
          if (!moved) break;
        }
        // Lay the outside labels in two columns (right/left of the pie) and
        // spread each one so small slices never overlap each other.
        const outside = labels.filter((item) => item.outside);
        const side = (item) => (item.right ? 1 : -1);
        const groups = { '-1': [], 1: [] };
        outside.forEach((item) => { groups[side(item)].push(item); });
        // Vertical bounds use the real font height, not a fixed 6px margin: an
        // 11px label needs ~9px above the baseline, so y=6 put half the text
        // above the canvas and it was silently cut off.
        context.font = `600 ${SIZE_SMALL}px ${LABEL_FONT}`;
        const halfLine = Math.ceil(SIZE_SMALL * 0.82);
        const top = Math.max(area ? area.top : 0, 0) + halfLine;
        const bottom = Math.min(area ? area.bottom : context.canvas.height, context.canvas.height) - halfLine;
        [-1, 1].forEach((key) => {
          const group = groups[key];
          if (group.length < 1) return;
          group.sort((a, b) => a.y - b.y || a.x - b.x);
          // Spread the column so neighbouring labels never touch.
          for (let i = 1; i < group.length; i += 1) {
            const gap = group[i].y - group[i - 1].y;
            if (gap < OUTSIDE_MIN_GAP) group[i].y = group[i - 1].y + OUTSIDE_MIN_GAP;
          }
          // Fit the column inside [top, bottom]. When even the compacted
          // column is taller than the space, centre it instead of clamping
          // every item to the same edge (which would re-introduce overlaps).
          const span = group[group.length - 1].y - group[0].y;
          const room = Math.max(0, bottom - top);
          if (span > room && span > 0) {
            const shift = (room - span) / 2;
            group.forEach((item) => { item.y += shift; });
          } else {
            const overflow = group[group.length - 1].y - bottom;
            if (overflow > 0) group.forEach((item) => { item.y -= overflow; });
          }
          // A single label (or any label still above the top edge) must be
          // pushed down: this ran only for multi-label columns, so a lone
          // label near the top was drawn half off-canvas.
          const underflow = top - group[0].y;
          if (underflow > 0) group.forEach((item) => { item.y += underflow; });
          group.forEach((item) => { item.elbowY = item.y; });
        });
        // Horizontal clamp: no outside label may leave the canvas bounds. Use
        // the canvas, not chartArea: a bottom legend pushes the area inside the
        // canvas, but the area can also start left of x=0 on narrow charts.
        if (area) {
          const boundLeft = Math.max(0, area.left);
          const boundRight = Math.min(context.canvas.width, area.right);
          outside.forEach((item) => {
            context.font = `600 ${SIZE_SMALL}px ${LABEL_FONT}`;
            const width = context.measureText(item.label).width;
            if (item.right) {
              const limit = boundRight - width;
              if (item.x > limit) {
                const shift = item.x - limit;
                item.x -= shift;
                item.tailX -= shift;
                item.elbowX = Math.min(item.elbowX, item.tailX);
              }
            } else {
              const limit = boundLeft + width;
              if (item.x < limit) {
                const shift = limit - item.x;
                item.x += shift;
                item.tailX += shift;
                item.elbowX = Math.max(item.elbowX, item.tailX);
              }
            }
          });
        }
        labels.forEach((item) => {
          if (!item.outside) {
            context.textAlign = 'center';
            context.font = `600 ${item.size}px ${LABEL_FONT}`;
            // Contrast follows the slice: white on a mid tone needs a dark halo,
            // but on a light tone the halo alone leaves a muddy smudge.
            const tone = item.tone || '#334155';
            const dark = isDarkColor(tone);
            context.lineWidth = 3;
            context.strokeStyle = dark ? 'rgba(15, 23, 42, 0.55)' : 'rgba(255, 255, 255, 0.85)';
            context.strokeText(item.label, item.x, item.y);
            context.fillStyle = dark ? '#ffffff' : '#0f172a';
            context.fillText(item.label, item.x, item.y);
            return;
          }
          // Skip any label that still does not fit: the legend already carries
          // its percentage, so a clipped number is worse than no number here.
          context.font = `600 ${SIZE_SMALL}px ${LABEL_FONT}`;
          const width = context.measureText(item.label).width;
          const left = item.right ? item.x : item.x - width;
          // Clamp against the canvas, not just the chart area: the chart area
          // can start outside the canvas (a legend narrows it past the left
          // edge), and an outside label placed at x<0 was silently cut off.
          const limitLeft = Math.max(0, area ? area.left : 0);
          const limitRight = Math.min(context.canvas.width, area ? area.right : context.canvas.width);
          if (left < limitLeft - 0.5 || left + width > limitRight + 0.5) return;
          if (item.y < 0 || item.y > (area ? area.bottom : item.y)) return;
          context.strokeStyle = 'rgba(100, 116, 139, 0.85)';
          context.lineWidth = 1;
          context.beginPath();
          context.moveTo(item.x0, item.y0);
          context.lineTo(item.elbowX, item.elbowY);
          context.lineTo(item.tailX, item.y);
          context.stroke();
          context.beginPath();
          context.arc(item.x0, item.y0, 2, 0, Math.PI * 2);
          context.fillStyle = 'rgba(100, 116, 139, 0.9)';
          context.fill();
          context.textAlign = item.right ? 'left' : 'right';
          context.fillStyle = '#334155';
          context.fillText(item.label, item.x, item.y);
        });
        context.restore();
      }
    });
    percentageLabelsRegistered = true;
  }

  function upsertChart(id, config) {
    const canvas = $(id);
    if (!canvas || typeof Chart === 'undefined') return;
    if (!state.charts[id]) { state.charts[id] = new Chart(canvas.getContext('2d'), config); return; }
    const chart = state.charts[id];
    chart.data.labels = config.data.labels.slice();
    config.data.datasets.forEach((dataset, index) => {
      if (!chart.data.datasets[index]) chart.data.datasets[index] = { ...dataset };
      chart.data.datasets[index].data = dataset.data.slice();
      if (dataset.backgroundColor) chart.data.datasets[index].backgroundColor = dataset.backgroundColor;
    });
    chart.update();
  }

  function renderCharts(model) {
    if (typeof Chart === 'undefined') return;
    registerPercentageLabels();
    upsertChart('chartRespCambios', chartConfig('doughnut', { labels: model.RESP_CAMBIOS.map((item) => item.label), datasets: [{ data: model.RESP_CAMBIOS.map((item) => item.count), backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ef4444'] }] }, { plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => { const total = ctx.dataset.data.reduce((a, b) => a + b, 0); return `${ctx.label}: ${ctx.parsed} (${total ? Math.round(ctx.parsed / total * 1000) / 10 : 0}%)`; } } } } }));
    upsertChart('chartCursos', chartConfig('pie', { labels: model.DEMO.secciones.map((item) => item.label), datasets: [{ data: model.DEMO.secciones.map((item) => item.count), backgroundColor: ['#059669', '#d97706', '#dc2626'] }] }, { plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, ...percentLegend() } }, tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed} familias` } } } }));
    const antiguedadLabels = ANTIGUEDAD;
    upsertChart('chartAntiguedad', chartConfig('bar', { labels: antiguedadLabels, datasets: [{ label: 'Familias', data: antiguedadLabels.map((label) => model.DEMO.antiguedad.find((item) => item.label === label)?.count || 0), backgroundColor: '#0284c7' }] }, { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }));
    upsertChart('chartParticipacion', chartConfig('doughnut', { labels: PARTICIPATION, datasets: [{ data: PARTICIPATION.map((label) => model.DEMO.participacion.find((item) => item.label === label)?.count || 0), backgroundColor: ['#059669', '#10b981', '#f59e0b', '#f97316', '#ef4444', '#8b5cf6'] }] }, { plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, ...percentLegend() } } } }));
    const aspects = [...model.aspects].sort((a, b) => b.satisfaccion_positiva_pct - a.satisfaccion_positiva_pct);
    upsertChart('chartAspectos', chartConfig('bar', { labels: aspects.map((item) => item.aspecto), datasets: [
      { label: 'Excelente (%)', data: aspects.map((item) => item.Excelente.pct), backgroundColor: '#059669' },
      { label: 'Bueno (%)', data: aspects.map((item) => item.Bueno.pct), backgroundColor: '#3b82f6' },
      { label: 'Aceptable (%)', data: aspects.map((item) => item.Aceptable.pct), backgroundColor: '#fbbf24' },
      { label: 'Deficiente (%)', data: aspects.map((item) => item[`Deficiente`].pct), backgroundColor: '#ef4444' }
    ] }, { indexAxis: 'y', scales: { x: { stacked: true, max: 100 }, y: { stacked: true, afterFit: wideCategoryAxis(), ticks: smallAxisTicks() } } }));
    const matrix = model.MATRIZ;
    upsertChart('chartMatriz', chartConfig('bar', { labels: matrix.map((item) => item.area), datasets: [
      { label: 'Transformar (%)', data: matrix.map((item) => item.Transformar.pct), backgroundColor: '#f59e0b' },
      { label: 'Mejorar (%)', data: matrix.map((item) => item.Mejorar.pct), backgroundColor: '#3b82f6' },
      { label: 'Mantener (%)', data: matrix.map((item) => item.Mantener.pct), backgroundColor: '#10b981' },
      { label: 'No Prioritario (%)', data: matrix.map((item) => item['No prioritario'].pct), backgroundColor: '#cbd5e1' }
    ] }, { indexAxis: 'y', scales: { x: { stacked: true, max: 100 }, y: { stacked: true, afterFit: wideCategoryAxis(), ticks: smallAxisTicks() } } }));
    const CATEGORY_AXIS = { afterFit: wideCategoryAxis(), ticks: smallAxisTicks() };
    const CATEGORY_TOOLTIP = {
      callbacks: {
        // An elided axis label must still be readable on demand, so the title
        // shows the full text rather than the shortened one.
        title: (items) => {
          const first = items[0];
          const label = first && first.chart.data.labels[first.dataIndex];
          return label === undefined ? undefined : String(label);
        }
      }
    };
    upsertChart('chartRetos', chartConfig('bar', { labels: model.retos.map((item) => item.reto), datasets: [{ label: 'Media de urgencia (1 = más urgente)', data: model.retos.map((item) => item.media_urgencia), backgroundColor: '#dc2626' }] }, { indexAxis: 'y', scales: { x: { min: 1, max: 7 }, y: CATEGORY_AXIS }, plugins: { tooltip: { callbacks: { ...CATEGORY_TOOLTIP.callbacks, afterBody: (items) => { const item = model.retos[items[0]?.dataIndex]; return item ? `% en prioridad 1 y 2: ${item.top2_pct}%` : ''; } } } } }));
    upsertChart('chartDiferencias', chartConfig('bar', { labels: model.DIFERENCIAS.map((item) => item.opcion), datasets: [{ label: '% Familias', data: model.DIFERENCIAS.map((item) => item.pct), backgroundColor: '#4f46e5' }] }, { indexAxis: 'y', scales: { y: CATEGORY_AXIS }, plugins: { legend: { display: false }, tooltip: CATEGORY_TOOLTIP } }));
    upsertChart('chartIniciativas', chartConfig('bar', { labels: model.INICIATIVAS.map((item) => item.opcion), datasets: [{ label: '% de Respaldos', data: model.INICIATIVAS.map((item) => item.pct), backgroundColor: '#0284c7' }] }, { indexAxis: 'y', scales: { y: CATEGORY_AXIS }, plugins: { legend: { display: false }, tooltip: CATEGORY_TOOLTIP } }));
    upsertChart('chartIdentidad', chartConfig('bar', { labels: model.IDENTITY.map((item) => item.opcion), datasets: [{ label: '% Menciones', data: model.IDENTITY.map((item) => item.pct), backgroundColor: '#0d9488' }] }, { indexAxis: 'y', scales: { y: CATEGORY_AXIS }, plugins: { legend: { display: false }, tooltip: CATEGORY_TOOLTIP } }));
    upsertChart('chartAporte', chartConfig('bar', { labels: model.APORTE.map((item) => item.opcion), datasets: [{ label: '% dispuestas a aportar', data: model.APORTE.map((item) => item.pct), backgroundColor: '#d97706' }] }, { indexAxis: 'y', scales: { y: CATEGORY_AXIS }, plugins: { legend: { display: false }, tooltip: CATEGORY_TOOLTIP } }));
  }

  function renderAspectTable(model) {
    const body = $('tableAspectosBody');
    if (!body) return;
    body.replaceChildren();
    [...model.aspects].sort((a, b) => b.satisfaccion_positiva_pct - a.satisfaccion_positiva_pct).forEach((item) => {
      const row = document.createElement('tr');
      const badge = item.satisfaccion_positiva_pct >= 90 ? '<span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">Consolidado</span>' : item.satisfaccion_positiva_pct >= 80 ? '<span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold text-[10px]">Bueno</span>' : '<span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">Atención</span>';
      row.innerHTML = `<td class="py-3 px-4 font-medium text-slate-900">${escapeHtml(item.aspecto)}</td><td class="py-3 px-3 text-center">${item.Excelente.pct}% (${item.Excelente.count})</td><td class="py-3 px-3 text-center">${item.Bueno.pct}% (${item.Bueno.count})</td><td class="py-3 px-3 text-center text-amber-700">${item.Aceptable.pct}% (${item.Aceptable.count})</td><td class="py-3 px-3 text-center text-rose-700">${item[`Deficiente`].pct}% (${item[`Deficiente`].count})</td><td class="py-3 px-3 text-center text-slate-400">${item['No conozco lo suficiente'].pct}%</td><td class="py-3 px-4 text-center font-bold text-blue-900">${item.satisfaccion_positiva_pct}%</td><td class="py-3 px-4 text-center">${badge}</td>`;
      body.appendChild(row);
    });
  }

  function renderMatrixGroups(model) {
    const container = $('matrixGroups');
    if (!container) return;
    container.replaceChildren();
    const config = [
      ['Mantener', 'Frentes para consolidar (Mantener)', 'emerald'],
      ['Mejorar', 'Frentes de fortalecimiento (Mejorar)', 'blue'],
      ['Transformar', 'Frentes de innovación (Transformar)', 'amber'],
      ['No prioritario', 'Áreas no prioritarias', 'slate'],
      ['Sin respuesta', 'Áreas sin respuesta', 'slate'],
      ['Empate', 'Empates de respuesta', 'rose']
    ];
    config.forEach(([key, title, color]) => {
      const entries = model.matrix_groups[key] || [];
      const card = document.createElement('div');
      card.className = 'bg-slate-50 border border-slate-200 p-5 rounded-xl';
      const heading = document.createElement('div');
      heading.className = 'flex items-center gap-2 mb-2';
      const badge = document.createElement('span');
      badge.className = 'p-1.5 bg-slate-600 text-white rounded-md text-xs font-bold';
      badge.textContent = key === 'Transformar' ? 'T' : key === 'Mejorar' ? 'Mej' : key === 'Mantener' ? 'M' : key === 'Empate' ? '=' : '—';
      const h3 = document.createElement('h3');
      h3.className = 'font-bold text-slate-900 text-sm';
      h3.textContent = title;
      heading.append(badge, h3);
      const description = document.createElement('p');
      description.className = 'text-xs text-slate-600 mb-3';
      description.textContent = key === 'Mantener' ? 'Áreas cuya respuesta predominante fue mantener.' : key === 'Mejorar' ? 'Áreas cuya respuesta predominante fue mejorar.' : key === 'Transformar' ? 'Áreas cuya respuesta predominante fue transformar.' : key === 'No prioritario' ? 'Áreas cuya respuesta predominante fue no prioritario.' : key === 'Sin respuesta' ? 'Áreas sin respuestas válidas para el filtro.' : 'Áreas con empate entre acciones; se muestran una sola vez.';
      const list = document.createElement('ul');
      list.className = 'text-xs text-slate-700 space-y-2 list-disc list-inside';
      entries.forEach((entry) => {
        const li = document.createElement('li');
        const strong = document.createElement('strong');
        strong.textContent = `${entry.area}:`;
        const percentage = key === 'Empate' ? Math.max(...ACTIONS.map((action) => entry.pcts[action] || 0)) : (entry.pcts[key] || 0);
        li.append(strong, document.createTextNode(` ${percentage}%`));
        list.appendChild(li);
      });
      if (!entries.length) { const li = document.createElement('li'); li.className = 'text-slate-400 italic'; li.textContent = 'Sin elementos para este filtro.'; list.appendChild(li); }
      card.append(heading, description, list);
      container.appendChild(card);
    });
  }

  function renderWordCloud(model) {
    const container = $('wordCloudContainer');
    if (!container) return;
    container.replaceChildren();
    if (!model.TOP_WORDS.length) { const empty = document.createElement('p'); empty.className = 'text-sm text-slate-400'; empty.textContent = 'No hay palabras suficientes para este filtro.'; container.appendChild(empty); return; }
    model.TOP_WORDS.forEach((item) => {
      const span = document.createElement('span');
      const size = item.frecuencia >= 6 ? 'text-lg font-bold text-blue-900 bg-blue-100 px-3 py-1' : item.frecuencia >= 4 ? 'text-sm font-semibold text-slate-800 bg-slate-200 px-2.5 py-0.5' : 'text-xs text-slate-600 bg-white border border-slate-200 px-2 py-0.5';
      span.className = `${size} rounded-full`;
      span.textContent = `${item.palabra} (${item.frecuencia})`;
      container.appendChild(span);
    });
  }

  function renderQuotes() {
    const list = $('quotesList');
    if (!list || !state.currentModel) return;
    const category = $('quoteCategory')?.value || state.quoteCategory;
    updateQuestionText(category);
    const query = text($('quoteSearch')?.value || state.quoteSearch).toLowerCase().trim();
    list.replaceChildren();
    const filtered = state.currentModel.QUOTES.filter((quote) => text(quote[category]).trim() && (!query || text(quote[category]).toLowerCase().includes(query) || text(quote.curso).toLowerCase().includes(query)));
    if (!filtered.length) { const empty = document.createElement('p'); empty.className = 'text-xs text-slate-400 p-4 col-span-2 text-center'; empty.textContent = 'No se encontraron comentarios con los criterios seleccionados.'; list.appendChild(empty); return; }
    filtered.forEach((quote) => {
      const card = document.createElement('div');
      card.className = 'bg-slate-50 border border-slate-200 p-4 rounded-lg flex flex-col justify-between';
      const content = document.createElement('p');
      content.className = 'text-xs text-slate-700 italic mb-2';
      content.textContent = `“${text(quote[category]).trim()}”`;
      const meta = document.createElement('div');
      meta.className = 'flex flex-wrap items-center justify-between gap-1 text-[11px] text-slate-400 border-t border-slate-200/60 pt-2 mt-2';
      const course = document.createElement('span');
      course.textContent = `Curso: ${text(quote.curso)}`;
      const age = document.createElement('span');
      age.textContent = `Antigüedad: ${text(quote.antiguedad)}`;
      meta.append(course, age); card.append(content, meta); list.appendChild(card);
    });
  }

  function updateQuestionText(category) {
    const key = text(category || $('quoteCategory')?.value || state.quoteCategory);
    const source = questions().voz || {};
    const node = $('vozQuestionText');
    if (node) node.textContent = text(source[key] || VOZ_QUESTION_FALLBACKS[key] || VOZ_QUESTION_FALLBACKS.cambiar);
  }

  function renderDashboard() {
    const filtered = getFilteredResponses();
    const model = computeModel(filtered);
    state.currentModel = model;
    updateStaticText(model);
    renderCharts(model);
    renderAspectTable(model);
    renderMatrixGroups(model);
    renderWordCloud(model);
    renderQuotes();
  }

  function saveState() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ filters: state.filters, panelCollapsed: state.panelCollapsed, activeTab: state.activeTab })); } catch (_) { /* private mode */ }
  }

  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      const available = new Set(responses().flatMap((record) => validArray(record.cursos)));
      ['seccion', 'antiguedad', 'curso'].forEach((key) => {
        const value = text(saved.filters?.[key]);
        const valid = key === 'seccion' ? SECTIONS.includes(value) : key === 'antiguedad' ? ANTIGUEDAD.includes(value) : !value || available.has(value);
        if (valid) state.filters[key] = value;
      });
      state.panelCollapsed = Boolean(saved.panelCollapsed);
      state.activeTab = ['resumen', 'calidad', 'matriz', 'retos', 'comunidad'].includes(saved.activeTab) ? saved.activeTab : 'resumen';
    } catch (_) { /* ignore malformed state */ }
  }

  function populateCourseDropdown() {
    const select = $('filterCurso');
    if (!select) return;
    const current = state.filters.curso;
    const courses = new Set(responses().flatMap((record) => validArray(record.cursos)));
    select.replaceChildren();
    const all = document.createElement('option'); all.value = ''; all.textContent = 'Todos'; select.appendChild(all);
    COURSES.filter((course) => courses.has(course)).forEach((course) => { const option = document.createElement('option'); option.value = course; option.textContent = course; select.appendChild(option); });
    select.value = courses.has(current) ? current : '';
    if (!select.value) state.filters.curso = '';
  }

  function applyFilters() {
    state.filters = { seccion: $('filterSeccion')?.value || '', antiguedad: $('filterAntiguedad')?.value || '', curso: $('filterCurso')?.value || '' };
    const count = Object.values(state.filters).filter(Boolean).length;
    const badge = $('filterBadge');
    if (badge) { badge.classList.toggle('hidden', count === 0); const countNode = $('filterCount'); if (countNode) countNode.textContent = count; }
    saveState(); renderDashboard();
  }

  function resetFilters() { ['filterSeccion', 'filterAntiguedad', 'filterCurso'].forEach((id) => { if ($(id)) $(id).value = ''; }); applyFilters(); }
  function toggleFilters() { state.panelCollapsed = !state.panelCollapsed; const panel = $('filterPanel'); if (panel) panel.classList.toggle('hidden', state.panelCollapsed); const button = $('filterToggle'); if (button) button.setAttribute('aria-expanded', String(!state.panelCollapsed)); saveState(); }
  function resizeCharts() {
    Object.values(state.charts).forEach((chart) => {
      if (chart && typeof chart.resize === 'function') chart.resize();
    });
  }

  function switchTab(tabName) {
    if (!['resumen', 'calidad', 'matriz', 'retos', 'comunidad', 'conclusiones', 'hojaruta'].includes(tabName)) return;
    document.querySelectorAll('.tab-btn').forEach((button) => button.classList.toggle('active', button.id === `tab-${tabName}`));
    document.querySelectorAll('.tab-content').forEach((content) => content.classList.toggle('hidden', content.id !== `content-${tabName}`));
    // On narrow screens the tab bar scrolls sideways: bring the active tab
    // into view so it is never hidden off-screen after a switch. The deltas
    // come from getBoundingClientRect because offsetLeft is relative to the
    // nearest positioned ancestor, not to the scrolling nav.
    const nav = $('tabNav');
    const active = $(`tab-${tabName}`);
    if (nav && active && nav.scrollWidth > nav.clientWidth + 1) {
      const navBox = nav.getBoundingClientRect();
      const activeBox = active.getBoundingClientRect();
      const current = nav.scrollLeft;
      const delta = (activeBox.left - navBox.left) - (nav.clientWidth - activeBox.width) / 2;
      const target = Math.max(0, Math.min(current + delta, nav.scrollWidth - nav.clientWidth));
      nav.scrollLeft = target;
    }
    resizeCharts();
    state.activeTab = tabName; saveState();
  }
  function onQuoteCategoryChange() { state.quoteCategory = $('quoteCategory')?.value || 'cambiar'; updateQuestionText(); renderQuotes(); }
  function onQuoteSearchInput() { state.quoteSearch = $('quoteSearch')?.value || ''; renderQuotes(); }

  async function updateDashboard() {
    const button = $('updateBtn'); const icon = $('updateIcon'); const label = $('updateText');
    if (button) button.disabled = true; if (icon) icon.classList.add('animate-spin'); if (label) label.textContent = 'Actualizando...';
    try {
      const response = await fetch('/api/update', { cache: 'no-store' }); const data = await response.json();
      if (data.success && data.reload) { if (label) label.textContent = 'Actualizado!'; setTimeout(() => location.reload(), 800); }
      else { if (label) label.textContent = 'Error: ' + (data.message || 'desconocido'); if (button) button.disabled = false; if (icon) icon.classList.remove('animate-spin'); }
    } catch (error) { if (label) label.textContent = 'Error de conexión'; if (button) button.disabled = false; if (icon) icon.classList.remove('animate-spin'); }
  }

  function init() {
    loadState(); populateCourseDropdown();
    [['filterSeccion', 'seccion'], ['filterAntiguedad', 'antiguedad'], ['filterCurso', 'curso']].forEach(([id, key]) => { if ($(id)) $(id).value = state.filters[key] || ''; });
    const panel = $('filterPanel'); if (panel) panel.classList.toggle('hidden', state.panelCollapsed);
    const toggle = $('filterToggle'); if (toggle) toggle.setAttribute('aria-expanded', String(!state.panelCollapsed));
    window.toggleFilters = toggleFilters; window.resetFilters = resetFilters; window.applyFilters = applyFilters; window.switchTab = switchTab; window.updateDashboard = updateDashboard; window.renderQuotes = onQuoteCategoryChange; window.onQuoteCategoryChange = onQuoteCategoryChange; window.onQuoteSearchInput = onQuoteSearchInput; window.updateQuestionText = updateQuestionText;
    state.ready = true; switchTab(state.activeTab); renderDashboard();
  }

  window.addEventListener('resize', resizeCharts, { passive: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true }); else init();
})();
