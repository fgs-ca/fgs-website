# Editing this site without a developer

This site is plain HTML — there's no login, no admin panel, and no database.
That's great for cost and control, but it means "editing the site" has meant
opening `.html` files in a text editor. This guide adds a friendlier path for
two things people ask for most: **updating the events calendar** and
**posting news announcements** — no HTML required, just a Google Sheet.

It also explains what to do if you want to actually *send* a newsletter
campaign, which is a different need than the sign-up form on the site.

---

## Part 1 — Updating events and news via Google Sheets

### One-time setup (do this once)

1. **Create a Google Sheet** for events. Give the first row these exact
   column headers (lowercase, no spaces), one per column:

   ```
   section | badge_top | badge_bottom | title | meta | link_text | link_href
   ```

   | column | what to put in it | example |
   |---|---|---|
   | `section` | `special` or `recurring` | `special` |
   | `badge_top` | small text above the date | `Aug` |
   | `badge_bottom` | the big number/word | `27` |
   | `title` | the event name | `Food Offering Service` |
   | `meta` | the line under the title | `11:30 AM` |
   | `link_text` | button text (optional — defaults to "Details") | `Details` |
   | `link_href` | which page the button opens (optional) | `cultivation.html` |

   Add one row per event. Rows are shown in the order they appear in the
   sheet — drag a row up or down in Google Sheets to reorder it on the site.
   Rows marked `recurring` land in the "Weekly & Ongoing" section instead of
   "Special Events."

2. **Create a second Google Sheet** for news, with these headers:

   ```
   pill | title | body
   ```

   | column | what to put in it | example |
   |---|---|---|
   | `pill` | small label tag (optional) | `Notice` |
   | `title` | headline | `Water Drop Teahouse Closures` |
   | `body` | the announcement text | `Closed August 8, 16, 22 & 23...` |

3. **Publish each sheet as CSV:**
   - `File` → `Share` → `Publish to web`
   - Under "Link", choose the specific sheet (not "Entire document")
   - Under the format dropdown, choose **Comma-separated values (.csv)**
   - Click **Publish**, confirm, then copy the link it gives you

4. **Paste the links into the site.** Open [`js/sheets-feed.js`](js/sheets-feed.js)
   in any text editor and find this block near the top:

   ```js
   var SHEETS_FEED_CONFIG = {
     eventsCsvUrl: { en: "", zh: "" },
     newsCsvUrl:   { en: "", zh: "" }
   };
   ```

   Paste your events sheet's CSV link between the `en: ""` quotes for
   `eventsCsvUrl`, and your news sheet's link into `newsCsvUrl`. If you're
   keeping a separate Chinese-language sheet, paste its link into the `zh`
   slot the same way — otherwise leave `zh` blank and the Chinese pages will
   keep showing their current fallback text.

That's it — save the file once. From then on:

### Ongoing editing (what the non-technical editor actually does)

- Open the Google Sheet, add/edit/delete a row, done.
- The live site checks the sheet every time someone loads the Calendar or
  News page, so changes usually show up within a minute or two (Google
  caches published sheets briefly).
- No code, no git, no login to the website itself — just Google Sheets.

### What happens if something goes wrong

By design, nothing on the site breaks: if a URL is left blank, the sheet
isn't published yet, someone's offline, or a row is missing a required
column, the page quietly keeps showing the last hand-written fallback
content instead of showing an error or a blank section. Worst case, an edit
just doesn't show up — it won't take the page down.

---

## Part 2 — About "creating newsletters"

Worth flagging a distinction: the sign-up form on `news.html` (wired up as a
`mailto:` handoff, per your earlier request) lets a visitor send *themselves*
an email to `info@fgs.ca` asking to be added to a list. **It does not create
or maintain an actual subscriber list anywhere** — there's no database. Each
submission just lands as a one-off email in the temple's inbox, which someone
has to manually track.

If "create newsletters" means **composing and sending an email campaign to a
list of subscribers** (the way Mailchimp, Buttondown, or ConvertKit work),
that requires an actual email service — the site alone can't do this, no
matter how it's coded, because sending bulk email needs a real mail-sending
service and a stored list.

The realistic path there:
1. Sign up for a free tier of an email service (Mailchimp is the most common,
   free up to 500 contacts).
2. Compose and send newsletters through *that service's own dashboard* —
   fully non-technical, no coding, no Claude needed for that part.
3. Swap this site's sign-up form to submit into that service's list instead
   of the mailto handoff, so new sign-ups land automatically in the list
   instead of in an inbox to be entered by hand.

I can wire up step 3 any time — just say which service, and once you've
created a free account and grabbed the embed/action URL it gives you, send
it over and I'll connect the form to it.

---

## Part 3 — Individual event & news pages (`events/` and `news/` folders)

Beyond the summary rows on the Calendar and News listing pages, each event
and each news story now has its own full page:

```
events/<slug>.html        one page per event (English)
zh/events/<slug>.html     the same event, in Chinese
news/<slug>.html          one page per news story (English)
zh/news/<slug>.html       the same story, in Chinese
```

Every page follows the same layout as the rest of the site (same header,
footer, fonts, colors) — a poster/photo, the date, a short write-up, and
either a **Registration** button (events, linking straight to that event's
real signup form) or a **Read the full story on fgs.ca** link (news, since
these are original short summaries, not full copies of the source article).

### How these get created today

Adding a new one of these is a built, working workflow — not a plan
anymore. Fill out
[`templates/fgs-content-submission-template.docx`](templates/fgs-content-submission-template.docx)
and run `scripts/convert_submission.py` against it. **See
[instruction.md](instruction.md) for the complete, up-to-date guide** —
the template's fields (English required, Chinese optional), the
step-by-step, how News and Events get inserted into their listing
differently, and troubleshooting.
