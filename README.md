# Svenningsen Imaging Lab website

A Quarto website, published free on GitHub Pages. Everything on the site is plain text and image
files in this folder. Search the project for **PLACEHOLDER** to find text that still needs replacing.

## Previewing changes on your computer

Install [Quarto](https://quarto.org/docs/get-started/) (tested with 1.10.18), then in this folder run:

```
quarto preview
```

The site opens in your browser and refreshes as you save files. If something looks stale or
strange, delete the `_site` and `.quarto` folders and run `quarto render` again.

## What is where

| File or folder | What it is |
|---|---|
| `_quarto.yml` | Site title, description, navigation menu, theme |
| `index.qmd` | Home page ("Our Mission") |
| `research.qmd`, `research/*.qmd` | Research overview and the four research pages |
| `team.qmd` + `pi.yml`, `members.yml`, `alumni.yml` | Team page and its people |
| `publications.qmd` + `publications.bib`, `ama.csl` | Full publication list and its citation style |
| `contact.qmd` | Contact details, map and partner logos |
| `styles.css` | All site styling, in numbered sections |
| `includes/site-scripts.html` | Small scripts: clicking "Research" opens the Overview; unlinked team cards aren't clickable |
| `images/`, `fonts/` | Pictures and web fonts |
| `scripts/`, `.github/workflows/` | Publication automation, and publishing |

## Everyday edits

| To do this | Edit this |
|---|---|
| Change the home page text | `index.qmd` |
| Change research text | `research.qmd` or the page in `research/` |
| Change contact details | `contact.qmd` |
| Add, edit, or remove a current member | `members.yml` (+ headshot in `images/team/`) |
| Move someone to past members | delete their entry in `members.yml`, add name and role to `alumni.yml` |
| Add publications | see below |
| Change the site-wide description or menu | `_quarto.yml` |

**Headshots:** any size works; they are cropped to a square. About 800 px on the long side is plenty; put the
face in the upper-centre. Members without a photo can use `images/team/placeholder.png`.

**Profile links on member cards:** an optional `path:` line in an entry in `members.yml` makes the
whole card link somewhere (for example a Google Scholar profile). Leave it out for no link.

**Image sizes:** shrink photos before adding them (about 800 px for headshots, 1200 px for figures). Large photos slow the page.

## Writing a page

Each page starts with a front-matter block between `---` lines:

```
---
title: "Page title"
description: "One sentence for Google and link previews. It is not shown on the page."
---
```

Keep the `description` on every page, and write it as a plain sentence.

### Text beside a figure

```
:::: {.columns}

::: {.column}
Text goes here.
:::

::: {.column}
![Caption shown under the picture](images/example.png){width=90% fig-align="center" fig-alt="What the picture shows, for screen readers"}
:::

::::
```

- Text goes on the left (wide) and the picture on the right (narrow).
- Every `::::` or `:::` that opens needs its own closing line.
- Leave a blank line before and after each fence, and a blank line between two images, or the
  captions disappear.
- On pages inside `research/`, start paths with `../` (`../images/x.png`).
- Always give a picture alt text: either a caption in the `[...]` or `fig-alt="..."` (use `fig-alt` when
  the caption doesn't describe what is shown). Decorative pictures can use `fig-alt=""`.

### Lists

A normal list is lines starting with `- `, with a blank line before the first. For several columns,
wrap it: `::: {.list-cols}` ... `:::`.

### Selected publications on a research page

In the page's front matter add:

```
bibliography: ../publications.bib
csl: ../ama.csl
nocite: |
  @citekey1, @citekey2
```

Then place the list where you want it:

```
## Selected publications

::: {#refs}
:::
```

The citation key is the text right after the opening brace of each entry in `publications.bib` (for example `friedlander2024`, written `@friedlander2024`).
Only use papers on which Dr. Svenningsen is the senior author.

### Logos in a row

```
::: {.logo-row}
![](images/logo1.png){fig-alt="Name of organization"}
![](images/logo2.png){fig-alt="Name of organization"}
:::
```

Logos are 60 px tall; change `.logo-row img` in `styles.css` to resize.

### Adding a new research page

1. Create `research/new-topic.qmd` (copy an existing one).
2. Add it to the Research menu in `_quarto.yml` and to the list in `research.qmd`.

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

A monthly job searches PubMed for the PI's **new** papers and proposes them.

- On the 1st of each month (or whenever you click **Actions > Find new publications > Run workflow**),
  GitHub searches PubMed (the search is in `pubmed_query.txt`) for matching papers added to PubMed
  since the date in `last_checked.txt`. It looks up their DOIs on Crossref and opens a
  **pull request** that adds them to `publications.bib` and moves that date forward.
- Because only new papers are searched, **old papers you delete from `publications.bib` stay deleted.**
- Open the pull request, check the added entries, delete any that are wrong, and click **Merge**.
  The site then rebuilds and publishes by itself.
- If papers by a different author with the same name show up, narrow the search in
  `pubmed_query.txt` (examples are in that file).
- PubMed lists some papers without a DOI. The pull request does not include these; add them by hand.
- To pick up an older paper that was missed, add its DOI to `dois.txt` and run `scripts/dois_to_bib.py`
  (see above).

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

## Troubleshooting

| Problem | Likely cause |
|---|---|
| Page layout breaks or text is missing | A `:::` fence was not closed, or a blank line is missing around it |
| Images missing on a `research/` page | Path needs `../images/...` |
| Captions missing | Two images on consecutive lines: add a blank line between them |
| "File 'ama.csl' not found" | On `research/` pages use `../ama.csl` and `../publications.bib` |
| Styles stop working below some point | An unclosed `{` in `styles.css` |
| Team or other changes don't appear | Delete `_site` and `.quarto`, then `quarto render` |
