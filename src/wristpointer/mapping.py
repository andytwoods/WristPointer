"""Turn a gravity vector into a screen position, and smooth the jumps between updates."""
import math
from dataclasses import dataclass


@dataclass
class TiltMapping:
    # Degrees of wrist roll / pitch that sweep the full screen width / height.
    roll_range: float = 50.0
    pitch_range: float = 35.0
    invert_x: bool = False
    invert_y: bool = False

    def angles(self, x: int, y: int, z: int) -> tuple[float, float]:
        """(roll, pitch) in degrees from an accelerometer reading in milli-g."""
        roll = math.degrees(math.atan2(x, math.hypot(y, z)))
        pitch = math.degrees(math.atan2(y, math.hypot(x, z)))
        return roll, pitch

    def to_screen(self, x: int, y: int, z: int, width: int, height: int,
                  centre: tuple[float, float] = (0.0, 0.0)) -> tuple[float, float]:
        """Screen position for a reading; `centre` is the (roll, pitch) that maps to mid-screen."""
        roll, pitch = self.angles(x, y, z)
        fx = (roll - centre[0]) / self.roll_range
        fy = (pitch - centre[1]) / self.pitch_range
        if self.invert_x:
            fx = -fx
        if self.invert_y:
            fy = -fy
        fx = min(max(fx, -0.5), 0.5)
        fy = min(max(fy, -0.5), 0.5)
        return (0.5 + fx) * width, (0.5 + fy) * height


def _unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v) if n else (0.0, 0.0, 0.0)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


@dataclass
class PointMapping:
    """Where the forearm points: compass direction -> left/right, elevation -> up/down.

    The forearm runs along the watch's x axis (the 9-3 o'clock line). Gravity (accelerometer)
    gives "up"; the magnetometer gives "north"; together they fix the arm's direction in
    the room, the way a laser pointer would.
    """
    yaw_range: float = 40.0        # degrees of sweep left-right across the screen
    elevation_range: float = 25.0  # degrees of sweep up-down
    invert_x: bool = False
    invert_y: bool = False
    forearm: tuple[float, float, float] = (1.0, 0.0, 0.0)

    def angles(self, accel, mag) -> tuple[float, float] | None:
        """(yaw, elevation) in degrees, or None if the readings are degenerate."""
        up = _unit(accel)
        east = _unit(_cross(up, mag))
        if east == (0.0, 0.0, 0.0):
            return None
        north = _cross(east, up)
        f = self.forearm
        yaw = math.degrees(math.atan2(_dot(f, east), _dot(f, north)))
        elevation = math.degrees(math.asin(max(-1.0, min(1.0, _dot(f, up)))))
        return yaw, elevation

    def to_screen(self, accel, mag, width: int, height: int,
                  centre: tuple[float, float]) -> tuple[float, float] | None:
        angles = self.angles(accel, mag)
        if angles is None:
            return None
        dyaw = (angles[0] - centre[0] + 180) % 360 - 180  # shortest way round the compass
        delev = angles[1] - centre[1]
        fx = dyaw / self.yaw_range
        fy = -delev / self.elevation_range  # arm up = hand up the screen
        if self.invert_x:
            fx = -fx
        if self.invert_y:
            fy = -fy
        fx = min(max(fx, -0.5), 0.5)
        fy = min(max(fy, -0.5), 0.5)
        return (0.5 + fx) * width, (0.5 + fy) * height


class Smoother:
    """Glides the drawn position toward the latest target each frame, hiding a 5-10 Hz update rate."""

    def __init__(self, follow: float = 0.25):
        self.follow = follow  # fraction of the remaining distance covered per frame
        self.pos: tuple[float, float] | None = None
        self.target: tuple[float, float] | None = None

    def set_target(self, x: float, y: float) -> None:
        self.target = (x, y)
        if self.pos is None:
            self.pos = self.target

    def step(self) -> tuple[float, float] | None:
        if self.pos is None or self.target is None:
            return None
        px, py = self.pos
        tx, ty = self.target
        self.pos = (px + (tx - px) * self.follow, py + (ty - py) * self.follow)
        return self.pos
