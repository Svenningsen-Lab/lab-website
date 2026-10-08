# Svenningsen Imaging Lab website

A simple Quarto website, published free on GitHub Pages. Everything on the site is
plain text and image files in this folder. All text marked **PLACEHOLDER** needs to be replaced.

## Previewing changes on your computer

Install [Quarto](https://quarto.org/docs/get-started/), then in this folder run:

```
quarto preview
```

The site opens in your browser and refreshes as you save files.

## Everyday edits

| To do this | Edit this |
|---|---|
| Change the home page text | `index.qmd` |
| Change research descriptions | `research.qmd` |
| Change contact details | `contact.qmd` |
| Add, edit, or remove a current member | `members.yml` (+ headshot in `images/team/`) |
| Move someone to past members | delete their entry in `members.yml`, add name and role to `alumni.yml` |
| Add lab photos | put images in `images/gallery/`, add a line to `gallery.qmd` |
| Add publications | see below |
| Set the lab's Google Scholar link | `publications.qmd` (and optionally `path:` on a member card) |

**Headshots:** any size works; they are cropped to a square automatically. About 600 x 600 px is plenty.
Put the face roughly in the upper-centre of the photo.

**Lab photos:** resize to about 1600 px wide before adding, so the page loads quickly on phones.

**Profile links on member cards:** the optional `path:` line in `members.yml` makes the whole card
link somewhere (for example a Google Scholar profile). Delete the line for no link.

## Adding publications

1. Add the new DOIs to `dois.txt`, one per line.
2. Run `python scripts/dois_to_bib.py` (add `--email you@example.com` if you like; Crossref
   appreciates a contact address).
3. Look over the new entries in `publications.bib`. Publishers sometimes deposit odd
   capitalization or missing fields, and you can edit the file by hand.

The script keeps what is already in `publications.bib`, skips DOIs it already has, and sorts the
file newest first. It needs Python 3 and an internet connection, and no extra packages.
You can also paste BibTeX entries from Zotero or PubMed straight into `publications.bib`.
New papers by the PI are also found automatically each month (see below).

## Automatic publication updates

A monthly job searches PubMed for the PI's papers and proposes any that are missing.

- On the 1st of each month (or whenever you click **Actions > Find new publications > Run workflow**),
  GitHub runs the search in `pubmed_query.txt`, looks up the new DOIs on Crossref, and opens a
  **pull request** that adds them to `publications.bib`.
- Open the pull request, check the added entries, delete any that are wrong, and click **Merge**.
  The site then rebuilds and publishes by itself.
- To stop a paper being proposed again, add its DOI to `dois_ignore.txt`.
- If papers by a different author with the same name show up, narrow the search in
  `pubmed_query.txt` (examples are in that file).
- PubMed lists some papers without a DOI. The pull request does not include these; add them by hand.

One-time setup: in the repository, go to **Settings > Actions > General > Workflow permissions**,
choose **Read and write permissions**, and tick **Allow GitHub Actions to create and approve pull
requests**. If that box is greyed out, enable it first at the organization level
(organization **Settings > Actions > General**).

GitHub pauses scheduled workflows after about 60 days with no activity in a public repository.
Merging the monthly pull request counts as activity, but if the job ever stops, re-enable it from the
**Actions** tab.

## Publishing

1. Create a GitHub repository and push this folder to its `main` branch.
2. In the repository, go to **Settings > Pages** and set **Source** to **GitHub Actions**.
3. Every push to `main` now rebuilds and publishes the site (see `.github/workflows/publish.yml`).
   The first run gives you a `https://<username>.github.io/<repo>/` address to test with.

## Using your own domain, and moving off Wix

Do these in this order so the site is never offline:

1. **Finish and test the new site** at its `github.io` address. Copy over text and images from Wix
   first (Wix cannot export the design, so this is a manual copy).
2. **Decide where the domain will live.** Either transfer it to another registrar, or keep it
   registered with Wix and just edit its DNS records. Domain transfers can take several days, and
   registrars often block transfers for 60 days after a domain is registered or changed; check
   with Wix before you start.
3. **Point DNS at GitHub Pages**, following GitHub's current instructions:
   <https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site>.
   Then enter the domain under **Settings > Pages > Custom domain** and tick **Enforce HTTPS**
   once it becomes available (it can take a while after DNS changes).
4. **Only after the new site works at your own domain**, cancel the Wix plan. The domain
   subscription is separate from the website plan, so check what you are cancelling.

## Notes

- The workflow pins Quarto to the version this site was tested with (1.10.18). Update the version in
  `.github/workflows/publish.yml` when you want to move to a newer one, and check the site afterwards.
- The action versions in that file (`actions/checkout@v4` and so on) are what was current when this
  was written. If GitHub shows a deprecation warning, bump them.
- Publication style is AMA (`ama.csl`). To change it, download another style from
  <https://github.com/citation-style-language/styles> and update `csl:` in `publications.qmd`.
