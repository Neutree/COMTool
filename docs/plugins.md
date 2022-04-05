COMTool plugins doc
=======


Before you start developing plugins, you need to know how to run the source code. See the [README.md](../README.MD) for the development introduction.


## Add plugin and integrated to COMTool as default plugin

* Go to `COMTool/plugins` dir
* Create a plugin file like `myplugin.py`
* Write a class in `myplugin.py`, and inherit from `.base.Plugin_Base`, and name must be `Plugin` e.g.
```python
from .base import Plugin_Base

class Plugin(Plugin_Base):
    pass
```
* Edit your plugin class, implement variables and functions inherit from `Plugin_Base`, and you can use translate in your code by function `_`, e.g. `_("hello")`.
Example plugin see [myplugin.py](../COMTool/plugins/myplugin.py)

* Add plugin in [COMTool/plugins/__init__.py](../COMTool/plugins/__init__.py) to enable plugin
```python
from . import myplugin
plugins = [..., myplugin.Plugin]
```

* OK, all works done! Just run program to see our plugin

```
python COMTool/Main.py
```

## Write an external plugin, can load by COMTool at any time

* Create a project dir and a `myplugin.py` file (any name is ok)
* Wite a plugin the as we said in [section one](#Add-plugin-and-integrated-to-COMTool-as-default-plugin), emample file see [myplugin.py](../COMTool/plugins/myplugin.py), and the plugin class' name must be `Plugin`
* Bootup COMTool, click plugins list and select add new plugin

And there's some points should be pay attention:
* When load plugin, the plugin's path will be insert to the start of `sys.path`, so you should name your files carefully, it's recommended to name all files to be likely `comtool_plugin_xxx.py`
* Comtool binary executable packed with `pyinstaller`, only packed some package comtool used, so if your plugin contain some special package, there's some resolution:
  * Just keep your plugin clean, no special package import
  * Or copy them to dir root dir of binary executable file too
  * Or use comtool program install as python package(installed by pip)


## Write an external plugin as a python package, can auto load by COMTool

Create a python package, example: [COMTool/plugins/myplugin2](../COMTool/plugins/myplugin2) 

* Package name must be `comtool_plugin_xxx`
* Build package with `python setup.py sdist bdist_wheel`
* You can upload your package to `pypi.org`, by `twine upload ./dist/*`
* Then user can install your package by `pip install comtool-plugin-xxx`, then comtool will automatically load plugin

## I18n of plugin

If you want to let your plugin support i18n(internationalization):
* Just like [COMTool/plugins/myplugin2](../COMTool/plugins/myplugin2) did, create a `plugin_18n.py` to define `_` function, and use it in your plugin like `_("Hello")`
* Use `comtool-i18n -p <package path> prepare` first, e.g. `comtool-i18n -p COMTool/plugins/myplugin2/comtool_plugin_myplugin2 prepare` to find strings need to translate in your code automatically, this will generate `messages.pot` and `po` files in `locales` directory
* Translate `po` files manually
* Run `comtool-i18n -p <package name> finish` to generate `mo` files in `locales` directory
* `setup.py` should include translate binary files (`*.mo`) to package data, so user can use these translation


## Add connection plugin

Connection plugin just the same as the plugins, have an base class `COMM` in [COMTool/conn/__init__.py](../COMTool/conn/__init__.py), just:
* Create a new file in `COMTool/conn` directory like `conn_serial.py`, `conn_ssh.py`, `conn_tcp_udp.py`, and implement the methods of `COMM` class'.
* Add your connection class to [COMTool/conn/__init__.py](../COMTool/conn/__init__.py)

* That's all, run COMTool

```
python COMTool/Main.py
```


