from wristpointer.protocol import Accel, Key, ToggleHand, parse


def test_accel():
    assert parse(b"a,12,-340,980") == Accel(12, -340, 980)


def test_keys():
    assert parse(b"k,next") == Key("next")
    assert parse(b"k,prev\n") == Key("prev")


def test_toggle():
    assert parse(b"h") == ToggleHand()


def test_garbage_is_ignored():
    for junk in (b"", b"a,1,2", b"a,x,2,3", b"k,sideways", b"\xff\xfe"):
        assert parse(junk) is None


def test_accel_with_magnetometer():
    assert parse(b"a,1,2,3,40,-50,60") == Accel(1, 2, 3, (40, -50, 60))
    assert parse(b"a,1,2,3,40,-50") is None
