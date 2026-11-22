"""Messages from the Android relay, one per UDP datagram, ASCII.

    a,<x>,<y>,<z>[,<mx>,<my>,<mz>]
                    accelerometer in milli-g, then magnetometer (any unit), watch axes
    k,next | k,prev slide change
    h               re-centre: the next reading becomes mid-screen
"""
from dataclasses import dataclass

PORT = 47800


@dataclass(frozen=True)
class Accel:
    x: int
    y: int
    z: int
    mag: tuple[int, int, int] | None = None


@dataclass(frozen=True)
class Key:
    direction: str  # "next" or "prev"


@dataclass(frozen=True)
class Recentre:
    pass


def parse(datagram: bytes) -> Accel | Key | Recentre | None:
    """Parse one datagram; returns None for anything malformed."""
    try:
        parts = datagram.decode("ascii").strip().split(",")
    except UnicodeDecodeError:
        return None
    match parts:
        case ["a", x, y, z, *mag] if len(mag) in (0, 3):
            try:
                return Accel(int(x), int(y), int(z), tuple(int(m) for m in mag) if mag else None)
            except ValueError:
                return None
        case ["k", ("next" | "prev") as direction]:
            return Key(direction)
        case ["h"]:
            return Recentre()
    return None
