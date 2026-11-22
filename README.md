# Wrist Pointer

Tilt your wrist and a ☝️ hand moves over your slides. The watch's Down button moves to the
next slide, Up goes back, and Start re-centres: point at the middle of the screen and press it.

```
fēnix 6S Pro ──Bluetooth──▶ Android relay app ──UDP 47800 (Wi-Fi)──▶ Mac overlay + arrow keys
   watch/                      android/                                src/wristpointer/
```

The watch sends raw accelerometer readings (milli-g). The Mac turns them into a position,
so tuning needs no watch rebuild. Expect 5-10 updates a second; the Mac glides between them.

## Mac side (this PyCharm project)

```
uv sync
uv run wristpointer -v            # the overlay; -v prints every message
uv run wristpointer-fake --mouse  # test without a watch: the mouse stands in for your wrist
uv run pytest
```

Slide keys need **Accessibility** permission for whatever runs it (PyCharm or Terminal):
System Settings → Privacy & Security → Accessibility. Without it, the hand still moves but
slides don't change. The arrow keys go to the app in front, so click into the slide show
first. Works with PowerPoint, Keynote and PDF viewers.

Tuning: `--invert-x` / `--invert-y` if the hand moves the wrong way; the sweep angles are
`PointMapping.yaw_range` / `elevation_range` in `mapping.py` (`--mode tilt` uses wrist twist
instead). Start re-centres: wherever your arm points on the next reading becomes mid-screen.

## Watch app (`watch/`)

Needs the Connect IQ SDK, `brew install openjdk@17`, and a developer key at
`~/.connectiq/developer_key.der` (all set up on the Mac laptop already).

```
scripts/build_watch.sh
```

Then plug the watch in, open OpenMTP and copy `watch/bin/WristPointer.prg` into `GARMIN/APPS/`.
The watch screen shows messages/second and the error count.

## Android relay (`android/`)

```
scripts/install_android.sh   # phone on USB with USB debugging allowed
```

Open **Wrist Pointer Relay** on the phone and keep it open while presenting. Phone and Mac
must be on the same Wi-Fi. Leave "Mac IP" blank to broadcast; if nothing arrives, type the
Mac's IP (`ipconfig getifaddr en0`). The watch app id in `MainActivity.WATCH_APP_ID` must
match `watch/manifest.xml`.
