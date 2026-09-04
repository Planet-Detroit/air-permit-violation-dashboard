"""Tests for the URL/dataset helpers. Run: python -m pytest test_parser_helpers.py"""
import pandas as pd
from parser_helpers import archive_filename, ensure_year_columns, legacy_parts, srn_for_urls, year_columns

LEGACY = "https://www.egle.state.mi.us/aps/downloads/SRN/N2688/N2688_VN_20230601.pdf"
NSITE = "https://mienviro.michigan.gov/ncore/downloadpdf/6635287174971505232"
DOCS = pd.DataFrame({"doc_url": [LEGACY, NSITE], "srn": ["N2688", "B5579"], "date": ["2023-06-01", "2026-08-26"]})


def test_legacy_url_is_recognised_and_new_url_is_not():
    # Old EGLE filenames encode facility, type, and date; MiEnviro URLs do not.
    assert legacy_parts(LEGACY) == ("N2688", "VN", "20230601")
    assert legacy_parts(NSITE) is None


def test_srn_comes_from_filename_or_dataset():
    # Old URL: facility ID parsed from the filename. New URL: looked up in the dataset.
    result = srn_for_urls(pd.Series([LEGACY, NSITE, "https://example.com/unknown"]), DOCS)
    assert list(result) == ["N2688", "B5579", None]


def test_archive_filename_keeps_old_names_and_builds_new_ones():
    # The archive folder keeps one naming convention for both eras.
    assert archive_filename(LEGACY, "N2688", "2023-06-01") == "archive/N2688_VN_20230601.pdf"
    assert archive_filename(NSITE, "B5579", "2026-08-26") == "archive/B5579_VN_20260826.pdf"
    assert archive_filename(NSITE, "B5579", pd.Timestamp("2026-08-26")) == "archive/B5579_VN_20260826.pdf"


def test_new_year_gets_a_zero_column_and_existing_years_are_untouched():
    # A notice dated in a year the map has never seen must add a column, not crash.
    map_df = pd.DataFrame({"srn": ["A0001"], "2023": [2], "2024": [1], "lat": [42.0]})
    out = ensure_year_columns(map_df, pd.Series([2024, 2026, None]))
    assert year_columns(out) == ["2023", "2024", "2026"]
    assert list(out["2026"]) == [0] and list(out["2024"]) == [1]
