"""Direct tests for strip_html utility."""

from regwatch.sources._utils import strip_html


def test_strip_html_removes_tags():
    assert strip_html("<p>Hello</p>") == "Hello"


def test_strip_html_nested_tags():
    assert strip_html("<div><p>Hello <b>world</b></p></div>") == "Hello world"


def test_strip_html_normalizes_whitespace():
    assert strip_html("<p>Hello</p>  <p>World</p>") == "Hello World"


def test_strip_html_empty_string():
    assert strip_html("") == ""


def test_strip_html_no_tags():
    assert strip_html("plain text") == "plain text"


def test_strip_html_self_closing_tags():
    assert strip_html("Hello<br/>World") == "Hello World"
