"""MiCA regulation definition."""

from regwatch.regulations.base import Regulation

mica = Regulation(
    id="mica",
    name="Markets in Crypto-Assets Regulation",
    celex_ids=["32023R1114"],
    eurovoc_codes=["5765"],
    keywords=[
        "MiCA",
        "MiCAR",
        "markets in crypto",
        "crypto-asset",
        "2023/1114",
        "CASP",
        "asset-referenced token",
        "e-money token",
    ],
    esma_tags=["mica", "crypto", "digital finance"],
    eba_tags=["mica", "crypto-asset"],
)
