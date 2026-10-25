/* OptiSense – tab “Learn & practise”: start page, step-by-step workspace with an interactive graph,
   and the evaluation. Texts come from window.OS_I18N (learn_… keys, optisense/pages/learn/texts.py);
   exercises, checks, hints and solutions come from the server (optisense/pages/learn/server.py). */
(function () {
  "use strict";

  // ------------------------------------------------------------------ texts and numbers
  function lang() {
    var l = document.documentElement.getAttribute("lang");
    return (window.OS_I18N || {})[l] ? l : "en";
  }
  function T(key, params) {
    var all = window.OS_I18N || {}, d = all[lang()] || {}, en = all.en || {};
    var s = d[key] !== undefined ? d[key] : en[key] !== undefined ? en[key] : key;
    return params ? s.replace(/\{(\w+)\}/g, function (m, k) { return params[k] !== undefined ? params[k] : m; }) : s;
  }
  function L(key, params) { return T("learn_" + key, params); }
  function esc(s) {
    return String(s === undefined || s === null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function isNum(v) { return typeof v === "number" && isFinite(v); }
  function fmt(v) {
    if (v === "∞" || v === Infinity) return "∞";
    if (v === "−∞" || v === -Infinity) return "−∞";
    var n = Number(v);
    if (!isFinite(n)) return "–";
    n = Math.round(n * 1e4) / 1e4;
    if (n === 0) n = 0;
    return n.toLocaleString(lang() === "de" ? "de-DE" : "en-US", { maximumFractionDigits: 4 }).replace("-", "−");
  }
  // a value for an input field: no thousands separator, decimal comma in German
  function fmtInput(v) {
    var s = String(Math.round(v * 1e4) / 1e4);
    return lang() === "de" ? s.replace(".", ",") : s;
  }
  // the learner's input: decimal comma or point, fractions like 3/4, ∞
  function num(v) {
    if (v === undefined || v === null) return NaN;
    var s = String(v).trim().replace(/−/g, "-").replace(/\s/g, "");
    if (!s) return NaN;
    var low = s.toLowerCase().replace(/^\+/, "");
    if (["inf", "∞", "infinity", "unendlich"].indexOf(low) >= 0) return Infinity;
    if (low[0] === "-" && ["inf", "∞", "infinity", "unendlich"].indexOf(low.slice(1)) >= 0) return -Infinity;
    if (lang() === "de" && /^-?[1-9]\d{0,2}(\.\d{3})+(,\d*)?$/.test(s)) s = s.replace(/\./g, "");
    else if (lang() !== "de" && /^-?[1-9]\d{0,2}(,\d{3})+(\.\d*)?$/.test(s)) s = s.replace(/,/g, "");
    s = s.replace(",", ".");
    if (s.indexOf("/") > 0) {
      var p = s.split("/");
      return p.length === 2 && p[0] !== "" && p[1] !== "" ? Number(p[0]) / Number(p[1]) : NaN;
    }
    return /^-?(\d+\.?\d*|\.\d+)(e-?\d+)?$/i.test(s) ? Number(s) : NaN;
  }
  function pt(x, y) { return "(" + fmt(x) + " | " + fmt(y) + ")"; }
  var NONE = ["-", "–", "—", "--", "keiner", "keine", "kein", "none", "no", "n/a"];
  function isNone(v) { return NONE.indexOf(String(v === undefined || v === null ? "" : v).trim().toLowerCase()) >= 0; }
  // a1·x1 + a2·x2 as on “Model & solution”: no zero terms, no written 1
  function formula(a) {
    var parts = [];
    [0, 1].forEach(function (j) {
      var c = a[j], v = "x" + (j + 1);
      if (isNum(c) && Math.abs(c) < 1e-12) return;
      var mag = isNum(c) ? Math.abs(c) : NaN;
      var term = !isNum(c) ? "?·" + v : Math.abs(mag - 1) < 1e-12 ? v : fmt(mag) + "·" + v;
      var neg = isNum(c) && c < 0;
      parts.push(parts.length ? (neg ? "− " : "+ ") + term : (neg ? "−" : "") + term);
    });
    return parts.length ? parts.join(" ") : "0";
  }
  var OP = { "<=": "≤", ">=": "≥", "=": "=" };
  var GREEN = "#1f7a1f", RED = "#cc0000", INK = "#1d1f21", GREY = "#808080";

  // ------------------------------------------------------------------ state
  var S = {
    view: "home",
    opts: { difficulty: "easy", form: "text", kind: "LP", mode: "practice", method: "both", topic: "random", sensitivity: false, simplex: false },
    ownOpts: { mode: "practice", method: "both", sensitivity: false, simplex: false },
    more: false, ownMore: false, own: null,
    ex: null, step: 0, answers: {}, feedback: {}, hints: {}, solutions: {}, result: null,
    activeRow: 0, level: null, help: false, sidebar: true, tableaus: 1, busy: null
  };

  function steps() { return S.ex ? S.ex.steps : []; }
  function cur() { return steps()[S.step]; }
  function nRows() { return S.ex ? S.ex.colors.length : 0; }
  function exam() { return S.ex && S.ex.options.mode === "exam"; }
  function tutorial() { return S.ex && S.ex.source === "tutorial"; }
  function textTask() { return S.ex && S.ex.options.form === "text"; }
  function hasGraph() { return S.ex && S.ex.options.method !== "calc"; }
  function ans(sid) { return S.answers[sid] || (S.answers[sid] = {}); }
  function val(sid, key) { var a = S.answers[sid]; return a && a[key] !== undefined ? a[key] : ""; }
  function label(i) { return S.ex.labels[i]; }
  function color(i) { return S.ex.colors[i]; }

  // the model the graph and the step texts use: given, or the learner's own from step 1
  function model() {
    if (S.ex.model) return S.ex.model;
    var a = S.answers.model || {};
    var rows = [];
    for (var i = 0; i < nRows(); i++) {
      rows.push({ a: [num(a["a" + i + "_0"]), num(a["a" + i + "_1"])], op: a["op" + i] || "", b: num(a["b" + i]) });
    }
    var k = (a.vt0 === "int" ? 1 : 0) * 2 + (a.vt1 === "int" ? 1 : 0);
    return { c: [num(a.c0), num(a.c1)], sense: a.sense || "", kind: ["LP", "MILP2", "MILP1", "ILP"][k], rows: rows };
  }
  function rowComplete(r) { return isNum(r.a[0]) && isNum(r.a[1]) && isNum(r.b) && !!r.op; }
  function ints(kind) { return { LP: [0, 0], ILP: [1, 1], MILP1: [1, 0], MILP2: [0, 1] }[kind] || [0, 0]; }

  // ------------------------------------------------------------------ server
  var seq = 0, pending = {};
  function call(action, payload) {
    return new Promise(function (resolve, reject) {
      if (!window.Shiny || !Shiny.setInputValue) { reject(new Error(L("err_request"))); return; }
      var id = ++seq;
      pending[id] = { resolve: resolve, reject: reject };
      Shiny.setInputValue("learn_req", Object.assign({ id: id, action: action, lang: lang() }, payload || {}), { priority: "event" });
    });
  }
  function busy(name, promise) {
    S.busy = name;
    paintBusy();
    return promise.then(function (d) { S.busy = null; return d; }, function (e) { S.busy = null; paintBusy(); toast(e.message); throw e; });
  }
  function paintBusy() {
    var el = root();
    if (!el) return;
    el.classList.toggle("is-busy", !!S.busy);
    el.querySelectorAll("[data-act]").forEach(function (b) {
      if (b.tagName === "BUTTON") b.toggleAttribute("aria-busy", S.busy === b.getAttribute("data-act"));
    });
  }

  var toastTimer = null;
  function toast(text) {
    var t = document.getElementById("ol-toast");
    if (!t) { t = document.createElement("div"); t.id = "ol-toast"; t.className = "ol-toast"; t.setAttribute("role", "alert"); document.body.appendChild(t); }
    t.textContent = text;
    t.classList.add("is-on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("is-on"); }, 6000);
  }

  // a small dialog in the style of the OptiSense modals; resolves true for OK.
  // (No <form method="dialog">: Shiny stops the submit of forms without an action.)
  function ask(title, text, okLabel, cancelLabel) {
    return new Promise(function (resolve) {
      var d = document.createElement("dialog");
      d.className = "ol-dialog";
      d.setAttribute("aria-labelledby", "ol-dialog-title");
      d.innerHTML = '<div class="ol-dialog-inner"><h2 id="ol-dialog-title">' + esc(title) + "</h2>" + text +
        '<div class="ol-dialog-foot"><button type="button" class="btn os-btn" data-answer="no">' + esc(cancelLabel || T("cancel")) + "</button>" +
        '<button type="button" class="btn os-btn os-btn-primary" data-answer="yes">' + esc(okLabel) + "</button></div></div>";
      document.body.appendChild(d);
      d.addEventListener("close", function () { resolve(d.returnValue === "yes"); d.remove(); });
      d.addEventListener("click", function (e) {
        var b = e.target.closest("[data-answer]");
        if (b) d.close(b.getAttribute("data-answer"));
        else if (e.target === d) d.close("no");
      });
      d.showModal();
      d.querySelector('[data-answer="yes"]').focus();
    });
  }

  // ------------------------------------------------------------------ rendering frame
  function root() { return document.getElementById("os-learn"); }

  function render() {
    var el = root();
    if (!el) return;
    var focus = document.activeElement && el.contains(document.activeElement) ? document.activeElement.id : null;
    var scroll = el.querySelector(".ol-step-body") ? el.querySelector(".ol-step-body").scrollTop : 0;
    el.setAttribute("data-view", S.view);
    el.innerHTML = S.view === "work" ? workHTML() : S.view === "result" ? resultHTML() : homeHTML();
    if (S.view === "work") {
      drawGraph();
      var body = el.querySelector(".ol-step-body");
      if (body && keepScroll) body.scrollTop = scroll;
    }
    keepScroll = false;
    if (focus && document.getElementById(focus)) document.getElementById(focus).focus({ preventScroll: true });
    paintBusy();
  }
  var keepScroll = false;
  function refresh() { keepScroll = true; render(); }

  function icon(name) {
    var p = {
      route: '<circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="6" r="2.2"/><path d="M8 18h6a3.5 3.5 0 0 0 0-7h-4a3.5 3.5 0 0 1 0-7h6"/>',
      dice: '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><circle cx="8.5" cy="8.5" r="1.2" fill="currentColor"/><circle cx="15.5" cy="15.5" r="1.2" fill="currentColor"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>',
      pencil: '<path d="M4 20l1-4L16 5l3 3L8 19l-4 1z"/><path d="M14 7l3 3"/>'
    }[name];
    return '<svg class="ol-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + p + "</svg>";
  }

  // segmented control (radio buttons), like the value-range choice on “Model & solution”
  function seg(name, items, value, attrs, cls) {
    return '<div class="ol-seg ' + (cls || "") + '" role="radiogroup" ' + (attrs || "") + ">" + items.map(function (it) {
      var id = name + "-" + String(it[0]).replace(/[^a-z0-9]/gi, "_");
      return '<label class="ol-seg-item"><input type="radio" id="' + esc(id) + '" name="' + esc(name) + '" value="' + esc(it[0]) + '"' +
        (String(value) === String(it[0]) ? " checked" : "") + (it[2] ? " disabled" : "") + "><span>" + it[1] + "</span></label>";
    }).join("") + "</div>";
  }
  function switchRow(id, title, hint, on, disabled, attr) {
    return '<div class="ol-switch-row' + (disabled ? " is-disabled" : "") + '"><label for="' + id + '"><b>' + esc(title) + "</b>" +
      (hint ? "<small>" + esc(hint) + "</small>" : "") + '</label><label class="os-switch"><input type="checkbox" id="' + id + '" ' + attr +
      (on ? " checked" : "") + (disabled ? " disabled" : "") + "><span></span></label></div>";
  }
  function swatch(c, dashed) {
    return '<span class="os-swatch' + (dashed ? " is-dashed" : "") + '" style="background:' + c + ";color:" + c + '" aria-hidden="true"></span>';
  }

  // ------------------------------------------------------------------ start page
  function practiceSimplexOk() { return S.opts.form === "math" && S.opts.kind === "LP"; }

  function homeHTML() {
    var o = S.opts, oo = S.ownOpts;
    var diff = seg("o-difficulty", [["easy", L("diff_easy")], ["medium", L("diff_medium")], ["hard", L("diff_hard")]], o.difficulty, 'data-opt="difficulty" aria-label="' + esc(L("opt_difficulty")) + '"');
    var form = seg("o-form", [["text", L("form_text")], ["math", L("form_math")]], o.form, 'data-opt="form" aria-label="' + esc(L("opt_form")) + '"');
    var kind = seg("o-kind", [["LP", L("kind_LP")], ["ILP", L("kind_ILP")], ["MILP", L("kind_MILP")]], o.kind, 'data-opt="kind" aria-label="' + esc(L("opt_kind")) + '"');
    var methodItems = [["both", L("method_both")], ["graph", L("method_graph")], ["calc", L("method_calc")]];
    var topics = ["random", "gastro", "production", "farming", "events", "transport", "advertising"];

    var practice =
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_difficulty")) + "</div>" + diff + '<p class="ol-field-hint">' + esc(L("diff_" + o.difficulty + "_hint")) + "</p></div>" +
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_form")) + "</div>" + form + '<p class="ol-field-hint">' + esc(L("form_" + o.form + "_hint")) + "</p></div>" +
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_kind")) + "</div>" + kind + '<p class="ol-field-hint">' + esc(L("kind_" + o.kind + "_hint")) + "</p></div>" +
      switchRow("o-exam", L("opt_exam"), L("opt_exam_hint"), o.mode === "exam", false, 'data-opt="mode"') +
      '<details class="ol-more"' + (S.more ? " open" : "") + ' data-more="practice"><summary>' + esc(L("more_options")) + "</summary>" +
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_method")) + "</div>" + seg("o-method", methodItems, o.method, 'data-opt="method" aria-label="' + esc(L("opt_method")) + '"', "is-small") + "</div>" +
      '<div class="ol-field"><label class="ol-field-label" for="o-topic">' + esc(L("opt_topic")) + '</label><select id="o-topic" class="form-select ol-select" data-opt="topic">' +
      topics.map(function (tp) { return '<option value="' + tp + '"' + (o.topic === tp ? " selected" : "") + ">" + esc(L("topic_" + tp)) + "</option>"; }).join("") + "</select></div>" +
      switchRow("o-sens", L("opt_sens"), L("opt_sens_hint"), o.sensitivity, false, 'data-opt="sensitivity"') +
      switchRow("o-simplex", L("opt_simplex"), practiceSimplexOk() ? L("opt_simplex_hint") : L("opt_simplex_off"), o.simplex && practiceSimplexOk(), !practiceSimplexOk(), 'data-opt="simplex"') +
      "</details>";

    var own = S.own;
    var ownBody;
    if (own && own.ready) {
      var rows = '<div class="ol-mini-list"><div class="ol-mini-row">' + swatch(GREEN, true) + "<span><b>F</b> = " + esc(formula(own.c)) + " → " + esc(own.sense) + "</span></div>" +
        own.rows.map(function (r) {
          return '<div class="ol-mini-row">' + swatch(r.color) + "<span><b>" + esc(r.name) + ":</b> " + esc(formula(r.a)) + " " + OP[r.op] + " " + esc(fmt(r.b)) + "</span></div>";
        }).join("") + '<div class="ol-mini-row ol-mini-type">' + esc(T("type_" + own.kind.replace(/[12]$/, ""))) + "</div></div>";
      ownBody = rows +
        switchRow("oo-exam", L("opt_exam"), L("opt_exam_hint"), oo.mode === "exam", false, 'data-own-opt="mode"') +
        '<details class="ol-more"' + (S.ownMore ? " open" : "") + ' data-more="own"><summary>' + esc(L("more_options")) + "</summary>" +
        '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_method")) + "</div>" + seg("oo-method", methodItems, oo.method, 'data-own-opt="method" aria-label="' + esc(L("opt_method")) + '"', "is-small") + "</div>" +
        switchRow("oo-sens", L("opt_sens"), L("opt_sens_hint"), oo.sensitivity, false, 'data-own-opt="sensitivity"') +
        switchRow("oo-simplex", L("opt_simplex"), own.simplex ? L("opt_simplex_hint_own") : L("opt_simplex_off_own"), oo.simplex && own.simplex, !own.simplex, 'data-own-opt="simplex"') +
        "</details>" +
        '<button class="btn os-btn os-btn-primary ol-cta" id="ol-start-own" data-act="own">' + esc(L("start_own")) + "</button>";
    } else {
      ownBody = '<div class="ol-empty"><p>' + esc(L("own_empty")) + '</p><button class="btn os-btn" id="ol-goto-work" data-act="goto-work">' + esc(L("own_goto")) + "</button></div>" +
        '<button class="btn os-btn os-btn-primary ol-cta" disabled>' + esc(L("start_own")) + "</button>";
    }

    var flow = ["flow_model", "flow_lines", "flow_optimum", "flow_sens", "flow_result"];
    return '<div class="ol-page">' +
      '<header class="ol-hero"><h1>' + esc(L("home_title")) + "</h1><p>" + esc(L("home_lead")) + "</p></header>" +
      '<div class="ol-cards">' +
      card("route", L("card_tutorial_title"), L("card_tutorial_tag"),
        "<p>" + esc(L("card_tutorial_text")) + '</p><ul class="ol-checks">' + ["tut_learn1", "tut_learn2", "tut_learn3"].map(function (k) { return "<li>" + esc(L(k)) + "</li>"; }).join("") + "</ul>" +
        '<p class="ol-meta">' + esc(L("card_tutorial_meta")) + "</p>" +
        '<button class="btn os-btn os-btn-primary ol-cta" id="ol-start-tutorial" data-act="tutorial">' + esc(L("start_tutorial")) + "</button>", "is-tutorial") +
      card("dice", L("card_practice_title"), L("card_practice_tag"),
        "<p>" + esc(L("card_practice_text")) + "</p>" + practice +
        '<button class="btn os-btn os-btn-primary ol-cta" id="ol-start-practice" data-act="create">' + esc(L("start_practice")) + "</button>") +
      card("pencil", L("card_own_title"), L("card_own_tag"), "<p>" + esc(L("card_own_text")) + "</p>" + ownBody) +
      "</div>" +
      '<section class="ol-flow os-card"><h2>' + esc(L("flow_title")) + '</h2><ol class="ol-flow-steps">' +
      flow.map(function (k, i) { return '<li><span class="os-num">' + (i + 1) + "</span><span>" + esc(L(k)) + "</span></li>"; }).join("") +
      '</ol><p class="ol-flow-note">' + esc(L("flow_note")) + '</p><p class="ol-flow-note">' + esc(L("numbers_note")) + " " + esc(L("reload_note")) + "</p></section>" +
      "</div>";
  }

  function card(ic, title, tag, body, cls) {
    return '<section class="ol-choice os-card ' + (cls || "") + '"><header class="ol-choice-head"><span class="ol-choice-icon">' + icon(ic) + "</span><div><h2>" + esc(title) + '</h2><span class="ol-choice-tag">' + esc(tag) + "</span></div></header>" +
      '<div class="ol-choice-body">' + body + "</div></section>";
  }

  // ------------------------------------------------------------------ starting and ending an exercise
  function startWith(action, payload) {
    return busy(action, call(action, payload)).then(function (ex) {
      S.ex = ex; S.step = 0; S.answers = {}; S.feedback = {}; S.hints = {}; S.solutions = ex.solutions || {}; S.result = null;
      S.activeRow = 0; S.level = null; S.tableaus = 1; S.help = false; S.view = "work";
      S.sidebar = true; S.taskOpen = null;
      render();
      var el = root();
      if (el) el.scrollTop = 0;
      window.scrollTo(0, 0);
    }, function () {});
  }

  function quit() {
    ask(L("quit_title"), "<p>" + esc(L("quit_text")) + "</p>", L("quit_btn"), L("keep_working")).then(function (ok) {
      if (!ok) return;
      call("quit").catch(function () {});
      S.ex = null; S.view = "home"; render();
    });
  }

  // ------------------------------------------------------------------ workspace
  var SHORT = { model: "short_model", lines: "short_lines", region: "short_region", intersection: "short_intersection", optimum: "short_optimum", sensitivity: "short_sensitivity", interpret: "short_interpret", simplex: "short_simplex" };

  function sensOnlySlack(s) { return s.id === "sensitivity" && !s.questions.some(function (q) { return /^(shadow|range|idelta)/.test(q.key); }); }
  function stepTitle(s) { return L(sensOnlySlack(s) ? "step_slack" : "step_" + s.id); }
  function stepShort(s) { return L(sensOnlySlack(s) ? "short_slack" : SHORT[s.id]); }

  function filled(s) {
    return s.questions.filter(function (q) { return String(val(s.id, q.key)).trim() !== ""; }).length;
  }
  function status(i) {
    var s = steps()[i], fb = S.feedback[s.id];
    if (!exam() && fb && !fb.stale) return fb.correct ? "ok" : "warn";
    var n = filled(s);
    return n === s.questions.length ? "done" : n > 0 ? "started" : "todo";
  }

  function stepperHTML() {
    var mode = tutorial() ? "mode_tutorial" : exam() ? "mode_exam" : "mode_practice";
    var items = steps().map(function (s, i) {
      var st = status(i), here = i === S.step;
      var dot = st === "ok" ? "✓" : st === "warn" ? "!" : String(i + 1);
      return '<li class="ol-st is-' + st + (here ? " is-current" : "") + '"><button type="button" id="ol-st-' + i + '" data-act="goto" data-step="' + i + '"' + (here ? ' aria-current="step"' : "") +
        ' title="' + esc(stepTitle(s)) + '"><span class="ol-st-dot">' + dot + '</span><span class="ol-st-label">' + esc(stepShort(s)) + "</span></button></li>";
    }).join("");
    items += '<li class="ol-st is-finish"><button type="button" id="ol-st-finish" data-act="finish" title="' + esc(L(tutorial() ? "finish_tutorial" : "to_submit")) + '"><span class="ol-st-dot">★</span><span class="ol-st-label">' + esc(L("short_result")) + "</span></button></li>";
    return '<nav class="ol-stepper os-card" aria-label="' + esc(L("path")) + '"><span class="os-tag ol-mode is-' + mode + '">' + esc(L(mode)) + '</span><ol>' + items +
      '</ol><button type="button" class="btn btn-link os-header-action" id="ol-quit" data-act="quit">' + esc(L("quit")) + "</button></nav>";
  }

  function sideHTML() {
    var st = S.ex.story, m = model(), s = cur(), html = "";
    var task = '<h3 class="ol-story-title">' + esc(st.title) + "</h3>";
    if (st.intro) {
      task += '<p class="ol-story-intro">' + esc(st.intro) + "</p>" +
        '<div class="ol-sought"><span class="ol-sought-title">' + esc(L("story_sought")) + "</span>" +
        st.sought.map(function (v, j) { return '<div class="ol-sought-row"><b>x' + (j + 1) + "</b><span>" + esc(v) + "</span></div>"; }).join("") + "</div>" +
        '<ul class="ol-story">' +
        '<li data-focus="obj">' + swatch(GREEN, true) + "<span>" + esc(st.objective) + "</span></li>" +
        st.rows.map(function (r, i) {
          return '<li data-focus="row' + i + '">' + swatch(color(i)) + '<span><b class="ol-lab" style="color:' + color(i) + '">' + esc(label(i)) + "</b> " + esc(r) + "</span></li>";
        }).join("") + "</ul>" +
        '<ul class="ol-story ol-story-domain">' + st.domain.map(function (d) { return '<li data-focus="vt"><span>' + esc(d) + "</span></li>"; }).join("") + "</ul>";
    } else {
      task += modelListHTML(S.ex.model, false);
    }
    if (st.question) task += '<p class="ol-story-q">' + esc(st.question) + "</p>";
    var open = S.taskOpen !== null ? S.taskOpen : window.innerWidth >= 1024 || s.id === "model";
    if (tutorial()) html += coachHTML(s);
    html += '<details class="os-card ol-panel ol-task"' + (open ? " open" : "") + '><summary class="ol-panel-head"><h2>' + esc(L("task")) + "</h2>" +
      '<span class="ol-task-title">' + esc(st.title) + '</span></summary><div class="ol-panel-body">' + task + "</div></details>";
    if (!exam()) html += helpCardHTML(s);
    if (textTask() && s.id !== "model") {
      html += '<section class="os-card ol-panel ol-yourmodel"><header class="ol-panel-head"><h2>' + esc(L("your_model")) + '</h2><button type="button" class="btn btn-link os-header-action" data-act="goto" data-step="0">' + esc(L("edit_model")) + '</button></header><div class="ol-panel-body">' + modelListHTML(m, true) + "</div></section>";
    }
    return '<aside class="ol-side" aria-label="' + esc(L("task")) + '">' + html + "</aside>";
  }

  function modelListHTML(m, own) {
    var obj = isNum(m.c[0]) || isNum(m.c[1]) || !own ? "<b>F</b> = " + esc(formula(m.c)) + " → " + esc(m.sense || "?") : '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>";
    var rows = m.rows.map(function (r, i) {
      var text = rowComplete(r) ? esc(formula(r.a)) + " " + OP[r.op] + " " + esc(fmt(r.b)) : '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>";
      var name = S.ex.names && S.ex.names[i] ? ' <span class="ol-muted">· ' + esc(S.ex.names[i]) + "</span>" : "";
      return '<div class="ol-mini-row">' + swatch(color(i)) + '<span><b style="color:' + color(i) + '">' + esc(label(i)) + ":</b> " + text + name + "</span></div>";
    }).join("");
    var a = S.answers.model || {};
    var vt = own && (!a.vt0 || !a.vt1) ? '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>" :
      "x1 " + esc(T(ints(m.kind)[0] ? "integer_short" : "continuous_short")) + ", x2 " + esc(T(ints(m.kind)[1] ? "integer_short" : "continuous_short"));
    return '<div class="ol-mini-list"><div class="ol-mini-row">' + swatch(GREEN, true) + "<span>" + obj + "</span></div>" + rows +
      '<div class="ol-mini-row ol-mini-type"><span>' + esc(L("g_range")) + ": " + vt + "</span></div></div>";
  }

  function workHTML() {
    var cls = "ol-work" + (hasGraph() ? "" : " is-calc") + (S.sidebar ? "" : " no-side");
    return '<div class="' + cls + '" data-step="' + cur().id + '">' + stepperHTML() + (S.sidebar ? sideHTML() : "") + (hasGraph() ? graphCardHTML() : "") + stepCardHTML() + "</div>";
  }

  function sidebarButton() {
    return '<button type="button" class="os-sidebar-btn" data-act="sidebar" aria-expanded="' + S.sidebar + '" aria-label="' + esc(L("toggle_task")) + '" title="' + esc(L("toggle_task")) + '">' + (S.sidebar ? "‹" : "›") + "</button>";
  }

  // ------------------------------------------------------------------ step card
  function stepCardHTML() {
    var s = cur(), total = steps().length;
    var head = '<header class="ol-panel-head ol-step-head">' + (hasGraph() ? "" : sidebarButton()) +
      '<div class="ol-step-heading"><div class="ol-step-meta">' + esc(L("step_of", { n: S.step + 1, total: total })) + " · " + esc(L("points", { n: s.points })) + "</div>" +
      '<h2 class="ol-step-title" id="ol-step-title">' + esc(stepTitle(s)) + "</h2></div>" +
      (exam() ? "" : '<button type="button" class="os-help' + (S.help ? " is-on" : "") + '" id="ol-help" data-act="help" aria-expanded="' + S.help + '" aria-label="' + esc(L("help_title")) + '" title="' + esc(L("help_title")) + '">?</button>') +
      "</header>";
    var body = "";
    if (textTask() && s.id !== "model" && !tutorial()) {
      var fb = S.feedback.model;
      if (!exam() && (!fb || fb.stale || !fb.correct)) body += '<div class="ol-banner is-info">' + esc(L(fb && !fb.stale ? "model_notice_wrong" : "model_notice")) + "</div>";
    }
    body += '<p class="ol-lead">' + esc(lead(s)) + "</p>";
    body += ({ model: modelStep, lines: linesStep, region: regionStep, intersection: crossStep, optimum: optimumStep, sensitivity: sensStep, interpret: interpretStep, simplex: simplexStep })[s.id](s);
    body += feedbackHTML(s) + hintHTML(s) + solutionHTML(s);

    var last = S.step === total - 1, fbS = S.feedback[s.id], solved = fbS && !fbS.stale && fbS.correct;
    var foot = '<footer class="ol-step-foot">' +
      '<button type="button" class="ol-icon-btn" id="ol-prev" data-act="prev" aria-label="' + esc(L("back")) + '" title="' + esc(L("back")) + '"' + (S.step === 0 ? " disabled" : "") + ">‹</button>" +
      (exam() ? "" : '<button type="button" class="ol-link-btn" id="ol-hint" data-act="hint">' + esc(L("hint")) + '</button><button type="button" class="ol-link-btn" id="ol-solution" data-act="solution">' + esc(L("solution")) + "</button>") +
      '<span class="ol-grow"></span>' +
      (exam() ? "" : '<button type="button" class="btn os-btn' + (solved ? "" : " os-btn-primary") + '" id="ol-check" data-act="check">' + esc(L("check")) + "</button>") +
      '<button type="button" class="btn os-btn' + (solved || exam() || last ? " os-btn-primary" : "") + '" id="ol-next" data-act="' + (last ? "finish" : "next") + '">' +
      esc(last ? L(tutorial() ? "finish_short" : "to_submit") : L("next")) + " ›</button></footer>";
    return '<section class="os-card ol-panel ol-stepcard" aria-labelledby="ol-step-title">' + head + '<div class="ol-step-body">' + body + "</div>" + foot + "</section>";
  }

  function lead(s) {
    if (s.id === "optimum") return L(hasGraph() ? "lead_optimum" : "lead_optimum_calc");
    if (s.id === "sensitivity") {
      var keys = s.questions.map(function (q) { return q.key; });
      return L(keys.indexOf("shadow0") >= 0 ? "lead_sensitivity_full" : keys.indexOf("idelta") >= 0 ? "lead_sensitivity_int" : "lead_sensitivity");
    }
    if (s.id === "lines" && tutorial()) return L("lead_lines");
    return L("lead_" + s.id);
  }

  // input field for a numeric answer
  function input(sid, key, aria, ph, wide, text) {
    var v = val(sid, key), mark = markOf(sid, key);
    return '<input class="ol-in' + (wide ? " is-wide" : "") + mark + '" id="q-' + key + '" data-q="' + key + '" value="' + esc(v) + '" autocomplete="off" spellcheck="false" inputmode="' + (text ? "text" : "decimal") + '"' +
      (ph ? ' placeholder="' + esc(ph) + '"' : "") + ' aria-label="' + esc(aria) + '"' + (locked(key) ? " readonly" : "") + ">";
  }
  function choice(sid, key, items, aria, cls) {
    var mark = markOf(sid, key), empty = !mark && String(val(sid, key)) === "" ? " is-empty" : "";
    return seg("q-" + key, items, val(sid, key), 'data-q="' + key + '" aria-label="' + esc(aria) + '"', (cls || "") + mark + empty);
  }
  // a formula part with a small caption above it; captions of choices ask to choose until something is chosen
  function cell(cap, inner, cls) { return '<div class="ol-cell' + (cls ? " " + cls : "") + '">' + cap + inner + "</div>"; }
  function cap(text) { return '<span class="ol-cap">' + esc(text) + "</span>"; }
  function pickCap(sid, key, base, pick) {
    var empty = String(val(sid, key)) === "";
    return '<span class="ol-cap' + (empty ? " is-pick" : "") + '" data-base="' + esc(L(base)) + '">' + esc(L(empty ? pick : base)) + "</span>";
  }
  function sym(text) { return '<span class="ol-sym">' + text + "</span>"; }
  function markOf(sid, key) {
    var fb = S.feedback[sid];
    if (!fb || exam() || !fb.checks || fb.checks[key] === undefined) return "";
    if (fb.checks[key]) return " is-right";
    return String(val(sid, key)).trim() === "" ? " is-missing" : " is-wrong";
  }
  function locked(key) {
    var m = /^(enter|leave|pivot|nextz)(\d+)$/.exec(key);
    return !!(m && exam() && Number(m[2]) < S.tableaus - 1);
  }
  function rowHead(i, eq) {
    var name = S.ex.names && S.ex.names[i] ? '<span class="ol-row-name">' + esc(S.ex.names[i]) + "</span>" : "";
    return '<div class="ol-row-head">' + swatch(color(i)) + '<b style="color:' + color(i) + '">' + esc(label(i)) + "</b>" + name +
      (eq ? '<span class="ol-eq">' + eq + "</span>" : "") + "</div>";
  }
  function rowEq(i, withOp) {
    var r = model().rows[i];
    if (!rowComplete(r) && !(isNum(r.a[0]) && isNum(r.a[1]) && isNum(r.b))) return '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>";
    return esc(formula(r.a)) + " " + (withOp ? OP[r.op] || "?" : "=") + " " + esc(fmt(r.b));
  }

  function modelStep(s) {
    var sid = s.id, h = "";
    h += '<section class="ol-group" data-group="obj"><h3 class="ol-group-title">' + esc(T("objective_function")) + "</h3>" +
      '<div class="ol-formula is-capped">' + sym("F =") + cell(cap("c1"), input(sid, "c0", L("a_c", { n: 1 }))) + sym("·x1 +") + cell(cap("c2"), input(sid, "c1", L("a_c", { n: 2 }))) + sym("·x2 →") +
      cell(pickCap(sid, "sense", "cap_sense", "cap_sense_pick"), choice(sid, "sense", [["max", "max"], ["min", "min"]], L("a_sense"), "is-inline")) + "</div></section>";
    h += '<section class="ol-group" data-group="vt"><h3 class="ol-group-title">' + esc(L("g_range")) + "</h3>" +
      [0, 1].map(function (j) {
        return '<div class="ol-vt-row"><span class="os-var">x' + (j + 1) + "</span>" + choice(sid, "vt" + j, [["con", esc(T("continuous_short"))], ["int", esc(T("integer_short"))]], L("a_vt", { n: j + 1 })) + "</div>";
      }).join("") + "</section>";
    h += '<section class="ol-group"><h3 class="ol-group-title">' + esc(T("constraints")) + "</h3>";
    for (var i = 0; i < nRows(); i++) {
      var lab = label(i);
      h += '<div class="ol-row" data-group="row' + i + '">' + rowHead(i) + '<div class="ol-formula is-capped">' +
        cell(cap("a1"), input(sid, "a" + i + "_0", L("a_a", { label: lab, n: 1 }))) + sym("·x1 +") +
        cell(cap("a2"), input(sid, "a" + i + "_1", L("a_a", { label: lab, n: 2 }))) + sym("·x2") +
        cell(pickCap(sid, "op" + i, "cap_op", "cap_op_pick"), choice(sid, "op" + i, [["<=", "≤"], [">=", "≥"], ["=", "="]], L("a_op", { label: lab }), "is-inline is-ops")) +
        cell(cap("b"), input(sid, "b" + i, L("a_b", { label: lab }))) + "</div></div>";
    }
    return h + "</section>";
  }

  function linesStep(s) {
    var h = '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_axes")) + "</h3>";
    for (var i = 0; i < nRows(); i++) {
      var lab = label(i);
      h += '<div class="ol-row ol-pick' + (i === S.activeRow ? " is-active" : "") + '" data-row="' + i + '" data-group="row' + i + '">' + rowHead(i, rowEq(i, false)) +
        '<div class="ol-axes">' + [0, 1].map(function (j) {
          var key = "ax" + i + "_" + j, none = isNone(val(s.id, key));
          return cell('<span class="ol-cap">' + esc(L(j ? "ax_x2" : "ax_x1")) + ' <span class="ol-cap-note">(' + (j ? "x1 = 0" : "x2 = 0") + ")</span></span>",
            '<div class="ol-axis-in">' + input(s.id, key, lab + ": " + L(j ? "ax_x2" : "ax_x1")) +
            '<button type="button" class="ol-none-btn' + (none ? " is-on" : "") + '" id="ol-none-' + key + '" data-act="none" data-key="' + key + '" aria-pressed="' + none + '" title="' + esc(L("ax_none")) + '" aria-label="' + esc(L("ax_none")) + '">–</button></div>');
        }).join("") + "</div></div>";
    }
    return h + '<p class="ol-field-hint">' + esc(L("none_hint")) + "</p></section>";
  }

  function regionStep(s) {
    var h = '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_sides")) + "</h3>";
    for (var i = 0; i < nRows(); i++) {
      var tp = S.ex.testPoints[i];
      h += '<div class="ol-row ol-pick' + (i === S.activeRow ? " is-active" : "") + '" data-row="' + i + '" data-group="row' + i + '">' + rowHead(i, rowEq(i, true)) +
        choice(s.id, "side" + i, [["in", esc(L("side_in", { p: pt(tp[0], tp[1]) }))], ["out", esc(L("side_out"))], ["line", esc(L("side_line"))]], L("a_side", { label: label(i) }), "is-wrap") + "</div>";
    }
    h += '</section><section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_points")) + "</h3>";
    S.ex.points.forEach(function (p, n) {
      h += '<div class="ol-check-row"><span class="ol-pt-label"><b>P' + (n + 1) + "</b> " + pt(p[0], p[1]) + "</span>" +
        choice(s.id, "p" + n, [["yes", esc(L("feasible_yes"))], ["no", esc(L("feasible_no"))]], L("a_point", { n: n + 1 }), "is-inline") + "</div>";
    });
    return h + "</section>";
  }

  function boundaryName(i) {
    return i < nRows() ? label(i) : i === nRows() ? L("axis_x1") : L("axis_x2");
  }
  function crossStep(s) {
    var a = ans(s.id), picked = [a.boundary1, a.boundary2].filter(function (v) { return v !== undefined && v !== ""; });
    var chips = "";
    for (var i = 0; i < nRows() + 2; i++) {
      var on = picked.indexOf(String(i)) >= 0;
      chips += '<button type="button" class="ol-chip' + (on ? " is-on" + markOf(s.id, "boundary1") : "") + '" id="ol-b-' + i + '" data-act="boundary" data-b="' + i + '" aria-pressed="' + on + '">' +
        (i < nRows() ? swatch(color(i)) : "") + esc(boundaryName(i)) + (i < nRows() ? '<span class="ol-chip-eq">' + rowEq(i, false) + "</span>" : "") + "</button>";
    }
    return '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_pick")) + '</h3><div class="ol-chips">' + chips + "</div>" +
      '<p class="ol-field-hint">' + esc(picked.length === 2 ? L("picked", { a: boundaryName(+picked[0]), b: boundaryName(+picked[1]) }) : L("pick_two")) + "</p></section>" +
      '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_cross")) + '</h3><div class="ol-formula"><span class="ol-sym">(</span>' +
      input(s.id, "crossx", L("a_cross", { n: 1 }), "x1") + '<span class="ol-sym">|</span>' + input(s.id, "crossy", L("a_cross", { n: 2 }), "x2") + '<span class="ol-sym">)</span></div></section>';
  }

  function optimumStep(s) {
    return '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_optimum")) + '</h3><div class="ol-formula"><span class="ol-sym">x* = (</span>' +
      input(s.id, "x", L("a_opt", { n: 1 }), "x1") + '<span class="ol-sym">|</span>' + input(s.id, "y", L("a_opt", { n: 2 }), "x2") + '<span class="ol-sym">)</span></div></section>' +
      '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_value")) + '</h3><div class="ol-formula"><span class="ol-sym">F =</span>' + input(s.id, "z", L("a_z"), "", true) + "</div></section>";
  }

  function sensStep(s) {
    var keys = s.questions.map(function (q) { return q.key; }), shadow = keys.indexOf("shadow0") >= 0;
    var o = S.answers.optimum || {}, h = "";
    if (o.x || o.y) h += '<p class="ol-ref">' + esc(L("your_opt")) + " <b>" + pt(num(o.x), num(o.y)) + "</b></p>";
    h += '<table class="ol-sens"><thead><tr><th>' + esc(T("col_constraint")) + "</th><th>" + esc(T("col_slack")) + "</th>" + (shadow ? "<th>" + esc(T("col_shadow")) + "</th>" : "") + "</tr></thead><tbody>";
    for (var i = 0; i < nRows(); i++) {
      h += '<tr data-group="row' + i + '"><th scope="row">' + rowHead(i) + '<div class="ol-eq-small">' + rowEq(i, true) + "</div></th><td>" + input(s.id, "slack" + i, L("a_slack", { label: label(i) })) + "</td>" +
        (shadow ? "<td>" + input(s.id, "shadow" + i, L("a_shadow", { label: label(i) }), "", false, true) + "</td>" : "") + "</tr>";
    }
    h += "</tbody></table>";
    if (keys.indexOf("range0_0") >= 0) {
      h += '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_ranges")) + "</h3>" + [0, 1].map(function (j) {
        return '<div class="ol-formula">' + input(s.id, "range" + j + "_0", L("a_rlo", { n: j + 1 }), "", false, true) + '<span class="ol-sym">≤ c' + (j + 1) + " ≤</span>" +
          input(s.id, "range" + j + "_1", L("a_rhi", { n: j + 1 }), "", false, true) + "</div>";
      }).join("") + '<p class="ol-field-hint">' + esc(L("inf_hint")) + "</p></section>";
    }
    if (keys.indexOf("idelta") >= 0) {
      h += '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_idelta", { label: label(0) })) + '</h3><div class="ol-formula"><span class="ol-sym">ΔF =</span>' +
        input(s.id, "idelta", L("a_idelta", { label: label(0) }), "", false, true) + "</div></section>";
    }
    return h;
  }

  function interpretStep(s) {
    return [["meaning", [["max", L("meaning_max")], ["min", L("meaning_min")]]], ["round", [["yes", L("round_yes")], ["no", L("round_no")]]]].map(function (q) {
      var mark = markOf(s.id, q[0]);
      return '<fieldset class="ol-group ol-mc' + mark + '"><legend class="ol-group-title">' + esc(L("q_" + q[0])) + "</legend>" + q[1].map(function (it) {
        var id = "q-" + q[0] + "-" + it[0];
        return '<label class="ol-option" for="' + id + '"><input type="radio" id="' + id + '" name="q-' + q[0] + '" value="' + it[0] + '" data-q="' + q[0] + '"' + (val(s.id, q[0]) === it[0] ? " checked" : "") + "><span>" + esc(it[1]) + "</span></label>";
      }).join("") + "</fieldset>";
    }).join("");
  }

  function colName(j) { return j < 2 ? "x" + (j + 1) : "s" + (j - 1); }
  function simplexStep(s) {
    var a = ans(s.id), h = '<p class="ol-field-hint">' + esc(L("pick_hint")) + "</p>";
    var shown = Math.min(S.tableaus, s.tableaus.length);
    for (var i = 0; i < shown; i++) {
      var t = s.tableaus[i], col = Number(a["enter" + i]) - 1, row = Number(a["leave" + i]);
      var lockT = locked("enter" + i);
      h += '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("tableau_n", { n: i + 1 })) + '</h3><div class="ol-scroll"><table class="ol-tableau"><thead><tr><th></th>' +
        t[0].map(function (_, j) {
          if (j === t[0].length - 1) return '<th class="ol-rs">' + esc(L("rhs")) + "</th>" + (exam() ? "" : '<th class="ol-q">Q</th>');
          return '<th><button type="button" class="ol-tb' + (col === j ? " is-on" : "") + '" id="ol-tc-' + i + "-" + j + '" data-act="pivot" data-key="enter' + i + '" data-value="' + (j + 1) + '" aria-pressed="' + (col === j) + '"' + (lockT ? " disabled" : "") + ">" + colName(j) + "</button></th>";
        }).join("") + "</tr></thead><tbody>" +
        t.map(function (r, k) {
          return "<tr><th>" + (k === 0 ? '<span class="ol-tb is-static">F</span>' : '<button type="button" class="ol-tb' + (row === k ? " is-on" : "") + '" id="ol-tr-' + i + "-" + k + '" data-act="pivot" data-key="leave' + i + '" data-value="' + k + '" aria-pressed="' + (row === k) + '"' + (lockT ? " disabled" : "") + ">" + esc(label(k - 1)) + "</button>") + "</th>" +
            r.map(function (v, j) {
              var c = (j === col ? " is-col" : "") + (k === row && k > 0 ? " is-row" : "") + (j === col && k === row && k > 0 ? " is-pivot" : "");
              return '<td class="' + c + '">' + esc(fmt(v)) + "</td>";
            }).join("") + (exam() ? "" : '<td class="ol-q' + (k === row && k > 0 ? " is-row" : "") + '">' + (k > 0 && col >= 0 ? (r[col] > 1e-12 ? esc(fmt(r[r.length - 1] / r[col])) : "–") : "") + "</td>") + "</tr>";
        }).join("") + "</tbody></table></div>" +
        '<div class="ol-pivot-picked">' + esc(L("pivot_col")) + ": <b class=\"" + markOf(s.id, "enter" + i).trim() + '">' + (col >= 0 ? colName(col) : "–") + "</b> · " + esc(L("pivot_row")) + ': <b class="' + markOf(s.id, "leave" + i).trim() + '">' + (row > 0 ? esc(label(row - 1)) : "–") + "</b></div>" +
        '<div class="ol-formula"><span class="ol-sym">' + esc(L("pivot_el")) + "</span>" + input(s.id, "pivot" + i, L("a_pivot", { n: i + 1 })) +
        '<span class="ol-sym">' + esc(L("next_z")) + "</span>" + input(s.id, "nextz" + i, L("a_nextz", { n: i + 1 }), "", false, true) + "</div></section>";
    }
    if (shown < s.tableaus.length) {
      var ready = tableauReady(shown - 1);
      h += '<button type="button" class="btn os-btn" id="ol-next-tableau" data-act="tableau"' + (ready ? "" : " disabled") + ">" + esc(L("show_next_tableau")) + "</button>" +
        '<p class="ol-field-hint"' + (ready ? " hidden" : "") + ">" + esc(L("next_tableau_hint")) + "</p>";
    }
    return h;
  }

  function feedbackHTML(s) {
    var fb = S.feedback[s.id];
    if (exam() || !fb || fb.stale) return "";
    var keys = Object.keys(fb.checks), right = keys.filter(function (k) { return fb.checks[k]; }).length;
    var missing = keys.filter(function (k) { return !fb.checks[k] && String(val(s.id, k)).trim() === ""; }).length;
    if (fb.correct) return '<div class="ol-banner is-ok" role="status"><b>' + esc(L("fb_correct")) + "</b> " + esc(L("points_of", { got: fmt(fb.points), max: fmt(fb.max) })) + "</div>";
    var detail = [right < keys.length - missing ? L("fb_marked") : "", missing ? L("fb_missing", { n: missing }) : ""].filter(Boolean).join(" ");
    return '<div class="ol-banner is-partial" role="status"><div><b>' + esc(L("fb_partial", { right: right, total: keys.length })) + "</b> " + esc(detail) +
      '<div class="ol-banner-sub">' + esc(L("points_of", { got: fmt(fb.points), max: fmt(fb.max) })) + "</div></div>" +
      (S.hints[s.id] ? "" : '<button type="button" class="btn os-btn" id="ol-hint-2" data-act="hint">' + esc(L("get_hint")) + "</button>") + "</div>";
  }
  function hintHTML(s) {
    var h = S.hints[s.id];
    if (!h || exam()) return "";
    if (!h.level) return '<div class="ol-note ol-hintbox" role="status"><div class="ol-note-title">' + esc(L("hint")) + "</div><p>" + esc(L("hint_none")) + "</p></div>";
    return '<div class="ol-note ol-hintbox" role="status"><div class="ol-note-title">' + esc(L("hint_level", { n: h.level })) + "</div><ul>" +
      h.ids.map(function (id) { return "<li>" + L("hint_" + id) + "</li>"; }).join("") + "</ul>" +
      (h.more ? '<button type="button" class="ol-link-btn" id="ol-more-hints" data-act="hint">' + esc(L("more_hints")) + "</button>" : "") + "</div>";
  }
  function solutionHTML(s) {
    var lines = S.solutions[s.id];
    if (!lines || exam()) return "";
    return '<div class="ol-note ol-solbox"><div class="ol-note-title">' + esc(L("sol_title")) + '</div><ul class="ol-sol">' +
      lines.map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("") + "</ul></div>";
  }

  // ------------------------------------------------------------------ left column: example coach and help
  function coachHTML(s) {
    var calc = s.id === "simplex" ? simplexCalc(s) : L("tut_calc_" + s.id);
    return '<section class="os-card ol-panel ol-coachcard" id="ol-coach"><header class="ol-panel-head"><span class="ol-badge">' + icon("route") + "</span><h2>" + esc(L("coach_title")) + "</h2>" +
      '<span class="ol-head-note">' + esc(stepShort(s)) + "</span></header><div class=\"ol-panel-body ol-coach\">" +
      (S.step === 0 ? '<p class="ol-coach-intro">' + esc(L("coach_intro")) + "</p>" : "") +
      "<p>" + esc(L("tut_coach_" + s.id)) + "</p>" +
      (calc ? '<details class="ol-calc-toggle"><summary>' + esc(L("coach_calc")) + '</summary><pre class="ol-calc">' + esc(calc) + "</pre></details>" : "") +
      '<button type="button" class="btn os-btn" id="ol-fill" data-act="fill">' + esc(L("coach_fill")) + "</button></div></section>";
  }
  function helpCardHTML(s) {
    return '<details class="os-card ol-panel ol-helpcard" id="ol-helpcard"' + (S.help ? " open" : "") + '><summary class="ol-panel-head"><span class="ol-badge is-help">?</span><h2>' + esc(L("help_title")) + "</h2>" +
      '<span class="ol-head-note">' + esc(stepShort(s)) + '</span></summary><div class="ol-panel-body ol-help-panel">' + L("help_" + s.id) + "</div></details>";
  }
  function simplexCalc(s) {
    var demo = S.ex.tutorial.answers.simplex || {}, out = [];
    s.tableaus.forEach(function (t, i) {
      var col = Number(demo["enter" + i]) - 1, row = Number(demo["leave" + i]);
      out.push(L("tableau_n", { n: i + 1 }) + ": " + L("pivot_col") + " " + colName(col) + " (" + fmt(t[0][col]) + ")");
      t.slice(1).forEach(function (r, k) {
        out.push("  " + label(k) + ": " + (r[col] > 0 ? fmt(r[r.length - 1]) + " ÷ " + fmt(r[col]) + " = " + fmt(r[r.length - 1] / r[col]) : "—"));
      });
      out.push("  → " + L("pivot_row") + " " + label(row - 1) + ", " + L("pivot_el") + " " + fmt(t[row][col]) + ", " + L("next_z") + " " + fmt(Number(demo["nextz" + i])));
    });
    return out.join("\n");
  }

  // ------------------------------------------------------------------ graph card
  function graphCardHTML() {
    var s = cur(), tools = "";
    if (s.id === "lines" || s.id === "region") {
      tools = '<div class="ol-chips is-compact" role="group" aria-label="' + esc(L("active_line")) + '">' + S.ex.colors.map(function (c, i) {
        return '<button type="button" class="ol-chip' + (i === S.activeRow ? " is-on" : "") + '" id="ol-gr-' + i + '" data-act="row" data-row="' + i + '" aria-pressed="' + (i === S.activeRow) + '">' + swatch(c) + esc(label(i)) + "</button>";
      }).join("") + "</div>";
    } else if (s.id === "optimum") {
      var m = model();
      if (isNum(m.c[0]) && isNum(m.c[1])) {
        tools = '<label class="ol-level"><span>F =</span><input class="ol-in" id="ol-level" data-act="level" inputmode="decimal" autocomplete="off" value="' + esc(fmtInput(levelValue())) + '" aria-label="' + esc(L("a_level")) + '"></label>';
      }
    }
    return '<section class="os-card ol-panel ol-graph"><header class="ol-panel-head">' + sidebarButton() + "<h2>" + esc(L("graph_title")) + "</h2>" + tools + "</header>" +
      '<div class="ol-plot-wrap"><div class="ol-plot" id="ol-plot"></div></div><p class="ol-graph-note" id="ol-graph-note">' + esc(graphNote(s)) + "</p></section>";
  }
  function graphNote(s) {
    if (s.id === "model") return L("gn_model");
    if (s.id !== "lines" && steps().some(function (x) { return x.id === "lines"; }) && learnerLines().some(function (l) { return !l; })) return L("gn_need_lines");
    if (s.id === "lines") return L("gn_lines", { label: label(S.activeRow) });
    if (s.id === "region") return L("gn_region");
    if (s.id === "intersection") return L("gn_intersection");
    if (s.id === "optimum") return L("gn_optimum");
    return L("gn_after");
  }

  function levelValue() {
    var m = model(), o = S.answers.optimum || {}, x = num(o.x), y = num(o.y);
    if (S.level !== null) return S.level;
    if (isNum(x) && isNum(y)) return m.c[0] * x + m.c[1] * y;
    var e = S.ex.extent;
    return Math.round((m.c[0] * e[0] + m.c[1] * e[1]) * 0.3 * 100) / 100;
  }

  // ------------------------------------------------------------------ graph drawing (SVG, same colours as the matplotlib graph)
  var G = null;   // geometry of the current drawing, used by the pointer handlers
  // touch screens: the handles get an invisible ring of about a fingertip (44 px), the drawing stays the same
  var COARSE = !!(window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
  function halo(cx, cy, k) { return COARSE ? '<circle cx="' + cx + '" cy="' + cy + '" r="' + 22 * k + '" fill="transparent"/>' : ""; }

  function niceStep(range) {
    var raw = range / 6, p = Math.pow(10, Math.floor(Math.log10(raw)));
    var m = [1, 2, 2.5, 5, 10].find(function (k) { return k * p >= raw; });
    return m * p;
  }
  function clipToBox(a, b, ex, ey) {
    var pts = [];
    if (Math.abs(a[1]) > 1e-12) { pts.push([0, b / a[1]]); pts.push([ex, (b - a[0] * ex) / a[1]]); }
    if (Math.abs(a[0]) > 1e-12) { pts.push([b / a[0], 0]); pts.push([(b - a[1] * ey) / a[0], ey]); }
    pts = pts.filter(function (p) { return isFinite(p[0]) && isFinite(p[1]) && p[0] >= -1e-9 && p[0] <= ex + 1e-9 && p[1] >= -1e-9 && p[1] <= ey + 1e-9; });
    if (pts.length < 2) return null;
    var q = pts.find(function (p) { return Math.hypot(p[0] - pts[0][0], p[1] - pts[0][1]) > 1e-9; });
    return q ? [pts[0], q] : null;
  }
  function clipPoly(poly, g) {
    var out = [];
    for (var k = 0; k < poly.length; k++) {
      var u = poly[k], v = poly[(k + 1) % poly.length], gu = g(u), gv = g(v);
      if (gu >= -1e-9) out.push(u);
      if ((gu >= -1e-9) !== (gv >= -1e-9)) { var t = gu / (gu - gv); out.push([u[0] + t * (v[0] - u[0]), u[1] + t * (v[1] - u[1])]); }
    }
    return out;
  }

  // lines as the learner drew them (or the model, if the exercise has no drawing step)
  function learnerLines() {
    var a = S.answers.lines || {}, drawn = steps().some(function (s) { return s.id === "lines"; }), m = model(), out = [];
    for (var i = 0; i < nRows(); i++) {
      if (drawn) {
        out.push(lineFromCuts(a["ax" + i + "_0"], a["ax" + i + "_1"]));
      } else {
        var r = m.rows[i];
        out.push(isNum(r.a[0]) && isNum(r.a[1]) && isNum(r.b) ? { a: r.a, b: r.b } : null);
      }
    }
    return out;
  }
  // the line through (p | 0) and (0 | q); “–” means parallel to that axis
  function lineFromCuts(p, q) {
    var np = isNone(p), nq = isNone(q), x = num(p), y = num(q);
    if (!np && !nq && isNum(x) && isNum(y)) {
      if (Math.abs(x) < 1e-12 && Math.abs(y) < 1e-12) return null;
      if (Math.abs(x) < 1e-12) return { a: [1, 0], b: 0 };
      if (Math.abs(y) < 1e-12) return { a: [0, 1], b: 0 };
      return { a: [y, x], b: x * y };
    }
    if (!np && isNum(x) && nq) return { a: [1, 0], b: x };
    if (np && !nq && isNum(y)) return { a: [0, 1], b: y };
    return null;
  }
  // the part of the line x_axis = v inside a convex polygon (for the MILP bars)
  function polySpan(poly, axis, v) {
    var lo = Infinity, hi = -Infinity, o = 1 - axis;
    for (var i = 0; i < poly.length; i++) {
      var a = poly[i], b = poly[(i + 1) % poly.length], da = a[axis] - v, db = b[axis] - v;
      if (Math.abs(da) < 1e-9) { lo = Math.min(lo, a[o]); hi = Math.max(hi, a[o]); }
      if (da * db < 0) { var w = a[o] + da / (da - db) * (b[o] - a[o]); lo = Math.min(lo, w); hi = Math.max(hi, w); }
    }
    return lo <= hi ? [lo, hi] : null;
  }
  // the region from the chosen sides: a polygon, or a segment for an equation
  function region(lines, ex, ey) {
    var sides = S.answers.region || {}, poly = [[0, 0], [ex, 0], [ex, ey], [0, ey]], any = false, eqLine = null;
    lines.forEach(function (ln, i) {
      var side = sides["side" + i];
      if (!ln || !side) return;
      var tp = S.ex.testPoints[i], f = function (x) { return ln.a[0] * x[0] + ln.a[1] * x[1] - ln.b; }, s0 = f(tp);
      if (side === "line") { poly = clipPoly(poly, function (x) { return f(x); }); poly = clipPoly(poly, function (x) { return -f(x); }); eqLine = true; any = true; return; }
      if (Math.abs(s0) < 1e-12) return;
      var sg = (side === "in" ? 1 : -1) * Math.sign(s0);
      poly = clipPoly(poly, function (x) { return sg * f(x); });   // keep the side where sign(f) == sg
      any = true;
    });
    return any ? { poly: poly, line: eqLine } : null;
  }
  function inPoly(p, poly) {
    var inside = false;
    for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      var a = poly[i], b = poly[j];
      if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1] + 1e-300) + a[0]) inside = !inside;
    }
    return inside;
  }
  function onBoundary(p, poly) {
    for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      var a = poly[i], b = poly[j], dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy);
      if (len < 1e-12) continue;
      var t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (len * len);
      if (t >= -1e-9 && t <= 1 + 1e-9 && Math.abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / len < 1e-6 * Math.max(1, len)) return true;
    }
    return false;
  }

  function drawGraph() {
    var host = document.getElementById("ol-plot");
    if (!host || !S.ex) return;
    var w = host.clientWidth, h = host.clientHeight;
    if (w < 50 || h < 50) return;
    var fs = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16, k = fs / 16;
    var ex = S.ex.extent[0], ey = S.ex.extent[1];
    var L0 = 44 * k, R0 = 18 * k, T0 = 16 * k, B0 = 34 * k;
    var pw = w - L0 - R0, ph = h - T0 - B0;
    var X = function (x) { return L0 + x / ex * pw; }, Y = function (y) { return T0 + ph - y / ey * ph; };
    G = { X: X, Y: Y, ex: ex, ey: ey, L0: L0, T0: T0, pw: pw, ph: ph, k: k };
    var s = cur(), sid = s.id, m = model(), o = [];
    var lines = sid === "model" ? [] : learnerLines();

    // grid, axes, ticks
    var sx = niceStep(ex), sy = niceStep(ey);
    o.push('<g class="ol-grid">');
    for (var gx = sx; gx <= ex + 1e-9; gx += sx) o.push('<line x1="' + X(gx) + '" y1="' + Y(0) + '" x2="' + X(gx) + '" y2="' + Y(ey) + '"/>');
    for (var gy = sy; gy <= ey + 1e-9; gy += sy) o.push('<line x1="' + X(0) + '" y1="' + Y(gy) + '" x2="' + X(ex) + '" y2="' + Y(gy) + '"/>');
    o.push("</g>");
    o.push('<g class="ol-ticks" font-size="' + 11.5 * k + '">');
    for (var tx = 0; tx <= ex + 1e-9; tx += sx) o.push('<text x="' + X(tx) + '" y="' + (Y(0) + 15 * k) + '" text-anchor="middle">' + fmt(tx) + "</text>");
    for (var ty = sy; ty <= ey + 1e-9; ty += sy) o.push('<text x="' + (X(0) - 6 * k) + '" y="' + (Y(ty) + 4 * k) + '" text-anchor="end">' + fmt(ty) + "</text>");
    o.push("</g>");
    o.push('<defs><clipPath id="ol-clip"><rect x="' + X(0) + '" y="' + Y(ey) + '" width="' + pw + '" height="' + ph + '"/></clipPath></defs>');
    o.push('<g clip-path="url(#ol-clip)">');

    // integer lattice
    var it = ints(m.kind), spacing = Math.min(pw / ex, ph / ey);
    var reg = sid !== "model" && sid !== "lines" ? region(lines, ex, ey) : null;
    if ((it[0] || it[1]) && spacing >= 5) {
      if (it[0] && it[1]) {
        for (var ix = 0; ix <= ex; ix++) for (var iy = 0; iy <= ey; iy++) {
          var inside = reg && reg.poly.length > 2 && (inPoly([ix, iy], reg.poly) || onBoundary([ix, iy], reg.poly));
          o.push('<circle cx="' + X(ix) + '" cy="' + Y(iy) + '" r="' + (inside ? 2.6 : 1.3) * k + '" fill="' + (inside ? "#5f5f5f" : "#c4c9ce") + '"/>');
        }
      } else {
        var axis = it[0] ? 0 : 1;
        for (var v = 0; v <= (axis ? ey : ex); v++) {
          o.push(axis === 0 ? '<line class="ol-lattice" x1="' + X(v) + '" y1="' + Y(0) + '" x2="' + X(v) + '" y2="' + Y(ey) + '"/>' : '<line class="ol-lattice" x1="' + X(0) + '" y1="' + Y(v) + '" x2="' + X(ex) + '" y2="' + Y(v) + '"/>');
          var span = reg && reg.poly.length > 2 ? polySpan(reg.poly, axis, v) : null;
          if (span) {
            o.push(axis === 0 ? '<line class="ol-bar" x1="' + X(v) + '" y1="' + Y(span[0]) + '" x2="' + X(v) + '" y2="' + Y(span[1]) + '" stroke-width="' + 5 * k + '"/>'
              : '<line class="ol-bar" x1="' + X(span[0]) + '" y1="' + Y(v) + '" x2="' + X(span[1]) + '" y2="' + Y(v) + '" stroke-width="' + 5 * k + '"/>');
          }
        }
      }
    }
    // feasible region (from the learner's sides)
    if (reg && reg.poly.length > 1) {
      var pts = reg.poly.map(function (p) { return X(p[0]) + "," + Y(p[1]); }).join(" ");
      if (reg.line || reg.poly.length < 3) o.push('<polyline points="' + pts + '" fill="none" stroke="' + GREY + '" stroke-opacity=".55" stroke-width="' + 7 * k + '"/>');
      else if (!(it[0] && it[1])) o.push('<polygon points="' + pts + '" fill="' + GREY + '" fill-opacity="' + (it[0] || it[1] ? 0.07 : 0.32) + '"/>');
      else o.push('<polygon points="' + pts + '" fill="' + GREY + '" fill-opacity=".1"/>');
    }
    // constraint lines
    var picks = sid === "intersection" ? [val("intersection", "boundary1"), val("intersection", "boundary2")] : [];
    lines.forEach(function (ln, i) {
      if (!ln) return;
      var seg2 = clipToBox(ln.a, ln.b, ex, ey);
      if (!seg2) return;
      var strong = ((sid === "lines" || sid === "region") && i === S.activeRow) || picks.indexOf(String(i)) >= 0;
      o.push('<line x1="' + X(seg2[0][0]) + '" y1="' + Y(seg2[0][1]) + '" x2="' + X(seg2[1][0]) + '" y2="' + Y(seg2[1][1]) + '" stroke="' + color(i) + '" stroke-width="' + (strong ? 3.4 : 2.2) * k + '"' + (i >= 5 ? ' stroke-dasharray="' + 8 * k + " " + 3 * k + " " + 2 * k + " " + 3 * k + '"' : "") + "/>");
      o.push('<line class="ol-hit" data-row="' + i + '" x1="' + X(seg2[0][0]) + '" y1="' + Y(seg2[0][1]) + '" x2="' + X(seg2[1][0]) + '" y2="' + Y(seg2[1][1]) + '" stroke-width="' + 16 * k + '"/>');
      var end = seg2[0][0] > seg2[1][0] || (seg2[0][0] === seg2[1][0] && seg2[0][1] > seg2[1][1]) ? seg2[0] : seg2[1];
      var lx = Math.min(X(end[0]) - 4 * k, X(ex) - 4 * k), ly = Math.max(Y(end[1]) - 6 * k, Y(ey) + 12 * k);
      o.push('<text class="ol-line-label" x="' + lx + '" y="' + ly + '" text-anchor="end" fill="' + color(i) + '" font-size="' + 12 * k + '">' + esc(label(i)) + "</text>");
    });
    // the axes as boundaries in the intersection step
    picks.forEach(function (p) {
      if (p === String(nRows())) o.push('<line x1="' + X(0) + '" y1="' + Y(0) + '" x2="' + X(0) + '" y2="' + Y(ey) + '" stroke="' + INK + '" stroke-width="' + 4 * k + '"/>');
      if (p === String(nRows() + 1)) o.push('<line x1="' + X(0) + '" y1="' + Y(0) + '" x2="' + X(ex) + '" y2="' + Y(0) + '" stroke="' + INK + '" stroke-width="' + 4 * k + '"/>');
    });
    // objective line
    var showObj = ["optimum", "sensitivity", "interpret", "simplex"].indexOf(sid) >= 0 && isNum(m.c[0]) && isNum(m.c[1]) && (Math.abs(m.c[0]) + Math.abs(m.c[1]) > 0);
    if (showObj) {
      var segO = clipToBox(m.c, levelValue(), ex, ey);
      if (segO) {
        o.push('<line x1="' + X(segO[0][0]) + '" y1="' + Y(segO[0][1]) + '" x2="' + X(segO[1][0]) + '" y2="' + Y(segO[1][1]) + '" stroke="' + GREEN + '" stroke-width="' + 2.4 * k + '" stroke-dasharray="' + 9 * k + " " + 6 * k + '"/>');
        if (sid === "optimum") {
          o.push('<line class="ol-drag-line" data-drag="objective" x1="' + X(segO[0][0]) + '" y1="' + Y(segO[0][1]) + '" x2="' + X(segO[1][0]) + '" y2="' + Y(segO[1][1]) + '" stroke-width="' + 26 * k + '"/>');
          var mx = (segO[0][0] + segO[1][0]) / 2, my = (segO[0][1] + segO[1][1]) / 2;
          o.push('<g class="ol-grip" data-drag="objective">' + halo(X(mx), Y(my), k) + '<circle cx="' + X(mx) + '" cy="' + Y(my) + '" r="' + 11 * k + '" fill="#fff" stroke="' + GREEN + '" stroke-width="' + 2.4 * k + '"/>' +
            '<path d="M' + X(mx) + " " + (Y(my) - 5.5 * k) + " l" + 3.5 * k + " " + 3.5 * k + " h" + -7 * k + "z M" + X(mx) + " " + (Y(my) + 5.5 * k) + " l" + 3.5 * k + " " + -3.5 * k + " h" + -7 * k + 'z" fill="' + GREEN + '"/></g>');
        }
      }
    }
    o.push("</g>");
    // axes on top
    o.push('<g class="ol-axes"><line x1="' + X(0) + '" y1="' + Y(0) + '" x2="' + (X(ex) + 10 * k) + '" y2="' + Y(0) + '"/><line x1="' + X(0) + '" y1="' + Y(0) + '" x2="' + X(0) + '" y2="' + (Y(ey) - 10 * k) + '"/>' +
      '<path d="M' + (X(ex) + 12 * k) + " " + Y(0) + " l" + -8 * k + " " + -4 * k + " v" + 8 * k + 'z" /><path d="M' + X(0) + " " + (Y(ey) - 12 * k) + " l" + -4 * k + " " + 8 * k + " h" + 8 * k + 'z"/></g>');
    o.push('<text class="ol-axis-label" x="' + (X(ex) + 4 * k) + '" y="' + (Y(0) + 30 * k) + '" text-anchor="end" font-size="' + 12.5 * k + '">x1</text>');
    o.push('<text class="ol-axis-label" x="' + (X(0) + 8 * k) + '" y="' + (Y(ey) + 2 * k) + '" font-size="' + 12.5 * k + '">x2</text>');

    // test points of the region step
    if (sid === "region") {
      S.ex.points.forEach(function (p, n) {
        var chosen = val("region", "p" + n);
        o.push('<g class="ol-testpt"><circle cx="' + X(p[0]) + '" cy="' + Y(p[1]) + '" r="' + 5 * k + '" fill="' + (chosen === "yes" ? INK : chosen === "no" ? "#fff" : INK) + '" stroke="' + INK + '" stroke-width="' + 1.8 * k + '"/>' +
          '<text x="' + (X(p[0]) + 8 * k) + '" y="' + (Y(p[1]) - 7 * k) + '" font-size="' + 12 * k + '">P' + (n + 1) + "</text></g>");
      });
      var tp = S.ex.testPoints[S.activeRow];
      if (tp && (tp[0] || tp[1])) o.push('<circle cx="' + X(tp[0]) + '" cy="' + Y(tp[1]) + '" r="' + 6 * k + '" fill="none" stroke="' + color(S.activeRow) + '" stroke-width="' + 2 * k + '" stroke-dasharray="' + 3 * k + '"/>');
    }
    // intersection point entered by the learner
    if (sid === "intersection") {
      var cx = num(val("intersection", "crossx")), cy = num(val("intersection", "crossy"));
      if (isNum(cx) && isNum(cy)) o.push('<circle cx="' + X(cx) + '" cy="' + Y(cy) + '" r="' + 6 * k + '" fill="#fff" stroke="' + RED + '" stroke-width="' + 2.4 * k + '"/>');
    }
    // the learner's optimum
    if (["optimum", "sensitivity", "interpret", "simplex"].indexOf(sid) >= 0) {
      var ox = num(val("optimum", "x")), oy = num(val("optimum", "y"));
      if (isNum(ox) && isNum(oy)) {
        o.push('<circle class="' + (sid === "optimum" ? "ol-grip" : "") + '" data-drag="' + (sid === "optimum" ? "point" : "") + '" cx="' + X(ox) + '" cy="' + Y(oy) + '" r="' + 6.5 * k + '" fill="' + RED + '" stroke="#fff" stroke-width="' + 2 * k + '"/>');
        if (sid === "optimum" && COARSE) o.push('<g class="ol-grip" data-drag="point">' + halo(X(ox), Y(oy), k) + "</g>");
        o.push('<text class="ol-opt-label" x="' + (X(ox) + 10 * k) + '" y="' + (Y(oy) - 9 * k) + '" fill="' + RED + '" font-size="' + 12.5 * k + '">' + esc(pt(ox, oy)) + "</text>");
      }
    }
    // handles of the active line
    if (sid === "lines") {
      var i0 = S.activeRow;
      [0, 1].forEach(function (j) {
        var v = val("lines", "ax" + i0 + "_" + j);
        if (isNone(v)) return;
        var n = num(v), set = isNum(n), lim = j ? ey : ex, pos = Math.max(0, Math.min(lim, set ? n : lim * 0.6));
        var cx = j ? X(0) : X(pos), cy = j ? Y(pos) : Y(0), out = set && (n > lim || n < 0);
        o.push('<g class="ol-grip ' + (j ? "is-v" : "is-h") + (set ? "" : " is-unset") + '" data-drag="' + j + '">' + halo(cx, cy, k) + '<circle cx="' + cx + '" cy="' + cy + '" r="' + 9 * k + '" fill="#fff" stroke="' + color(i0) + '" stroke-width="' + 3 * k + '"' + (set ? "" : ' stroke-dasharray="' + 3 * k + " " + 2.5 * k + '"') + "/></g>");
        if (set) {
          var anchor = j ? "start" : out || pos > lim * 0.9 ? "end" : "middle";
          o.push('<text class="ol-cut-label" x="' + (j ? cx + 13 * k : anchor === "end" ? cx + 9 * k : cx) + '" y="' + (j ? (out || pos > lim * 0.9 ? cy + 18 * k : cy + 4 * k) : cy - 13 * k) + '" text-anchor="' + anchor + '" font-size="' + 11.5 * k + '" fill="' + color(i0) + '">' + esc(fmt(n)) + (out ? (j ? " ↑" : " →") : "") + "</text>");
        }
      });
    }
    host.innerHTML = '<svg class="ol-svg" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + esc(L("graph_aria")) + '">' + o.join("") + '<g id="ol-tip"></g></svg>';
  }

  function toData(ev) {
    var svg = document.querySelector("#ol-plot svg"), r = svg.getBoundingClientRect();
    var x = (ev.clientX - r.left - G.L0) / G.pw * G.ex, y = (G.T0 + G.ph - (ev.clientY - r.top)) / G.ph * G.ey;
    return [Math.max(0, Math.min(G.ex, x)), Math.max(0, Math.min(G.ey, y))];
  }
  function snap(v, ext) { var st = niceStep(ext) / 20; return Math.round(v / st) * st; }

  var drag = null;
  function onPointerDown(ev) {
    var svg = ev.target.closest && ev.target.closest("#ol-plot svg");
    if (!svg || !G || !S.ex) return;
    var sid = cur().id, t = ev.target.closest("[data-drag]"), hit = ev.target.closest(".ol-hit");
    var host = document.getElementById("ol-plot");   // stays while the SVG inside is redrawn
    if (t && t.getAttribute("data-drag")) {
      drag = t.getAttribute("data-drag");
      host.setPointerCapture(ev.pointerId);
      ev.preventDefault();
      return;
    }
    if (hit && (sid === "lines" || sid === "region")) { setActiveRow(+hit.getAttribute("data-row")); ev.preventDefault(); return; }
    if (sid === "optimum" && ev.pointerType === "touch") { tapStart = { id: ev.pointerId, x: ev.clientX, y: ev.clientY }; return; }   // a swipe scrolls the page
    if (sid === "optimum") { setOptPoint(toData(ev)); drag = "point"; host.setPointerCapture(ev.pointerId); ev.preventDefault(); }
  }
  // touch: a tap sets the optimum; dragging works on the handles, which stop the page from scrolling
  var tapStart = null;
  function onTouchStart(ev) {
    var t = ev.target.closest && ev.target.closest("#ol-plot [data-drag]");
    if (t && t.getAttribute("data-drag") && ev.cancelable) ev.preventDefault();
  }
  function setOptPoint(p) {
    var it = ints(model().kind);
    var x = it[0] ? Math.round(p[0]) : snap(p[0], G.ex), y = it[1] ? Math.round(p[1]) : snap(p[1], G.ey);
    setAnswer("optimum", "x", fmtInput(x));
    setAnswer("optimum", "y", fmtInput(y));
    var m = model();
    S.level = m.c[0] * x + m.c[1] * y;
    syncInputs(["x", "y"]);
    var lv = document.getElementById("ol-level");
    if (lv) lv.value = fmtInput(S.level);
    drawGraph();
  }
  function onPointerMove(ev) {
    if (drag === null || !G) return;
    var p = toData(ev), sid = cur().id;
    if (drag === "objective") {
      var m = model();
      S.level = Math.round((m.c[0] * p[0] + m.c[1] * p[1]) * 100) / 100;
      var lv = document.getElementById("ol-level");
      if (lv) lv.value = fmtInput(S.level);
    } else if (drag === "point") {
      setOptPoint(p);
      return;
    } else if (sid === "lines") {
      var j = +drag, key = "ax" + S.activeRow + "_" + j, v = snap(p[j], j ? G.ey : G.ex);
      setAnswer("lines", key, fmtInput(v));
      syncInputs([key]);
    }
    drawGraph();
  }
  function onPointerUp(ev) {
    if (tapStart && ev.pointerId === tapStart.id) {
      var tap = ev.type === "pointerup" && Math.hypot(ev.clientX - tapStart.x, ev.clientY - tapStart.y) < 10 && G && cur().id === "optimum";
      tapStart = null;
      if (tap) { setOptPoint(toData(ev)); paintStatus(); }
    }
    if (drag === null) return;
    drag = null;
    paintStatus();
    drawGraph();
  }
  function tip(x, y, text) {
    var g = document.getElementById("ol-tip");
    if (!g || !G) return;
    var k = G.k, px = G.X(x) + 14 * k, py = G.Y(y) - 14 * k;
    g.innerHTML = '<rect x="' + (px - 4 * k) + '" y="' + (py - 13 * k) + '" width="' + (text.length * 7 * k + 8 * k) + '" height="' + 18 * k + '" rx="' + 3 * k + '" fill="#fff" stroke="#dee2e6"/><text x="' + px + '" y="' + py + '" font-size="' + 12 * k + '">' + esc(text) + "</text>";
  }

  // ------------------------------------------------------------------ answers
  function related(key) {
    var m;
    if ((m = /^(?:a(\d+)_\d|op(\d+)|b(\d+))$/.exec(key))) { var i = m[1] || m[2] || m[3]; return ["a" + i + "_0", "a" + i + "_1", "op" + i, "b" + i]; }
    if (key === "x" || key === "y") return ["x", "y"];
    if (/^(boundary\d|cross[xy])$/.test(key)) return ["boundary1", "boundary2", "crossx", "crossy"];
    return [key];
  }
  function setAnswer(sid, key, value) {
    ans(sid)[key] = value;
    var fb = S.feedback[sid];
    if (fb) {
      fb.stale = true;
      related(key).forEach(function (k) {
        delete fb.checks[k];
        var el = document.getElementById("q-" + k);
        if (el) el.classList.remove("is-right", "is-wrong", "is-missing");
        var g = document.querySelector('.ol-seg[data-q="' + k + '"]');
        if (g) g.classList.remove("is-right", "is-wrong", "is-missing");
      });
      var banner = root() && root().querySelector(".ol-step-body .ol-banner.is-ok, .ol-step-body .ol-banner.is-partial");
      if (banner) banner.remove();
    }
  }
  function syncInputs(keys) {
    keys.forEach(function (k) { var el = document.getElementById("q-" + k); if (el && document.activeElement !== el) el.value = val(cur().id, k); });
  }
  function paintStatus() {
    var nav = root() && root().querySelector(".ol-stepper");
    if (nav) nav.outerHTML = stepperHTML();
    var side = root() && root().querySelector(".ol-yourmodel .ol-panel-body");
    if (side) side.innerHTML = modelListHTML(model(), true);
  }
  function setActiveRow(i) {
    if (i === S.activeRow) return;
    S.activeRow = i;
    root().querySelectorAll(".ol-pick").forEach(function (r) { r.classList.toggle("is-active", +r.getAttribute("data-row") === i); });
    root().querySelectorAll(".ol-graph .ol-chip").forEach(function (c) { var on = +c.getAttribute("data-row") === i; c.classList.toggle("is-on", on); c.setAttribute("aria-pressed", on); });
    var note = document.getElementById("ol-graph-note");
    if (note) note.textContent = graphNote(cur());
    drawGraph();
  }
  function highlightStory(group) {
    root().querySelectorAll(".ol-story li").forEach(function (li) { li.classList.toggle("is-focus", li.getAttribute("data-focus") === group); });
  }

  // ------------------------------------------------------------------ actions
  function goto(i) {
    if (i < 0 || i >= steps().length) return;
    S.step = i; S.activeRow = 0; S.level = null;
    render();
    var body = root().querySelector(".ol-step-body");
    if (body) body.scrollTop = 0;
  }

  function check() {
    var s = cur();
    if (!filled(s)) { toast(L("fb_empty")); return; }
    busy("check", call("check", { step: s.id, answers: S.answers })).then(function (g) {
      S.feedback[s.id] = g;
      refresh();
      var b = root().querySelector(".ol-banner.is-ok, .ol-banner.is-partial");
      if (b) b.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }, function () {});
  }
  function hint() {
    var s = cur();
    busy("hint", call("hint", { step: s.id, answers: S.answers })).then(function (h) {
      S.hints[s.id] = h;
      refresh();
      var b = root().querySelector(".ol-hintbox");
      if (b) b.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }, function () {});
  }
  function showSolution() {
    var s = cur();
    if (S.solutions[s.id]) { var b0 = root().querySelector(".ol-solbox"); if (b0) b0.scrollIntoView({ block: "nearest", behavior: "smooth" }); return; }
    var go = tutorial() ? Promise.resolve(true) : ask(L("sol_confirm_title"), "<p>" + esc(L("sol_confirm")) + "</p>", L("sol_show"));
    go.then(function (ok) {
      if (!ok) return;
      busy("solution", call("solution", { step: s.id })).then(function (d) {
        S.solutions[s.id] = d.lines;
        refresh();
        var b = root().querySelector(".ol-solbox");
        if (b) b.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }, function () {});
    });
  }
  function fill() {
    var s = cur(), demo = (S.ex.tutorial.answers || {})[s.id] || {};
    Object.keys(demo).forEach(function (k) { setAnswer(s.id, k, lang() === "de" ? String(demo[k]).replace(".", ",") : String(demo[k])); });
    if (s.id === "simplex") S.tableaus = s.tableaus.length;
    if (s.id === "optimum") S.level = null;
    refresh();
  }
  function missingCount() {
    return steps().reduce(function (n, s) { return n + s.questions.length - filled(s); }, 0);
  }
  function finish() {
    var miss = missingCount();
    var text = "<p>" + esc(L(tutorial() ? "finish_tutorial_text" : "submit_text")) + "</p>" + (miss ? '<p class="ol-warn">' + esc(L("submit_missing", { n: miss })) + "</p>" : "");
    ask(L(tutorial() ? "finish_tutorial" : "submit_title"), text, L(tutorial() ? "finish_tutorial" : "submit_btn"), L("keep_working")).then(function (ok) {
      if (!ok) return;
      busy("finish", call("submit", { answers: S.answers })).then(function (r) {
        S.result = r; S.view = "result";
        render();
        window.scrollTo(0, 0);
        var el = root(); if (el) el.scrollTop = 0;
      }, function () {});
    });
  }

  // ------------------------------------------------------------------ evaluation
  function choiceLabel(key, v) {
    if (v === "" || v === undefined) return "–";
    var m;
    if (key === "sense" || key === "meaning") return key === "sense" ? v : L("meaning_" + v);
    if (/^vt\d$/.test(key)) return T(v === "int" ? "integer_short" : "continuous_short");
    if (/^op\d+$/.test(key)) return OP[v] || v;
    if ((m = /^side(\d+)$/.exec(key))) { var tp = S.ex.testPoints[+m[1]]; return v === "in" ? L("side_in", { p: pt(tp[0], tp[1]) }) : L("side_" + v); }
    if (/^p\d+$/.test(key)) return L(v === "yes" ? "feasible_yes" : "feasible_no");
    if (key === "round") return L("round_" + v);
    if (/^boundary\d$/.test(key)) return boundaryName(+v);
    if (/^enter\d+$/.test(key)) return colName(+v - 1);
    if (/^leave\d+$/.test(key)) return label(+v - 1);
    return v;
  }
  function qLabel(key) {
    var m;
    if (key === "sense") return L("a_sense");
    if ((m = /^vt(\d)$/.exec(key))) return L("a_vt", { n: +m[1] + 1 });
    if ((m = /^c(\d)$/.exec(key))) return L("a_c", { n: +m[1] + 1 });
    if ((m = /^a(\d+)_(\d)$/.exec(key))) return L("a_a", { label: label(+m[1]), n: +m[2] + 1 });
    if ((m = /^op(\d+)$/.exec(key))) return L("a_op", { label: label(+m[1]) });
    if ((m = /^b(\d+)$/.exec(key))) return L("a_b", { label: label(+m[1]) });
    if ((m = /^ax(\d+)_(\d)$/.exec(key))) return label(+m[1]) + " · " + L(m[2] === "0" ? "ax_x1" : "ax_x2");
    if ((m = /^side(\d+)$/.exec(key))) return L("a_side", { label: label(+m[1]) });
    if ((m = /^p(\d+)$/.exec(key))) { var p = S.ex.points[+m[1]]; return "P" + (+m[1] + 1) + " " + pt(p[0], p[1]); }
    if (key === "boundary1" || key === "boundary2") return L("a_boundary", { n: key.slice(-1) });
    if (key === "crossx" || key === "crossy") return L("a_cross", { n: key === "crossx" ? 1 : 2 });
    if (key === "x" || key === "y") return L("a_opt", { n: key === "x" ? 1 : 2 });
    if (key === "z") return L("a_z");
    if ((m = /^slack(\d+)$/.exec(key))) return L("a_slack", { label: label(+m[1]) });
    if ((m = /^shadow(\d+)$/.exec(key))) return L("a_shadow", { label: label(+m[1]) });
    if ((m = /^range(\d)_(\d)$/.exec(key))) return L(m[2] === "0" ? "a_rlo" : "a_rhi", { n: +m[1] + 1 });
    if (key === "idelta") return L("a_idelta", { label: label(0) });
    if (key === "meaning" || key === "round") return L("q_" + key);
    if ((m = /^enter(\d+)$/.exec(key))) return L("tableau_n", { n: +m[1] + 1 }) + ": " + L("pivot_col");
    if ((m = /^leave(\d+)$/.exec(key))) return L("tableau_n", { n: +m[1] + 1 }) + ": " + L("pivot_row");
    if ((m = /^pivot(\d+)$/.exec(key))) return L("a_pivot", { n: +m[1] + 1 });
    if ((m = /^nextz(\d+)$/.exec(key))) return L("a_nextz", { n: +m[1] + 1 });
    return key;
  }
  // review rows; the two coordinates of a drawn point form one row
  function reviewRows(s, g) {
    var a = S.answers[s.id] || {};
    return s.questions.map(function (q) {
      return [qLabel(q.key), q.choices ? choiceLabel(q.key, a[q.key]) : (a[q.key] || "–"), !!g.checks[q.key]];
    });
  }

  function resultHTML() {
    var r = S.result, score = r.score, tut = tutorial();
    var ok = r.grades.filter(function (g) { return g.correct; }).length;
    var verdict = tut ? L("res_tut_title") : score >= 99.9 ? L("res_great") : score >= 70 ? L("res_good") : L("res_try");
    var note = tut ? L("res_tut_text") : exam() ? L("res_note_exam") : L("res_note_practice");
    var kpis = '<div class="os-kpis ol-kpis"><div class="os-kpi is-value"><small>' + esc(L("kpi_score")) + "</small><b>" + fmt(score) + ' <span class="ol-of">/ 100</span></b></div>' +
      '<div class="os-kpi"><small>' + esc(L("kpi_steps")) + "</small><b>" + ok + ' <span class="ol-of">/ ' + r.grades.length + "</span></b></div>" +
      (exam() ? "" : '<div class="os-kpi"><small>' + esc(L("kpi_hints")) + "</small><b>" + Object.keys(r.hints).length + '</b></div><div class="os-kpi"><small>' + esc(L("kpi_seen")) + "</small><b>" + r.reveals.length + "</b></div>") + "</div>";
    var items = steps().map(function (s, i) {
      var g = r.grades[i], badges = [];
      if (r.reveals.indexOf(s.id) >= 0) badges.push(L("res_seen"));
      else if (r.hints[s.id]) badges.push(L("res_with_hint"));
      var first = r.first[s.id] && !exam() ? '<p class="ol-muted">' + esc(L("res_first", { got: fmt(r.first[s.id].points), max: fmt(g.max) })) + "</p>" : "";
      var table = '<div class="ol-scroll"><table class="os-table"><thead><tr><th>' + esc(L("res_item")) + "</th><th>" + esc(L("res_your")) + '</th><th class="num">' + esc(L("res_ok")) + "</th></tr></thead><tbody>" +
        reviewRows(s, g).map(function (row) { return "<tr><td>" + esc(row[0]) + "</td><td>" + esc(row[1]) + '</td><td class="num ' + (row[2] ? "ol-good" : "ol-bad") + '">' + (row[2] ? "✓" : "✕") + "</td></tr>"; }).join("") + "</tbody></table></div>";
      var sol = (r.solutions[s.id] || []).map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("");
      return '<details class="ol-review"' + (g.correct ? "" : " open") + '><summary><span class="ol-review-dot ' + (g.correct ? "is-ok" : "is-warn") + '">' + (g.correct ? "✓" : "○") + "</span>" +
        '<span class="ol-review-title">' + esc(stepTitle(s)) + (badges.length ? ' <span class="os-tag">' + esc(badges.join(" · ")) + "</span>" : "") + "</span>" +
        '<span class="ol-review-pts">' + esc(L("points_of", { got: fmt(g.points), max: fmt(g.max) })) + "</span></summary>" +
        '<div class="ol-review-body">' + first + table + '<h4>' + esc(L("sol_title")) + '</h4><ul class="ol-sol">' + sol + "</ul></div></details>";
    }).join("");
    return '<div class="ol-page ol-result"><section class="os-card ol-result-head"><div class="ol-result-text"><span class="os-tag ol-mode is-' + (tut ? "mode_tutorial" : exam() ? "mode_exam" : "mode_practice") + '">' + esc(L(tut ? "mode_tutorial" : exam() ? "mode_exam" : "mode_practice")) + "</span>" +
      "<h1>" + esc(verdict) + "</h1><p>" + esc(S.ex.story.title) + "</p><p class=\"ol-muted\">" + esc(note) + "</p></div>" + kpis + "</section>" +
      '<section class="os-card ol-panel ol-review-list"><header class="ol-panel-head"><h2>' + esc(L("res_steps")) + '</h2></header><div class="ol-panel-body">' + items + "</div></section>" +
      (r.python ? '<section class="os-card ol-panel ol-pycard"><header class="ol-panel-head"><h2>' + esc(L("py_title")) + '</h2><button type="button" class="btn btn-link os-header-action" id="ol-copy-py" data-act="copy-py">' + esc(L("py_copy")) + "</button></header>" +
        '<div class="ol-panel-body"><p class="ol-muted">' + esc(L("py_text")) + '</p><pre class="ol-code" id="ol-py-code">' + esc(r.python) + "</pre></div></section>" : "") +
      '<div class="ol-actions"><button class="btn os-btn os-btn-primary" id="ol-new" data-act="new">' + esc(L(tut ? "res_to_practice" : "res_new")) + "</button>" +
      (S.ex.source === "generated" ? '<button class="btn os-btn" id="ol-again" data-act="again">' + esc(L("res_again")) + "</button>" : "") +
      '<button class="btn os-btn" id="ol-download" data-act="download">' + esc(L("res_download")) + '</button><button class="btn os-btn" id="ol-print" data-act="print">' + esc(L("res_print")) + "</button></div></div>";
  }

  function download() {
    var el = root().querySelector(".ol-result").cloneNode(true);
    el.querySelectorAll("details").forEach(function (d) { d.setAttribute("open", ""); });
    var actions = el.querySelector(".ol-actions");
    if (actions) actions.remove();
    var css = "body{font:15px/1.5 system-ui,sans-serif;color:#1d1f21;max-width:60rem;margin:2rem auto;padding:0 1rem}h1{font-size:1.5rem;margin:.25rem 0}" +
      ".os-kpis{display:flex;gap:.75rem;flex-wrap:wrap;margin:1rem 0}.os-kpi{border:1px solid #dee2e6;border-radius:8px;padding:.4rem .75rem}.os-kpi small{display:block;color:#555}.os-kpi b{font-size:1.3rem}" +
      "table{border-collapse:collapse;width:100%;margin:.5rem 0}td,th{border-bottom:1px solid #dee2e6;padding:.35rem;text-align:left}.num{text-align:right}.ol-good{color:#1f7a1f}.ol-bad{color:#cc0000}" +
      "details{border:1px solid #dee2e6;border-radius:8px;padding:.5rem .75rem;margin:.5rem 0}summary{font-weight:600;display:flex;gap:.5rem}.ol-review-pts{margin-left:auto}.os-tag{font-size:.75rem;border:1px solid #dee2e6;border-radius:.6rem;padding:0 .4rem}.ol-muted{color:#555}";
    var html = '<!doctype html><html lang="' + lang() + '"><head><meta charset="utf-8"><title>OptiSense – ' + esc(L("res_title")) + "</title><style>" + css + "</style></head><body>" + el.innerHTML + "</body></html>";
    var url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
    var a = document.createElement("a");
    a.href = url; a.download = "OptiSense-" + L("res_title").replace(/\s+/g, "-") + ".html";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  // ------------------------------------------------------------------ events
  function onClick(ev) {
    var sum = ev.target.closest && ev.target.closest("details.ol-task > summary");
    if (sum) { S.taskOpen = !sum.parentElement.open; return; }
    var hsum = ev.target.closest && ev.target.closest("details.ol-helpcard > summary");
    if (hsum) { S.help = !hsum.parentElement.open; var hb = document.getElementById("ol-help"); if (hb) { hb.classList.toggle("is-on", S.help); hb.setAttribute("aria-expanded", S.help); } return; }   // remember the learner's choice (the toggle event also fires on render)
    var el = ev.target.closest && ev.target.closest("[data-act]");
    if (!el || !root() || !root().contains(el) || el.disabled) return;
    var act = el.getAttribute("data-act");
    if (S.busy && ["tutorial", "create", "own", "check", "hint", "solution", "finish"].indexOf(act) >= 0) return;
    switch (act) {
      case "tutorial": startWith("tutorial"); break;
      case "create": startWith("create", { options: Object.assign({}, S.opts, { simplex: S.opts.simplex && practiceSimplexOk() }) }); break;
      case "own": startWith("own", { options: Object.assign({}, S.ownOpts, { form: "math", simplex: S.ownOpts.simplex && S.own && S.own.simplex }) }); break;
      case "goto-work": var tab = document.querySelector('.navbar [data-value="work"]'); if (tab) tab.click(); break;
      case "goto": goto(+el.getAttribute("data-step")); break;
      case "prev": goto(S.step - 1); break;
      case "next": goto(S.step + 1); break;
      case "finish": finish(); break;
      case "quit": quit(); break;
      case "help":
        S.help = !S.help || !S.sidebar;
        S.sidebar = true;
        refresh();
        if (S.help) { var hc = document.getElementById("ol-helpcard"); if (hc) hc.scrollIntoView({ block: "nearest", behavior: "smooth" }); }
        break;
      case "none": {
        var nk = el.getAttribute("data-key"), sidN = cur().id;
        setAnswer(sidN, nk, isNone(val(sidN, nk)) ? "" : "–");
        refresh();
        break;
      }
      case "copy-py": {
        var code = document.getElementById("ol-py-code");
        if (code && navigator.clipboard) navigator.clipboard.writeText(code.textContent).then(function () { el.textContent = L("py_copied"); }, function () {});
        break;
      }
      case "sidebar": S.sidebar = !S.sidebar; render(); break;
      case "check": check(); break;
      case "hint": hint(); break;
      case "solution": showSolution(); break;
      case "fill": fill(); break;
      case "row": setActiveRow(+el.getAttribute("data-row")); break;
      case "boundary": {
        var a = ans("intersection"), b = el.getAttribute("data-b"), picked = [a.boundary1, a.boundary2].filter(function (v) { return v !== undefined && v !== ""; });
        if (picked.indexOf(b) >= 0) picked.splice(picked.indexOf(b), 1); else { picked.push(b); if (picked.length > 2) picked.shift(); }
        setAnswer("intersection", "boundary1", picked[0] || "");
        setAnswer("intersection", "boundary2", picked[1] || "");
        refresh();
        break;
      }
      case "pivot": setAnswer("simplex", el.getAttribute("data-key"), el.getAttribute("data-value")); refresh(); break;
      case "tableau": S.tableaus += 1; refresh(); break;
      case "new": S.view = "home"; S.ex = null; render(); window.scrollTo(0, 0); break;
      case "again": startWith("create", { options: Object.assign({}, S.opts, { simplex: S.opts.simplex && practiceSimplexOk() }) }); break;
      case "download": download(); break;
      case "print": root().querySelectorAll("details").forEach(function (d) { d.open = true; }); window.print(); break;
    }
  }

  function onInput(ev) {
    var t = ev.target;
    if (!root() || !root().contains(t)) return;
    if (t.id === "ol-level") {
      var v = num(t.value);
      if (isNum(v)) { S.level = v; drawGraph(); }
      return;
    }
    if (t.type === "radio" && ev.type === "input") return;   // radios are handled on change
    var key = t.getAttribute("data-q") || (t.closest(".ol-seg") && t.closest(".ol-seg").getAttribute("data-q"));
    if (key && S.view === "work") {
      setAnswer(cur().id, key, t.value);
      if (t.type === "radio" && t.closest(".ol-seg")) t.closest(".ol-seg").classList.remove("is-right", "is-wrong", "is-missing");
      if (t.type === "radio" && t.closest(".ol-mc")) t.closest(".ol-mc").classList.remove("is-right", "is-wrong", "is-missing");
      if (t.type === "radio" && t.closest(".ol-seg")) {
        t.closest(".ol-seg").classList.remove("is-empty");
        var capEl = t.closest(".ol-cell") && t.closest(".ol-cell").querySelector(".ol-cap.is-pick");
        if (capEl) { capEl.textContent = capEl.getAttribute("data-base"); capEl.classList.remove("is-pick"); }
      }
      if (/^ax\d+_\d$/.test(key)) { var nb = document.getElementById("ol-none-" + key); if (nb) { var on = isNone(t.value); nb.classList.toggle("is-on", on); nb.setAttribute("aria-pressed", on); } }
      if (cur().id === "simplex" && /^(enter|leave)/.test(key)) { refresh(); return; }
      if (cur().id === "simplex") updateTableauButton();
      if (hasGraph()) drawGraph();
      paintStatusSoon();
    }
  }
  var statusTimer = null;
  function paintStatusSoon() { clearTimeout(statusTimer); statusTimer = setTimeout(paintStatus, 150); }
  function tableauReady(n) {
    var a = S.answers.simplex || {};
    return ["enter", "leave", "pivot", "nextz"].every(function (k) { return String(a[k + n] || "").trim() !== ""; });
  }
  function updateTableauButton() {
    var b = document.getElementById("ol-next-tableau");
    if (!b) return;
    var ready = tableauReady(S.tableaus - 1);
    b.disabled = !ready;
    var hint = b.nextElementSibling;
    if (hint && hint.classList.contains("ol-field-hint")) hint.hidden = ready;
  }

  function onChange(ev) {
    var t = ev.target;
    if (!root() || !root().contains(t) || S.view !== "home") return;
    var group = t.closest("[data-opt]") || t.closest("[data-own-opt]");
    if (!group) return;
    var own = group.hasAttribute("data-own-opt"), key = group.getAttribute(own ? "data-own-opt" : "data-opt"), target = own ? S.ownOpts : S.opts;
    if (key === "mode") target.mode = t.checked ? "exam" : "practice";
    else if (key === "sensitivity" || key === "simplex") target[key] = t.checked;
    else target[key] = t.value;
    render();
  }
  function onToggle(ev) {
    var d = ev.target;
    if (d.matches && d.matches("details[data-more]")) { if (d.getAttribute("data-more") === "own") S.ownMore = d.open; else S.more = d.open; }
  }
  function onFocusIn(ev) {
    if (S.view !== "work" || !root().contains(ev.target)) return;
    var g = ev.target.closest("[data-group]");
    if (g) highlightStory(g.getAttribute("data-group"));
    var row = ev.target.closest(".ol-pick");
    if (row) setActiveRow(+row.getAttribute("data-row"));
  }
  function onKey(ev) {
    if (S.view !== "work" || !root().contains(ev.target)) return;
    if (ev.key === "Enter" && ev.target.classList && ev.target.classList.contains("ol-in") && ev.target.id !== "ol-level") {
      ev.preventDefault();
      var inputs = Array.prototype.slice.call(root().querySelectorAll(".ol-step-body .ol-in"));
      var i = inputs.indexOf(ev.target);
      if (i >= 0 && i < inputs.length - 1) inputs[i + 1].focus(); else if (!exam()) check();
    }
  }

  // ------------------------------------------------------------------ language and lifecycle
  function onLanguage() {
    if (!root()) return;
    if (S.view === "home" || !S.ex) { render(); return; }
    render();
    call("texts").then(function (d) {
      if (!S.ex) return;
      S.ex.story = d.story; S.ex.labels = d.labels; S.ex.names = d.names;
      Object.keys(d.solutions || {}).forEach(function (k) { S.solutions[k] = d.solutions[k]; });
      if (S.result && d.resultSolutions) S.result.solutions = d.resultSolutions;
      refresh();
    }, function () {});
  }

  var resizeTimer = null;
  function onResize() { clearTimeout(resizeTimer); resizeTimer = setTimeout(function () { if (S.view === "work") drawGraph(); }, 120); }

  document.addEventListener("click", onClick);
  document.addEventListener("input", onInput);
  document.addEventListener("change", function (ev) { onChange(ev); if (ev.target.type === "radio" && S.view === "work") onInput(ev); });
  document.addEventListener("toggle", onToggle, true);
  document.addEventListener("focusin", onFocusIn);
  document.addEventListener("keydown", onKey);
  document.addEventListener("pointerdown", onPointerDown);
  document.addEventListener("pointermove", onPointerMove);
  document.addEventListener("pointerup", onPointerUp);
  document.addEventListener("pointercancel", onPointerUp);
  document.addEventListener("touchstart", onTouchStart, { passive: false });
  window.addEventListener("resize", onResize);
  window.addEventListener("beforeunload", function (ev) {
    if (S.view === "work" && steps().some(function (s) { return filled(s) > 0; })) { ev.preventDefault(); ev.returnValue = ""; }
  });

  document.addEventListener("DOMContentLoaded", function () {
    render();
    new MutationObserver(onLanguage).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    // the graph needs its real size: draw again when the tab becomes visible
    document.addEventListener("shown.bs.tab", function () { if (S.view === "work") drawGraph(); });
    if (window.ResizeObserver) new ResizeObserver(onResize).observe(root() || document.body);
  });

  if (window.jQuery) {
    jQuery(document).on("shiny:connected", function () {
      Shiny.addCustomMessageHandler("os-learn", function (msg) {
        var p = pending[msg.id];
        if (!p) return;
        delete pending[msg.id];
        if (msg.ok) p.resolve(msg.data); else p.reject(new Error(msg.error));
      });
      Shiny.addCustomMessageHandler("os-learn-own", function (d) {
        S.own = d;
        if (S.view === "home") render();
      });
    });
  }
})();
