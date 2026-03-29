"""EU AI Act regulation definition."""

from regwatch.regulations.base import Regulation

ai_act = Regulation(
    id="ai_act",
    name="EU Artificial Intelligence Act",
    celex_ids=["32024R1689"],
    eurovoc_codes=["2445"],
    keywords=[
        "AI Act",
        "artificial intelligence act",
        "2024/1689",
        "high-risk AI",
        "AI system",
        "general-purpose AI",
        "GPAI",
    ],
    esma_tags=["artificial intelligence", "ai act"],
    eba_tags=["artificial intelligence", "ai act"],
)
