#!/bin/bash
# Compile the watch app for the fenix 6S Pro -> watch/bin/WristPointer.prg
set -euo pipefail
cd "$(dirname "$0")/../watch"
export JAVA_HOME="$(brew --prefix openjdk@17)"
SDK="$(cat ~/Library/Application\ Support/Garmin/ConnectIQ/current-sdk.cfg)"
"$SDK/bin/monkeyc" -d "${DEVICE:-fenix6spro}" -f monkey.jungle -o bin/WristPointer.prg -y ~/.connectiq/developer_key.der
echo "Copy watch/bin/WristPointer.prg into GARMIN/APPS/ with OpenMTP."
