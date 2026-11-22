# Wrist Pointer

A Garmin watch steers a virtual pointing hand (☝️) drawn over a presentation on a Mac. Built and tried on a fenix 6S Pro, it uses the watch’s Down button for the next slide, Up for the previous slide, and Start to re-centre the hand.

> **Experimental and probably unusable in practice.** In testing, only about 2–3 sensor updates per second reached the Mac. The fenix 6S Pro’s accelerometer and compass were not sensitive or fast enough for this use, leaving the hand jerky and imprecise. The code is public in case it helps someone, perhaps with a newer watch or a different approach.

## How it works

```text
Garmin watch (Monkey C)
    -> Bluetooth
Android relay (Java, Connect IQ Mobile SDK)
    -> UDP port 47800 over Wi-Fi
Mac overlay (Python, PyQt6 and Quartz)
```

Connect IQ apps cannot act as a Bluetooth mouse or keyboard, or communicate directly with a computer in this setup. The Android app receives watch messages through Garmin’s Connect IQ Mobile SDK and forwards them to the Mac.

The Mac draws the hand in a transparent, click-through, always-on-top PyQt6 window covering the primary screen. Quartz sends left and right arrow-key presses to the foreground application for slide changes. The overlay smooths movement between readings, but this cannot recover the missing sensor updates.

The default **pointing mode** uses the accelerometer to establish “up” and the magnetometer to establish “north”. It assumes the forearm follows the watch’s positive x axis, along the 9–3 o’clock line. It calculates the arm’s yaw and elevation, then maps changes from the centre position to screen coordinates.

**Tilt mode** maps accelerometer-derived wrist roll and pitch to screen coordinates. It is used when a message has no magnetometer readings, or when selected with `--mode tilt`.

The first usable reading establishes the centre. Point towards the middle of the screen and press Start to make the next usable reading the new centre.

## Mac setup

Requirements: macOS, `uv`, and Python 3.13 or newer. Run commands from the repository root.

```sh
uv sync
uv run wristpointer -v
```

`-v` prints parsed incoming messages. Press Ctrl+C to quit.

For slide keys, grant **Accessibility** permission to the application running Python, such as Terminal or PyCharm:

**System Settings → Privacy & Security → Accessibility**

Without this permission, the hand can move but slide keys are dropped. Bring the presentation to the foreground before using the watch buttons; arrow keys go to whichever application has focus.

## Watch setup

Install the Garmin Connect IQ SDK and the device support for `fenix6spro`. Select the SDK in Garmin’s SDK Manager so that this file points to its installation:

```text
~/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg
```

Create a Connect IQ developer signing key and save it at:

```text
~/.connectiq/developer_key.der
```

Install Java 17 and build:

```sh
brew install openjdk@17
scripts/build_watch.sh
```

The script sets `JAVA_HOME` using Homebrew’s `openjdk@17`, reads the SDK path above, and runs `monkeyc` with the developer key. Its default target is `fenix6spro`; the manifest also includes `fenix6xpro`, selectable with:

```sh
DEVICE=fenix6xpro scripts/build_watch.sh
```

Connect the watch by USB, open **OpenMTP**, and copy `watch/bin/WristPointer.prg` into the watch’s `GARMIN/APPS/` directory. Disconnect it and launch Wrist Pointer.

The watch screen shows completed messages per second and a send-error count. Only one transmission is allowed at a time; button messages are queued ahead of sensor readings.

## Android relay setup

Use an Android phone running Android 8.0 or newer, with **Garmin Connect** installed and the watch paired through it.

Install Android Studio, Android SDK Platform 36 and Android SDK Platform-Tools. Make sure `adb` is on your `PATH`. The installation script uses Android Studio’s bundled Java runtime at:

```text
/Applications/Android Studio.app/Contents/jbr/Contents/Home
```

Check `android/local.properties`: its `sdk.dir` must point to your Android SDK installation. The script creates this file with `$HOME/Library/Android/sdk` only if it does not already exist.

