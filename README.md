# Fo Guang Shan Temple of Toronto — Website Rebuild

A full static rebuild of the temple's public website, replacing the current official website.

## What this is

Plain HTML/CSS/JS, no build step or framework required. Ten pages sharing one
stylesheet and one small script:

```
index.html         Home
about.html          Mission, history, facility
cultivation.html    Dharma services
education.html      Education programs
participate.html    BLIA, YAD, volunteer groups
events.html         Calendar (real upcoming events; see note below)
news.html           Announcements + newsletter signup form (17 stories back
                    to July 1, 2026, newest first, with "Load More" paging)
global.html         Worldwide affiliation / BLIA network
donate.html         Donation methods & categories
contact.html        Three GTA locations, hours, map

zh/*.html           Chinese (Traditional) mirror of all 10 pages above,
                    same filenames, sourced from fgs.ca's own /ch/ pages

events/<slug>.html       One full page per event (English) — poster,
                          date, short original summary, Registration button
zh/events/<slug>.html    Same event pages, in Chinese
news/<slug>.html         One full page per news story (English) — photo,
                          date, short original summary, link to fgs.ca
zh/news/<slug>.html      Same news pages, in Chinese

css/styles.css      Shared design system (colors, type, components)
js/main.js          Mobile nav toggle, active-link highlighting, newsletter
                    form UX (mailto handoff, language-aware)
js/sheets-feed.js   Optional Google Sheet → live content feed for the
                    Calendar and News listing pages (see EDITING.md)
js/news-loadmore.js News listing pagination — hides everything past the
                    first 9 cards and reveals more via a "Load More" button
                    (click, or auto when scrolled into view) once the list
                    passes 15 stories; harmless no-op below that
```

## Editing without a developer

See [EDITING.md](EDITING.md) — it walks through updating events and news via
a Google Sheet (no HTML, no login to the site itself), and explains the
difference between the sign-up form here and actually sending newsletter
campaigns (which needs a real email service like Mailchimp).

## Adding content via the submission Doc → `scripts/convert_submission.py`

Turns a filled-out copy of
[`templates/fgs-content-submission-template.docx`](templates/fgs-content-submission-template.docx)
into a real page on the site — a full event or news write-up, not just a
listing-page row (that's what the Google Sheet feed above is for).

**Requires:** Python 3.7+ (nothing else — no `pip install`, it only uses the
standard library).

**See [instruction.md](instruction.md) for the complete guide** — the
template's fields, the step-by-step workflow, how News (always newest-first)
and Events (real chronological order) get inserted differently, what to do
if something goes wrong, and why news pages no longer link out to fgs.ca.

## Chinese (中文) version

`zh/` mirrors the English site page-for-page. Content was drafted from
fgs.ca's own `/ch/` pages (not machine-translated from the English copy), so
wording like the four core objectives, the founder's quotes, and event names
matches how the temple already describes itself in Chinese. A few notes:

- Every page has a language-switch pill in the header (`EN` / `中文`) linking
  to its counterpart in the other language.
- Street addresses are kept in English/Latin form on the Chinese pages, same
  as fgs.ca/ch does — Canadian addresses aren't usually translated.
- Two upcoming events (`Lotus Mornings`, the Lydia Chao talk) don't have an
  official Chinese title on the source site, so they're left in English on
  `zh/events.html` too, matching the temple's own practice.
- Fonts add Noto Serif TC / Noto Sans TC (Google Fonts) alongside the
  English faces so headings and body text render properly in Chinese.

## How to preview or deploy

No build tools needed — open `index.html` directly in a browser, or serve the
folder with any static host:

```bash
npx serve .
```

To publish, drop the whole folder onto any static host (Netlify, GitHub Pages,
Cloudflare Pages, or your own web server).

## Where the content came from

Per your request, real content was drafted from the temple's actual current
website, **fgs.ca** (not the Wix placeholder), covering mission, history,
programs, locations, and donation methods. A few things to double check before
this goes live:

- **`events.html`** / **`zh/events.html`** — lists all 10 currently-upcoming
  special events pulled from fgs.ca's own paginated events listing (both
  page 1 and page 2), plus the recurring weekly/ongoing items. Each row
  shows the real poster image (hotlinked from fgs.ca's own CDN, not
  downloaded/re-hosted); clicking it opens our own local page at
  `events/<slug>.html` (or `zh/events/<slug>.html`) instead of fgs.ca. The
  **Registration** button links straight to that event's real signup: a
  Google Form, a JotForm, or a DonorPerfect page, whichever fgs.ca itself
  uses for that specific event. For the recurring services that fgs.ca
  points at its own general donation page (no dedicated form exists there),
  this site instead uses the general-purpose JotForm
  (`https://form.jotform.com/222486208918059`) so every event has an actual
  sign-up form rather than a donation page standing in for one. This is a
  snapshot as of when it was last refreshed; fgs.ca's own listing changes
  as events pass and new ones are added, so re-pull it periodically (see
  `implementation.md` in the Claude
  project folder for the exact DOM structure this was scraped from).
- **`news.html`** / **`zh/news.html`** — lists the 5 real news stories from
  fgs.ca published August 1, 2026 or later (an earlier story from July 30
  was intentionally left out per that cutoff). Each card links to a local
  page at `news/<slug>.html` with a short original summary — not a copy of
  the full article — plus a "Read the full story on fgs.ca" link for anyone
  who wants the complete piece.
- **Newsletter signup** (`news.html`) is wired to a `mailto:` fallback (see
  `js/main.js`): submitting opens the visitor's own email client with a
  pre-filled message to info@fgs.ca — no third-party mailing list or backend
  required, but also no automatic list management. Upgrade to Formspree,
  Netlify Forms, or a real ESP (Mailchimp, etc.) later if you want automatic
  subscriber tracking.
- **Contact form / donation buttons** — donation instructions (cheque, e-transfer,
  PayPal) are described as text per fgs.ca; no payment collection happens on
  this site itself, consistent with the source site's approach.
- **中文 (Chinese) version** — done; see the "Chinese (中文) version" section
  above.
- **Logo** — `assets/logo.png` is the temple's real logo (provided by the
  user), cropped to its content bounds from the original file and used as-is
  in the header (`.logo-img`) and footer (`.footer-logo`) on every page in
  both languages. It has a transparent background, so it sits cleanly on
  both the cream header and the dark footer.
- **Photography** — beyond the logo, this rebuild still uses original line
  icons instead of downloaded photos for everything else, since real site
  photography is not ours to redistribute. Swap in the temple's own approved
  photos wherever you'd like — hero sections and location cards are the
  natural spots.

## Design

- Palette: warm gold + maroon on a cream background, echoing traditional
  temple color language, defined as CSS variables at the top of `styles.css`.
- Type: Playfair Display for headings, Noto Sans for body text (loaded via
  Google Fonts, with system-font fallbacks for offline use).
- Fully responsive with a collapsing mobile nav (see `js/main.js`).
