import pytest

from wristpointer.fake_sender import tilt_to_accel
from wristpointer.mapping import Smoother, TiltMapping


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
