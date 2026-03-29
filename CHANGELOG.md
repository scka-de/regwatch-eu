# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-29

### Added
- Monitor 5 EU financial regulations: DORA, MiCA, AI Act, PSD3, AMLD6
- 3 data sources: EUR-Lex (SPARQL), ESMA (RSS), EBA (RSS)
- 3-layer deterministic classifier: CELEX ID match, keyword/EuroVoc scoring, optional LLM fallback
- SQLite cache with schema versioning, upsert, and multi-filter queries
- CLI with `update`, `check`, `status`, and `regulations` commands
- Output formats: table (rich), JSON, CSV
- Optional LLM classification via Claude or OpenAI API
- CI/CD: GitHub Actions for testing (Python 3.10-3.12) and PyPI publishing
- 133 tests covering data layer, classifier, CLI, pipeline, and source error paths
