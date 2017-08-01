from cx_Freeze import setup,Executable
from codecs import open
from os import path
from COMTool import parameters,helpAbout
import sys
import traceback
import msilib

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Dependencies are automatically detected, but it might need fine tuning.

#中文需要显式用gbk方式编码
product_name = parameters.appName.encode('gbk')
unproduct_name = (parameters.strUninstallApp).encode('gbk')
product_desc = (parameters.appName+" V"+str(helpAbout.versionMajor)+"."+str(helpAbout.versionMinor)).encode("gbk")

#uuid叫通用唯一识别码，后面再卸载快捷方式中要用到
product_code = msilib.gen_uuid()
#主程序手动命名
target_name= 'comtool.exe'


build_exe_options = {
    "include_files":["COMToolData","README.MD","LICENSE"],    
    #包含外围的ini、jpg文件，以及data目录下所有文件，以上所有的文件路径都是相对于cxsetup.py的路径。
    "packages": [],                #包含用到的包
    "includes": [], 
    "excludes": ["unittest"],                #提出wx里tkinter包
    "path": sys.path,                       #指定上述的寻找路径
    #  "icon": "COMToolData/assets/logo.ico"                        #指定ico文件
};

#快捷方式表，这里定义了三个快捷方式
shortcut_table = [
     
     #1、桌面快捷方式
    ("DesktopShortcut",           # Shortcut
     "DesktopFolder",             # Directory_ ，必须在Directory表中
     product_name,                # Name
     "TARGETDIR",                 # Component_，必须在Component表中
     "[TARGETDIR]"+target_name,   # Target
     None,                        # Arguments
     product_desc,                # Description
     None,                        # Hotkey
     None,                        # Icon
     None,                        # IconIndex
     None,                        # ShowCmd
     'TARGETDIR'                  # WkDir
     ),
    
    #2、开始菜单快捷方式
    ("StartupShortcut",           # Shortcut
     "MenuDir",                   # Directory_
     product_name,                # Name
     "TARGETDIR",                 # Component_
     "[TARGETDIR]"+target_name,   # Target
     None,                        # Arguments
     product_desc,                # Description
     None,                        # Hotkey
     None,                        # Icon
     None,                        # IconIndex
     None,                        # ShowCmd
     'TARGETDIR'                  # WkDir
     ),
    
    #3、程序卸载快捷方式
    ("UniShortcut",              # Shortcut
     "MenuDir",                  # Directory_
     unproduct_name,             # Name
     "TARGETDIR",                # Component_
     "[System64Folder]msiexec.exe",  # Target
     r"/x"+product_code,         # Arguments
     product_desc,               # Description
     None,                       # Hotkey
     None,                       # Icon
     None,                       # IconIndex
     None,                       # ShowCmd
     'TARGETDIR'                 # WkDir
     )      
    ]


#手动建设的目录，在这里定义。
'''
自定义目录说明：
==============
1、3个字段分别为 Directory,Directory_Parent,DefaultDir
2、字段1指目录名，可以随意命名，并在后面直接使用
3、字段2是指字段1的上级目录，上级目录本身也是需要预先定义，除了某些系统自动定义的目录，譬如桌面快捷方式中使用DesktopFolder
参考网址 https://msdn.microsoft.com/en-us/library/aa372452(v=vs.85).aspx
'''
directories = [
     ( "ProgramMenuFolder","TARGETDIR","." ),
     ( "MenuDir", "ProgramMenuFolder", product_name)
     ]

# Now create the table dictionary
# 也可把directories放到data里。
'''
快捷方式说明：
============
1、windows的msi安装包文件，本身都带一个install database，包含很多表（用一个Orca软件可以看到）。
2、下面的 Directory、Shortcut都是msi数据库中的表，所以冒号前面的名字是固定的(貌似大小写是区分的)。
3、data节点其实是扩展很多自定义的东西，譬如前面的directories的配置，其实cxfreeze中代码的内容之一，就是把相关配置数据写入到msi数据库的对应表中
参考网址：https://msdn.microsoft.com/en-us/library/aa367441(v=vs.85).aspx
'''
msi_data = {#"Directory":directories ,
            "Shortcut": shortcut_table 
          }

# Change some default MSI options and specify the use of the above defined tables
#注意product_code是我扩展的，现有的官网cx_freeze不支持该参数，为此简单修改了cx_freeze包的代码，后面贴上修改的代码。
bdist_msi_options = { 'data': msi_data,
                      'upgrade_code': '{9f21e33d-48f7-cf34-33e9-efcfd80eed10}',
                      'add_to_path': False,
                      'directories': directories,
                      'product_code': product_code,
                      'initial_target_dir': r'[ProgramFilesFolder]\%s' % (product_name)}
                      

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None;
if sys.platform == "win32":
     base = "Win32GUI"

#简易方式定义快捷方式，放到Executeable()里。
#shortcutName = "AppName",
#shortcutDir = "ProgramMenuFolder" 
setup(  name = parameters.appName,
        author=parameters.author,
        version = str(helpAbout.versionMajor)+"."+str(helpAbout.versionMinor)+"."+str(helpAbout.versionDev),
        description = product_desc.decode('gbk'),
        options = {"build_exe": build_exe_options,
                   "bdist_msi": bdist_msi_options},
        executables = [Executable("COMTool/Main.py",
                                  targetName= target_name,
                                  base=base,
                                  icon= r"COMToolData/assets/logo.ico")
                       ]) 

