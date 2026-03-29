from regwatch.regulations.ai_act import ai_act
from regwatch.regulations.amld6 import amld6
from regwatch.regulations.dora import dora
from regwatch.regulations.mica import mica
from regwatch.regulations.psd3 import psd3

ALL_REGULATIONS = [dora, mica, ai_act, psd3, amld6]

__all__ = ["ALL_REGULATIONS", "dora", "mica", "ai_act", "psd3", "amld6"]
