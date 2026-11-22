"""A transparent, click-through, always-on-top window that draws the hand."""
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtWidgets import QWidget

from wristpointer.mapping import Smoother

HAND = "\N{WHITE UP POINTING INDEX}\N{VARIATION SELECTOR-16}"


class HandOverlay(QWidget):
    def __init__(self, screen, size: int = 96):
        super().__init__(None, Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool
                         | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setGeometry(screen.geometry())
        self.smoother = Smoother()
        self.visible_hand = True
        self.font = QFont("Apple Color Emoji", size)
        self.size = size
        self.timer = QTimer(self, interval=16, timeout=self._frame)  # ~60 fps
        self.timer.start()

    def show(self):
        super().show()
        _float_over_fullscreen(self)

    def set_target(self, x: float, y: float) -> None:
        self.smoother.set_target(x, y)

    def toggle(self) -> None:
        self.visible_hand = not self.visible_hand
        self.update()

    def _frame(self):
        if self.smoother.step() is not None:
            self.update()

    def paintEvent(self, event):
        pos = self.smoother.pos
        if not self.visible_hand or pos is None:
            return
        p = QPainter(self)
        p.setFont(self.font)
        p.setPen(QColor("white"))
        # Put the fingertip, not the glyph's corner, on the target point, and keep the
        # whole glyph on screen even when the target is pinned to an edge.
        x = min(max(pos[0] - self.size * 0.45, 0), self.width() - self.size * 1.2)
        y = min(max(pos[1] + self.size * 1.1, self.size * 1.2), self.height() - self.size * 0.2)
        p.drawText(QPointF(x, y), HAND)


def _float_over_fullscreen(widget: QWidget) -> None:
    """Keep the window above full-screen slide shows and on every Space."""
    try:
        import AppKit
        import objc
        view = objc.objc_object(c_void_p=int(widget.winId()))
        window = view.window()
        window.setLevel_(AppKit.NSScreenSaverWindowLevel)
        window.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                                      | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                                      | AppKit.NSWindowCollectionBehaviorStationary)
        window.setIgnoresMouseEvents_(True)
    except Exception as e:  # not fatal: the hand still shows over normal windows
        print(f"Could not raise overlay above full-screen apps: {e}")
