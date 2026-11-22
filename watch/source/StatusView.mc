import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;

class StatusView extends WatchUi.View {
    private var _link as Link?;

    function initialize(link as Link?) {
        View.initialize();
        _link = link;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
        var cx = dc.getWidth() / 2;
        var h = dc.getHeight();
        var status = "No link";
        if (_link != null) {
            status = _link.rate + "/s  err " + _link.errors;
        }
        dc.drawText(cx, h * 0.22, Graphics.FONT_SMALL, "Wrist Pointer", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx, h * 0.42, Graphics.FONT_MEDIUM, status, Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx, h * 0.66, Graphics.FONT_XTINY, "Down next / Up back", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx, h * 0.76, Graphics.FONT_XTINY, "Start: re-centre", Graphics.TEXT_JUSTIFY_CENTER);
    }
}

class PointerDelegate extends WatchUi.BehaviorDelegate {
    private var _link as Link?;

    function initialize(link as Link?) {
        BehaviorDelegate.initialize();
        _link = link;
    }

    function onNextPage() as Boolean {
        _link.key("k,next");
        return true;
    }

    function onPreviousPage() as Boolean {
        _link.key("k,prev");
        return true;
    }

    function onSelect() as Boolean {
        _link.key("h");
        return true;
    }
}