Enable USB debugging on the phone, connect it by USB, and accept the debugging authorisation prompt.

```sh
adb devices
scripts/install_android.sh
```

The script runs `./gradlew assembleDebug -q` inside `android/`, then installs the APK with:

```sh
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

Open **Wrist Pointer Relay** and keep it open while using the watch. Put the phone and Mac on the same Wi-Fi network, start the Mac overlay, and launch the watch app.

Leave the relay’s **Mac IP** field blank to broadcast to `255.255.255.255`. If messages do not arrive, enter the Mac’s local IP address instead. On a Mac using `en0` for Wi-Fi:

```sh
ipconfig getifaddr en0
```

Broadcast can be blocked, for example by a phone VPN. Check the VPN and network settings if entering the Mac’s address does not help. The relay displays its connection status, message count and last forwarded message.

`MainActivity.WATCH_APP_ID` must match the application ID in `watch/manifest.xml`.

## UDP protocol

Messages are ASCII, one message per UDP datagram. The default destination port is **47800**. The relay forwards the watch’s message text unchanged.

| Message | Meaning |
| --- | --- |
| `a,<x>,<y>,<z>` | Accelerometer readings in milli-g, in watch axes; uses tilt mapping. |
| `a,<x>,<y>,<z>,<mx>,<my>,<mz>` | Accelerometer plus magnetometer readings; uses pointing mapping unless tilt mode is forced. |
| `k,next` | Press the right arrow key. |
| `k,prev` | Press the left arrow key. |
| `h` | Clear the centre; the next usable sensor reading establishes a new centre. |

All sensor fields are integers. Magnetometer units are arbitrary because the mapping uses direction. Malformed messages are ignored.

## Tuning

Pass these options to `uv run wristpointer`:

| Option | Effect |
| --- | --- |
| `--mode point` | Aim with the forearm using accelerometer and magnetometer readings; the default. |
| `--mode tilt` | Use wrist roll and pitch, ignoring magnetometer readings. |
| `--invert-x` / `--invert-y` | Reverse horizontal or vertical movement. |
| `--forearm 1,0,0` | Forearm direction in watch axes; the default. Try `--forearm=-1,0,0` for the opposite direction. |
| `--port 47800` | UDP listening port. The Android relay and fake sender use a fixed port of 47800. |
| `-v` / `--verbose` | Print every parsed message. |

Edit `src/wristpointer/mapping.py` to change the angles needed to cross the full screen:

| Mapping | Horizontal range | Vertical range |
| --- | --- | --- |
| `PointMapping` | `yaw_range = 40.0°` | `elevation_range = 25.0°` |
| `TiltMapping` | `roll_range = 50.0°` | `pitch_range = 35.0°` |

Smaller ranges make movement more sensitive. Positions are clamped to the screen edges. `Smoother.follow` defaults to `0.25`, the fraction of the remaining distance covered each frame. These changes require restarting the Mac app, without rebuilding the watch app.

## Testing without a watch

Start the overlay, then run a fake sender in a second terminal:

```sh
uv run wristpointer --mode tilt
```

```sh
uv run wristpointer-fake          # move in a slow circle
uv run wristpointer-fake --mouse  # use the mouse position instead
```

Run one sender at a time. It sends accelerometer-only messages to `127.0.0.1:47800`, defaulting to 8 updates per second. Use `--hz 2` to try a slower rate, or `--host <Mac-IP>` to send elsewhere. This exercises tilt mapping, not compass-based pointing or watch-button delivery.

Run the protocol and mapping tests with:

```sh
uv run pytest
```

## Repository layout

```text
src/wristpointer/  Mac overlay, UDP receiver, mapping, slide keys and fake sender
watch/            Garmin Connect IQ app written in Monkey C
android/          Java relay app using the Connect IQ Mobile SDK
scripts/          Watch build and Android build/install scripts
tests/            Protocol parsing and mapping tests
pyproject.toml    Python dependencies and command-line entry points
```

## Licence

MIT. See [LICENSE](LICENSE).