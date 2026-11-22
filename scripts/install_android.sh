#!/bin/bash
# Build the relay app and install it on the USB-connected phone.
set -euo pipefail
cd "$(dirname "$0")/../android"
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
[ -f local.properties ] || echo "sdk.dir=$HOME/Library/Android/sdk" > local.properties
./gradlew assembleDebug -q
adb install -r app/build/outputs/apk/debug/app-debug.apk
