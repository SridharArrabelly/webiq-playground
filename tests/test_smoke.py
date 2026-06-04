"""Offline smoke tests - no network calls."""

from webiq_playground import build_query


def test_build_query_adds_site_operator():
    assert build_query("tax", "sars.gov.za") == "tax site:sars.gov.za"


def test_build_query_without_site_is_unchanged():
    assert build_query("tax") == "tax"
