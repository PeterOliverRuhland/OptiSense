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

  // the legal notice (Impressum): a small dialog, opened by any element with data-os-imprint
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function imprint(opener) {
    var d = (window.OS_I18N || {})[current] || {}, t = function (k) { return d[k] !== undefined ? d[k] : k; };
    var old = document.getElementById("os-imprint");
    if (old) old.remove();
    var dlg = document.createElement("dialog"), mail = t("imprint_mail");
    dlg.id = "os-imprint";
    dlg.className = "os-dialog";
    dlg.setAttribute("aria-labelledby", "os-imprint-title");
    dlg.innerHTML = '<h2 id="os-imprint-title">' + esc(t("imprint")) + '</h2><p class="os-dialog-sub">' + esc(t("imprint_law")) + "</p>" +
      "<p>" + [t("imprint_name"), t("imprint_street"), t("imprint_city")].map(esc).join("<br>") + "</p>" +
      "<p><b>" + esc(t("imprint_contact")) + '</b><br><a href="mailto:' + esc(mail) + '">' + esc(mail) + "</a></p>" +
      '<div class="os-dialog-foot"><button type="button" class="btn os-btn os-btn-primary" data-os-close>' + esc(t("close")) + "</button></div>";
    document.body.appendChild(dlg);
    dlg.addEventListener("click", function (ev) { if (ev.target === dlg || ev.target.closest("[data-os-close]")) dlg.close(); });
    dlg.addEventListener("close", function () { dlg.remove(); if (opener && opener.focus) opener.focus(); });
    dlg.showModal();
  }
  document.addEventListener("click", function (ev) {
    var el = ev.target.closest && ev.target.closest("[data-os-imprint]");
    if (el) { ev.preventDefault(); imprint(el); }
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
