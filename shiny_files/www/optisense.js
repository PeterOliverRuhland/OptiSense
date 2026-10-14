/* OptiSense browser helpers: language switching for static text, remembering the
   language, list-row interactions, help buttons and the guide navigation. */
(function () {
  "use strict";
  var LANGS = Object.keys(window.OS_I18N || { en: 1 });
  var current = "en";

  function storedLang() {
    try { var v = window.localStorage.getItem("optisense-lang"); if (LANGS.indexOf(v) >= 0) return v; } catch (e) {}
    var nav = (navigator.language || "en").toLowerCase();
    if (nav.indexOf("de") === 0) return "de";
    if (nav.indexOf("fil") === 0 || nav.indexOf("tl") === 0) return "fil";
    return "en";
  }

  function translate(root) {
    var dict = (window.OS_I18N || {})[current] || {};
    (root || document).querySelectorAll("[data-i18n]").forEach(function (el) {
      var k = el.getAttribute("data-i18n");
      if (dict[k] !== undefined && el.textContent !== dict[k]) el.textContent = dict[k];
    });
    (root || document).querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-aria");
      if (dict[k] !== undefined) el.setAttribute("aria-label", dict[k]);
    });
  }

  function setLang(lang) {
    if (LANGS.indexOf(lang) < 0) lang = "en";
    current = lang;
    document.documentElement.setAttribute("lang", lang === "fil" ? "fil" : lang);
    try { window.localStorage.setItem("optisense-lang", lang); } catch (e) {}
    translate(document);
  }

  // Shiny's own language radio buttons drive everything
  document.addEventListener("change", function (ev) {
    var t = ev.target;
    if (t && t.id === "lang") setLang(t.value);
    if (t && t.matches && t.matches("[data-toggle-kind]")) {
      Shiny.setInputValue("row_toggle", { kind: t.getAttribute("data-toggle-kind"), id: +t.getAttribute("data-id"),
        on: t.checked, n: Date.now() }, { priority: "event" });
    }
  });

  function rowActivate(row) {
    Shiny.setInputValue("row_click", { kind: row.getAttribute("data-kind"), id: +row.getAttribute("data-id"), n: Date.now() },
      { priority: "event" });
  }

  document.addEventListener("click", function (ev) {
    var el = ev.target;
    if (!el || !el.closest) return;
    if (el.closest(".os-switch")) return;            // the switch has its own handler
    var row = el.closest(".os-row[data-kind]");
    if (row) { rowActivate(row); return; }
    var help = el.closest("[data-help]");
    if (help) { Shiny.setInputValue("help_topic", { topic: help.getAttribute("data-help"), n: Date.now() }, { priority: "event" }); return; }
    var add = el.closest("[data-add]");
    if (add) { Shiny.setInputValue("add_click", { kind: add.getAttribute("data-add"), n: Date.now() }, { priority: "event" }); return; }
    var tg = el.closest("[data-sidebar-toggle]");
    if (tg) { var native = document.querySelector(".bslib-sidebar-layout > .collapse-toggle"); if (native) native.click(); [50, 400].forEach(function (d) { setTimeout(syncSidebarBtn, d); }); return; }
    var g = el.closest("[data-guide]");
    if (g) {
      var target = document.getElementById("guide-" + g.getAttribute("data-guide"));
      if (target) { ev.preventDefault(); target.scrollIntoView({ behavior: "smooth", block: "start" }); markGuide(g.getAttribute("data-guide")); }
    }
  });

  document.addEventListener("keydown", function (ev) {
    var row = ev.target && ev.target.closest && ev.target.closest(".os-row[data-kind]");
    if (row && (ev.key === "Enter" || ev.key === " ") && !ev.target.closest(".os-switch")) { ev.preventDefault(); rowActivate(row); }
  });

  function syncSidebarBtn() {
    var layout = document.querySelector(".bslib-sidebar-layout");
    var open = !layout || !layout.classList.contains("sidebar-collapsed");
    document.querySelectorAll("[data-sidebar-toggle]").forEach(function (b) {
      b.textContent = open ? "‹" : "›";
      b.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // tell the server how much the page is scaled (root font size / 16) so the graph's labels grow with it
  var lastScale = null, scaleTimer = null;
  function sendScale() {
    var scale = Math.round(parseFloat(getComputedStyle(document.documentElement).fontSize) / 16 * 100) / 100;
    if (scale !== lastScale && window.Shiny && Shiny.setInputValue) { lastScale = scale; Shiny.setInputValue("ui_scale", scale); }
  }
  window.addEventListener("resize", function () { clearTimeout(scaleTimer); scaleTimer = setTimeout(sendScale, 250); });

  // guide: highlight the section that is currently being read
  function markGuide(topic) {
    document.querySelectorAll(".os-guide-tab").forEach(function (a) {
      var on = a.getAttribute("data-guide") === topic;
      a.classList.toggle("is-active", on);
      if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
  }

  var guideObserver = null;
  function watchGuide() {
    if (guideObserver) guideObserver.disconnect();
    guideObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) markGuide(e.target.id.replace("guide-", "")); });
    }, { rootMargin: "-15% 0px -75% 0px" });
    document.querySelectorAll(".os-doc-section").forEach(function (s) { guideObserver.observe(s); });
  }

  // re-translate content Shiny inserts later (modals, tabs)
  var observer = new MutationObserver(function (muts) {
    muts.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) translate(n); }); });
  });

  document.addEventListener("DOMContentLoaded", function () {
    observer.observe(document.body, { childList: true, subtree: true });
    setLang(storedLang());
  });

  $(document).on("shiny:connected", function () {
    var lang = storedLang();
    var sel = document.getElementById("lang");
    if (sel && sel.value !== lang) { sel.value = lang; $(sel).trigger("change"); }
    setLang(lang);
    markGuide("steps");
    sendScale();
    setTimeout(syncSidebarBtn, 300);
    var native = document.querySelector(".bslib-sidebar-layout > .collapse-toggle");
    if (native) new MutationObserver(syncSidebarBtn).observe(native, { attributes: true, attributeFilter: ["aria-expanded"] });
  });

  // the guide is re-rendered when the language changes
  $(document).on("shiny:value", function (ev) { if (ev.name === "guide_view") setTimeout(watchGuide, 0); });

  if (window.Shiny) {
    $(document).on("shiny:connected", function () {
      Shiny.addCustomMessageHandler("os-btn-state", function (s) {
        Object.keys(s).forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.classList.toggle("is-active", !!s[id]);
        });
      });
    });
  }
})();
