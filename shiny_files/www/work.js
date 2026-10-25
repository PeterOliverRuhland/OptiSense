/* Page “Model & solution” (start page): list-row interactions, the ? buttons, the sidebar button
   in the graph header, the page scale for the graph and the state of the run buttons. */
(function () {
  "use strict";

  document.addEventListener("change", function (ev) {
    var t = ev.target;
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
    if (tg) { var native = document.querySelector(".bslib-sidebar-layout > .collapse-toggle"); if (native) native.click(); [50, 400].forEach(function (d) { setTimeout(syncSidebarBtn, d); }); }
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

  // tell the server how much the page is scaled (root font size / 16) so the graph's labels grow with it,
  // and whether it is shown on a smartphone (one column, see work.css)
  var PHONE = window.matchMedia("(max-width: 575.98px), (max-width: 1023.98px) and (max-height: 500px)");
  var lastScale = null, lastPhone = null, scaleTimer = null;
  function sendScale() {
    if (!window.Shiny || !Shiny.setInputValue) return;
    var scale = Math.round(parseFloat(getComputedStyle(document.documentElement).fontSize) / 16 * 100) / 100;
    if (scale !== lastScale) { lastScale = scale; Shiny.setInputValue("ui_scale", scale); }
    if (PHONE.matches !== lastPhone) { lastPhone = PHONE.matches; Shiny.setInputValue("ui_phone", lastPhone); }
  }
  window.addEventListener("resize", function () { clearTimeout(scaleTimer); scaleTimer = setTimeout(sendScale, 250); });

  // smartphones: after a run, scroll to what changed – the graph shows the optimum, the results the analysis
  var scrollTo = null;
  document.addEventListener("click", function (ev) {
    var b = ev.target && ev.target.closest && ev.target.closest("#btn_opt, #btn_sens");
    if (b && PHONE.matches) scrollTo = b.id;
  });
  function revealResult(state) {
    if (!scrollTo || !state[scrollTo]) return;
    var target = document.querySelector(scrollTo === "btn_opt" ? ".os-graph" : ".os-results");
    scrollTo = null;
    if (target) setTimeout(function () { target.scrollIntoView({ behavior: "smooth", block: "start" }); }, 150);
  }

  $(document).on("shiny:connected", function () {
    sendScale();
    setTimeout(syncSidebarBtn, 300);
    var native = document.querySelector(".bslib-sidebar-layout > .collapse-toggle");
    if (native) new MutationObserver(syncSidebarBtn).observe(native, { attributes: true, attributeFilter: ["aria-expanded"] });
  });

  if (window.Shiny) {
    $(document).on("shiny:connected", function () {
      Shiny.addCustomMessageHandler("os-btn-state", function (s) {
        Object.keys(s).forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.classList.toggle("is-active", !!s[id]);
        });
        revealResult(s);
      });
    });
  }
})();
