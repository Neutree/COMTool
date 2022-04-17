import os

try:
    from i18n import locales, main
    from parameters import log
except Exception:
    from COMTool.i18n import locales, main
    from COMTool.parameters import log


import gettext

currDir = os.path.abspath(os.path.dirname(__file__))
localesDir = os.path.join(currDir, 'locales')
mo_path = os.path.join(localesDir, "en", "LC_MESSAGES", "messages.mo")
# detect if no translate binary files, generate
if not os.path.exists(mo_path):
    main("finish", path = currDir)

try:
    lang = gettext.translation('messages', localedir=localesDir, languages=locales)
    lang.install()
    _ = lang.gettext
except Exception as e:
    msg = "can not find plugin i18n files in {}".format(currDir)
    log.e(msg)
    raise Exception(msg)

