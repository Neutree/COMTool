COMTool 插件文档
=======

在学会开发插件前， 需要了解如何将源码跑起来，看项目[README_ZH.md](../README_ZH.MD) 开发介绍


## 添加插件并集成到 COMTool 作为默认插件

* 去 `COMTool/plugins` 目录
* 创建一个插件文件，如 `myplugin.py`
* 写一个类，继承自 `.base.Plugin_Base`，并命名为 `Plugin`，例如
```python
from .base import Plugin_Base

class Plugin(Plugin_Base):
    pass
```
* 编辑您的插件类，实现继承自 `Plugin_Base` 的变量和函数，并使用函数 `_` 在您的代码中使用翻译，例如 `_("hello")`。
插件参见 [myplugin.py](../COMTool/plugins/myplugin.py)

* 在 [COMTool/plugins/__init__.py](../COMTool/plugins/__init__.py) 添加插件，以启用插件
```python
from . import myplugin
plugins = [..., myplugin.Plugin]
```

* OK，所有工作都完成！只需运行程序就可以看到我们的插件

```
python COMTool/Main.py
```


## 编写一个外部插件，可以通过 COMTool 在任何时候加载

* 创建一个项目目录和一个 `myplugin.py` 文件（任何名字都可以）
* 写一个插件像我们在 [section one](#Add-plugin-and-integrated-to-COMTool-as-default-plugin) 说的那样，示例文件参见 [myplugin.py](../COMTool/plugins/myplugin.py)，插件类的名字必须是 `Plugin`
* 启动 COMTool，点击插件列表并选择添加新插件

有几个点需要注意
* 加载插件时，插件的路径将被插入 `sys.path` 的开头，所以文件名的命名需要格外小心，建议所有文件命名为可能的 `comtool_plugin_xxx.py`
* Comtool 可执行文件使用了 `pyinstaller` 打包， 只会将使用到了包打包进去，所以如果你的插件包含一些特殊的包，解决方法如下：
  * 保持插件的纯净，不要包含特殊包
  * 或者将它们拷贝到可执行文件的根目录
  * 或者使用 COMTool 程序安装为 python 包（通过 pip 安装）


## 编写一个 python 包作为插件，可以被 COMTool 自动加载

创建一个 python 包， 比如: [COMTOOL/plugins/myplugin2](../COMTool/plugins/myplugin2)

* 包名必须是 `comtool_plugin_xxx`
* 构建包使用 `python setup.py sdist bdist_wheel`
* 你可以将包上传到 `pypi.org`，使用 `twine upload ./dist/*`
* 然后用户使用 `pip install comtool-plugin-xxx` 安装包，启动软件时 COMTool 将自动加载插件


## 插件 i18n (国际化/翻译)

如果你想要让你的插件支持国际化（i18n）：
* 正如 [COMTool/plugins/myplugin2](../COMTool/plugins/myplugin2) 那样，创建一个 `plugin_18n.py` 来定义 `_` 函数，并在你的插件中使用它，如 `_("Hello")`
* 用 `comtool-i18n -p <package path> prepare` 命令首先准备翻译，比如 `comtool-i18n -p COMTool/plugins/myplugin2/comtool_plugin_myplugin2 prepare` 将自动在你的代码中找到需要翻译的字符串，并生成 `messages.pot` 和 `po` 文件
* 手动翻译 `po` 文件
* 执行 `comtool-i18n -p <package name> finish` 命令生成 `mo` 文件
* `setup.py` 应该包含翻译二进制文件（`*.mo`）到`package data`，这样用户才可以使用这些翻译


## 添加连接插件

新的连接插件， 和普通插件类似， 有一个基类 `COMM`，在 [COMTool/conn/__init__.py](../COMTool/conn/__init__.py), 只需要：
* 在`COMTool/conn` 创建一个新文件, 如 `conn_serial.py`, `conn_ssh.py`, `conn_tcp_udp.py`, 并实现 `COMM` 类
* 将你的连接类添加到 [COMTool/conn/__init__.py](../COMTool/conn/__init__.py)
* 到此就可以使用了，执行 COMTool 就可以看到新的连接了
```
python COMTool/Main.py
```

