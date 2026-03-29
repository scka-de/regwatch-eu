"""DORA regulation definition."""

from regwatch.regulations.base import Regulation

dora = Regulation(
    id="dora",
    name="Digital Operational Resilience Act",
    celex_ids=["32022R2554"],
    eurovoc_codes=["2441", "3236", "1452"],
    keywords=[
        "DORA",
        "digital operational resilience",
        "2022/2554",
        "ICT risk management",
        "ICT third-party",
        "ICT-related incident",
    ],
    esma_tags=["dora", "digital operational resilience"],
    eba_tags=["dora", "ict-risk", "digital operational resilience"],
)
