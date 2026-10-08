#!/usr/bin/env python3
"""Build publications.bib from a list of DOIs using the free Crossref API.

Usage (run from the project root):

    python scripts/dois_to_bib.py
    python scripts/dois_to_bib.py --email you@example.com

What it does:
  * Reads DOIs from dois.txt (one per line; bare DOIs or https://doi.org/... links;
    lines starting with # are ignored).
  * Looks each one up on Crossref and writes a BibTeX entry.
  * Keeps entries already in publications.bib (it never overwrites your edits) and
    skips DOIs that are already there.
  * Re-sorts the whole file newest first, which is the order the website shows.

Only the Python standard library is needed. Crossref asks for a contact email in
requests so they can reach you if something goes wrong; pass --email, or set the
CROSSREF_EMAIL environment variable. It is optional but polite.

Always glance over the result: Crossref data is generally good, but a few
publishers deposit odd capitalization or missing fields.
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.crossref.org/works/"


# --------------------------------------------------------------------------- #
# DOI handling
# --------------------------------------------------------------------------- #
def clean_doi(raw):
    """Return a bare, lower-case DOI from a DOI, doi: string, or doi.org URL."""
    s = raw.strip()
    s = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^doi:\s*", "", s, flags=re.I)
    return s.strip().lower()


def read_dois(path):
    dois = []
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            doi = clean_doi(line)
            if doi and doi not in seen:
                seen.add(doi)
                dois.append(doi)
    return dois


# --------------------------------------------------------------------------- #
# Crossref
# --------------------------------------------------------------------------- #
def fetch_work(doi, email=None, retries=3):
    """Fetch the Crossref 'message' record for a DOI, or None if not found."""
    url = API + urllib.parse.quote(doi, safe="/")
    agent = "svenningsen-lab-site/1.0 (static site build script)"
    if email:
        agent += f" (mailto:{email})"
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)["message"]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise
    return None


# --------------------------------------------------------------------------- #
# BibTeX building
# --------------------------------------------------------------------------- #
def strip_markup(text):
    """Crossref titles can contain JATS/HTML tags and entities; reduce to plain text."""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def bib_escape(text):
    """Escape characters that are special to BibTeX/LaTeX in plain-text values."""
    for ch in ("&", "%", "$", "#", "_"):
        text = text.replace(ch, "\\" + ch)
    return text


def format_authors(authors):
    names = []
    for a in authors or []:
        family = (a.get("family") or "").strip()
        given = (a.get("given") or "").strip()
        if family:
            names.append(f"{family}, {given}" if given else family)
        elif a.get("name"):  # consortium / group author
            names.append("{" + a["name"].strip() + "}")
    return " and ".join(names)


def get_year(work):
    for key in ("issued", "published", "published-print", "published-online", "created"):
        parts = (work.get(key) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return str(parts[0][0])
    return ""


def first(value):
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def make_key(work, year, used):
    authors = work.get("author") or []
    surname = ""
    if authors:
        surname = authors[0].get("family") or authors[0].get("name") or ""
    surname = re.sub(r"[^A-Za-z]", "", surname).lower() or "anon"
    base = f"{surname}{year}"
    key, n = base, 0
    while key in used:
        n += 1
        key = base + chr(ord("a") + n - 1) if n <= 26 else f"{base}{n}"
    used.add(key)
    return key


def work_to_bibtex(work, doi, used_keys):
    year = get_year(work)
    title = strip_markup(first(work.get("title")))
    journal = strip_markup(first(work.get("container-title")))
    ctype = work.get("type", "")

    if ctype == "proceedings-article":
        entry_type, container_field = "inproceedings", "booktitle"
    elif ctype in ("journal-article", "posted-content", ""):
        entry_type, container_field = "article", "journal"
    elif ctype == "book-chapter":
        entry_type, container_field = "incollection", "booktitle"
    else:
        entry_type, container_field = "article", "journal"

    # Preprints often have no container title; fall back to the server name.
    if not journal:
        inst = work.get("institution") or []
        if isinstance(inst, dict):
            inst = [inst]
        journal = strip_markup(first([i.get("name", "") for i in inst]))
    if not journal and ctype == "posted-content":
        journal = "Preprint"

    fields = []
    authors = format_authors(work.get("author"))
    if authors:
        fields.append(("author", bib_escape(authors)))
    # Double braces stop BibTeX/citeproc from changing capitalization in titles.
    fields.append(("title", "{" + bib_escape(title) + "}"))
    if journal:
        fields.append((container_field, bib_escape(journal)))
    if year:
        fields.append(("year", year))
    if work.get("volume"):
        fields.append(("volume", str(work["volume"])))
    if work.get("issue"):
        fields.append(("number", str(work["issue"])))
    page = work.get("page") or work.get("article-number")
    if page:
        fields.append(("pages", re.sub(r"[-\u2013\u2014]+", "--", str(page))))
    fields.append(("doi", doi))

    key = make_key(work, year or "nd", used_keys)
    lines = [f"@{entry_type}{{{key},"]
    for i, (name, value) in enumerate(fields):
        comma = "," if i < len(fields) - 1 else ""
        lines.append(f"  {name:<9}= {{{value}}}{comma}")
    lines.append("}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Existing .bib handling
# --------------------------------------------------------------------------- #
def split_entries(text):
    """Split a .bib file into entries (each starting at a line beginning with '@')."""
    entries, current = [], []
    for line in text.splitlines():
        if line.startswith("@") and current:
            entries.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current and "\n".join(current).strip():
        entries.append("\n".join(current).strip())
    return [e for e in entries if e.startswith("@")]


def entry_doi(entry):
    m = re.search(r"\bdoi\s*=\s*[{\"]\s*([^}\"]+?)\s*[}\"]", entry, flags=re.I)
    return clean_doi(m.group(1)) if m else None


def entry_year(entry):
    m = re.search(r"\byear\s*=\s*[{\"]?\s*(\d{4})", entry, flags=re.I)
    return int(m.group(1)) if m else 0


def entry_key(entry):
    m = re.match(r"@\w+\s*\{\s*([^,\s]+)", entry)
    return m.group(1) if m else ""


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dois", default="dois.txt", help="file listing DOIs (default: dois.txt)")
    p.add_argument("--bib", default="publications.bib", help="BibTeX file to update (default: publications.bib)")
    p.add_argument("--email", default=os.environ.get("CROSSREF_EMAIL"),
                   help="contact email sent to Crossref (or set CROSSREF_EMAIL)")
    p.add_argument("--no-sort", action="store_true", help="do not re-sort the file newest first")
    args = p.parse_args(argv)

    if not os.path.exists(args.dois):
        sys.exit(f"Could not find {args.dois}. Run this from the project root.")

    existing = []
    if os.path.exists(args.bib):
        with open(args.bib, encoding="utf-8") as f:
            existing = split_entries(f.read())
    have_dois = {d for d in (entry_doi(e) for e in existing) if d}
    used_keys = {entry_key(e) for e in existing}

    wanted = read_dois(args.dois)
    new_entries, not_found, failed = [], [], []
    for doi in wanted:
        if doi in have_dois:
            print(f"  skip (already in {args.bib}): {doi}")
            continue
        try:
            work = fetch_work(doi, args.email)
        except Exception as e:  # network problems, bad responses
            failed.append((doi, str(e)))
            print(f"  FAILED: {doi} ({e})")
            continue
        if work is None:
            not_found.append(doi)
            print(f"  not found on Crossref: {doi}")
            continue
        new_entries.append(work_to_bibtex(work, doi, used_keys))
        print(f"  added: {doi}")
        time.sleep(0.2)  # be gentle with the API

    all_entries = existing + new_entries
    if not args.no_sort:
        # Stable sort: newest year first, ties keep their existing order.
        all_entries.sort(key=lambda e: -entry_year(e))

    with open(args.bib, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_entries) + "\n")

    print(f"\n{len(new_entries)} added, {len(existing)} kept, {len(all_entries)} total in {args.bib}.")
    if not_found:
        print("Not found on Crossref (check for typos, or add these by hand):")
        for d in not_found:
            print("  ", d)
    if failed:
        print("Could not be fetched (network or server problem; try again):")
        for d, msg in failed:
            print("  ", d, "-", msg)
    return 1 if (failed or not_found) else 0


if __name__ == "__main__":
    sys.exit(main())
