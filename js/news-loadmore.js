// Fo Guang Shan Temple of Toronto — News "Load More" pagination
//
// The News page lists every story in the HTML (newest first) so nothing
// depends on JavaScript to exist or be indexable. Once there are more than
// NEWS_LOADMORE_THRESHOLD cards, this script hides everything past the
// first NEWS_LOADMORE_INITIAL and reveals NEWS_LOADMORE_STEP more at a time
// — either by clicking the "Load More" button or by scrolling it into view.
// If this script fails to load for any reason, every card is already in the
// page and simply shows (same fail-safe pattern as js/sheets-feed.js).

(function () {
  var THRESHOLD = 15;
  var INITIAL = 9;
  var STEP = 6;

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.getElementById("news-cards");
    if (!container) return;

    var cards = Array.prototype.slice.call(container.children).filter(function (el) {
      return el.classList.contains("news-card");
    });
    if (cards.length <= THRESHOLD) return;

    var lang = document.documentElement.lang.indexOf("zh") === 0 ? "zh" : "en";
    var shown = INITIAL;
    cards.forEach(function (card, i) {
      if (i >= shown) card.style.display = "none";
    });

    var wrap = document.createElement("div");
    wrap.className = "news-loadmore-wrap";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-outline news-loadmore-btn";
    btn.textContent = lang === "zh" ? "載入更多" : "Load More";
    wrap.appendChild(btn);
    container.insertAdjacentElement("afterend", wrap);

    var observer;
    function reveal() {
      var next = cards.slice(shown, shown + STEP);
      next.forEach(function (card) { card.style.display = ""; });
      shown += next.length;
      if (shown >= cards.length) {
        if (observer) observer.disconnect();
        wrap.remove();
      }
    }

    btn.addEventListener("click", reveal);

    // Also auto-load as the button scrolls into view, so scrolling down the
    // page feels continuous — the click handler above still works as a
    // fallback if IntersectionObserver isn't available.
    if ("IntersectionObserver" in window) {
      observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) reveal();
        });
      }, { rootMargin: "200px" });
      observer.observe(btn);
    }
  });
})();
