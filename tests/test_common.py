import pytest

from webpub1c.common import slugify, urlpath_join


@pytest.mark.parametrize(
    "input_str,expected_str",
    [
        ("Бухгалтерия 2345", "buhgalterija-2345"),
        ("true & false", "true-false"),
    ],
)
def test_slugify(input_str: str, expected_str: str):
    assert slugify(input_str) == expected_str


@pytest.mark.parametrize(
    "prefix,url_path,expected_str",
    [
        ("/base", "path", "/base/path"),
        ("/base", "/path", "/base/path"),
        ("/base/", "path", "/base/path"),
        ("/base/", "/path", "/base/path"),
        ("/base/", "/base/path", "/base/path"),
    ],
)
def test_urlpath_join(prefix: str, url_path: str, expected_str: str):
    assert urlpath_join(prefix, url_path) == expected_str
