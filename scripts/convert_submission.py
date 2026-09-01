#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_submission.py — turn a filled-out submission Doc into a live page.

Takes a Google Doc (filled out from templates/fgs-content-submission-template.docx),
fetches its published plain-text export, parses the labeled fields, and:

  1. Generates a new detail page in events/<slug>.html + zh/events/<slug>.html
     (or news/<slug>.html + zh/news/<slug>.html), matching the site's existing
     design.
  2. Inserts a matching summary row/card into the listing page
     (events.html + zh/events.html, or news.html + zh/news.html), in date order.

Nothing is committed to git — review the new/changed files yourself and
commit when you're happy with them (see README.md for the full workflow).

USAGE
-----
    python scripts/convert_submission.py "<google-doc-url-or-id>"
    python scripts/convert_submission.py "<google-doc-url-or-id>" --image path/to/poster.jpg
    python scripts/convert_submission.py "<google-doc-url-or-id>" --dry-run

See README.md → "Adding content via the submission Doc" for the full
step-by-step (how to get a Doc into the right shareable state, what each
flag does, and what to check afterward).
"""

import argparse
import datetime
import os
import re
import shutil
import sys
import urllib.request
import urllib.error

# Windows consoles often default to a legacy code page (cp1252) that can't
# print Chinese text — reconfigure stdout/stderr to UTF-8 so status messages
# with Chinese titles don't crash the script. No-op on setups where this
# isn't supported (older Python) or isn't needed (most non-Windows terminals).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Registration fallback for events that don't have their own sign-up form —
# matches the site-wide convention already in use.
DEFAULT_REGISTRATION_URL = "https://form.jotform.com/222486208918059"

FIELD_ALIASES = {
    "content type": "content_type",
    "title (english)": "title_en",
    "title (chinese)": "title_zh",
    "date": "date",
    "time": "time",
    "venue / location": "venue",
    "venue": "venue",
    "image url or file": "image",
    "registration link": "registration",
    "source / reference link": "source",
    "summary (english)": "summary_en",
    "summary (chinese)": "summary_zh",
}


# ---------------------------------------------------------------------------
# Fetching + parsing the Doc
# ---------------------------------------------------------------------------

def extract_doc_id(url_or_id):
    """Accept a full Google Docs URL or a bare document ID."""
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url_or_id)
    if m:
        return m.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]{20,}", url_or_id.strip()):
        return url_or_id.strip()
    raise ValueError(
        "Couldn't find a Google Doc ID in that input. Pass either the full "
        "share URL (https://docs.google.com/document/d/<ID>/edit...) or the "
        "bare <ID> from it."
    )


def fetch_doc_text(doc_id):
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    req = urllib.request.Request(export_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"Could not fetch the Doc (HTTP {e.code}). Make sure it's shared "
            f"as 'Anyone with the link can view' (Share button, top right of "
            f"the Doc), then try again."
        )
    return raw.decode("utf-8", errors="replace")


def parse_fields(text):
    """
    Parses "Label<TAB>Value" lines, which is how Google Docs' plain-text
    export renders a two-column table row. Only the FIRST occurrence of each
    label is kept, so the worked examples further down the template
    (which reuse the same labels) are safely ignored.
    """
    fields = {}
    for line in text.splitlines():
        if "\t" not in line:
            continue
        label, _, value = line.partition("\t")
        key = FIELD_ALIASES.get(label.strip().lower().rstrip(":"))
        if key and key not in fields:
            value = value.strip()
            if value and not value.lower().startswith(("type your", "e.g.", "optional", "paste a link", "leave blank")):
                fields[key] = value
    return fields


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def slugify(title):
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def parse_date(date_str):
    """Best-effort parse of 'September 6, 2026' style dates. Returns a date
    object, or None if it can't be parsed (in which case the new item is
    appended at the end of the listing instead of inserted in order)."""
    if not date_str:
        return None
    cleaned = re.split(r"[–—-]", date_str)[0].strip()  # take the start of a date range
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def month_day_badge(d, lang):
    if d is None:
        return ("&#9737;", "&#9737;")
    if lang == "en":
        return (d.strftime("%b"), str(d.day))
    return (f"{d.month}月", str(d.day))


def copy_local_image(image_field, slug, image_arg):
    """If --image was passed, copy it into assets/uploads/ and return the
    site-relative path. Otherwise, if the Doc's Image field already looks
    like a URL, use it as-is (hotlinked)."""
    if image_arg:
        ext = os.path.splitext(image_arg)[1] or ".jpg"
        dest_dir = os.path.join(ROOT, "assets", "uploads")
        os.makedirs(dest_dir, exist_ok=True)
        dest_name = f"{slug}{ext}"
        shutil.copy2(image_arg, os.path.join(dest_dir, dest_name))
        return f"assets/uploads/{dest_name}"
    if image_field and image_field.startswith("http"):
        return image_field
    return None


# ---------------------------------------------------------------------------
# Page templates (mirrors the header/footer already used across the site)
# ---------------------------------------------------------------------------

# Head/tail of the nav — the "Service" dropdown (Cultivation/Education/
# Spiritual Care, all anchors into service.html) is inserted between them
# by header() below, matching the markup already used across the site.
NAV_EN_HEAD = [("index.html", "Home"), ("about.html", "About")]
NAV_EN_TAIL = [
    ("events.html", "Calendar"), ("news.html", "News"), ("participate.html", "Participate"),
    ("contact.html", "Contact"), ("donate.html", "Donate"),
]
NAV_ZH_HEAD = [("index.html", "首頁"), ("about.html", "關於我們")]
NAV_ZH_TAIL = [
    ("events.html", "行事曆"), ("news.html", "佛光新聞"), ("participate.html", "加入佛光"),
    ("contact.html", "聯繫我們"), ("donate.html", "捐款"),
]

FONTS_LINK = ('<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&'
              'family=Noto+Serif+TC:wght@600;700&family=Noto+Sans:wght@400;500;600;700&'
              'family=Noto+Sans+TC:wght@400;500;600;700&display=swap" rel="stylesheet">')


def service_dropdown(base, is_zh_page):
    """The header's "Service"/"服務" dropdown — Cultivation, Education, and
    Spiritual Care all live as expandable sections on one page
    (service.html), not separate pages, so every nav item below points at
    an anchor on it rather than its own file."""
    label = "服務" if is_zh_page else "Service"
    caret_label = "展開服務選單" if is_zh_page else "Toggle Service menu"
    cultivation = "修持活動" if is_zh_page else "Cultivation"
    education = "文化教育" if is_zh_page else "Education"
    spiritual_care = "心靈關懷" if is_zh_page else "Spiritual Care"
    return f'''      <div class="nav-item-dropdown">
        <div class="nav-dropdown-head">
          <a href="{base}service.html">{label}</a>
          <button class="nav-dropdown-caret" type="button" aria-expanded="false" aria-label="{caret_label}">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
          </button>
        </div>
        <div class="nav-dropdown-panel">
          <a href="{base}service.html#cultivation">{cultivation}</a>
          <a href="{base}service.html#education">{education}</a>
          <a href="{base}service.html#spiritual-care">{spiritual_care}</a>
        </div>
      </div>'''


def header(base, is_zh_page, lang_href):
    head = NAV_ZH_HEAD if is_zh_page else NAV_EN_HEAD
    tail = NAV_ZH_TAIL if is_zh_page else NAV_EN_TAIL
    lang_label = "EN" if is_zh_page else "中文"
    donate_label = "捐款" if is_zh_page else "Donate"
    toggle_label = "開啟導覽選單" if is_zh_page else "Toggle navigation"
    skip_label = "跳至主要內容" if is_zh_page else "Skip to main content"
    brand_top = "多倫多佛光山" if is_zh_page else "Fo Guang Shan Temple of Toronto"
    head_html = "\n".join(f'      <a href="{base}{href}">{label}</a>' for href, label in head)
    tail_html = "\n".join(f'      <a href="{base}{href}">{label}</a>' for href, label in tail)
    links_html = head_html + "\n" + service_dropdown(base, is_zh_page) + "\n" + tail_html
    return f'''<a class="skip-link" href="#main">{skip_label}</a>

<header class="site-header">
  <nav class="nav">
    <a class="brand" href="{base}index.html">
      <img class="logo-img" src="{base}assets/logo.png" alt="{brand_top}">
    </a>
    <div class="nav-links">
{links_html}
    </div>
    <div class="nav-right">
      <a class="lang-switch" href="{lang_href}" hreflang="{'en' if is_zh_page else 'zh'}">{lang_label}</a>
      <div class="nav-cta desktop-only">
        <a class="btn btn-gold" href="{base}donate.html">{donate_label}</a>
      </div>
      <button class="nav-toggle" aria-label="{toggle_label}" aria-expanded="false">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
    </div>
  </nav>
</header>'''


def footer(base, is_zh_page):
    if is_zh_page:
        return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">
          <img class="logo-img footer-logo" src="{base}assets/logo.png" alt="多倫多佛光山">
        </div>
        <p style="color:#a89d8d; font-size:0.9rem; max-width:32ch;">以文化弘揚佛法，以教育培養人才，以慈善福利社會，以共修淨化人心。</p>
        <div class="footer-social">
          <a href="https://facebook.com/fgstoronto" aria-label="Facebook" target="_blank" rel="noopener"><span style="color:#fff;font-weight:700;font-size:0.75rem;">FB</span></a>
          <a href="https://youtube.com/FGSToronto" aria-label="YouTube" target="_blank" rel="noopener"><span style="color:#fff;font-weight:700;font-size:0.75rem;">YT</span></a>
          <a href="https://instagram.com/fgstoronto" aria-label="Instagram" target="_blank" rel="noopener"><span style="color:#fff;font-weight:700;font-size:0.75rem;">IG</span></a>
        </div>
      </div>
      <div>
        <h4>探索</h4>
        <a href="{base}about.html">關於我們</a>
        <a href="{base}service.html#cultivation">修持活動</a>
        <a href="{base}service.html#education">文化教育</a>
        <a href="{base}service.html#spiritual-care">心靈關懷</a>
        <a href="{base}participate.html">加入佛光</a>
      </div>
      <div>
        <h4>聯繫</h4>
        <a href="{base}events.html">行事曆</a>
        <a href="{base}news.html">佛光新聞</a>
        <a href="{base}global.html">全球道場</a>
        <a href="{base}contact.html">聯繫我們</a>
      </div>
      <div>
        <h4>參訪</h4>
        <a href="{base}contact.html">6525 Millcreek Drive<br>Mississauga, ON L5N 7K6</a>
        <a href="tel:+19058140465">(905) 814-0465</a>
        <a href="mailto:info@fgs.ca">info@fgs.ca</a>
        <a href="{base}donate.html">立即捐款</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 多倫多佛光山（I.B.P.S. of Toronto）版權所有。</span>
      <span><a href="#">隱私權政策</a> &middot; <a href="#">無障礙聲明</a></span>
    </div>
  </div>
</footer>

<script src="{base}js/main.js"></script>'''
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">
          <img class="logo-img footer-logo" src="{base}assets/logo.png" alt="Fo Guang Shan Temple of Toronto">
        </div>
        <p style="color:#a89d8d; font-size:0.9rem; max-width:32ch;">Connecting people with Humanistic Buddhism &mdash; a spiritual and cultural home for the Greater Toronto Area.</p>
        <div class="footer-social">
          <a href="https://facebook.com/fgstoronto" aria-label="Facebook" target="_blank" rel="noopener"><span style="color:#fff;font-weight:700;font-size:0.75rem;">FB</span></a>
          <a href="https://youtube.com/FGSToronto" aria-label="YouTube" target="_blank" rel="noopener"><span style="color:#fff;font-weight:700;font-size:0.75rem;">YT</span></a>
          <a href="https://instagram.com/fgstoronto" aria-label="Instagram" target="_blank" rel="noopener"><span style="color:#fff;font-weight:700;font-size:0.75rem;">IG</span></a>
        </div>
      </div>
      <div>
        <h4>Explore</h4>
        <a href="{base}about.html">About</a>
        <a href="{base}service.html#cultivation">Cultivation</a>
        <a href="{base}service.html#education">Education</a>
        <a href="{base}service.html#spiritual-care">Spiritual Care</a>
        <a href="{base}participate.html">Participate</a>
      </div>
      <div>
        <h4>Connect</h4>
        <a href="{base}events.html">Calendar</a>
        <a href="{base}news.html">News &amp; Newsletter</a>
        <a href="{base}global.html">Global Affiliations</a>
        <a href="{base}contact.html">Contact</a>
      </div>
      <div>
        <h4>Visit</h4>
        <a href="{base}contact.html">6525 Millcreek Drive<br>Mississauga, ON L5N 7K6</a>
        <a href="tel:+19058140465">(905) 814-0465</a>
        <a href="mailto:info@fgs.ca">info@fgs.ca</a>
        <a href="{base}donate.html">Make a Donation</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 Fo Guang Shan Temple of Toronto (I.B.P.S. of Toronto). All rights reserved.</span>
      <span><a href="#">Privacy Policy</a> &middot; <a href="#">Accessibility Statement</a></span>
    </div>
  </div>
</footer>

<script src="{base}js/main.js"></script>'''


def event_detail_page(base, is_zh_page, lang_href, f, slug, badge_top, badge_day, img_url):
    lang_attr = 'lang="zh-Hant"' if is_zh_page else 'lang="en"'
    eyebrow = "活動" if is_zh_page else "Event"
    reg_label = "報名" if is_zh_page else "Registration"
    back_label = "&larr; 返回行事曆" if is_zh_page else "&larr; Back to Calendar"
    venue_heading = "地點" if is_zh_page else "Venue"
    about_heading = "關於此活動" if is_zh_page else "About This Event"

    title = f["title_zh"] if is_zh_page and f.get("title_zh") else f["title_en"]
    summary = f["summary_zh"] if is_zh_page and f.get("summary_zh") else f.get("summary_en", "")
    date_line = f.get("date", "")
    meta_line = f.get("time", "")
    venue = f.get("venue", "")
    reg_url = f.get("registration") or DEFAULT_REGISTRATION_URL
    poster = img_url or ""

    return f'''<!doctype html>
<html {lang_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {"多倫多佛光山" if is_zh_page else "Fo Guang Shan Temple of Toronto"}</title>
<meta name="description" content="{title} — {date_line}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONTS_LINK}
<link rel="stylesheet" href="{base}css/styles.css">
</head>
<body>
{header(base, is_zh_page, lang_href)}

<main id="main">

  <section class="page-hero">
    <div class="container">
      <span class="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{date_line} &middot; {meta_line}</p>
    </div>
  </section>

  <section>
    <div class="container">
      <div class="two-col">
        <div>
          <a class="event-poster-link-large" href="{poster}" target="_blank" rel="noopener">
            <img class="event-poster-large" src="{poster}" alt="{title}" loading="lazy">
          </a>
        </div>
        <div>
          <div class="event-date" style="display:inline-flex; flex-direction:column; padding:14px 22px; margin-bottom:20px;">
            <span class="month">{badge_top}</span><span class="day">{badge_day}</span>
          </div>
          <h2 style="margin-top:0;">{about_heading}</h2>
          <p>{summary}</p>
          <div class="quote-block" style="font-style:normal;">
            <strong>{venue_heading}</strong>
            <p>{venue}</p>
          </div>
          <a class="btn btn-gold" href="{reg_url}" target="_blank" rel="noopener" style="margin-top:12px;">{reg_label}</a>
          <div style="margin-top:20px;">
            <a class="btn btn-outline" href="{base}events.html">{back_label}</a>
          </div>
        </div>
      </div>
    </div>
  </section>

</main>

{footer(base, is_zh_page)}
</body>
</html>
'''


def news_detail_page(base, is_zh_page, lang_href, f, slug, img_url, source_url):
    lang_attr = 'lang="zh-Hant"' if is_zh_page else 'lang="en"'
    eyebrow = "佛光新聞" if is_zh_page else "Temple News"
    back_label = "&larr; 返回佛光新聞" if is_zh_page else "&larr; Back to News"

    title = f["title_zh"] if is_zh_page and f.get("title_zh") else f["title_en"]
    summary = f["summary_zh"] if is_zh_page and f.get("summary_zh") else f.get("summary_en", "")
    date_line = f.get("date", "")
    poster = img_url or ""
    # News pages no longer link out to the source (matches the rest of the
    # site — every existing story is an original write-up, not a "read more
    # on fgs.ca" pointer). The source is still worth keeping for whoever
    # reviews/edits this page later, so it's stashed as a comment instead
    # of a visible link.
    source_comment = f"<!-- source: {source_url} -->\n  " if source_url else ""

    return f'''<!doctype html>
<html {lang_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {"多倫多佛光山" if is_zh_page else "Fo Guang Shan Temple of Toronto"}</title>
<meta name="description" content="{title} — {date_line}">
{source_comment}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONTS_LINK}
<link rel="stylesheet" href="{base}css/styles.css">
</head>
<body>
{header(base, is_zh_page, lang_href)}

<main id="main">

  <section class="page-hero">
    <div class="container">
      <span class="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{date_line}</p>
    </div>
  </section>

  <section>
    <div class="container">
      <div class="two-col">
        <div>
          <div class="map-frame">
            <img src="{poster}" alt="{title}" loading="lazy" style="width:100%; display:block;">
          </div>
        </div>
        <div>
          <p>{summary}</p>
          <a class="btn btn-outline" href="{base}news.html" style="margin-top:8px;">{back_label}</a>
        </div>
      </div>
    </div>
  </section>

</main>

{footer(base, is_zh_page)}
</body>
</html>
'''


# ---------------------------------------------------------------------------
# Listing-page insertion
# ---------------------------------------------------------------------------

def build_event_row(f, slug, badge_top, badge_day, poster, is_zh_page):
    title = f["title_zh"] if is_zh_page and f.get("title_zh") else f["title_en"]
    meta = f.get("time", "")
    detail_href = f"{'' if is_zh_page else ''}events/{slug}.html"
    label = "詳情" if is_zh_page else "Details"
    poster_html = (
        f'<a class="event-poster-link" href="{detail_href}" aria-label="{title}">'
        f'<img class="event-poster" src="{poster}" alt="{title}" loading="lazy"></a>'
        if poster else ""
    )
    return f'''      <div class="event-row">
        <div class="event-date"><span class="month">{badge_top}</span><span class="day">{badge_day}</span></div>
        <div class="event-body">
          <h4>{title}</h4>
          <p class="meta">{meta}</p>
        </div>
        <div class="event-actions">
          {poster_html}
          <a class="btn btn-outline event-cta" href="{detail_href}">{label}</a>
        </div>
      </div>
'''


def build_news_card(f, slug, poster, is_zh_page):
    title = f["title_zh"] if is_zh_page and f.get("title_zh") else f["title_en"]
    summary = f["summary_zh"] if is_zh_page and f.get("summary_zh") else f.get("summary_en", "")
    date_label = f.get("date", "")
    return f'''        <a class="card news-card" href="news/{slug}.html">
          <img class="news-thumb" src="{poster}" alt="" loading="lazy">
          <span class="pill">{date_label}</span>
          <h3 style="margin-top:14px;">{title}</h3>
          <p>{summary}</p>
        </a>
'''


def _parse_event_row_date(row_html, year):
    """Best-effort: pull the month/day badge back out of an existing
    <div class="event-row"> block and turn it into a date, for ordering
    against a new submission. Returns None (never sortable) for recurring
    rows like "Every / Sun" or "Ongoing / ☉" — those aren't calendar dates."""
    m = re.search(r'<span class="month">([^<]+)</span><span class="day">([^<]+)</span>', row_html)
    if not m:
        return None
    month_raw, day_raw = m.group(1).strip(), m.group(2).strip()
    if not day_raw.isdigit():
        return None
    day = int(day_raw)
    try:
        if month_raw.endswith("月"):  # Chinese badge, e.g. "9月"
            return datetime.date(year, int(month_raw[:-1]), day)
        return datetime.datetime.strptime(f"{month_raw} {day} {year}", "%b %d %Y").date()
    except (ValueError, IndexError):
        return None


