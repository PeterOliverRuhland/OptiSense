/* Page “Guide”: the contents list scrolls to a section and highlights the section being read. */
(function () {
  "use strict";

  var PHONE = window.matchMedia("(max-width: 575.98px), (max-width: 1023.98px) and (max-height: 500px)");

  function markGuide(topic) {
    document.querySelectorAll(".os-guide-tab").forEach(function (a) {
      var on = a.getAttribute("data-guide") === topic;
      a.classList.toggle("is-active", on);
      if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
      // smartphones: the contents strip scrolls sideways to the current section
      if (on && PHONE.matches) {
        var nav = a.parentNode;
        nav.scrollTo({ left: a.offsetLeft - (nav.clientWidth - a.offsetWidth) / 2, behavior: "smooth" });
      }
    });
  }

  document.addEventListener("click", function (ev) {
    var g = ev.target && ev.target.closest && ev.target.closest("[data-guide]");
    if (!g) return;
    var target = document.getElementById("guide-" + g.getAttribute("data-guide"));
    if (target) { ev.preventDefault(); target.scrollIntoView({ behavior: "smooth", block: "start" }); markGuide(g.getAttribute("data-guide")); }
  });

  var guideObserver = null;
  function watchGuide() {
    if (guideObserver) guideObserver.disconnect();
    guideObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) markGuide(e.target.id.replace("guide-", "")); });
    }, { rootMargin: "-15% 0px -75% 0px" });
    document.querySelectorAll(".os-doc-section").forEach(function (s) { guideObserver.observe(s); });
  }

  $(document).on("shiny:connected", function () { markGuide("steps"); });
  // the guide is re-rendered when the language changes
  $(document).on("shiny:value", function (ev) { if (ev.name === "guide_view") setTimeout(watchGuide, 0); });
})();
