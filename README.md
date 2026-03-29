# regwatch-eu

Monitor EU regulatory changes across EUR-Lex, ESMA and EBA. Track DORA, MiCA, AI Act, PSD3, AMLD6.

Zero hosting. Zero API keys. Local-first.

## Install

```
pip install regwatch-eu
```

## Quick Start

```bash
# Fetch latest regulatory changes
regwatch update

# Check DORA-related changes
regwatch check --regulation dora

# Multiple regulations
regwatch check --regulation dora,mica --since 2025-01-01

# Export as JSON
regwatch check --format json > changes.json

# Cache status
regwatch status
```

## Python API

```python
from regwatch import RegWatch

rw = RegWatch()
rw.update()

# Query as pandas DataFrame
df = rw.check(regulations=["dora", "mica"], since="2025-01-01")
print(df[["date", "title", "regulation", "type"]])
```

## Supported Regulations

| ID | Name |
|---|---|
| dora | Digital Operational Resilience Act |
| mica | Markets in Crypto-Assets Regulation |
| ai_act | EU Artificial Intelligence Act |
| psd3 | Payment Services Directive 3 |
| amld6 | Anti-Money Laundering Directive 6 |

## Data Sources

- **EUR-Lex** (Cellar SPARQL) — Legislative acts, delegated acts, implementing acts
- **ESMA** (RSS) — Guidelines, consultations, Q&As
- **EBA** (RSS) — Technical standards, guidelines, press releases

All sources are public. No API keys required.

## LLM Classification (Optional)

For higher classification accuracy, provide an LLM API key:

```python
rw = RegWatch(llm_api_key="sk-ant-...")  # Claude
rw = RegWatch(llm_api_key="sk-...")      # OpenAI
```

Without an LLM key, classification uses deterministic keyword matching (~80% accuracy).

## CLI Reference

```
regwatch update [--source SOURCE]
regwatch check [--regulation REG] [--since DATE] [--type TYPE] [--source SOURCE] [--format FORMAT]
regwatch status
regwatch regulations
```

## License

Apache 2.0