def _find_matching_div_close(content, search_from):
    """Given an index right after a <div ...> opening tag's '>', scan
    forward tracking <div>/</div> nesting depth and return the index of the
    '<' that starts THIS div's own matching closing tag.

    A plain non-greedy regex like `.*?</div>` can't do this reliably —
    it stops at the first </div> it finds, which for a container holding
    several rows/cards is almost always the FIRST row's own closing tag,
    not the container's. That was a real (pre-existing) bug: it silently
    truncated `inner` to roughly "just the first row," so every insertion
    landed right after row/card #1 regardless of any date-ordering logic
    layered on top of it."""
    depth = 1
    for tm in re.finditer(r"<(/?)div\b", content[search_from:]):
        depth += -1 if tm.group(1) else 1
        if depth == 0:
            return search_from + tm.start()
    raise ValueError("unbalanced <div> tags")


def insert_into_listing(listing_path, container_id, new_block, new_date):
    """Insert new_block into the named container, in date order when a date
    is available and the existing rows parse cleanly; otherwise falls back
    to appending at the end (news-cards, and any listing whose rows this
    can't confidently parse), which is always safe."""
    with open(listing_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    open_re = re.compile(r'<div id="' + re.escape(container_id) + r'"[^>]*>')
    om = open_re.search(content)
    if not om:
        print(f"  ! Could not find #{container_id} in {listing_path} — skipping listing insert.")
        return
    try:
        close_start = _find_matching_div_close(content, om.end())
    except ValueError:
        print(f"  ! Could not find the matching closing tag for #{container_id} in {listing_path} — skipping listing insert.")
        return

    inner = content[om.end():close_start]

    if container_id == "news-cards":
        # The News listing is strictly newest-first (see js/news-loadmore.js,
        # which relies on that DOM order to decide what's "the first 9").
        # A new submission is being published now, so it always belongs at
        # the top — no date parsing needed, and nothing to get wrong.
        new_inner = "\n" + new_block + inner.lstrip("\n")
    elif container_id == "special-events" and new_date is not None:
        row_re = re.compile(r'<div class="event-row">.*?</div>\s*</div>\n', re.DOTALL)
        rows = list(row_re.finditer(inner))
        insert_at = None
        for row_m in rows:
            row_date = _parse_event_row_date(row_m.group(0), new_date.year)
            if row_date is None:
                # Couldn't confidently parse an existing row — don't guess
                # at a position among rows we can't compare against.
                insert_at = None
                break
            if row_date > new_date:
                insert_at = row_m.start()
                break
        if insert_at is not None:
            new_inner = inner[:insert_at] + new_block + inner[insert_at:]
        else:
            new_inner = inner.rstrip() + "\n" + new_block
    else:
        new_inner = inner.rstrip() + "\n" + new_block

    content = content[:om.end()] + new_inner + content[close_start:]
    with open(listing_path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", help="Google Doc URL or ID (must be shared 'Anyone with the link can view')")
    ap.add_argument("--image", help="Path to a local image file to attach (copied into assets/uploads/)")
    ap.add_argument("--dry-run", action="store_true", help="Parse and show what would be created, but don't write any files")
    args = ap.parse_args()

    doc_id = extract_doc_id(args.doc)
    print(f"Fetching Doc {doc_id} ...")
    text = fetch_doc_text(doc_id)
    fields = parse_fields(text)

    required = ["content_type", "title_en", "date", "summary_en"]
    missing = [r for r in required if not fields.get(r)]
    if missing:
        raise SystemExit(
            "Missing required field(s): " + ", ".join(missing) +
            "\nMake sure the Doc follows the submission template's table layout."
        )

    content_type = fields["content_type"].strip().lower()
    if content_type not in ("event", "news"):
        raise SystemExit(f"Content Type must be 'Event' or 'News', got: {fields['content_type']!r}")

    slug = slugify(fields["title_en"])
    d = parse_date(fields.get("date"))
    poster = copy_local_image(fields.get("image"), slug, args.image)
    if not poster:
        print("  ! No image URL and no --image given — pages will have a blank poster slot.")

    print(f"  Type: {content_type}")
    print(f"  Slug: {slug}")
    print(f"  Title (EN): {fields['title_en']}")
    print(f"  Title (ZH): {fields.get('title_zh', '(none — English will show on both)')}")
    print(f"  Date: {fields.get('date')}  Time: {fields.get('time', '')}")
    print(f"  Poster: {poster or '(none)'}")

    if args.dry_run:
        print("\n--dry-run set: no files were written.")
        return

    if content_type == "event":
        badge_en = month_day_badge(d, "en")
        badge_zh = month_day_badge(d, "zh")
        reg_url = fields.get("registration") or DEFAULT_REGISTRATION_URL

        en_path = os.path.join(ROOT, "events", f"{slug}.html")
        zh_path = os.path.join(ROOT, "zh", "events", f"{slug}.html")
        os.makedirs(os.path.dirname(en_path), exist_ok=True)
        os.makedirs(os.path.dirname(zh_path), exist_ok=True)

        with open(en_path, "w", encoding="utf-8") as fh:
            fh.write(event_detail_page("../", False, f"../zh/events/{slug}.html", fields, slug, badge_en[0], badge_en[1], poster))
        with open(zh_path, "w", encoding="utf-8") as fh:
            fh.write(event_detail_page("../../", True, f"../../events/{slug}.html", fields, slug, badge_zh[0], badge_zh[1], poster))
        print(f"  Wrote {os.path.relpath(en_path, ROOT)}")
        print(f"  Wrote {os.path.relpath(zh_path, ROOT)}")

        insert_into_listing(
            os.path.join(ROOT, "events.html"), "special-events",
            build_event_row(fields, slug, badge_en[0], badge_en[1], poster, False), d,
        )
        insert_into_listing(
            os.path.join(ROOT, "zh", "events.html"), "special-events",
            build_event_row(fields, slug, badge_zh[0], badge_zh[1], poster, True), d,
        )
        print("  Updated events.html and zh/events.html")
        print(f"  Registration link: {reg_url}")

    else:  # news
        source_url = fields.get("source", "")
        en_path = os.path.join(ROOT, "news", f"{slug}.html")
        zh_path = os.path.join(ROOT, "zh", "news", f"{slug}.html")
        os.makedirs(os.path.dirname(en_path), exist_ok=True)
        os.makedirs(os.path.dirname(zh_path), exist_ok=True)

        with open(en_path, "w", encoding="utf-8") as fh:
            fh.write(news_detail_page("../", False, f"../zh/news/{slug}.html", fields, slug, poster, source_url))
        with open(zh_path, "w", encoding="utf-8") as fh:
            fh.write(news_detail_page("../../", True, f"../../news/{slug}.html", fields, slug, poster, source_url))
        print(f"  Wrote {os.path.relpath(en_path, ROOT)}")
        print(f"  Wrote {os.path.relpath(zh_path, ROOT)}")

        insert_into_listing(
            os.path.join(ROOT, "news.html"), "news-cards",
            build_news_card(fields, slug, poster, False), d,
        )
        insert_into_listing(
            os.path.join(ROOT, "zh", "news.html"), "news-cards",
            build_news_card(fields, slug, poster, True), d,
        )
        print("  Updated news.html and zh/news.html")

    print("\nDone. Nothing was committed — review the new/changed files, then")
    print("`git add` / `git commit` / `git push` yourself when you're happy with them.")


if __name__ == "__main__":
    main()
