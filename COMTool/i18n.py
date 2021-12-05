import gettext
import os
import babel
from collections import OrderedDict

locales=["en", "zh_CN", "zh_TW", "ja"]


root_dir = os.path.abspath(os.path.dirname(__file__))
locale = "en"

tr = lambda x:x

def _(text):
    return tr(text)

def set_locale(locale_in):
    global locale, tr
    locale = locale_in
    lang = gettext.translation('messages', localedir=os.path.join(root_dir, 'locales'), languages=[locale])
    tr = lang.gettext

def get_languages():
    languages = OrderedDict()
    for locale in locales:
        obj = babel.Locale.parse(locale)
        languages[locale] = obj.language_name + (" " + obj.script_name if obj.script_name else "")
    return languages

def main(cmd):
    cwd = os.getcwd()
    os.chdir(root_dir)
    if cmd == "prepare":
        print(f"== translate locales: {locales} ==")
        print("-- extract keys from files")
        if not os.path.exists("locales"):
            os.makedirs("locales")
        os.system("pybabel extract -F babel.cfg -o locales/messages.pot ./")
        for locale in locales:
            print(f"-- generate {locale} po files from pot files")
            if os.path.exists(f'locales/{locale}/LC_MESSAGES/messages.po'):
                print("-- file already exits, only update")
                os.system(f"pybabel update -i locales/messages.pot -d locales -l {locale}")
            else:
                print("-- file not exits, now create")
                os.system(f"pybabel init -i locales/messages.pot -d locales -l {locale}")
    elif cmd == "finish":
        print(f"== translate locales: {locales} ==")
        for locale in locales:
            print(f"-- generate {locale} mo file from po files")
            os.system(f"pybabel compile -d locales -l {locale}")
    os.chdir(cwd)



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("tranlate tool")
    parser.add_argument("cmd", type=str, choices=["prepare", "finish"])
    args = parser.parse_args()
    main(args.cmd)
