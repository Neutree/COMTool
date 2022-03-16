开发日记( development notes)
======

分功能将开发时的思路和方法记录在这里，如果有开发者想参与开发或者基于这个项目修改，可以先看本文档

如果你贡献了代码，也欢迎你把你贡献的功能模块的思路记录在这里


## 协议插件中的快捷键发送

给 key mode 按钮定义了一个 eventFilter, 拦截所有按钮按下和抬起按键的操作
> 代码为`protocol.py`中的`ModeButtonEventFilter`类



## 国际化支持

程序执行时先从文件加载配置，设置语言，再初始化其它内容，目的是保证在代码任何地方都能通过 i18n 模块正确地获取到翻译


## TCP UDP 连接支持

使用模块化（/插件化）开发， 在[conn/conn_tcp_udp.py](../conn/conn_tcp_udp.py) 中定义了这个类，可以直接执行 [conn/test_tcp_udp.py](../conn/test_tcp_udp.py) 测试模块

## 终端

使用了 `paramiko` 作为 `ssh`连接的后端，解析接收到的数据（`VT100`格式）使用了`pyte`， 根据`pyte`获取到的输出使用一个`pixmap`进行绘制，然后将`pixmap`刷到`QWidget`上实现显示

这里需要注意的是关于刷新和绘制，为了同步数据以及防止界面卡死：
接收和解析以及绘制`pixmap`都在`onReceived`函数中进行，这个函数在接收线程中执行，没在`UI`线程中执行，所以在绘制`pixmap`过程中不要直接调用任何直接操作界面的方法，所有操作都对这个`pixmap`进行操作，等绘制完成后再用`update()`函数通知`UI`线程，在`paintEvent`函数中将`pixmap`画到`widget`上



