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

  // a click scrolls smoothly past other sections: the clicked one stays marked until the scroll is over
  var clickedUntil = 0;
  document.addEventListener("click", function (ev) {
    var g = ev.target && ev.target.closest && ev.target.closest("[data-guide]");
    if (!g) return;
    var target = document.getElementById("guide-" + g.getAttribute("data-guide"));
    if (target) { ev.preventDefault(); clickedUntil = Date.now() + 1500; markGuide(g.getAttribute("data-guide")); target.scrollIntoView({ behavior: "smooth", block: "start" }); }
  });

  var guideObserver = null;
  function watchGuide() {
    if (guideObserver) guideObserver.disconnect();
    guideObserver = new IntersectionObserver(function (entries) {
      if (Date.now() < clickedUntil) return;
      entries.forEach(function (e) { if (e.isIntersecting) markGuide(e.target.id.replace("guide-", "")); });
    }, { rootMargin: "-15% 0px -75% 0px" });
    document.querySelectorAll(".os-doc-section").forEach(function (s) { guideObserver.observe(s); });
  }

  // the last section is too short to reach the reading line: at the end of the page it is the one being read
  window.addEventListener("scroll", function () {
    var guide = document.querySelector(".os-guide"), tabs = document.querySelectorAll(".os-guide-tab");
    if (Date.now() < clickedUntil || !guide || !guide.offsetParent || !tabs.length) return;
    if (Math.ceil(window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight - 2) markGuide(tabs[tabs.length - 1].getAttribute("data-guide"));
  }, { passive: true });

  $(document).on("shiny:connected", function () { markGuide("steps"); });
  // the guide is re-rendered when the language changes
  $(document).on("shiny:value", function (ev) { if (ev.name === "guide_view") setTimeout(watchGuide, 0); });
})();
