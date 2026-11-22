"""Press the arrow keys in whatever app is in front (PowerPoint, Keynote, a PDF viewer)."""
import Quartz

RIGHT_ARROW = 124
LEFT_ARROW = 123


def press(direction: str) -> None:
    code = RIGHT_ARROW if direction == "next" else LEFT_ARROW
    for down in (True, False):
        event = Quartz.CGEventCreateKeyboardEvent(None, code, down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def accessibility_allowed() -> bool:
    """Key presses are silently dropped unless this process has Accessibility permission."""
    from ApplicationServices import AXIsProcessTrusted
    return bool(AXIsProcessTrusted())
