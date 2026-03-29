"""Tests for source fetch() error paths — timeout and HTTP errors."""

from datetime import date
from unittest.mock import patch

import httpx
import pytest

from regwatch.regulations.dora import dora
from regwatch.sources.eba import EbaSource
from regwatch.sources.esma import EsmaSource
from regwatch.sources.eurlex import EurLexSource

REGULATIONS = [dora]
SINCE = date(2026, 1, 1)


class TestEurLexErrors:
    def test_timeout_raises(self):
        with patch("regwatch.sources.eurlex.httpx.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(httpx.TimeoutException):
                EurLexSource().fetch(since=SINCE, regulations=REGULATIONS)

    def test_http_error_raises(self):
        mock_response = httpx.Response(500, request=httpx.Request("POST", "http://test"))
        with patch("regwatch.sources.eurlex.httpx.post") as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(httpx.HTTPStatusError):
                EurLexSource().fetch(since=SINCE, regulations=REGULATIONS)


class TestEsmaErrors:
    def test_timeout_raises(self):
        with patch("regwatch.sources.esma.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(httpx.TimeoutException):
                EsmaSource().fetch(since=SINCE, regulations=REGULATIONS)

    def test_http_error_raises(self):
        mock_response = httpx.Response(503, request=httpx.Request("GET", "http://test"))
        with patch("regwatch.sources.esma.httpx.get") as mock_get:
            mock_get.return_value = mock_response
            with pytest.raises(httpx.HTTPStatusError):
                EsmaSource().fetch(since=SINCE, regulations=REGULATIONS)


class TestEbaErrors:
    def test_timeout_raises(self):
        with patch("regwatch.sources.eba.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(httpx.TimeoutException):
                EbaSource().fetch(since=SINCE, regulations=REGULATIONS)

    def test_http_error_raises(self):
        mock_response = httpx.Response(502, request=httpx.Request("GET", "http://test"))
        with patch("regwatch.sources.eba.httpx.get") as mock_get:
            mock_get.return_value = mock_response
            with pytest.raises(httpx.HTTPStatusError):
                EbaSource().fetch(since=SINCE, regulations=REGULATIONS)
