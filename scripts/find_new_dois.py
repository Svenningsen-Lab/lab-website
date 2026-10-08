#!/usr/bin/env python3
"""Find DOIs of new publications by running a saved PubMed search.

Usage (run from the project root):

    python scripts/find_new_dois.py

What it does:
  * Reads the search from pubmed_query.txt (lines starting with # are ignored).
  * Asks PubMed (NCBI E-utilities, free, no key needed) for everything that matches.
  * Drops anything already in publications.bib or listed in dois_ignore.txt.
  * Drops errata, comments, and retraction notices.
  * Writes the remaining DOIs to new_dois.txt, ready for scripts/dois_to_bib.py.

It never edits publications.bib itself. Papers PubMed lists without a DOI are
reported at the end so you can add them by hand.

Only the Python standard library is needed.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SKIP_TYPES = {
    "Published Erratum",
    "Erratum",
    "Comment",
    "Retraction of Publication",
    "Retracted Publication",
    "Expression of Concern",
}


def clean_doi(raw):
    s = raw.strip()
    s = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^doi:\s*", "", s, flags=re.I)
    return s.strip().lower()


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [ln.split("#", 1)[0].strip() for ln in f if ln.split("#", 1)[0].strip()]


def read_query(path):
    parts = read_lines(path)
    return " ".join(parts).strip()


def bib_dois(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    found = re.findall(r"\bdoi\s*=\s*[{\"]\s*([^}\"]+?)\s*[}\"]", text, flags=re.I)
    return {clean_doi(d) for d in found}


def get_json(endpoint, params, email=None):
    params = dict(params)
    params["retmode"] = "json"
    params["tool"] = "svenningsen-lab-site"
    if email:
        params["email"] = email
    url = EUTILS + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "svenningsen-lab-site/1.0"})
    last = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception as e:  # network trouble or rate limiting; back off and retry
            last = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"PubMed request failed: {last}")


def search_pmids(query, email=None, retmax=1000):
    data = get_json("esearch.fcgi", {"db": "pubmed", "term": query, "retmax": retmax, "sort": "pub_date"}, email)
    res = data.get("esearchresult", {})
    ids = res.get("idlist", [])
    count = int(res.get("count", len(ids)))
    return ids, count


def summaries(pmids, email=None, batch=100):
    out = {}
    for i in range(0, len(pmids), batch):
        chunk = pmids[i:i + batch]
        data = get_json("esummary.fcgi", {"db": "pubmed", "id": ",".join(chunk)}, email)
        result = data.get("result", {})
        for uid in result.get("uids", chunk):
            if uid in result:
                out[uid] = result[uid]
        time.sleep(0.4)  # stay under NCBI's 3 requests/second limit
    return out


def doi_of(summary):
    for aid in summary.get("articleids", []):
        if aid.get("idtype") == "doi" and aid.get("value"):
            return clean_doi(aid["value"])
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--query-file", default="pubmed_query.txt")
    p.add_argument("--bib", default="publications.bib")
    p.add_argument("--ignore", default="dois_ignore.txt")
    p.add_argument("--out", default="new_dois.txt")
    p.add_argument("--email", default=os.environ.get("CROSSREF_EMAIL"),
                   help="contact email sent to NCBI (or set CROSSREF_EMAIL); optional")
    args = p.parse_args(argv)

    query = read_query(args.query_file)
    if not query:
        sys.exit(f"No search found in {args.query_file}. Run this from the project root.")
    print(f"PubMed search: {query}")

    pmids, count = search_pmids(query, args.email)
    print(f"PubMed returned {count} matching records.")
    if count > len(pmids):
        print(f"WARNING: only the first {len(pmids)} were retrieved. Narrow the search in {args.query_file}.")

    have = bib_dois(args.bib)
    ignore = {clean_doi(d) for d in read_lines(args.ignore)}
    info = summaries(pmids, args.email)

    new, no_doi, skipped = [], [], 0
    for pmid in pmids:
        s = info.get(pmid)
        if not s:
            continue
        if set(s.get("pubtype", [])) & SKIP_TYPES:
            skipped += 1
            continue
        doi = doi_of(s)
        if not doi:
            no_doi.append((pmid, s.get("title", "").strip()))
            continue
        if doi in have or doi in ignore or doi in new:
            continue
        new.append(doi)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(new) + ("\n" if new else ""))

    print(f"{len(new)} new DOIs written to {args.out} "
          f"({len(have)} already in {args.bib}, {len(ignore)} on the ignore list, "
          f"{skipped} errata/comments skipped).")
    if no_doi:
        print("\nPubMed lists these without a DOI, so add them by hand if you want them:")
        for pmid, title in no_doi:
            print(f"  PMID {pmid}: {title[:100]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
