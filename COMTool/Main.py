import sys
import gc
import copy
# import importlib


if __name__ == '__main__':
    old_modules = copy.copy(sys.modules)
    try:
        from main2 import main
    except Exception:
        from COMTool.main2 import main
    while 1:
        ret = main()
        if not ret is None:
            break
        # TODO: unload all modules, and reload them
        #       to make translate of class member to take effect
    print("-- program exit, code:", ret)
    sys.exit(ret)
