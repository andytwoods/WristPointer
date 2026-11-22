"""Listen for the watch (via the Android relay) and drive the hand and slides."""
import argparse
import socket
import sys

from PyQt6.QtCore import QObject, QSocketNotifier
from PyQt6.QtWidgets import QApplication

from wristpointer import keys, protocol
from wristpointer.mapping import PointMapping, TiltMapping
from wristpointer.overlay import HandOverlay


class Receiver(QObject):
    def __init__(self, overlay: HandOverlay, mapping: TiltMapping, pointing: PointMapping | None,
                 port: int, verbose: bool):
        super().__init__()
        self.overlay = overlay
        self.mapping = mapping
        self.pointing = pointing  # None = tilt mode even if the watch sends compass data
        self.verbose = verbose
        self.centre: tuple[float, float] | None = None  # first reading = mid-screen
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", port))
        self.sock.setblocking(False)
        self.notifier = QSocketNotifier(self.sock.fileno(), QSocketNotifier.Type.Read, self)
        self.notifier.activated.connect(self._read)

    def _read(self):
        while True:
            try:
                data, _ = self.sock.recvfrom(256)
            except BlockingIOError:
                return
            self.handle(protocol.parse(data))

    def handle(self, msg):
        if self.verbose:
            print(msg)
        match msg:
            case protocol.Accel(x, y, z, mag) if mag is not None and self.pointing is not None:
                if self.centre is None:
                    self.centre = self.pointing.angles((x, y, z), mag)
                    if self.centre is None:
                        return
                geo = self.overlay.geometry()
                target = self.pointing.to_screen((x, y, z), mag, geo.width(), geo.height(), self.centre)
                if target is not None:
                    self.overlay.set_target(*target)
            case protocol.Accel(x, y, z):
                if self.centre is None:
                    self.centre = self.mapping.angles(x, y, z)
                geo = self.overlay.geometry()
                self.overlay.set_target(*self.mapping.to_screen(x, y, z, geo.width(), geo.height(), self.centre))
            case protocol.Key(direction):
                keys.press(direction)
            case protocol.ToggleHand():
                # The watch's Start button: wherever the arm points next becomes mid-screen.
                self.centre = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=protocol.PORT)
    parser.add_argument("--invert-x", action="store_true")
    parser.add_argument("--invert-y", action="store_true")
    parser.add_argument("--mode", choices=["point", "tilt"], default="point",
                        help="point: aim with your forearm (needs the compass); tilt: twist your wrist")
    parser.add_argument("--forearm", default="1,0,0",
                        help="forearm direction in watch axes, e.g. -1,0,0 on the other wrist")
    parser.add_argument("-v", "--verbose", action="store_true", help="print every message")
    args = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    app = QApplication(sys.argv)
    if not keys.accessibility_allowed():
        print("Slide keys need Accessibility permission: System Settings > Privacy & Security > "
              "Accessibility > enable the app running this (PyCharm or Terminal).")
    overlay = HandOverlay(app.primaryScreen())
    overlay.show()
    pointing = None
    if args.mode == "point":
        pointing = PointMapping(invert_x=args.invert_x, invert_y=args.invert_y,
                                forearm=tuple(float(c) for c in args.forearm.split(",")))
    receiver = Receiver(overlay, TiltMapping(invert_x=args.invert_x, invert_y=args.invert_y), pointing,
                        args.port, args.verbose)  # noqa: F841 (kept alive by the event loop)
    print(f"Listening on UDP {args.port}. Ctrl+C to quit.")
    import signal
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    from PyQt6.QtCore import QTimer
    QTimer(app, interval=200, timeout=lambda: None).start()  # lets Python see Ctrl+C
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
