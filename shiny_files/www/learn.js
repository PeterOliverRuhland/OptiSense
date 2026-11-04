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
  // a point; no line break inside it (narrow buttons on phones)
  function pt(x, y) { return "(" + fmt(x) + "\u00a0|\u00a0" + fmt(y) + ")"; }
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
    opts: { difficulty: "easy", form: "text", kind: "LP", mode: "practice", topic: "random" },
    ownOpts: { mode: "practice" },
    more: false, own: null,
    ex: null, step: 0, answers: {}, feedback: {}, hints: {}, solutions: {}, solWay: {}, result: null,
    activeRow: 0, level: null, help: false, sidebar: true, busy: null
  };

  // steps of the exercise; the first one ("task", added in the browser) only shows the task and has no points
  function steps() { return S.ex ? S.ex.steps : []; }
  function graded() { return steps().filter(function (s) { return s.id !== "task"; }); }
  function stepIndex(id) { return steps().findIndex(function (s) { return s.id === id; }); }
  function isModel(sid) { return sid === "objective" || sid === "constraints"; }
  function cur() { return steps()[S.step]; }
  function nRows() { return S.ex ? S.ex.colors.length : 0; }
  function exam() { return S.ex && S.ex.options.mode === "exam"; }
  function tutorial() { return S.ex && S.ex.source === "tutorial"; }
  function textTask() { return S.ex && S.ex.options.form === "text"; }
  // while the model is set up the graph would stay empty: it appears with the lines
  function showsGraph() { return !isModel(cur().id); }
  // LP: the optimal corner is found with the objective line, then calculated; integer tasks pick a point instead
  function hasCorner() { return stepIndex("corner") >= 0; }
  function tapsPoint(sid) { return sid === "optimum" && !hasCorner(); }
  function dragsObjective(sid) { return sid === "corner" || tapsPoint(sid); }
  function picked() {
    var a = S.answers.corner || {};
    return [a.boundary1, a.boundary2].filter(function (v) { return v !== undefined && v !== ""; });
  }
  function ans(sid) { return S.answers[sid] || (S.answers[sid] = {}); }
  function val(sid, key) { var a = S.answers[sid]; return a && a[key] !== undefined ? a[key] : ""; }
  function label(i) { return S.ex.labels[i]; }
  function color(i) { return S.ex.colors[i]; }

  // the model the graph and the step texts use: given, or the learner's own from step 1
  function model() {
    if (S.ex.model) return S.ex.model;
    var a = Object.assign({}, S.answers.objective, S.answers.constraints);
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
  function homeHTML() {
    var o = S.opts, oo = S.ownOpts;
    var diff = seg("o-difficulty", [["easy", L("diff_easy")], ["medium", L("diff_medium")]], o.difficulty, 'data-opt="difficulty" aria-label="' + esc(L("opt_difficulty")) + '"');
    var form = seg("o-form", [["text", L("form_text")], ["math", L("form_math")]], o.form, 'data-opt="form" aria-label="' + esc(L("opt_form")) + '"');
    var kind = seg("o-kind", [["LP", L("kind_LP")], ["ILP", L("kind_ILP")]], o.kind, 'data-opt="kind" aria-label="' + esc(L("opt_kind")) + '"');
    var topics = ["random", "gastro", "production", "farming", "events", "transport", "advertising"];

    var practice =
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_difficulty")) + "</div>" + diff + '<p class="ol-field-hint">' + esc(L("diff_" + o.difficulty + "_hint")) + "</p></div>" +
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_form")) + "</div>" + form + '<p class="ol-field-hint">' + esc(L("form_" + o.form + "_hint")) + "</p></div>" +
      '<div class="ol-field"><div class="ol-field-label">' + esc(L("opt_kind")) + "</div>" + kind + '<p class="ol-field-hint">' + esc(L("kind_" + o.kind + "_hint")) + "</p></div>" +
      switchRow("o-exam", L("opt_exam"), L("opt_exam_hint"), o.mode === "exam", false, 'data-opt="mode"') +
      '<details class="ol-more"' + (S.more ? " open" : "") + ' data-more="practice"><summary>' + esc(L("more_options")) + "</summary>" +
      '<div class="ol-field"><label class="ol-field-label" for="o-topic">' + esc(L("opt_topic")) + '</label><select id="o-topic" class="form-select ol-select" data-opt="topic">' +
      topics.map(function (tp) { return '<option value="' + tp + '"' + (o.topic === tp ? " selected" : "") + ">" + esc(L("topic_" + tp)) + "</option>"; }).join("") + "</select></div>" +
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
        '<button class="btn os-btn os-btn-primary ol-cta" id="ol-start-own" data-act="own">' + esc(L("start_own")) + "</button>";
    } else {
      ownBody = '<div class="ol-empty"><p>' + esc(L("own_empty")) + '</p><button class="btn os-btn" id="ol-goto-work" data-act="goto-work">' + esc(L("own_goto")) + "</button></div>" +
        '<button class="btn os-btn os-btn-primary ol-cta" disabled>' + esc(L("start_own")) + "</button>";
    }

    var flow = ["flow_task", "flow_model", "flow_lines", "flow_optimum", "flow_slack", "flow_result"];
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
      '<p class="ol-imprint"><button type="button" class="btn btn-link os-imprint-link" data-os-imprint>' + esc(T("imprint")) + "</button></p>" +
      "</div>";
  }

  function card(ic, title, tag, body, cls) {
    return '<section class="ol-choice os-card ' + (cls || "") + '"><header class="ol-choice-head"><span class="ol-choice-icon">' + icon(ic) + "</span><div><h2>" + esc(title) + '</h2><span class="ol-choice-tag">' + esc(tag) + "</span></div></header>" +
      '<div class="ol-choice-body">' + body + "</div></section>";
  }

  // ------------------------------------------------------------------ starting and ending an exercise
  function startWith(action, payload) {
    return busy(action, call(action, payload)).then(function (ex) {
      ex.steps.unshift({ id: "task", questions: [], points: 0 });   // first read the task, then enter answers
      S.ex = ex; S.step = 0; S.answers = {}; S.feedback = {}; S.hints = {}; S.solutions = ex.solutions || {}; S.solWay = {}; S.result = null;
      S.activeRow = 0; S.level = null; S.help = false; S.view = "work";
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
  var SHORT = { task: "short_task", objective: "short_objective", constraints: "short_constraints", lines: "short_lines", region: "short_region", corner: "short_corner", optimum: "short_optimum", slack: "short_slack", interpret: "short_interpret" };

  function stepTitle(s) { return L(s.id === "optimum" && hasCorner() ? "step_optimum_calc" : "step_" + s.id); }
  function stepShort(s) { return L(SHORT[s.id]); }

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

  // the task text (word problems) or the given model (formulas)
  function taskHTML() {
    var st = S.ex.story, task = '<h3 class="ol-story-title">' + esc(st.title) + "</h3>";
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
    return task;
  }

  function sideHTML() {
    var m = model(), s = cur(), html = "";
    // phones: the task was read in step 1 and would push the step far down – one tap opens it.
    // Word problems: once the model is set up, “Your model” stands in for the long task text.
    var open = S.taskOpen !== null ? S.taskOpen : !phone() && (isModel(s.id) || (window.innerWidth >= 1024 && !textTask()));
    if (tutorial() && !phone()) html += coachHTML(s);
    html += '<details class="os-card ol-panel ol-task"' + (open ? " open" : "") + '><summary class="ol-panel-head"><h2>' + esc(L("task")) + "</h2>" +
      '<span class="ol-task-title">' + esc(S.ex.story.title) + '</span></summary><div class="ol-panel-body">' + taskHTML() + "</div></details>";
    if (textTask() && !isModel(s.id)) {
      html += '<section class="os-card ol-panel ol-yourmodel"><header class="ol-panel-head"><h2>' + esc(L("your_model")) + '</h2><button type="button" class="btn btn-link os-header-action" data-act="goto" data-step="' + stepIndex("objective") + '">' + esc(L("edit_model")) + '</button></header><div class="ol-panel-body">' + modelListHTML(m, true) + "</div></section>";
    }
    return '<aside class="ol-side" aria-label="' + esc(L("task")) + '">' + html + "</aside>";
  }

  function modelListHTML(m, own) {
    // names in front, as in the task: “Revenue: F = …”, “C1 Buns: …”
    var obj = (fName() ? "<b>" + esc(fName()) + ":</b> " : "") +
      (isNum(m.c[0]) || isNum(m.c[1]) || !own ? "F = " + esc(formula(m.c)) + " → " + esc(m.sense || "?") : '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>");
    var rows = m.rows.map(function (r, i) {
      var text = rowComplete(r) ? esc(formula(r.a)) + " " + OP[r.op] + " " + esc(fmt(r.b)) : '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>";
      return '<div class="ol-mini-row">' + swatch(color(i)) + '<span><b style="color:' + color(i) + '">' + esc(boundaryName(i)) + ":</b> " + text + "</span></div>";
    }).join("");
    var a = S.answers.objective || {};
    var vt = own && (!a.vt0 || !a.vt1) ? '<span class="ol-muted">' + esc(L("model_incomplete")) + "</span>" :
      "x1 " + esc(T(ints(m.kind)[0] ? "integer_short" : "continuous_short")) + ", x2 " + esc(T(ints(m.kind)[1] ? "integer_short" : "continuous_short"));
    return '<div class="ol-mini-list"><div class="ol-mini-row">' + swatch(GREEN, true) + "<span>" + obj + "</span></div>" + rows +
      '<div class="ol-mini-row ol-mini-type"><span>' + esc(L("g_range")) + ": " + vt + "</span></div></div>";
  }

  function workHTML() {
    // the first step shows only the task: one reading column, no graph yet
    if (cur().id === "task") return '<div class="ol-work is-intro" data-step="task">' + stepperHTML() + stepCardHTML() + "</div>";
    var cls = "ol-work" + (showsGraph() ? "" : " no-graph") + (S.sidebar ? "" : " no-side");
    return '<div class="' + cls + '" data-step="' + cur().id + '">' + stepperHTML() + (S.sidebar ? sideHTML() : "") + (showsGraph() ? graphCardHTML() : "") + stepCardHTML() + "</div>";
  }

  function sidebarButton() {
    return '<button type="button" class="os-sidebar-btn" data-act="sidebar" aria-expanded="' + S.sidebar + '" aria-label="' + esc(L("toggle_task")) + '" title="' + esc(L("toggle_task")) + '">' + (S.sidebar ? "‹" : "›") + "</button>";
  }

  // ------------------------------------------------------------------ step card
  function stepCardHTML() {
    var s = cur(), total = steps().length, intro = s.id === "task";
    var head = '<header class="ol-panel-head ol-step-head">' + (showsGraph() || intro ? "" : sidebarButton()) +
      '<div class="ol-step-heading"><div class="ol-step-meta">' + esc(L("step_of", { n: S.step + 1, total: total })) + (intro ? "" : " · " + esc(L("points", { n: s.points }))) + "</div>" +
      '<h2 class="ol-step-title" id="ol-step-title">' + esc(stepTitle(s)) + "</h2></div>" +
      (exam() || intro ? "" : '<button type="button" class="os-help' + (S.help ? " is-on" : "") + '" id="ol-help" data-act="help" aria-expanded="' + S.help + '" aria-label="' + esc(L("help_title")) + '" title="' + esc(L("help_title")) + '">?</button>') +
      "</header>";
    var body = S.help && !exam() && !intro ? howtoHTML(s) : "";
    if (textTask() && !intro && !isModel(s.id) && !tutorial() && !exam()) {
      var fbs = [S.feedback.objective, S.feedback.constraints];
      var wrong = fbs.some(function (f) { return f && !f.stale && !f.correct; });
      if (wrong || fbs.some(function (f) { return !f || f.stale; })) body += '<div class="ol-banner is-info">' + esc(L(wrong ? "model_notice_wrong" : "model_notice")) + "</div>";
    }
    // phones, guided example: the explanation of the example stands in for the general lead, right above the fields
    body += tutorial() && phone() && !intro ? coachInlineHTML(s) : '<p class="ol-lead">' + esc(lead(s)) + "</p>";
    body += ({ task: taskStep, objective: objectiveStep, constraints: constraintsStep, lines: linesStep, region: regionStep, corner: cornerStep, optimum: optimumStep, slack: slackStep, interpret: interpretStep })[s.id](s);
    body += feedbackHTML(s) + hintHTML(s) + solutionHTML(s);

    var last = S.step === total - 1, fbS = S.feedback[s.id], solved = fbS && !fbS.stale && fbS.correct;
    var foot = '<footer class="ol-step-foot">' +
      '<button type="button" class="ol-icon-btn" id="ol-prev" data-act="prev" aria-label="' + esc(L("back")) + '" title="' + esc(L("back")) + '"' + (S.step === 0 ? " disabled" : "") + ">‹</button>" +
      (exam() || intro ? "" : '<button type="button" class="ol-link-btn" id="ol-hint" data-act="hint">' + esc(L("hint")) + '</button><button type="button" class="ol-link-btn" id="ol-solution" data-act="solution">' + esc(L("solution")) + "</button>") +
      '<span class="ol-grow"></span>' +
      (exam() || intro ? "" : '<button type="button" class="btn os-btn' + (solved ? "" : " os-btn-primary") + '" id="ol-check" data-act="check">' + esc(L("check")) + "</button>") +
      '<button type="button" class="btn os-btn' + (solved || exam() || last || intro ? " os-btn-primary" : "") + '" id="ol-next" data-act="' + (last ? "finish" : "next") + '">' +
      esc(last ? L(tutorial() ? "finish_short" : "to_submit") : L("next")) + " ›</button></footer>";
    return '<section class="os-card ol-panel ol-stepcard" aria-labelledby="ol-step-title">' + head + '<div class="ol-step-body">' + body + "</div>" + foot + "</section>";
  }

  function lead(s) {
    if (s.id === "task") return L(textTask() ? "lead_task_text" : "lead_task_math");
    if (s.id === "optimum") return L(hasCorner() ? "lead_optimum_calc" : "lead_optimum");
    if (s.id === "lines" && tutorial()) return L("lead_lines");
    return L("lead_" + s.id);
  }

  // input field for a numeric answer
  function input(sid, key, aria, ph, wide, text) {
    var v = val(sid, key), mark = markOf(sid, key);
    return '<input class="ol-in' + (wide ? " is-wide" : "") + mark + '" id="q-' + key + '" data-q="' + key + '" value="' + esc(v) + '" autocomplete="off" spellcheck="false" inputmode="' + (text ? "text" : "decimal") + '"' +
      (ph ? ' placeholder="' + esc(ph) + '"' : "") + ' aria-label="' + esc(aria) + '">';
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

  // the task, then once how the following steps work (exam mode: without hints and solutions)
  function taskStep() {
    var tips = (exam() ? [] : ["intro_help", "intro_check", "intro_solution"]).concat("task_note");
    return '<div class="ol-intro"><div>' + taskHTML() + '</div><section class="ol-note ol-howto"><h3 class="ol-note-title">' + esc(L("intro_title")) + "</h3><ul>" +
      tips.map(function (k) { return "<li>" + esc(L(k)) + "</li>"; }).join("") + "</ul></section></div>";
  }

  // phones, word problems: the sentence of the task that belongs to these fields, right above them
  // (the task card is closed there – otherwise the fields would move far down)
  function storyHint(text) { return textTask() && phone() && text ? '<p class="ol-story-inline">' + esc(text) + "</p>" : ""; }

  function objectiveStep(s) {
    var sid = s.id, h = "", st = S.ex.story;
    h += '<section class="ol-group" data-group="obj"><h3 class="ol-group-title">' + esc(T("objective_function") + (fName() ? ": " + fName() : "")) + "</h3>" + storyHint(st.objective) +
      '<div class="ol-formula is-capped">' + sym("F =") + cell(cap("c1"), input(sid, "c0", L("a_c", { n: 1 }))) + sym("·x1 +") + cell(cap("c2"), input(sid, "c1", L("a_c", { n: 2 }))) + sym("·x2 →") +
      cell(pickCap(sid, "sense", "cap_sense", "cap_sense_pick"), choice(sid, "sense", [["max", "max"], ["min", "min"]], L("a_sense"), "is-inline")) + "</div></section>";
    var dom = st.domain || [];   // one sentence per variable, or one for both
    h += '<section class="ol-group" data-group="vt"><h3 class="ol-group-title">' + esc(L("g_range")) + "</h3>" + (dom.length === 2 ? "" : storyHint(dom.join(" "))) +
      [0, 1].map(function (j) {
        return (dom.length === 2 ? storyHint(dom[j]) : "") + '<div class="ol-vt-row"><span class="os-var">x' + (j + 1) + "</span>" + choice(sid, "vt" + j, [["con", esc(T("continuous_short"))], ["int", esc(T("integer_short"))]], L("a_vt", { n: j + 1 })) + "</div>";
      }).join("") + "</section>";
    return h;
  }

  function constraintsStep(s) {
    var sid = s.id, h = '<section class="ol-group"><h3 class="ol-group-title">' + esc(T("constraints")) + "</h3>";
    for (var i = 0; i < nRows(); i++) {
      var lab = label(i);
      h += '<div class="ol-row" data-group="row' + i + '">' + rowHead(i) + storyHint((S.ex.story.rows || [])[i]) + '<div class="ol-formula is-capped">' +
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
    var h = '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_sides")) + '</h3><p class="ol-field-hint">' + esc(L("sides_how")) + "</p>";
    for (var i = 0; i < nRows(); i++) {
      var tp = S.ex.testPoints[i];
      h += '<div class="ol-row ol-pick' + (i === S.activeRow ? " is-active" : "") + '" data-row="' + i + '" data-group="row' + i + '">' + rowHead(i, rowEq(i, true)) +
        choice(s.id, "side" + i, [["in", esc(L("side_in", { p: pt(tp[0], tp[1]) }))], ["out", esc(L("side_out"))], ["line", esc(L("side_line"))]], L("a_side", { label: label(i) }), "is-wrap") + "</div>";
    }
    h += '</section><section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_points")) + '</h3><p class="ol-field-hint">' + esc(L("points_how")) + "</p>";
    S.ex.points.forEach(function (p, n) {
      h += '<div class="ol-check-row"><span class="ol-pt-label"><b>P' + (n + 1) + "</b> " + pt(p[0], p[1]) + "</span>" +
        choice(s.id, "p" + n, [["yes", esc(L("feasible_yes"))], ["no", esc(L("feasible_no"))]], L("a_point", { n: n + 1 }), "is-inline") + "</div>";
    });
    return h + "</section>";
  }

  function boundaryName(i) {
    return i < nRows() ? label(i) + (S.ex.names && S.ex.names[i] ? " " + S.ex.names[i] : "") : i === nRows() ? L("axis_x1") : L("axis_x2");
  }
  // what F stands for (revenue, costs …) in word problems
  function fName() { return S.ex.story && S.ex.story.fname; }
  function cornerStep(s) {
    var picks = picked(), chips = "";
    for (var i = 0; i < nRows() + 2; i++) {
      var on = picks.indexOf(String(i)) >= 0;
      chips += '<button type="button" class="ol-chip' + (on ? " is-on" + markOf(s.id, "boundary1") : "") + '" id="ol-b-' + i + '" data-act="boundary" data-b="' + i + '" aria-pressed="' + on + '">' +
        (i < nRows() ? swatch(color(i)) : "") + "<b>" + esc(boundaryName(i)) + "</b>" + (i < nRows() ? '<span class="ol-chip-eq">' + rowEq(i, false) + "</span>" : "") + "</button>";
    }
    return '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_pick")) + '</h3><div class="ol-chips">' + chips + "</div>" +
      '<p class="ol-field-hint">' + esc(picks.length === 2 ? L("picked", { a: boundaryName(+picks[0]), b: boundaryName(+picks[1]) }) : L("pick_two")) + "</p></section>";
  }

  function optimumStep(s) {
    var h = "";
    if (hasCorner()) {
      // the corner from the step before: the two equations to solve
      var picks = picked();
      h = picks.length === 2 ? '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_your_corner")) + "</h3>" + picks.map(function (b) {
        return +b < nRows() ? rowHead(+b, rowEq(+b, false)) : '<div class="ol-row-head"><b>' + esc(boundaryName(+b)) + "</b></div>";
      }).join("") + "</section>" : '<div class="ol-banner is-info">' + esc(L("corner_missing")) + "</div>";
    }
    return h + '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_optimum")) + '</h3><div class="ol-formula"><span class="ol-sym">x* = (</span>' +
      input(s.id, "x", L("a_opt", { n: 1 }), "x1") + '<span class="ol-sym">|</span>' + input(s.id, "y", L("a_opt", { n: 2 }), "x2") + '<span class="ol-sym">)</span></div></section>' +
      '<section class="ol-group"><h3 class="ol-group-title">' + esc(L("g_value") + (fName() ? " (" + fName() + ")" : "")) + '</h3><div class="ol-formula"><span class="ol-sym">F =</span>' + input(s.id, "z", L("a_z"), "", true) + "</div></section>";
  }

  // what is left over of every constraint at the optimum, and whether it is used up (binding)
  function slackStep(s) {
    var o = S.answers.optimum || {}, h = "";
    if (o.x || o.y) h += '<p class="ol-ref">' + esc(L("your_opt")) + " <b>" + pt(num(o.x), num(o.y)) + "</b></p>";
    h += '<table class="ol-sens"><thead><tr><th>' + esc(T("col_constraint")) + "</th><th>" + esc(T("col_slack")) + "</th><th>" + esc(L("g_bind")) + "</th></tr></thead><tbody>";
    for (var i = 0; i < nRows(); i++) {
      h += '<tr data-group="row' + i + '"><th scope="row">' + rowHead(i) + '<div class="ol-eq-small">' + rowEq(i, true) + "</div></th><td>" + input(s.id, "slack" + i, L("a_slack", { label: label(i) })) + "</td>" +
        "<td>" + choice(s.id, "bind" + i, [["yes", esc(L("bind_yes"))], ["no", esc(L("bind_no"))]], L("a_bind", { label: label(i) }), "is-inline") + "</td></tr>";
    }
    return h + "</tbody></table>";
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

  function feedbackHTML(s) {
    var fb = S.feedback[s.id];
    if (exam() || !fb || fb.stale) return "";
    var keys = Object.keys(fb.checks), right = keys.filter(function (k) { return fb.checks[k]; }).length;
    var missing = keys.filter(function (k) { return !fb.checks[k] && String(val(s.id, k)).trim() === ""; }).length;
    if (fb.correct && S.solutions[s.id]) return "";   // the solution box says it
    if (fb.correct) return '<div class="ol-banner is-ok" role="status"><b>' + esc(L("fb_correct")) + "</b> " + esc(L("points_of", { got: fmt(fb.points), max: fmt(fb.max) })) + "</div>";
    var detail = [right < keys.length - missing ? L("fb_marked") : "", missing ? L("fb_missing", { n: missing }) : ""].filter(Boolean).join(" ");
    return '<div class="ol-banner is-partial" role="status"><div><b>' + esc(L("fb_partial", { right: right, total: keys.length })) + "</b> " + esc(detail) +
      '<div class="ol-banner-sub">' + esc(L("points_of", { got: fmt(fb.points), max: fmt(fb.max) })) + "</div></div>" +
      (S.hints[s.id] ? "" : '<button type="button" class="btn os-btn" id="ol-hint-2" data-act="hint">' + esc(L("get_hint")) + "</button>") + "</div>";
  }
  function hintHTML(s) {
    var h = S.hints[s.id];
    if (!h || exam() || S.solutions[s.id]) return "";   // with the solution filled in, the hint is not needed any more
    if (!h.level) return '<div class="ol-note ol-hintbox" role="status"><div class="ol-note-title">' + esc(L("hint")) + "</div><p>" + esc(L("hint_none")) + "</p></div>";
    return '<div class="ol-note ol-hintbox" role="status"><div class="ol-note-title">' + esc(L("hint_level", { n: h.level })) + "</div><ul>" +
      h.ids.map(function (id) { return "<li>" + L("hint_" + id) + "</li>"; }).join("") + "</ul>" +
      (h.more ? '<button type="button" class="ol-link-btn" id="ol-more-hints" data-act="hint">' + esc(L("more_hints")) + "</button>" : "") + "</div>";
  }
  // after “Solution” the values are in the fields; the worked solution stays one click away
  function solutionHTML(s) {
    var lines = S.solutions[s.id];
    if (!lines || exam()) return "";
    return '<div class="ol-note ol-solbox" role="status"><div class="ol-note-title">' + esc(L("sol_filled_title")) + "</div><p>" + esc(L("sol_filled")) + "</p>" +
      '<details class="ol-calc-toggle" data-sol="' + s.id + '"' + (S.solWay[s.id] ? " open" : "") + "><summary>" + esc(L("sol_way")) + '</summary><ul class="ol-sol">' +
      lines.map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("") + "</ul></details></div>";
  }

  // ------------------------------------------------------------------ left column: example coach and help
  function coachHTML(s) {
    var calc = L("tut_calc_" + s.id);
    return '<section class="os-card ol-panel ol-coachcard" id="ol-coach"><header class="ol-panel-head"><span class="ol-badge">' + icon("route") + "</span><h2>" + esc(L("coach_title")) + "</h2>" +
      '<span class="ol-head-note">' + esc(stepShort(s)) + "</span></header><div class=\"ol-panel-body ol-coach\">" +
      "<p>" + esc(L("tut_coach_" + s.id)) + "</p>" +
      (calc ? '<details class="ol-calc-toggle"><summary>' + esc(L("coach_calc")) + '</summary><pre class="ol-calc">' + esc(calc) + "</pre></details>" : "") + "</div></section>";
  }
  function coachInlineHTML(s) {
    var calc = L("tut_calc_" + s.id);
    return '<div class="ol-note ol-coach ol-coach-inline"><div class="ol-note-title">' + esc(L("coach_title")) + "</div><p>" + esc(L("tut_coach_" + s.id)) + "</p>" +
      (calc ? '<details class="ol-calc-toggle"><summary>' + esc(L("coach_calc")) + '</summary><pre class="ol-calc">' + esc(calc) + "</pre></details>" : "") + "</div>";
  }
  // “?”: how to do this step, right below the step's title
  function howtoHTML(s) {
    return '<section class="ol-note ol-howto is-help" id="ol-howto" aria-labelledby="ol-howto-title"><div class="ol-howto-head"><h3 class="ol-note-title" id="ol-howto-title">' + esc(L("help_title")) + "</h3>" +
      '<button type="button" class="ol-howto-close" data-act="help" aria-label="' + esc(T("close")) + '" title="' + esc(T("close")) + '">×</button></div>' +
      '<div class="ol-help-panel">' + L(s.id === "optimum" && hasCorner() ? "help_optimum_calc" : "help_" + s.id) + "</div></section>";
  }
  // ------------------------------------------------------------------ graph card
  function graphCardHTML() {
    var s = cur(), tools = "";
    if (s.id === "lines" || s.id === "region") {
      tools = '<div class="ol-chips is-compact" role="group" aria-label="' + esc(L("active_line")) + '">' + S.ex.colors.map(function (c, i) {
        return '<button type="button" class="ol-chip' + (i === S.activeRow ? " is-on" : "") + '" id="ol-gr-' + i + '" data-act="row" data-row="' + i + '" aria-pressed="' + (i === S.activeRow) + '">' + swatch(c) + esc(label(i)) + "</button>";
      }).join("") + "</div>";
    }
    return '<section class="os-card ol-panel ol-graph"><header class="ol-panel-head">' + sidebarButton() + "<h2>" + esc(L("graph_title")) + "</h2>" + tools + "</header>" +
      '<div class="ol-plot-wrap"><div class="ol-plot" id="ol-plot"></div></div><p class="ol-graph-note" id="ol-graph-note">' + esc(graphNote(s)) + "</p></section>";
  }
  function graphNote(s) {
    if (isModel(s.id)) return L("gn_model");
    if (s.id !== "lines" && steps().some(function (x) { return x.id === "lines"; }) && learnerLines().some(function (l) { return !l; })) return L("gn_need_lines");
    if (s.id === "lines") return L("gn_lines", { label: label(S.activeRow) });
    if (s.id === "region") return L("gn_region");
    if (s.id === "corner") return L("gn_corner");
    if (s.id === "optimum") return L(hasCorner() ? "gn_optimum_calc" : "gn_optimum");
    return L("gn_after");
  }

  // the green line: where it was dragged, else through the chosen corner or the learner's optimum
  function levelValue() {
    if (S.level !== null) return S.level;
    var m = model(), o = S.answers.optimum || {}, x = num(o.x), y = num(o.y), c = cornerPoint(), typed = isNum(x) && isNum(y);
    var p = c && (cur().id === "corner" || !typed) ? c : typed ? [x, y] : null;
    if (p) return m.c[0] * p[0] + m.c[1] * p[1];
    var e = S.ex.extent;
    return Math.round((m.c[0] * e[0] + m.c[1] * e[1]) * 0.3 * 100) / 100;
  }

  // ------------------------------------------------------------------ graph drawing (SVG, same colours as the matplotlib graph)
  var G = null;   // geometry of the current drawing, used by the pointer handlers
  // smartphones: the same query as the one-column layout in learn.css
  var PHONE = "(max-width: 575.98px), (max-width: 1023.98px) and (max-height: 500px)";
  function phone() { return !!(window.matchMedia && window.matchMedia(PHONE).matches); }
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
  // sides: the answers of the region step (side0 … : in / out / line)
  function region(lines, ex, ey, sides) {
    var poly = [[0, 0], [ex, 0], [ex, ey], [0, ey]], any = false, eqLine = null;
    sides = sides || {};
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
  // where two lines a·x = b meet, or null if they are parallel
  function meet(u, v) {
    var det = u.a[0] * v.a[1] - u.a[1] * v.a[0];
    if (Math.abs(det) <= 1e-9 * Math.hypot(u.a[0], u.a[1]) * Math.hypot(v.a[0], v.a[1])) return null;
    return [(u.b * v.a[1] - u.a[1] * v.b) / det, (u.a[0] * v.b - u.b * v.a[0]) / det];
  }
  // the learner's lines and the two axes, numbered like the boundaries on the server
  function boundaryLines() { return learnerLines().concat([{ a: [1, 0], b: 0 }, { a: [0, 1], b: 0 }]); }
  // the corners that can be tapped: where two lines meet inside the grey region (three lines through one point: the first pair)
  function cornersOf(reg) {
    var ls = boundaryLines(), poly = reg && reg.poly.length > 2 ? reg.poly : null, out = [], tol = 1e-7 * (1 + G.ex + G.ey);
    for (var i = 0; i < ls.length; i++) for (var j = i + 1; j < ls.length; j++) {
      var xy = ls[i] && ls[j] ? meet(ls[i], ls[j]) : null;
      if (!xy || xy[0] < -tol || xy[1] < -tol || xy[0] > G.ex + tol || xy[1] > G.ey + tol) continue;
      if (poly && !inPoly(xy, poly) && !onBoundary(xy, poly)) continue;
      if (out.some(function (c) { return Math.abs(c.p[0] - xy[0]) + Math.abs(c.p[1] - xy[1]) < tol; })) continue;
      out.push({ p: xy, b: [i, j] });
    }
    return out;
  }
  function cornerPoint() {
    var b = picked(), ls = boundaryLines();
    return b.length === 2 && ls[+b[0]] && ls[+b[1]] ? meet(ls[+b[0]], ls[+b[1]]) : null;
  }
  // the feasible sides of a model, in the form of the region step's answers
  function feasibleSides(m) {
    var out = {};
    m.rows.forEach(function (r, i) {
      var tp = S.ex.testPoints[i], lhs = r.a[0] * tp[0] + r.a[1] * tp[1];
      out["side" + i] = r.op === "=" ? "line" : (r.op === "<=" ? lhs <= r.b : lhs >= r.b) ? "in" : "out";
    });
    return out;
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
    host.innerHTML = graphSVG(cur().id, w, h);
  }
  // the graph of a step as SVG (sets the geometry G for the pointer handlers);
  // sol (after handing in): the correct model and optimum instead of the learner's answers
  function graphSVG(sid, w, h, sol) {
    var fs = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16, k = fs / 16;
    var ex = S.ex.extent[0], ey = S.ex.extent[1];
    var L0 = 44 * k, R0 = 18 * k, T0 = 16 * k, B0 = 34 * k;
    var pw = w - L0 - R0, ph = h - T0 - B0;
    var X = function (x) { return L0 + x / ex * pw; }, Y = function (y) { return T0 + ph - y / ey * ph; };
    G = { X: X, Y: Y, ex: ex, ey: ey, L0: L0, T0: T0, pw: pw, ph: ph, k: k };
    var m = sol ? sol.model : model(), o = [];
    var lines = sol ? m.rows.map(function (r) { return { a: r.a, b: r.b }; }) : isModel(sid) ? [] : learnerLines();

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
    var reg = !isModel(sid) && sid !== "lines" ? region(lines, ex, ey, sol ? feasibleSides(m) : S.answers.region) : null;
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
    var picks = sid === "corner" || sid === "optimum" ? picked() : [];
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
    // the axes as chosen boundaries of the corner
    picks.forEach(function (p) {
      if (p === String(nRows())) o.push('<line x1="' + X(0) + '" y1="' + Y(0) + '" x2="' + X(0) + '" y2="' + Y(ey) + '" stroke="' + INK + '" stroke-width="' + 4 * k + '"/>');
      if (p === String(nRows() + 1)) o.push('<line x1="' + X(0) + '" y1="' + Y(0) + '" x2="' + X(ex) + '" y2="' + Y(0) + '" stroke="' + INK + '" stroke-width="' + 4 * k + '"/>');
    });
    // objective line
    var showObj = ["corner", "optimum", "slack", "interpret"].indexOf(sid) >= 0 && isNum(m.c[0]) && isNum(m.c[1]) && (Math.abs(m.c[0]) + Math.abs(m.c[1]) > 0);
    var segO = showObj ? clipToBox(m.c, sol ? sol.z : levelValue(), ex, ey) : null;
    if (segO) o.push('<line x1="' + X(segO[0][0]) + '" y1="' + Y(segO[0][1]) + '" x2="' + X(segO[1][0]) + '" y2="' + Y(segO[1][1]) + '" stroke="' + GREEN + '" stroke-width="' + 2.4 * k + '" stroke-dasharray="' + 9 * k + " " + 6 * k + '"/>');
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
      // the test point of the chosen line – also (0 | 0), which the answer “side with test point (0 | 0)” refers to
      if (tp) o.push('<circle cx="' + X(tp[0]) + '" cy="' + Y(tp[1]) + '" r="' + 8 * k + '" fill="none" stroke="' + color(S.activeRow) + '" stroke-width="' + 2.2 * k + '" stroke-dasharray="' + 3 * k + '"/>');
    }
    // the corners to tap, and the chosen one with a red ring
    G.corners = sid === "corner" ? cornersOf(reg) : [];
    G.corners.forEach(function (c) { o.push('<circle cx="' + X(c.p[0]) + '" cy="' + Y(c.p[1]) + '" r="' + 4 * k + '" fill="#fff" stroke="' + INK + '" stroke-width="' + 1.6 * k + '"/>'); });
    var cp = sid === "corner" || sid === "optimum" ? cornerPoint() : null;
    if (cp) o.push('<circle cx="' + X(cp[0]) + '" cy="' + Y(cp[1]) + '" r="' + 8.5 * k + '" fill="none" stroke="' + RED + '" stroke-width="' + 2.4 * k + '"/>');
    // the learner's optimum (integer tasks: it can be dragged)
    var ox = sol ? sol.x[0] : num(val("optimum", "x")), oy = sol ? sol.x[1] : num(val("optimum", "y")), grab = tapsPoint(sid);
    if (["optimum", "slack", "interpret"].indexOf(sid) >= 0 && isNum(ox) && isNum(oy)) {
      o.push('<circle class="' + (grab ? "ol-grip" : "") + '" data-drag="' + (grab ? "point" : "") + '" cx="' + X(ox) + '" cy="' + Y(oy) + '" r="' + 6.5 * k + '" fill="' + RED + '" stroke="#fff" stroke-width="' + 2 * k + '"/>');
      if (grab && COARSE) o.push('<g class="ol-grip" data-drag="point">' + halo(X(ox), Y(oy), k) + "</g>");
      o.push('<text class="ol-opt-label" x="' + (X(ox) + 10 * k) + '" y="' + (Y(oy) - 9 * k) + '" fill="' + RED + '" font-size="' + 12.5 * k + '">' + esc(pt(ox, oy)) + "</text>");
    }
    // the handle of the green line sits away from the corners and points, so a tap there never grabs the line;
    // its arrows show the two directions in which the line moves
    if (segO && dragsObjective(sid)) {
      var avoid = G.corners.map(function (c) { return c.p; }).concat(reg && reg.poly.length > 2 ? reg.poly : []);
      if (isNum(ox) && isNum(oy)) avoid.push([ox, oy]);
      if (drag !== "objective" || gripT === null) gripT = gripSpot(segO, avoid);
      var hx = X(segO[0][0] + gripT * (segO[1][0] - segO[0][0])), hy = Y(segO[0][1] + gripT * (segO[1][1] - segO[0][1]));
      var ang = Math.atan2(-m.c[1] * ey / ph, m.c[0] * ex / pw) * 180 / Math.PI;
      o.push('<g class="ol-grip" data-drag="objective">' + halo(hx, hy, k) + '<circle cx="' + hx + '" cy="' + hy + '" r="' + 11 * k + '" fill="#fff" stroke="' + GREEN + '" stroke-width="' + 2.4 * k + '"/>' +
        '<path transform="rotate(' + ang + " " + hx + " " + hy + ')" d="M' + (hx + 7.5 * k) + " " + hy + " l" + -4 * k + " " + -3.5 * k + " v" + 7 * k + "z M" + (hx - 7.5 * k) + " " + hy + " l" + 4 * k + " " + -3.5 * k + " v" + 7 * k + 'z" fill="' + GREEN + '"/></g>');
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
    return '<svg class="ol-svg' + (sid === "corner" || grab ? " is-pick" : "") + '" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + esc(L("graph_aria")) + '">' + o.join("") + '<g id="ol-tip"></g></svg>';
  }

  function toData(ev) {
    var svg = document.querySelector("#ol-plot svg"), r = svg.getBoundingClientRect();
    var x = (ev.clientX - r.left - G.L0) / G.pw * G.ex, y = (G.T0 + G.ph - (ev.clientY - r.top)) / G.ph * G.ey;
    return [Math.max(0, Math.min(G.ex, x)), Math.max(0, Math.min(G.ey, y))];
  }
  function snap(v, ext) { var st = niceStep(ext) / 20; return Math.round(v / st) * st; }
  // the spot on the green line farthest from the points to avoid (far enough is enough – then rather the middle)
  var gripT = null;
  function gripSpot(seg, avoid) {
    var best = 0.5, score = -Infinity;
    for (var t = 0.15; t <= 0.851; t += 0.05) {
      var px = G.X(seg[0][0] + t * (seg[1][0] - seg[0][0])), py = G.Y(seg[0][1] + t * (seg[1][1] - seg[0][1]));
      var d = avoid.reduce(function (mn, p) { return Math.min(mn, Math.hypot(G.X(p[0]) - px, G.Y(p[1]) - py)); }, Infinity);
      d = Math.min(d, 64 * G.k) - Math.abs(t - 0.5) * 12 * G.k;
      if (d > score) { score = d; best = t; }
    }
    return best;
  }

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
    if (sid !== "corner" && !tapsPoint(sid)) return;
    if (ev.pointerType === "touch") { tapStart = { id: ev.pointerId, x: ev.clientX, y: ev.clientY }; return; }   // a swipe scrolls the page
    ev.preventDefault();
    if (sid === "corner") { pickCorner(ev); return; }
    setOptPoint(toData(ev)); drag = "point"; host.setPointerCapture(ev.pointerId);
  }
  // touch: a tap chooses the corner or sets the optimum; dragging works on the handles, which stop the page from scrolling
  var tapStart = null;
  function onTouchStart(ev) {
    var t = ev.target.closest && ev.target.closest("#ol-plot [data-drag]");
    if (t && t.getAttribute("data-drag") && ev.cancelable) ev.preventDefault();
  }
  // a tap near a corner chooses the two lines that meet there; the green line then runs through it
  function pickCorner(ev) {
    var r = document.querySelector("#ol-plot svg").getBoundingClientRect(), px = ev.clientX - r.left, py = ev.clientY - r.top;
    var best = null, dist = (COARSE ? 32 : 24) * G.k;
    G.corners.forEach(function (c) { var d = Math.hypot(G.X(c.p[0]) - px, G.Y(c.p[1]) - py); if (d < dist) { dist = d; best = c; } });
    if (!best) { toast(L("corner_none")); return; }
    setAnswer("corner", "boundary1", String(best.b[0]));
    setAnswer("corner", "boundary2", String(best.b[1]));
    S.level = null;
    refresh();
  }
  // integer coordinates round; a continuous one (mixed tasks) snaps onto a line nearby, where the optimum lies
  function setOptPoint(p) {
    var it = ints(model().kind), x = it[0] ? Math.round(p[0]) : snap(p[0], G.ex), y = it[1] ? Math.round(p[1]) : snap(p[1], G.ey);
    if (it[0] !== it[1]) {
      var j = it[0] ? 1 : 0, q = [x, y], tol = (COARSE ? 24 : 14) * G.k, near = null;
      boundaryLines().forEach(function (ln) {
        if (!ln || Math.abs(ln.a[j]) < 1e-12) return;
        var w = (ln.b - ln.a[1 - j] * q[1 - j]) / ln.a[j], d = j ? Math.abs(G.Y(w) - G.Y(p[1])) : Math.abs(G.X(w) - G.X(p[0]));
        if (w >= 0 && d < tol) { tol = d; near = w; }
      });
      if (near !== null) { if (j) y = near; else x = near; }
    }
    setAnswer("optimum", "x", fmtInput(x));
    setAnswer("optimum", "y", fmtInput(y));
    var m = model();
    S.level = m.c[0] * x + m.c[1] * y;
    syncInputs(["x", "y"]);
    drawGraph();
  }
  function onPointerMove(ev) {
    if (drag === null || !G) return;
    var p = toData(ev), sid = cur().id;
    if (drag === "objective") {
      var m = model();
      S.level = m.c[0] * p[0] + m.c[1] * p[1];
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
      var tap = ev.type === "pointerup" && Math.hypot(ev.clientX - tapStart.x, ev.clientY - tapStart.y) < 10 && G;
      tapStart = null;
      if (tap && cur().id === "corner") pickCorner(ev);
      else if (tap && tapsPoint(cur().id)) { setOptPoint(toData(ev)); paintStatus(); }
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
    if (/^boundary\d$/.test(key)) return ["boundary1", "boundary2"];
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
    S.step = i; S.activeRow = 0; S.level = null; S.help = false;
    render();
    var body = root().querySelector(".ol-step-body");
    if (body) body.scrollTop = 0;
    if (phone()) window.scrollTo(0, 0);
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
  // fills the correct values into the fields (again, if the learner changed them since)
  function showSolution() {
    var s = cur();
    var go = tutorial() || S.solutions[s.id] ? Promise.resolve(true) : ask(L("sol_confirm_title"), "<p>" + esc(L("sol_confirm")) + "</p>", L("sol_show"));
    go.then(function (ok) {
      if (!ok) return;
      busy("solution", call("solution", { step: s.id, answers: S.answers })).then(function (d) {
        Object.keys(d.values).forEach(function (k) { var v = d.values[k]; setAnswer(s.id, k, typeof v === "number" ? fmtInput(v) : String(v)); });
        S.solutions[s.id] = d.lines;
        S.feedback[s.id] = d.grade;
        if (s.id === "optimum" || s.id === "corner") S.level = null;
        refresh();
        var b = root().querySelector(".ol-solbox");
        if (b) b.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }, function () {});
    });
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
    if (/^bind\d+$/.test(key)) return L("bind_" + v);
    if (/^boundary\d$/.test(key)) return boundaryName(+v);
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
    if (key === "x" || key === "y") return L("a_opt", { n: key === "x" ? 1 : 2 });
    if (key === "z") return L("a_z");
    if ((m = /^slack(\d+)$/.exec(key))) return L("a_slack", { label: label(+m[1]) });
    if ((m = /^bind(\d+)$/.exec(key))) return L("a_bind", { label: label(+m[1]) });
    if (key === "meaning" || key === "round") return L("q_" + key);
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
    var r = S.result, score = r.score, tut = tutorial();   // r.grades: one per graded step, in order
    var ok = r.grades.filter(function (g) { return g.correct; }).length;
    var verdict = tut ? L("res_tut_title") : score >= 99.9 ? L("res_great") : score >= 70 ? L("res_good") : L("res_try");
    var note = tut ? L("res_tut_text") : exam() ? L("res_note_exam") : L("res_note_practice");
    var kpis = '<div class="os-kpis ol-kpis"><div class="os-kpi is-value"><small>' + esc(L("kpi_score")) + "</small><b>" + fmt(score) + ' <span class="ol-of">/ 100</span></b></div>' +
      '<div class="os-kpi"><small>' + esc(L("kpi_steps")) + "</small><b>" + ok + ' <span class="ol-of">/ ' + r.grades.length + "</span></b></div>" +
      (exam() ? "" : '<div class="os-kpi"><small>' + esc(L("kpi_hints")) + "</small><b>" + Object.keys(r.hints).length + '</b></div><div class="os-kpi"><small>' + esc(L("kpi_seen")) + "</small><b>" + r.reveals.length + "</b></div>") + "</div>";
    var items = graded().map(function (s, i) {
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
      '<div class="ol-actions"><button class="btn os-btn os-btn-primary" id="ol-new" data-act="new">' + esc(L(tut ? "res_to_practice" : "res_new")) + "</button>" +
      (S.ex.source === "generated" ? '<button class="btn os-btn" id="ol-again" data-act="again">' + esc(L("res_again")) + "</button>" : "") +
      '<button class="btn os-btn" id="ol-download" data-act="download">' + esc(L("res_download")) + "</button></div></div>";
  }

  // a file that can be read on its own: the score, the task, the graphical solution and every step
  function download() {
    var el = root().querySelector(".ol-result").cloneNode(true);
    el.querySelectorAll("details").forEach(function (d) { d.setAttribute("open", ""); });
    var actions = el.querySelector(".ol-actions");
    if (actions) actions.remove();
    var sol = S.result.solution, graph = "";
    if (sol) {
      // the feasible region, the green line and the optimal point – like the graphical solution in the lecture
      graph = '<section class="ol-export"><h2>' + esc(L("res_graph")) + "</h2>" + graphSVG("interpret", 640, 460, sol) +
        '<p class="ol-export-opt">' + esc(L("res_optimum", { x1: fmt(sol.x[0]), x2: fmt(sol.x[1]), f: fName() ? fName() + " F" : "F", z: fmt(sol.z) })) + "</p></section>";
    }
    el.querySelector(".ol-result-head").insertAdjacentHTML("afterend", '<section class="ol-export"><h2>' + esc(L("task")) + "</h2>" + taskHTML() + "</section>" + graph);
    var css = "body{font:15px/1.5 system-ui,sans-serif;color:#1d1f21;max-width:60rem;margin:2rem auto;padding:0 1rem}h1{font-size:1.5rem;margin:.25rem 0}h2{font-size:1.15rem;margin:1.5rem 0 .5rem}" +
      ".ol-export{border:1px solid #dee2e6;border-radius:8px;padding:.5rem 1rem;margin:1rem 0}.ol-story-title{font-size:1rem;margin:.25rem 0}.ol-story,.ol-story-domain{list-style:none;padding:0;margin:.5rem 0}.ol-story li{margin:.2rem 0}" +
      ".ol-export-opt{font-weight:600;margin:.5rem 0}.ol-sought{margin:.5rem 0}.ol-sought-title{font-weight:600;display:block}.ol-sought-row b{margin-right:.4rem}.ol-story-q{font-weight:600}.ol-mini-row{margin:.2rem 0}" +
      ".os-swatch{display:inline-block;width:.75rem;height:.75rem;border-radius:3px;margin-right:.4rem;vertical-align:-1px}.os-swatch.is-dashed{height:.25rem;vertical-align:3px;background:repeating-linear-gradient(90deg,currentColor 0 5px,transparent 5px 8px)!important}" +
      "svg{display:block;max-width:100%;height:auto;font-family:system-ui,sans-serif}.ol-grid line{stroke:#dee2e6;stroke-dasharray:4 3;stroke-width:1}.ol-ticks text,.ol-axis-label{fill:#1d1f21}.ol-axis-label{font-weight:700}" +
      ".ol-axes line{stroke:#1d1f21;stroke-width:1.3}.ol-axes path{fill:#1d1f21}.ol-lattice{stroke:#c4c9ce;stroke-width:1;stroke-dasharray:2 4}.ol-bar{stroke:#a6a6a6;stroke-opacity:.85;stroke-linecap:round}.ol-hit{stroke:transparent}" +
      ".ol-line-label,.ol-opt-label{font-weight:700;paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}" +
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
    var el = ev.target.closest && ev.target.closest("[data-act]");
    if (!el || !root() || !root().contains(el) || el.disabled) return;
    var act = el.getAttribute("data-act");
    if (S.busy && ["tutorial", "create", "own", "check", "hint", "solution", "finish"].indexOf(act) >= 0) return;
    switch (act) {
      case "tutorial": startWith("tutorial"); break;
      case "create": startWith("create", { options: S.opts }); break;
      case "own": startWith("own", { options: Object.assign({}, S.ownOpts, { form: "math" }) }); break;
      case "goto-work": var tab = document.querySelector('.navbar [data-value="work"]'); if (tab) tab.click(); break;
      case "goto": goto(+el.getAttribute("data-step")); break;
      case "prev": goto(S.step - 1); break;
      case "next": goto(S.step + 1); break;
      case "finish": finish(); break;
      case "quit": quit(); break;
      case "help": {
        S.help = !S.help;
        refresh();
        var hb = document.getElementById(S.help ? "ol-howto" : "ol-help");
        if (S.help && hb) { hb.closest(".ol-step-body").scrollTop = 0; hb.scrollIntoView({ block: "nearest", behavior: "smooth" }); }
        if (!S.help && hb) hb.focus({ preventScroll: true });
        break;
      }
      case "none": {
        var nk = el.getAttribute("data-key"), sidN = cur().id;
        setAnswer(sidN, nk, isNone(val(sidN, nk)) ? "" : "–");
        refresh();
        break;
      }
      case "sidebar": S.sidebar = !S.sidebar; render(); break;
      case "check": check(); break;
      case "hint": hint(); break;
      case "solution": showSolution(); break;
      case "row": setActiveRow(+el.getAttribute("data-row")); break;
      case "boundary": {
        var b = el.getAttribute("data-b"), picks = picked();
        if (picks.indexOf(b) >= 0) picks.splice(picks.indexOf(b), 1); else { picks.push(b); if (picks.length > 2) picks.shift(); }
        setAnswer("corner", "boundary1", picks[0] || "");
        setAnswer("corner", "boundary2", picks[1] || "");
        S.level = null;
        refresh();
        break;
      }
      case "new": S.view = "home"; S.ex = null; render(); window.scrollTo(0, 0); break;
      case "again": startWith("create", { options: S.opts }); break;
      case "download": download(); break;
    }
  }

  function onInput(ev) {
    var t = ev.target;
    if (!root() || !root().contains(t)) return;
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
      drawGraph();
      paintStatusSoon();
    }
  }
  var statusTimer = null;
  function paintStatusSoon() { clearTimeout(statusTimer); statusTimer = setTimeout(paintStatus, 150); }
  function onChange(ev) {
    var t = ev.target;
    if (!root() || !root().contains(t) || S.view !== "home") return;
    var group = t.closest("[data-opt]") || t.closest("[data-own-opt]");
    if (!group) return;
    var own = group.hasAttribute("data-own-opt"), key = group.getAttribute(own ? "data-own-opt" : "data-opt"), target = own ? S.ownOpts : S.opts;
    if (key === "mode") target.mode = t.checked ? "exam" : "practice";
    else target[key] = t.value;
    render();
  }
  function onToggle(ev) {
    var d = ev.target;
    if (d.matches && d.matches("details[data-more]")) S.more = d.open;
    if (d.matches && d.matches("details[data-sol]")) S.solWay[d.getAttribute("data-sol")] = d.open;
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
    if (ev.key === "Enter" && ev.target.classList && ev.target.classList.contains("ol-in")) {
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
  if (window.matchMedia) {
    var phoneQuery = window.matchMedia(PHONE), onPhoneChange = function () { if (S.view === "work") refresh(); };
    if (phoneQuery.addEventListener) phoneQuery.addEventListener("change", onPhoneChange); else phoneQuery.addListener(onPhoneChange);
  }
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
