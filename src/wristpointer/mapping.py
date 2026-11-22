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
