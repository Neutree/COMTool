import os
import gettext
import babel
from collections import OrderedDict

locales=["en", "zh_CN", "zh_TW", "ja"]


root_dir = os.path.abspath(os.path.dirname(__file__))
locale = "en"

tr = lambda x:x

def _(text):
    return tr(text)

def set_locale(locale_in):
    global locale, tr, root_dir
    print("-- set locale to", locale_in)
    locale = locale_in
    locales_path = os.path.join(root_dir, 'locales')
    if not os.path.exists(locales_path): # for pyinstaller pack
        locales_path = os.path.join(os.path.dirname(root_dir), 'locales')
    # check translate binary file
    mo_path = os.path.join(locales_path, "en", "LC_MESSAGES", "messages.mo")
    if not os.path.exists(mo_path):
        main("finish")
    lang = gettext.translation('messages', localedir=locales_path, languages=[locale])
    tr = lang.gettext

def get_languages():
    languages = OrderedDict()
    for locale in locales:
        obj = babel.Locale.parse(locale)
        languages[locale] = obj.language_name + (" " + obj.script_name if obj.script_name else "")
    return languages

def extract(src_path, config_file_path, out_path):
    from distutils.errors import DistutilsOptionError
    from babel.messages.frontend import extract_messages
    cmdinst = extract_messages()
    cmdinst.initialize_options()
    cmdinst.mapping_file = config_file_path
    cmdinst.output_file = out_path
    cmdinst.input_paths = src_path
    try:
        cmdinst.ensure_finalized()
        cmdinst.run()
    except DistutilsOptionError as err:
        raise err

def init(template_path, out_dir, locale, domain="messages"):
    from distutils.errors import DistutilsOptionError
    from babel.messages.frontend import init_catalog
    cmdinst = init_catalog()
    cmdinst.initialize_options()
    cmdinst.input_file = template_path
    cmdinst.output_dir = out_dir
    cmdinst.locale = locale
    cmdinst.domain = domain
    try:
        cmdinst.ensure_finalized()
        cmdinst.run()
    except DistutilsOptionError as err:
        raise err

def update(template_path, out_dir, locale, domain="messages"):
    from distutils.errors import DistutilsOptionError
    from babel.messages.frontend import update_catalog
    cmdinst = update_catalog()
    cmdinst.initialize_options()
    cmdinst.input_file = template_path
    cmdinst.output_dir = out_dir
    cmdinst.locale = locale
    cmdinst.domain = domain
    try:
        cmdinst.ensure_finalized()
        cmdinst.run()
    except DistutilsOptionError as err:
        raise err

def compile(translate_dir, locale, domain="messages"):
    from distutils.errors import DistutilsOptionError
    from babel.messages.frontend import compile_catalog
    cmdinst = compile_catalog()
    cmdinst.initialize_options()
    cmdinst.directory = translate_dir
    cmdinst.locale = locale
    cmdinst.domain = domain
    try:
        cmdinst.ensure_finalized()
        cmdinst.run()
    except DistutilsOptionError as err:
        raise err



def main(cmd, path=None):
    global root_dir
    babel_cfg_path = os.path.join(root_dir, "babel.cfg")
    if path:
        if os.path.exists(path):
            root_dir = os.path.abspath(path)
            if os.path.exists(os.path.join(root_dir, "babel.cfg")):
                babel_cfg_path = os.path.join(root_dir, "babel.cfg")
        else:
            print("path {} not exists".format(path))
            return

    cwd = os.getcwd()
    os.chdir(root_dir)
    if cmd == "prepare":
        print("== translate locales: {} ==".format(locales))
        print("-- extract keys from files")
        if not os.path.exists("locales"):
            os.makedirs("locales")
        # os.system("pybabel extract -F babel.cfg -o locales/messages.pot ./")
        extract("./", babel_cfg_path, "locales/messages.pot")
        for locale in locales:
            print("-- generate {} po files from pot files".format(locale))
            if os.path.exists('locales/{}/LC_MESSAGES/messages.po'.format(locale)):
                print("-- file already exits, only update")
                # "pybabel update -i locales/messages.pot -d locales -l {}".format(locale)
                update("locales/messages.pot", "locales", locale)
            else:
                print("-- file not exits, now create")
                # "pybabel init -i locales/messages.pot -d locales -l {}".format(locale)
                init("locales/messages.pot", "locales", locale)
    elif cmd == "finish":
        print("== translate locales: {} ==".format(locales))
        for locale in locales:
            print("-- generate {} mo file from po files".format(locale))
            # "pybabel compile -d locales -l {}".format(locale)
            compile("locales", locale)
    os.chdir(cwd)


def cli_main():
    import argparse
    parser = argparse.ArgumentParser("tranlate tool")
    parser.add_argument("-p", "--path", default="", help="path to the root of plugin")
    parser.add_argument("cmd", type=str, choices=["prepare", "finish"])
    args = parser.parse_args()
    main(args.cmd, args.path)

if __name__ == "__main__":
    cli_main()
