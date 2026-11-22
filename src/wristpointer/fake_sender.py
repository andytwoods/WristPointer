"""Pretend to be the watch: the mouse position becomes a tilt, so the Mac side can be tested alone.

Moves the hand in a slow circle by default; --mouse follows the real mouse pointer instead.
"""
import argparse
import math
import socket
import time

from wristpointer import protocol


def tilt_to_accel(roll_deg: float, pitch_deg: float) -> tuple[int, int, int]:
    r, p = math.radians(roll_deg), math.radians(pitch_deg)
    x, y = math.sin(r), math.sin(p)
    z = math.sqrt(max(0.0, 1 - x * x - y * y))
    return round(x * 1000), round(y * 1000), round(z * 1000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--hz", type=float, default=8, help="updates per second, like the real relay")
    parser.add_argument("--mouse", action="store_true")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send = lambda text: sock.sendto(text.encode(), (args.host, protocol.PORT))
    send("a,0,0,1000")  # centre
    start = time.time()
    while True:
        if args.mouse:
            import Quartz
            loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
            bounds = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
            roll = (loc.x / bounds.size.width - 0.5) * 50
            pitch = (loc.y / bounds.size.height - 0.5) * 35
        else:
            t = time.time() - start
            roll, pitch = 20 * math.cos(t), 14 * math.sin(t)
        send("a,%d,%d,%d" % tilt_to_accel(roll, pitch))
        time.sleep(1 / args.hz)


if __name__ == "__main__":
    main()
