from enum import Enum, auto


class OverlayMode(Enum):
    UNION = auto()
    CONSENSUS = auto()
    INTERSECTION = auto()