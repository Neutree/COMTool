#!/bin/sh
# `sh build_bin.sh`
# please install cx-freeze first and make sure command `cxfreeze` can execute`
# pip install cx-freeze

if [[ $1 == "windows" ]]; then
    cxfreeze  main.py --target-dir PySerialAssistant  --icon ../assets/logo.ico --base-name=win32gui
elif [[ $1 == "linux" ]]; then
    echo 'not test on linux yet'
    exit 0
elif [[ $1 == "macos" ]]; then
    echo 'not test linux yet'
    exit 0
else
    echo 'no parameter: linux windows or mac'
    exit 0
fi

cp ../assets/logo.png PySerialAssistant/logo.png
echo "bin file in folder PySerialAssistant"
