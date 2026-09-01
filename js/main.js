// Fo Guang Shan Temple of Toronto — shared site behavior

document.addEventListener("DOMContentLoaded", function () {
  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var isOpen = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
    // Close menu when a link is tapped (mobile)
    links.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        links.classList.remove("open");
      });
    });
  }

  // Mark current page's nav link as active
  var current = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-links a").forEach(function (a) {
    var href = a.getAttribute("href");
    if (href === current) a.classList.add("active");
  });

  // Newsletter form: no mailing-list backend, so this hands off to the
  // visitor's own email client with a pre-filled sign-up request. Nothing is
  // sent automatically — the visitor still has to review and hit send.
  var form = document.querySelector(".newsletter-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var emailInput = form.querySelector("input[type=email]");
      var email = emailInput ? emailInput.value.trim() : "";
      var lang = document.documentElement.lang.indexOf("zh") === 0 ? "zh" : "en";
      var subject = lang === "zh" ? "訂閱電子報" : "Newsletter Sign-up Request";
      var body = lang === "zh"
        ? "請將以下電子郵件地址加入電子報訂閱名單：\n\n" + email
        : "Please add the following email address to the temple newsletter list:\n\n" + email;
      var mailto = "mailto:info@fgs.ca"
        + "?subject=" + encodeURIComponent(subject)
        + "&body=" + encodeURIComponent(body);

      var note = form.querySelector(".form-note");
      if (note) {
        note.textContent = lang === "zh"
          ? "即將開啟您的電子郵件程式，內容已預先填寫 — 請確認後點擊「傳送」完成訂閱。"
          : "Opening your email app with the request pre-filled — just hit send to complete your sign-up.";
        note.style.color = "var(--maroon-dark)";
      }
      window.location.href = mailto;
      form.reset();
    });
  }

  // "Service" nav dropdown. Desktop reveals the panel on hover via CSS
  // alone (no JS needed for that) — this only wires the caret button for
  // click/tap toggling (touch devices, keyboard users) and closes an open
  // panel when the user clicks anywhere outside it.
  document.querySelectorAll(".nav-item-dropdown").forEach(function (item) {
    var caret = item.querySelector(".nav-dropdown-caret");
    if (!caret) return;
    caret.addEventListener("click", function (e) {
      e.preventDefault();
      var isOpen = item.classList.toggle("open");
      caret.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  });
  document.addEventListener("click", function (e) {
    document.querySelectorAll(".nav-item-dropdown.open").forEach(function (item) {
      if (item.contains(e.target)) return;
      item.classList.remove("open");
      var caret = item.querySelector(".nav-dropdown-caret");
      if (caret) caret.setAttribute("aria-expanded", "false");
    });
  });

  // Recent-events carousel (homepage): arrow buttons scroll the track by
  // roughly one slide-width. The track itself is a plain scrollable flex
  // row (scroll-snap handles alignment), so this is optional enhancement —
  // dragging/swiping the track directly always works even without JS.
  document.querySelectorAll(".carousel-arrow").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var track = document.querySelector(btn.getAttribute("data-carousel-target"));
      if (!track) return;
      var slide = track.querySelector(".event-slide");
      var amount = slide ? slide.getBoundingClientRect().width + 20 : 280;
      track.scrollBy({
        left: btn.getAttribute("data-carousel-dir") === "prev" ? -amount : amount,
        behavior: "smooth"
      });
    });
  });
});
