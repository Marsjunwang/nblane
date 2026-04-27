"""Tests for nblane.web_linkify."""

from nblane.web_linkify import (
    extract_plain_urls,
    linkify_plain_to_html,
    text_contains_linkified_url,
)


def test_linkify_empty() -> None:
    assert linkify_plain_to_html("") == ""
    assert text_contains_linkified_url("") is False


def test_linkify_escapes_html() -> None:
    out = linkify_plain_to_html("<script>x</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_linkify_wraps_https() -> None:
    s = "see https://example.com/path ok"
    out = linkify_plain_to_html(s)
    assert 'href="https://example.com/path"' in out
    assert "noopener" in out
    assert text_contains_linkified_url(s) is True


def test_linkify_multiple_urls() -> None:
    s = "a https://a.com b https://b.com"
    out = linkify_plain_to_html(s)
    assert out.count("<a ") == 2


def test_linkify_no_false_positive_for_plain_text() -> None:
    s = "no urls here just words"
    out = linkify_plain_to_html(s)
    assert "<a " not in out
    assert text_contains_linkified_url(s) is False


def test_mailto_when_valid() -> None:
    s = "mail mailto:user@example.com end"
    out = linkify_plain_to_html(s)
    assert "mailto:user@example.com" in out
    assert "<a " in out


def test_javascript_url_not_linked() -> None:
    s = "bad javascript:alert(1)"
    out = linkify_plain_to_html(s)
    assert "<a " not in out


def test_extract_plain_urls_dedupes_and_trims_punctuation() -> None:
    s = "see https://a.com, then https://a.com and mailto:u@example.com."
    assert extract_plain_urls(s) == [
        "https://a.com",
        "mailto:u@example.com",
    ]


def test_extract_plain_urls_rejects_unsafe_schemes() -> None:
    assert extract_plain_urls("bad javascript:alert(1)") == []
