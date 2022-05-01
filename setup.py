from setuptools import setup,find_packages
from codecs import open
from os import path
import os
from COMTool import version
import platform

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.MD'), encoding='utf-8') as f:
    long_description = f.read()

systemPlatform = platform.platform()
    
if "Linux" in systemPlatform and "arm" in systemPlatform :
    print("platform is arm linux: will install lib first")
    ret = os.system("sudo apt install python3 python3-pip python3-pyqt5")
    if ret != 0:
        raise Exception("install python3 pyqt5 failed")
    ret = os.system("sudo pip3 install --upgrade pyserial requests Babel qtawesome paramiko pyte pyperclip coloredlogs pyqtgraph")
    if ret != 0:
        raise Exception("install packages failed")
    installRequires = []
else:
    installRequires = ['pyqt5>=5',
                      'pyserial>=3.4',
                      'requests',
                      'Babel',
                      'qtawesome>=1.1.1',
                      'paramiko',
                      'pyte',
                      'pyperclip',
                      'coloredlogs',
                      'pyqtgraph'
                      ]

setup(
    name='COMTool',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version.__version__,

    # Author details
    author='Neucrack',
    author_email='czd666666@gmail.com',

    description='Cross platform serial debug assistant with GUI',
    long_description=long_description,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    url='https://github.com/Neutree/COMTool',



    # Choose your license
    license='LGPL-3.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Debuggers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],

    # What does your project relate to?
    keywords='Serial Debug Tool Assistant ',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=installRequires,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        # 'dev': ['check-manifest'],
        # 'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
          'COMTool': ['assets/*', "assets/qss/*", "locales/*/*/*.?o", "protocols/*"],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[
	        ("",["LICENSE","README.MD"])
        ],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'comtool-i18n=COMTool.i18n:cli_main',
        ],
        'gui_scripts': [
            'comtool=COMTool.Main:main',
        ],
    },
)

