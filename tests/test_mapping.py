import pytest

from wristpointer.fake_sender import tilt_to_accel
import math

from wristpointer.mapping import PointMapping, Smoother, TiltMapping


def test_flat_watch_is_mid_screen():
    assert TiltMapping().to_screen(0, 0, 1000, 1920, 1080) == (960, 540)


def test_roll_moves_right_and_clamps():
    m = TiltMapping(roll_range=50)
    x, _ = m.to_screen(*tilt_to_accel(12.5, 0), 1000, 1000)
    assert x == pytest.approx(750, abs=2)
    x, _ = m.to_screen(*tilt_to_accel(60, 0), 1000, 1000)
    assert x == 1000


def test_centre_offset():
    m = TiltMapping()
    reading = tilt_to_accel(10, 5)
    assert m.to_screen(*reading, 1000, 1000, centre=m.angles(*reading)) == pytest.approx((500, 500))


def test_smoother_glides():
    s = Smoother(follow=0.5)
    s.set_target(0, 0)
    s.set_target(100, 0)
    assert s.step() == (50, 0)
    assert s.step() == (75, 0)


def _arm(yaw_deg, elev_deg):
    """Readings for a forearm (watch x axis) pointing at compass yaw / elevation, watch face up-ish.

    World: north=(1,0,0) east=(0,1,0) up=(0,0,1). Field points north and down (UK-like dip).
    """
    y, e = math.radians(yaw_deg), math.radians(elev_deg)
    fx = (math.cos(e) * math.cos(y), math.cos(e) * math.sin(y), math.sin(e))
    side = (-math.sin(y), math.cos(y), 0.0)              # watch y axis, level
    fz = (fx[1] * side[2] - fx[2] * side[1], fx[2] * side[0] - fx[0] * side[2], fx[0] * side[1] - fx[1] * side[0])
    up, field = (0.0, 0.0, 1.0), (0.4, 0.0, -0.9)
    to_watch = lambda v: tuple(round(1000 * sum(a * b for a, b in zip(axis, v))) for axis in (fx, side, fz))
    return to_watch(up), to_watch(field)


def test_pointing_angles():
    m = PointMapping()
    yaw, elev = m.angles(*_arm(30, 10))
    assert yaw == pytest.approx(30, abs=1)
    assert elev == pytest.approx(10, abs=1)


def test_pointing_right_and_up_moves_hand_right_and_up():
    m = PointMapping(yaw_range=40, elevation_range=25)
    centre = m.angles(*_arm(0, 0))
    x, y = m.to_screen(*_arm(10, 5), 1000, 1000, centre)
    assert x == pytest.approx(750, abs=10)
    assert y == pytest.approx(300, abs=10)


def test_pointing_wraps_round_north():
    m = PointMapping(yaw_range=40)
    centre = m.angles(*_arm(355, 0))
    x, _ = m.to_screen(*_arm(5, 0), 1000, 1000, centre)
    assert x == pytest.approx(750, abs=10)
