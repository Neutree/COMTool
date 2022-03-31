import sys
import os
try:
    from main2 import main
    from parameters import log
except Exception:
    from COMTool.main2 import main
    from COMTool.parameters import log

def restart_program():
    '''
        restart program, not return
    '''
    python = sys.executable
    log.i("Restarting program, comand: {} {} {}".format(python, python, *sys.argv))
    os.execl(python, python, * sys.argv)

if __name__ == '__main__':
    while 1:
        ret = main()
        if not ret is None:
            break
        restart_program()
    print("-- program exit, code:", ret)
    sys.exit(ret)
