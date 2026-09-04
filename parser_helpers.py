"""Helpers for the violation-notice parser.

Why this exists: until September 2024 EGLE hosted every document at a URL whose
filename encoded the facility ID and issue date (N2155_VN_20211011.pdf), and the
parser read both from the URL. EGLE now publishes through MiEnviro, whose URLs
are opaque (mienviro.michigan.gov/ncore/downloadpdf/6635287174971505232), so
the facility ID and date must come from the document dataset instead. These
helpers handle both URL styles so the historical rows keep working.
"""
import os
import re

import pandas as pd

LEGACY_NAME = re.compile(r"^([A-Z]\d{4})_([A-Z]+)_(\d{8})\.pdf$", re.IGNORECASE)


def legacy_parts(doc_url):
    """Return (srn, doc_type, yyyymmdd) for an old-style URL, else None."""
    match = LEGACY_NAME.match(os.path.basename(str(doc_url)))
    return match.groups() if match else None


def srn_for_urls(doc_urls, docs):
    """Facility ID for each URL: from the filename when it has one, otherwise
    from the document dataset (which always carries srn)."""
    lookup = docs.drop_duplicates(subset="doc_url").set_index("doc_url")["srn"]

    def one(url):
        parts = legacy_parts(url)
        if parts:
            return parts[0]
        return lookup.get(url)

    return doc_urls.map(one)


def archive_filename(doc_url, srn, date):
    """Where to save the PDF locally. Old URLs keep their own filename; new ones
    get the same convention built from the dataset's srn and date."""
    if legacy_parts(doc_url):
        return os.path.join("archive", os.path.basename(doc_url))
    stamp = str(date)[:10].replace("-", "")
    return os.path.join("archive", f"{srn}_VN_{stamp}.pdf")


def year_columns(map_df):
    """The per-year violation-count columns in the map data ('2018', '2019', …)."""
    return [c for c in map_df.columns if str(c).isdigit() and len(str(c)) == 4]


def ensure_year_columns(map_df, years):
    """Add a zero-filled count column for every year in `years` the map lacks,
    so a notice from a new calendar year never crashes the map update."""
    for year in sorted({int(y) for y in years if pd.notnull(y)}):
        if str(year) not in map_df.columns:
            map_df[str(year)] = 0
    return map_df
