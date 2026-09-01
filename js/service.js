// Fo Guang Shan Temple of Toronto — Service page expand/collapse sections
//
// Each .service-block has a .service-toggle button and a .service-block-body
// that starts collapsed (max-height: 0 in CSS). This measures the body's
// real height so the open/close transition animates smoothly regardless of
// how much text each section holds, and supports deep-linking: opening
// service.html#education (from the header dropdown, or any link on the
// site) auto-expands that one section and scrolls to it — while landing on
// bare service.html (no hash, or the "Service" label itself, which links
// to service.html with no anchor) leaves every section collapsed.

(function () {
  function setToggleState(block, open) {
    var toggle = block.querySelector(".service-toggle");
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    block.classList.toggle("open", open);
  }

  function openBlock(block, animate) {
    var body = block.querySelector(".service-block-body");
    setToggleState(block, true);
    if (!body) return;
    if (animate === false) {
      var prevTransition = body.style.transition;
      body.style.transition = "none";
      body.style.maxHeight = body.scrollHeight + "px";
      // Re-enable the transition on the next frame so a later close/resize
      // still animates, without animating this initial open.
      requestAnimationFrame(function () { body.style.transition = prevTransition; });
    } else {
      body.style.maxHeight = body.scrollHeight + "px";
    }
  }

  function closeBlock(block) {
    var body = block.querySelector(".service-block-body");
    setToggleState(block, false);
    if (body) body.style.maxHeight = "0px";
  }

  function closeAll() {
    document.querySelectorAll(".service-block.open").forEach(closeBlock);
  }

  // Waits for the *next* fully-settled layout (one paint past the one
  // triggered by open/close) before scrolling, so the scroll targets the
  // section's real, post-expand position instead of a stale one measured
  // mid-transition — this is what made "jump to the section" sometimes land
  // inside the newly-opened body instead of at the photo header above it.
  function afterLayoutSettles(fn) {
    requestAnimationFrame(function () { requestAnimationFrame(fn); });
  }

  function openFromHash() {
    var id = decodeURIComponent(window.location.hash.replace("#", ""));
    if (!id) {
      closeAll();
      return false;
    }
    var block = document.getElementById(id);
    if (!block || !block.classList.contains("service-block")) {
      closeAll();
      return false;
    }
    document.querySelectorAll(".service-block.open").forEach(function (b) {
      if (b !== block) closeBlock(b);
    });
    openBlock(block, false);
    afterLayoutSettles(function () {
      block.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return true;
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".service-block").forEach(function (block) {
      var toggle = block.querySelector(".service-toggle");
      if (!toggle) return;
      toggle.addEventListener("click", function () {
        if (block.classList.contains("open")) closeBlock(block);
        else openBlock(block, true);
      });
    });

    // Landing on service.html with no hash (including via the bare
    // "Service" nav link) leaves everything collapsed — openFromHash()
    // already does that itself when there's no usable hash, so it's safe
    // to just call it once up front rather than special-casing this.
    openFromHash();

    window.addEventListener("hashchange", openFromHash);

    // If the window is resized while a section is open, its measured
    // max-height can go stale (text reflows to more/fewer lines).
    var resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        document.querySelectorAll(".service-block.open .service-block-body").forEach(function (body) {
          body.style.maxHeight = body.scrollHeight + "px";
        });
      }, 150);
    });
  });
})();
