#!/bin/sh

# This script is meant to be run through MinGW

APP=comtool

if [ ! -d ../venv ]; then
	echo "Setting up virtual environment..."
	python3 -m venv --system-site-packages venv
	. venv/bin/activate
	python3 -m pip install --upgrade pip
	PYINSTALLER_COMPILE_BOOTLOADER=1 PYI_STATIC_ZLIB=1 python3 -m pip install -r ../requirements.txt
else
	. ../venv/bin/activate
fi

echo "Running pyinstaller..."

if [ "$1" != "portable" ]; then
	python3 -m PyInstaller $APP.spec
	echo "Preparing app..."
	cd dist/$APP
	zip -r $APP.zip *
	mv $APP.zip ../..
	cd ../..
	echo $(du -sk dist/$APP | cut -f 1) > INSTALLSIZE
	echo $(uname -m) > ARCH
	echo "Running makensis..."
	makensis $APP.nsi
else
	python3 -m PyInstaller $APP-portable.spec
	echo "Preparing app..."
	version=$(cat ../VERSION)
	mv dist/* ./$APP-$version-$(uname -m)-portable.exe
fi
for exe in $APP*.exe; do
    echo $(sha256sum $exe) > $exe.sha256
done

echo "Cleaning up..."

deactivate
mv $APP*.exe* ../..
rm -r build
if [ "$1" != "portable" ]; then
	rm $APP.zip
	rm INSTALLSIZE
	rm ARCH
	rm -r dist/*/*
	rm -r dist
else
	rm -r dist
fi
if [ ! -d ../venv ]; then
	rm -r venv
fi
