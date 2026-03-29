from regwatch.sources.eba import EbaSource
from regwatch.sources.esma import EsmaSource
from regwatch.sources.eurlex import EurLexSource

ALL_SOURCES = [EurLexSource(), EsmaSource(), EbaSource()]

__all__ = ["ALL_SOURCES", "EurLexSource", "EsmaSource", "EbaSource"]
