import os

try:
    from i18n import locales
    from parameters import log
except Exception:
    from COMTool.i18n import locales
    from COMTool.parameters import log


import gettext

currDir = os.path.abspath(os.path.dirname(__file__))
localesDir = os.path.join(currDir, 'locales')

try:
    lang = gettext.translation('messages', localedir=localesDir, languages=locales)
    lang.install()
    _ = lang.gettext
except Exception as e:
    msg = "can not find plugin i18n files in {}".format(currDir)
    log.e(msg)
    raise Exception(msg)

