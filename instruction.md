# Adding Events & News to the Site

This is the complete guide to adding a **new** Event or News story using the
submission template and `scripts/convert_submission.py`. If you just need to
tweak an existing listing row (change a date, fix a typo in a summary that's
already live), that's a different, lighter-weight path — see
[EDITING.md](EDITING.md) Part 1 (the Google Sheet feed) instead. This
document is specifically about publishing a **whole new page**.

## What one submission produces

Every submission goes through one template and produces four things:

```
events/<slug>.html        the new event, full page (English)
zh/events/<slug>.html     the same event, in Chinese
                           — or, for news —
news/<slug>.html          the new story, full page (English)
zh/news/<slug>.html       the same story, in Chinese
```

...plus an updated entry on the matching listing page (`events.html` +
`zh/events.html`, or `news.html` + `zh/news.html`).

**Requires:** Python 3.7+ on whoever's machine runs the script — nothing
else, no `pip install` (the script only uses Python's standard library).

## The template

**[`templates/fgs-content-submission-template.docx`](templates/fgs-content-submission-template.docx)**
— one Word document, one two-column table, one field per row:

| Field | Required? | Notes |
|---|---|---|
| Content Type | **Required** | Exactly `Event` or `News` |
| Title (English) | **Required** | |
| Title (Chinese) | Optional | If left blank, the Chinese page shows the *English* title, not a translation |
| Date | **Required** | A format like `September 6, 2026` — needed for correct ordering, see below |
| Time | Optional | |
| Venue / Location | Optional | Mainly for events |
| Image URL or File | Optional | A real photo link, or leave blank and pass `--image` when running the script (see Step 3) |
| Registration Link | Optional (events only) | If blank, defaults to the temple's shared sign-up form |
| Source / Reference Link | Optional (news only) | Kept as an internal note on the page, not shown as a link — see "Why there's no 'read more' link" below |
| Summary (English) | **Required** | An original write-up in your own words — see the note below on what this needs to be |
| Summary (Chinese) | Optional | Same English fallback as Title (Chinese) if left blank |

**This is one template for both languages, not two separate ones.** There's
no English-only or Chinese-only version to choose between, and no need to
submit twice. Whether the result is fully bilingual depends only on whether
*this* submission's two Chinese fields were filled in.

**The Summary needs to be the actual story, not a teaser.** The site used to
pair a short summary with a "read the full story on fgs.ca" link. That
outbound link has been removed sitewide — every page is now a complete,
original account on its own. Write Summary (English) — and Summary
(Chinese), if provided — as a real write-up someone could read start to
finish without needing to click anywhere else. If you have a source article
you're drawing facts from, paste its link into "Source / Reference Link" for
the record (it's kept as an invisible comment in the generated file for
whoever edits it later), but write the summary itself as your own account of
what happened, not a copy of the source's wording.

## Step by step

1. **Get the filled-out template into a Google Doc.** Either upload the
   completed `.docx` (Google Docs → **File → Open → Upload**), or type it
   directly into a new Doc — as long as it keeps the same two-column table,
   one field per row.

2. **Share it so the script can read it.** **Share** (top right) → under
   "General access" choose **Anyone with the link** → **Viewer**. Copy the
   link.

3. **Run the script** from the project root:

   ```bash
   python scripts/convert_submission.py "<the Doc link you copied>"
   ```

   - Add `--image path/to/photo.jpg` if a photo was attached as a file
     rather than pasted as a URL — it gets copied into `assets/uploads/`
     and wired in automatically.
   - Add `--dry-run` first if you just want to see what it *would* create
     (title, date, slug, poster) without writing any files yet.

4. **Review what it created.** The script prints exactly which files it
   wrote or changed. Preview them locally before trusting them (see
   README.md → "How to preview or deploy").

5. **Commit when you're happy with it.** The script never touches git —
   review, then do this yourself:

   ```bash
   git add -A
   git commit -m "Add news: <title>"
   git push
   ```

## How the listing gets ordered — Events vs. News behave differently

- **News always goes to the very top.** The News page is strictly
  newest-first (that's also what the "Load More" button, further down,
  relies on to know which 9 cards to show first). The script doesn't even
  look at the Date field for this — a news submission is assumed to be
  about something happening *now*, so it always becomes the first card.
  **If you're ever backfilling an older story** that shouldn't read as the
  newest thing on the site, move its card down manually after running the
  script — the tool has no way to know that wasn't the intent.

- **Events are inserted into the correct chronological slot.** The Calendar
  page needs to stay in real date order regardless of submission order, so
  the script parses the Date field and finds the right spot among the
  existing rows. If the Date can't be parsed, or an existing row's own date
  can't be read back, it safely falls back to appending at the end rather
  than guessing wrong.

## What happens automatically

- The page's URL slug, generated from the English title.
- The Chinese-title/Chinese-summary fallback described above.
- An event's Registration button defaults to
  `https://form.jotform.com/222486208918059` if no link was given — the
  same fallback used everywhere else on the site for services without a
  dedicated sign-up form.
- The header and footer on every generated page — including the "Service"
  dropdown menu and the current nav order — match what's live on the rest
  of the site today. If the site's shared header/footer ever changes again,
  `scripts/convert_submission.py`'s `header()`/`footer()` functions need a
  matching update, or new pages will drift out of sync with everything
  else (this happened once already — see `implementation.md` if you're
  Claude picking this up in a future session).
- The listing insertion described above.

## What still needs a human

- **Writing the Summary itself.** The script doesn't write, translate, or
  paraphrase anything — it only places whatever you typed into the
  right spot on the page.
- **Double-checking the inserted position**, especially for an event with
  an unusual date format, or a news story you're backfilling (see above).
- **Reviewing the generated pages** before committing — open them locally,
  check the photo loads, check the Registration link (events) goes where
  it should.
- **The `git add` / `commit` / `push` step.** Nothing is ever committed
  automatically.

## Troubleshooting

| Problem | Likely cause |
|---|---|
| `Could not fetch the Doc (HTTP ...)` | The Doc isn't shared as "Anyone with the link can view" yet. Fix the sharing setting, try again. |
| `Missing required field(s): ...` | One of Content Type / Title (English) / Date / Summary (English) wasn't found — check the Doc still uses the same two-column, one-field-per-row table as the template. |
| `Content Type must be 'Event' or 'News'` | Check that field for typos or extra words — it needs to be exactly one of those two words. |
| Photo doesn't show up on the page | The Image URL field wasn't a real, publicly reachable URL, and `--image` wasn't passed for a locally attached file. |
| A new event landed in the wrong spot on the Calendar | Its Date field probably wasn't in a recognizable format (`September 6, 2026`-style) — it fell back to being appended at the end. Move it manually, and consider re-entering the date in that format for next time. |

## See also

- [README.md](README.md) — technical overview of the whole site, how to preview it locally
- [EDITING.md](EDITING.md) — the Google Sheet workflow for quick listing-row edits (not full new pages)
