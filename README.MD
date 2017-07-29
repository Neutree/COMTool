COMTool
========

 [![PyPI](https://img.shields.io/pypi/v/comtool.svg)](https://pypi.python.org/pypi/comtool/)

A cross platform serial debug tools written by python
![screenshot](./COMToolData/assets/screenshot_V1.0.png)
> screenshot shows the version 1.0, the latest may not the same totally! But better performance、more easy to use and more elegant

## Features

- [x] cross platform
- [x] port baudrate bytesize parity stopbits settings
- [x] basic send data (ascii and hex)
- [x] basic receive data (ascii and hex)
- [x] send and receive data count
- [x] clear received data area
- [x] auto linefeed on every once receive
- [x] scheduled auto send
- [x] send history and select send again
- [x] serial auto detect
- [x] CR LF / LF select support
- [x] auto save settings
- [x] <kbd>Ctrl+Enter</kbd> to send
- [ ] escape character support, like \x \r \n etc.
- [ ] multiple character encode support
- [ ] multiple auto send (order and disorder)
- [ ] unix style terminal color support
- [ ] night theme and White theme

## Install

### Windows

there's three ways:
1. download excutable bin file, easiest way for one never used python
  * Download the latest bin file at the [release page](https://github.com/Neutree/COMTool/releases)
  * unzip, and run COMTool.exe
2. Install Python3 first then install from pypi:
  * [dowload python3](https://www.python.org/downloads/)
  * Install pip,save https://bootstrap.pypa.io/get-pip.py as file get-pip.py
```
sduo python get-pip.py
```
  * Install by pip,
```
pip install COMTool
```
3. Or you can download source code, then install from source code
  * download sourcecode
  * install
```
python setup.py bdist_wheel
```
COMTool.exe in dir `C:\Users\yourName\AppData\Local\Programs\Python\Python36-32\Scripts`
  * you can click `COMTool.exe` or run command `pycom or COMTool` to run app


### Linux

* download and install
```
sudo apt install python3
sudo apt install python3-pip
sudo pip3 install comtool
```
or
```
sudo apt install python3
wget https://bootstrap.pypa.io/get-pip.py 
sudo python3 get-pip.py
sudo pip3 install comtool
```
be sure python bin path already in the `$PATH` env(add `export PATH=$PATH:~/.local/bin` to ~/.bashrc).
then enjoy by type `COMTool`


 Or you can download source code, then install from source code
  * download sourcecode
```
python setup.py bdist_wheel
sudo pip3 install dist/COMTool-*.*.*-py3-none-any.whl
```


### macOS

```
brew install python3 python3-pip
pip install COMTool
```

## Development

1. Install python3.6 and pip
Linux:
```
sudo apt install python3 python3-pip
```

Windows: 
  [dowload python3](https://www.python.org/downloads/)

2. install pyserial and PyQt5
```
pip install pyserail pyqt5
```

3. clone project
```
git clone https://github.com/Neutree/COMTool.git
```

4. code, resolve bugs or add new reatures


5. pull request


