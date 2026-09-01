// Fo Guang Shan Temple of Toronto — optional Google Sheet content feed
//
// Lets a non-technical editor update the Calendar and News pages by editing a
// Google Sheet instead of touching HTML. See EDITING.md for the full setup
// walkthrough (creating the sheet, publishing it, and what each column means).
//
// How it works: each URL below points to a Google Sheet published as CSV.
// On page load, this script fetches that CSV and, if it parses successfully
// with at least one usable row, replaces the static placeholder content in
// the matching container. If a URL is left blank, or the fetch fails for any
// reason (offline, sheet not published, typo in the link), the page silently
// keeps showing the hand-written fallback content that's already in the
// HTML — nothing breaks, nothing shows an error to visitors.
//
// Nothing here requires Claude, a build step, or any coding tool beyond a
// text editor to paste in a link once.

var SHEETS_FEED_CONFIG = {
  // Paste your published-CSV links between the quotes below.
  // Leave a URL as "" to keep using the hand-written fallback rows.
  eventsCsvUrl: {
    en: "",
    zh: ""
  },
  newsCsvUrl: {
    en: "",
    zh: ""
  }
};

(function () {
  function parseCSV(text) {
    // Minimal RFC4180-ish CSV parser: handles quoted fields containing
    // commas, quotes ("" escaping), and newlines — which is what Google
    // Sheets produces when you "Publish to web" as CSV.
    var rows = [];
    var row = [];
    var field = "";
    var inQuotes = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (inQuotes) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else { inQuotes = false; }
        } else {
          field += c;
        }
      } else if (c === '"') {
        inQuotes = true;
      } else if (c === ',') {
        row.push(field); field = "";
      } else if (c === '\n') {
        row.push(field); field = "";
        rows.push(row); row = [];
      } else if (c === '\r') {
        // ignore, \n handles the line break
      } else {
        field += c;
      }
    }
    if (field.length || row.length) { row.push(field); rows.push(row); }
    if (!rows.length) return [];

    var headers = rows[0].map(function (h) { return h.trim().toLowerCase(); });
    return rows.slice(1)
      .filter(function (r) { return r.some(function (cell) { return cell.trim() !== ""; }); })
      .map(function (r) {
        var obj = {};
        headers.forEach(function (h, idx) { obj[h] = (r[idx] || "").trim(); });
        return obj;
      });
  }

  function fetchCSV(url) {
    if (!url) return Promise.resolve(null);
    return fetch(url, { cache: "no-store" })
      .then(function (res) { if (!res.ok) throw new Error("Feed request failed: " + res.status); return res.text(); })
      .then(parseCSV)
      .catch(function (err) {
        console.warn("[sheets-feed] Could not load feed, keeping fallback content:", err.message);
        return null;
      });
  }

  function el(tag, className, html) {
    var e = document.createElement(tag);
    if (className) e.className = className;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function buildEventRow(row) {
    var wrap = el("div", "event-row");
    var date = el("div", "event-date");
    date.appendChild(el("span", "month", row.badge_top || ""));
    date.appendChild(el("span", "day", row.badge_bottom || ""));
    var body = el("div", "event-body");
    body.appendChild(el("h4", null, row.title || ""));
    if (row.meta) body.appendChild(el("p", "meta", row.meta));
    wrap.appendChild(date);
    wrap.appendChild(body);
    var link = document.createElement("a");
    link.className = "btn btn-outline event-cta";
    link.href = row.link_href || "contact.html";
    link.textContent = row.link_text || "Details";
    wrap.appendChild(link);
    return wrap;
  }

  function renderEvents(rows) {
    if (!rows || !rows.length) return;
    var special = rows.filter(function (r) { return (r.section || "").toLowerCase() !== "recurring"; });
    var recurring = rows.filter(function (r) { return (r.section || "").toLowerCase() === "recurring"; });

    var specialEl = document.getElementById("special-events");
    if (specialEl && special.length) {
      specialEl.innerHTML = "";
      special.forEach(function (r) { specialEl.appendChild(buildEventRow(r)); });
      specialEl.removeAttribute("data-fallback");
    }
    var recurringEl = document.getElementById("recurring-events");
    if (recurringEl && recurring.length) {
      recurringEl.innerHTML = "";
      recurring.forEach(function (r) { recurringEl.appendChild(buildEventRow(r)); });
      recurringEl.removeAttribute("data-fallback");
    }
  }

  function buildNewsCard(row) {
    var card = el("div", "card");
    if (row.pill) card.appendChild(el("span", "pill", row.pill));
    card.appendChild(el("h3", null, row.title || ""));
    card.lastChild.style.marginTop = "14px";
    if (row.body) card.appendChild(el("p", null, row.body));
    return card;
  }

  function renderNews(rows) {
    if (!rows || !rows.length) return;
    var container = document.getElementById("news-cards");
    if (!container) return;
    container.innerHTML = "";
    rows.forEach(function (r) { container.appendChild(buildNewsCard(r)); });
    container.removeAttribute("data-fallback");
  }

  document.addEventListener("DOMContentLoaded", function () {
    var lang = document.documentElement.lang.indexOf("zh") === 0 ? "zh" : "en";

    if (document.getElementById("special-events") || document.getElementById("recurring-events")) {
      fetchCSV(SHEETS_FEED_CONFIG.eventsCsvUrl[lang]).then(renderEvents);
    }
    if (document.getElementById("news-cards")) {
      fetchCSV(SHEETS_FEED_CONFIG.newsCsvUrl[lang]).then(renderNews);
    }
  });
})();
