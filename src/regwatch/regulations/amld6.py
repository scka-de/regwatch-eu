"""AMLD6 regulation definition."""

from regwatch.regulations.base import Regulation

amld6 = Regulation(
    id="amld6",
    name="Anti-Money Laundering Directive 6",
    celex_ids=[],
    eurovoc_codes=["560"],
    keywords=[
        "AMLD6",
        "AMLD",
        "anti-money laundering",
        "AML authority",
        "AMLA",
        "money laundering directive",
        "beneficial ownership",
    ],
    esma_tags=["anti-money laundering", "aml"],
    eba_tags=["amld", "aml", "anti-money laundering", "amla"],
)
