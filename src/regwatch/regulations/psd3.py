"""PSD3 regulation definition."""

from regwatch.regulations.base import Regulation

psd3 = Regulation(
    id="psd3",
    name="Payment Services Directive 3",
    celex_ids=[],
    eurovoc_codes=["2446"],
    keywords=[
        "PSD3",
        "payment services directive",
        "PSR",
        "payment services regulation",
        "open finance",
        "instant payments",
    ],
    esma_tags=["payment services"],
    eba_tags=["psd3", "payment services", "psr"],
)
