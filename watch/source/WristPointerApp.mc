import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

// Streams wrist tilt and button presses to the Android relay app, which forwards
// them to the Mac. Down = next slide, Up = previous slide, Start = hand on/off.
class WristPointerApp extends Application.AppBase {
    private var _link as Link?;

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
        _link = new Link();
        _link.start();
    }

    function onStop(state as Dictionary?) as Void {
        if (_link != null) {
            _link.stop();
        }
    }

    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        var view = new StatusView(_link);
        return [view, new PointerDelegate(_link)];
    }
}
