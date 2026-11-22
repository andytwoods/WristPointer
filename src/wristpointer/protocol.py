"""Messages from the Android relay, one per UDP datagram, ASCII.

    a,<x>,<y>,<z>   accelerometer reading in milli-g (watch axes)
    k,next | k,prev slide change
    h               toggle the hand on/off
"""
from dataclasses import dataclass

PORT = 47800


@dataclass(frozen=True)
class Accel:
    x: int
    y: int
    z: int


@dataclass(frozen=True)
class Key:
    direction: str  # "next" or "prev"


@dataclass(frozen=True)
class ToggleHand:
    pass


def parse(datagram: bytes) -> Accel | Key | ToggleHand | None:
    """Parse one datagram; returns None for anything malformed."""
    try:
        parts = datagram.decode("ascii").strip().split(",")
    except UnicodeDecodeError:
        return None
    match parts:
        case ["a", x, y, z]:
            try:
                return Accel(int(x), int(y), int(z))
            except ValueError:
                return None
        case ["k", ("next" | "prev") as direction]:
            return Key(direction)
        case ["h"]:
            return ToggleHand()
    return None
