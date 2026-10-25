/* OptiSense browser helpers shared by all pages: language switching for static text and
   remembering the language. Page scripts: work.js, learn.js, guide.js. */
(function () {
  "use strict";
  var LANGS = Object.keys(window.OS_I18N || { en: 1 });
  var current = "en";

  function storedLang() {
    try { var v = window.localStorage.getItem("optisense-lang"); if (LANGS.indexOf(v) >= 0) return v; } catch (e) {}
    var nav = (navigator.language || "en").toLowerCase();
    return nav.indexOf("de") === 0 ? "de" : "en";
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
    document.documentElement.setAttribute("lang", lang);
    try { window.localStorage.setItem("optisense-lang", lang); } catch (e) {}
    translate(document);
  }

  // Shiny's own language select drives everything
  document.addEventListener("change", function (ev) {
    var t = ev.target;
    if (t && t.id === "lang") setLang(t.value);
  });

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
  });
})();
