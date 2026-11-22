import Toybox.Communications;
import Toybox.Lang;
import Toybox.Sensor;
import Toybox.System;
import Toybox.Timer;
import Toybox.WatchUi;

// Sends one message at a time to the phone. Tilt readings are dropped while a send is in
// flight, so the rate adapts to the Bluetooth link; button presses queue and go first.
class Link extends Communications.ConnectionListener {
    private var _timer as Timer.Timer;
    private var _busy as Boolean = false;
    private var _keys as Array<String> = [] as Array<String>;
    var sent as Number = 0;
    var errors as Number = 0;
    var rate as Number = 0;  // messages per second, updated every second
    private var _sentAtLastTick as Number = 0;
    private var _ticks as Number = 0;

    function initialize() {
        ConnectionListener.initialize();
        _timer = new Timer.Timer();
    }

    function start() as Void {
        _timer.start(method(:tick), 50, true);
    }

    function stop() as Void {
        _timer.stop();
    }

    function key(message as String) as Void {
        _keys.add(message);
        pump();
    }

    function tick() as Void {
        _ticks += 1;
        if (_ticks % 20 == 0) {
            rate = sent - _sentAtLastTick;
            _sentAtLastTick = sent;
            WatchUi.requestUpdate();
        }
        pump();
    }

    private function pump() as Void {
        if (_busy) {
            return;
        }
        var message = null;
        if (_keys.size() > 0) {
            message = _keys[0];
            _keys = _keys.slice(1, null);
        } else {
            var accel = Sensor.getInfo().accel;
            if (accel != null) {
                message = "a," + accel[0] + "," + accel[1] + "," + accel[2];
            }
        }
        if (message != null) {
            _busy = true;
            Communications.transmit(message, null, self);
        }
    }

    function onComplete() as Void {
        sent += 1;
        _busy = false;
    }

    function onError() as Void {
        errors += 1;
        _busy = false;
    }
}
