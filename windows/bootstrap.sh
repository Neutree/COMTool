#!/bin/sh

# This script is meant to be run through MinGW


pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-pip mingw-w64-ucrt-x86_64-nsis mingw-w64-ucrt-x86_64-nsis-nsisunz mingw-w64-ucrt-x86_64-gcc zip unzip

# pip install error:  : --plat-name must be one of ('win32', 'win-amd64', 'win-arm32', 'win-arm64')
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-pynacl mingw-w64-ucrt-x86_64-python-pyqt5 mingw-w64-ucrt-x86_64-python-cryptography

# pip install error:  : can't find Rust compiler
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-bcrypt

# setuptools
pacman -S --needed --noconfirm python-setuptools
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-pyserial
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-requests
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-babel
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-qtawesome
pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-paramiko

pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-pyperclip

pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python-pyqtgraph
echo "Done"
