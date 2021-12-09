COMTool
========

 ![GitHub](https://img.shields.io/github/license/neutree/comtool) [![PyPI](https://img.shields.io/pypi/v/comtool.svg)](https://pypi.python.org/pypi/comtool/) ![GitHub Workflow Status](https://img.shields.io/github/workflow/status/neutree/comtool/pack) ![GitHub repo size](https://img.shields.io/github/repo-size/neutree/comtool) ![GitHub Repo stars](https://img.shields.io/github/stars/neutree/comtool?style=social)
 
 ![GitHub all releases](https://img.shields.io/github/downloads/neutree/comtool/total?label=release%20downloads) ![PyPI - Downloads](https://img.shields.io/pypi/dm/comtool?label=pypi%20downloads) ![SourceForge](https://img.shields.io/sourceforge/dt/comtool?label=sourceforge%20downloads)
 

A cross platform serial debug tools written by python

--------

| Windows | Linux | Raspberry Pi | macOS |
| ------- | ----- | ------------ | ----- |
| ![comtool Windows screenshot](./COMTool/assets/screenshot_v2_white.png) | ![comtool linux screenshot](./COMTool/assets/screenshot_V1.4_night.png) | ![comtool Raspberry Pi screenshot](./COMTool/assets/RaspberryPiScreenshot.png)
 | |


| White theme | Dark theme |
| ----------- | ---------- |
| ![comtool white theme](./COMTool/assets/screenshot_v2_white.png) | ![comtool dark theme](./COMTool/assets/screenshot_v2.png) |





> screenshot maybe the old version, the latest may not the same totally! But better performance、more easy to use and more elegant

## Features

- [x] cross platform (Windows, Linux, macOS, Raspberry Pi)(code with python, only if your platform support python)
- [x] reliable stability, no UI freeze
- [x] multiple language support
- [x] serial auto detect
- [x] port baudrate bytesize parity stopbits flow control etc. settings
- [x] basic send/receive data (ascii and hex)
- [x] send and receive data count
- [x] clear received data area
- [x] auto linefeed
- [x] scheduled auto send
- [x] send history and select send again
- [x] custom send items and one click to send
- [x] CR LF(\r\n) / LF(\n) select support
- [x] auto save settings
- [x] key shortcuts like <kbd>Ctrl+Enter</kbd> to send
- [x] escape character support, like `\r \n \t \x` etc.
- [x] multiple character encode support(ASII,GBK(Chinese),UTF-8,UTF-16......)
- [x] receive and send record support add timestamp and save log to file
- [x] unix style terminal color support(e.g.`\x1b[33;42mhello\x1b[0mhello2`)
- [x] night theme and White theme
- [x] rts & dtr control by hand
- [ ] multiple auto send (order and disorder)
- [ ] real time data graphic display
- [ ] TCP UDP support
- [ ] plugin support

## Install binary

### Windows

* Download the latest bin file at the [release page](https://github.com/Neutree/COMTool/releases) or [sourceforge](https://sourceforge.net/projects/comtool/files/)
* Unzip `.zip` file, and click `comtool.exe` to run

### Linux

> Linux has too much version, so we only compile binary for ubuntu.
> Other distribution please install from pypi or source code.
> If you have any idea to pack cross platform binary like flatpak or appimage, you can contribute a pull request or add an issue to tell me how to

* Download release at [release](https://github.com/Neutree/COMTool/releases) page  or [sourceforge](https://sourceforge.net/projects/comtool/files/)

* Add current user to dialout group to avoid `sudo` command
```shell
sudo usermod -a -G dialout $USER
grep 'dialout' /etc/group
reboot #must reboot to take effect
```

* Unzip `.zip` file, and click `comtool` to run

### Rasberry Pi


just open terminal, type the command below:
```
sudo apt install git
git clone https://github.com/Neutree/COMTool.git --depth=1
cd COMTool
pip3 install .
# or
# python setup.py bdist_wheel
# sudo pip3 install dist/COMTool-*.*.*-py3-none-any.whl
```

* Add current user to dialout group to avoid `sudo` command
```shell
sudo usermod -a -G dialout $USER
grep 'dialout' /etc/group
reboot #must reboot to take effect
```

then enjoy by command
```
comtool
``

### macOS

* Download release at [release](https://github.com/Neutree/COMTool/releases) page or [sourceforge](https://sourceforge.net/projects/comtool/files/)
* Install dmg package

If you want to open multiple comtool, now [you have to](https://github.com/Neutree/COMTool/issues/30) open terminal and type
```
open -n /Application/comtool.app
```
or
```
cd /Applicatioin/comtool.app/Contents/MacOS
./comtool
```

## Install python package

For developers or the binary not support your platform's, use this way to install

* Install Python3 first
  * If windows or macOS: [dowload python3](https://www.python.org/downloads/)
  * If linux: ubuntu for example `sudo apt install python3 python3-pip`, macOS `brew install python3 python3-pip`

* Ensure you have `pip`
```shell
pip3 --version
# or
pip --version
```

If no this command, install by
```shell
python3 -m ensurepip
```

* Then install from pypi:
```shell
pip3 install comtool
comtool
```

for Chinese, you can use tuna mirrors to download faster by:
```shell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple comtool
```

* Or you can directly install from github
```
pip3 install git+https://github.com/Neutree/COMTool
```

* Or you can download source code, then install from source code
  * download source code, download [in web page](https://github.com/Neutree/COMTool) or `git clone https://github.com/Neutree/COMTool.git`
  * install
```
cd COMTool
pip install .
```
or build your own wheel binary
```
pip3 install wheel
python setup.py bdist_wheel
pip install dist/COMTool-*.*.*-py3-none-any.whl
comtool
```


## Pack binary


```shell
pip3 install pyinstaller
python pack.py
cd dist
ls
```



## Development

1. Install python(>=3.8) and pip3

Linux:
```
sudo apt install python3 python3-pip
```

Windows: 
  [dowload python3](https://www.python.org/downloads/)

2. install packages like `pyserial` and `PyQt5` etc.(list in [requirements.txt](requirements.txt))
```
cd COMTool
pip3 install -r requirements.txt
```

On Raspberry, `python3-pyqt5` can be install by `apt` command:
```
sudo pip3 install --upgrade pyserial
sudo apt install python3-pyqt5
```

3. clone project
```
git clone https://github.com/Neutree/COMTool.git
```

4. code, resolve bugs or add new reatures

Recommended `PyCharm` IDE or `vscode` to get start


5. pull request

## Add translate

* Install environment first(python pip packages in the requirments.txt)
```shell
apt install python3 python3-pip
pip3 install -r requirements.txt
```

* If you need to add a new lanuage, or skip

Add locale in [i18n.py](./COMTool/i18n.py)
```
locales=["en", "zh_CN", "zh_TW", "ja"]
```
append your language to this list, locales can be found [here](https://www.science.co.il/language/Locale-codes.php) or [wikipedia](https://en.wikipedia.org/wiki/Language_localisation), `zh_CN` for example means China Mainland, corresponding luanguage is simplified Chinese characters, `zh_TW` means China Taiwan, and language is traditional Chinese characters, you can also only use `zh` to use simplified Chinese characters.

* Generate translate files

```shell
python i18n.py prepare
```

This command will generate `.po` files in locales folder

* Translate mannually

Then translate `.po` files, this is a standard translate file format which named `gettext`

* Generate binary translate files

to make it read faster, the text files `.po` should be convert to binary file `.mo`, just run command:
```shell
python i18n.py finish
```
and then you can see `locales/<locale>/LC_MESSAGES/messages.mo` file

* Test

Run application, you will see the new translation

* Pull request

Create a PR to merge your changes to [this repo](https://github.com/Neutree/COMTool)




## Issue and improvement

Create issue [here](https://github.com/Neutree/COMTool/issues/new)


## License

[LGPL-3.0 License](LICENSE)

