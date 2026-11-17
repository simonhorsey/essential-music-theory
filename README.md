# Essential Music Theory

Static rebuild of essential-music-theory.com (previously on Solo Build It).
It uses the same page pattern as Essential Music Practice and LearningForSuccess:
hero, three paths, three-step plan, numbered showcase, free download, testimonials, closing paths.
The colours are the old Theory site's own: charcoal, fresh green and white, with Raleway headings and Open Sans text.

The product ladder is: free lessons → **Essential Music Theory, Volume 1** (Apple Books; Volumes 2 and 3 to follow) →
**the theory courses** (Beginner, then Grade 1 to Grade 5, and no further).
No ads, no trackers, and nothing to install beyond Python 3.

## Change the words

Sales copy, prices, links, navigation and redirects all live in **`site.json`**.
Lessons, reader questions and simple pages are one file each in **`content/`**.

While `"draft": true` is set, anything still waiting on you shows a red "Draft" tag and search
engines are told not to index the site. Fill a `null` in and its tag goes. Set `"draft": false` to launch.

## Run it

```bash
python3 build.py --serve
```

Builds into `dist/` and serves it at http://localhost:8001.

## Put it on Cloudflare

Same setup as Essential Music Practice: a Worker serving static files (`wrangler.jsonc` points at `dist/`).

1. Cloudflare dashboard → Workers & Pages → `essentialmusictheory` → Settings → Build → connect this GitHub repository.
2. Build command `python3 build.py`. Deploy command `npx wrangler deploy`.
3. Every push to `main` rebuilds the site.

Preview address: https://essentialmusictheory.simonhorsey.workers.dev

`html_handling` is set to `none` in `wrangler.jsonc` so the old `.html` addresses keep working unchanged.
In that mode Cloudflare does not serve `index.html` at `/` by itself, so `build.py` writes a
`/ /index.html 200` line at the top of `_redirects`. Leave both in place.

## Where things are

| Path | What it is |
| --- | --- |
| `site.json` | All sales copy, prices, links, navigation, lesson sections and redirects |
| `content/*.html` | One file per page: a short header, then the page HTML |
| `build.py` | Builds the site. Page layouts are described at the top of the file |
| `static/` | CSS, scripts, fonts, images and the manuscript paper files, copied to `dist/` unchanged |
| `source/pages/` | Untouched copy of every page from the old site (17 Nov 2026) |
| `tools/crawl.py`, `tools/capture_assets.py` | One-off: saved the old pages, images and PDFs |
| `tools/convert.py` | One-off converter from `source/pages` to `content/`. Never run it with `--force`: it overwrites hand edits |
| `tools/question-titles.json` | Clearer titles for the reader questions (visitors typed titles like "chords" and "Miss") |

## What changed from the old site

- 19 lessons and 42 reader questions carried over at their old addresses. Six questions nobody answered,
  the book comments page and every "add a comment" form page redirect to the nearest live page.
- The quizzes the lessons linked to were on a third-party service that has closed, so those links are gone.
- The Rocket Piano recommendation (a dead affiliate link) and the "book due March 2010" note came out of the piano keyboard page.
- New pages: `/music-theory-courses.html`, `/simon-horsey.html`, `/contact.html` (the old `/getintouch.html` redirects to it).

## Before launch

- [ ] Courses: where they are hosted, a link and a price for each, and check the outline of each level (`offers.courses` in `site.json`)
- [ ] Volumes 2 and 3: what each covers and when (`offers.book.series`)
- [ ] The unanswered questions on the book and courses pages (`faqs` with `"a": null`)
- [ ] Activity Books page (`content/music-theory-workbook.html`): were they published? Add a link or remove the page
- [ ] Check the credentials (`guide` in `site.json`) and `content/simon-horsey.html`
- [ ] Contact form (`forms.contact_action`)
- [ ] Review `content/privacy-policy.html`
- [ ] Transfer the domain away from SiteSell and copy any mail (MX) records first
- [ ] Set `"draft": false`
