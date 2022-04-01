COMTool
========

English | [中文](./README_ZH.MD)

 ![GitHub](https://img.shields.io/github/license/neutree/comtool) [![PyPI](https://img.shields.io/pypi/v/comtool.svg)](https://pypi.python.org/pypi/comtool/) ![GitHub Workflow Status](https://img.shields.io/github/workflow/status/neutree/comtool/pack) ![GitHub repo size](https://img.shields.io/github/repo-size/neutree/comtool) ![GitHub Repo stars](https://img.shields.io/github/stars/neutree/comtool?style=social)

 [![GitHub all releases](https://img.shields.io/github/downloads/neutree/comtool/total?label=release%20downloads)](https://github.com/Neutree/COMTool/releases) [![PyPI - Downloads](https://img.shields.io/pypi/dm/comtool?label=pypi%20downloads)](https://pypi.org/project/COMTool/) [![SourceForge](https://img.shields.io/sourceforge/dt/comtool?label=sourceforge%20downloads)](https://sourceforge.net/projects/comtool)


A cross platform serial debug tools written by python

--------

| Windows | Linux | Raspberry Pi | macOS |
| ------- | ----- | ------------ | ----- |
| ![comtool Windows screenshot](./COMTool/assets/screenshot_v2_white.png) | ![comtool linux screenshot](./COMTool/assets/screenshot_V1.4_night.png) | ![comtool Raspberry Pi screenshot](./COMTool/assets/RaspberryPiScreenshot.png)
 | |


| White theme | Dark theme | protocol plugin | TCP/UDP | Terminal |
| ----------- | ---------- | --------------- | ------- | -------- |
| ![comtool white theme](./COMTool/assets/screenshot_v2_white.png) | ![comtool dark theme](./COMTool/assets/screenshot_v2.png) | ![comtool protocol plugin](./COMTool/assets/screenshot_protocol_v2.3.png) | ![tcp udp plugin](./COMTool/assets/tcp_udp.png) | ![terminal](./COMTool/assets/screenshot_terminal.png) |






> screenshot maybe the old version, the latest may not the same totally! But better performance、more easy to use and more elegant

## Features

- [x] cross platform (Windows, Linux, macOS, Raspberry Pi)(code with python, only if your platform support python)
- [x] reliable stability, no UI freeze
- [x] multiple language support
- [x] serial auto detect, and remember last selected support
- [x] serial offline auto reconnect support
- [x] port baudrate(any value) bytesize parity stopbits flow control etc. settings
- [x] basic send/receive data (ascii and hex)
- [x] send and receive data count
- [x] clear received data area
- [x] auto linefeed
- [x] scheduled auto send
- [x] send history and select send again
- [x] custom most usage data items and one click to send
- [x] CR LF(\r\n) or LF(\n)  support
- [x] auto save settings
- [x] key shortcuts like <kbd>Ctrl+Enter</kbd> to send
- [x] escape character support, like `\r \n \t \x` etc.
- [x] multiple character encode support(`ASII,GBK(Chinese),UTF-8,UTF-16` etc.)
- [x] receive and send record support add timestamp and save log to file
- [x] send file
- [x] unix terminal style color support(e.g.`\x1b[33;42mhello\x1b[0mhello2`)
- [x] night theme and White theme
- [x] rts & dtr control by hand
- [x] protocol with customable encoding and decoding method support, 
- [x] Custom shortcut send(in protocol plugin)
- [x] TCP UDP support
- [x] Terminal mode support
- [x] plugin support(Create plugin see [docs/plugins.md](./docs/plugins.md))
- [ ] real time data graphic display

## Install binary

### Windows

* Download the latest bin file at the [release page](https://github.com/Neutree/COMTool/releases) or [sourceforge](https://sourceforge.net/projects/comtool/files/)
* Unzip `.zip` file, and click `comtool.exe` to run
> And you can install by scoop, maintained by [StudentWeis](https://github.com/Neutree/COMTool/issues/50)
> ```
> scoop bucket add Nightly https://github.com/StudentWeis/Nightly
> scoop install comtool
> ```

### Linux

Linux has too much version, so we only compile binary for ubuntu.
Other distribution please [install from pypi or source code](#Install-python-package).
If you have any idea to pack cross platform binary like flatpak or appimage, you can contribute a pull request or add an issue to tell me how to

> Arch Linux and its derivative distributions can install from AUR(maintained by [taotieren](https://github.com/Neutree/COMTool/issues/44))：
> ```bash
> # Release version
> yay -S python-comtool
> # Development version
> yay -S python-comtool-git
> ```

* Download release at [release](https://github.com/Neutree/COMTool/releases) page, and extract files from `.zip` file, and click `comtool` to run

* Add current user to dialout group to avoid `sudo` command
```shell
sudo usermod -a -G dialout $USER
grep 'dialout' /etc/group
reboot #must reboot to take effect
```

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
```

### macOS

* Download release at [release](https://github.com/Neutree/COMTool/releases) page or [sourceforge](https://sourceforge.net/projects/comtool/files/)
* Install dmg package

If you want to open multiple comtool, just right click dock icon, then click `New Window`.

or you can open terminal and type
```
open -n /Application/comtool.app
```
or
```
cd /Applicatioin/comtool.app/Contents/MacOS
./comtool
```

> Because the program is not signed by the developer, it will warn when you open it for the first time. You need to go to `Settings -> Security and Privacy -> General` to see the prompt `comtool` and click `Open anyway`.

## Windows defender shows comtool binary is malware?

If your program is download from [here](https://github.com/Neutree/COMTool/releases), it's ok, the error caused by [pack issue](https://github.com/pyinstaller/pyinstaller/issues/4852), all the source code and pack script is here, even the pack progress is totally automated with github action, no one manually pack.

If you remain have concern, just download source code to run with python or pack yourself.

Of course, if you find a better pack way, please open issue to tell us.


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

* By the way, you should add current user to dialout group to avoid `sudo` command
```shell
sudo usermod -a -G dialout $USER
grep 'dialout' /etc/group
reboot #must reboot to take effect
```

## Manually add app to start menu on Linux

* Copy [tool/comtool.desktop](tool/comtool.desktop) to `/usr/share/applications` folder(may need `root` user to do this)
* Edit `/usr/share/applications/comtool.desktop`, change icon path `Icon=/usr/local/COMTool/assets/logo.ico` to actual [icon](COMTool/assets/logo.ico) path, you can also use your love icon
* Then you can find comtool app in start menu(or app center)

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

How to run:
Generate translate binary files first(`.mo`)

```
python COMTool/i18n.py finish
```

Then execute main program

```
python COMTool/Main.py
```

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
append your language to this list, locales can be found [here](https://www.science.co.il/language/Locale-codes.php) or [wikipedia](https://en.wikipedia.org/wiki/Language_localisation), `zh_CN` for example means China Mainland, corresponding language is simplified Chinese characters, `zh_TW` means China Taiwan, and language is traditional Chinese characters, you can also only use `zh` to use simplified Chinese characters.

* Generate translate files

```shell
python i18n.py prepare
```

This command will generate `.po` files in locales folder

* Translate mannually

Then translate `.po` files, this is a standard translate file format which named `gettext`

* Generate binary translate files

to make program read faster, the text files `.po` should be convert to binary file `.mo`, just run command:
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

And used these open source projects as libraries:

* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/): [GNU GPL v3](https://www.riverbankcomputing.com/software/pyqt/)
* [pyserial](https://github.com/pyserial/pyserial): [BSD-3-Clause](https://github.com/pyserial/pyserial/blob/master/LICENSE.txt)
* [requests](https://github.com/psf/requests): [Apache 2.0](https://github.com/psf/requests/blob/main/LICENSE)
* [Babel](https://github.com/python-babel/babel): [BSD](https://github.com/python-babel/babel/blob/master/LICENSE)
* [qtawesome](https://github.com/spyder-ide/qtawesome): [MIT](https://github.com/spyder-ide/qtawesome/blob/master/LICENSE.txt)
* [pyte](https://github.com/selectel/pyte): [LGPL 3.0](https://github.com/selectel/pyte/blob/master/LICENSE)
* [paramiko](https://github.com/paramiko/paramiko): [LGPL 2.1](https://github.com/paramiko/paramiko/blob/main/LICENSE)
* [pyperclip](https://github.com/asweigart/pyperclip): [BSD-3-Clause](https://github.com/asweigart/pyperclip/blob/master/LICENSE.txt)