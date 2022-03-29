'''
    logger wrapper based oh logging

    @author neucrack
    @license MIT copyright 2020-2021 neucrack CZD666666@gmail.com
'''



import logging
import coloredlogs
import sys

class Logger:
    '''
        use logging module to record log to console or file
    '''
    def __init__(self, level="d", stdout = True, file_path=None,
                fmt = '%(asctime)s - [%(levelname)s] - %(message)s',
                logger_name = "logger"):
        self.log = logging.getLogger(logger_name)
        formatter=logging.Formatter(fmt=fmt)
        level_ = logging.INFO
        if level == "i":
            level_ = logging.INFO
        elif level == "w":
            level_ = logging.WARNING
        elif level == "e":
            level_ = logging.ERROR
        # terminal output
        coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'}, 'hostname': {'color': 'magenta'},
                                    'levelname': {'color': 'green', 'bold': True}, 'request_id': {'color': 'yellow'},
                                    'name': {'color': 'blue'}, 'programname': {'color': 'cyan'},
                                    'processName': {'color': 'magenta'},
                                    'threadName': {'color': 'magenta'},
                                    'filename': {'color': 'white'},
                                    'lineno': {'color': 'white'}}
        level_styles = {
            'debug': {
                'color': "white"
            },
            'info': {
                'color': "green"
            },
            'warn': {
                'color': "yellow"
            },
            'error': {
                'color': "red"
            }
        }

        coloredlogs.install(level=level_, fmt=fmt, level_styles=level_styles)
        self.log.setLevel(level_)
        # sh = logging.StreamHandler()
        # sh.setFormatter(formatter)
        # sh.setLevel(level_)
        # self.log.addHandler(sh)
        # file output
        if not stdout:
            self.log.propagate = False
        if file_path:
            fh = logging.FileHandler(file_path, mode="a", encoding="utf-8")
            fh.setFormatter(formatter)
            fh.setLevel(level_)
            self.log.addHandler(fh)

    def d(self, *args):
        out = ""
        for arg in args:
            out += " " + str(arg)
        self.log.debug(out)

    def i(self, *args):
        out = ""
        for arg in args:
            out += " " + str(arg)
        self.log.info(out)

    def w(self, *args):
        out = ""
        for arg in args:
            out += " " + str(arg)
        self.log.warning(out)

    def e(self, *args):
        out = ""
        for arg in args:
            out += " " + str(arg)
        self.log.error(out)

class Fake_Logger:
    '''
        use logging module to record log to console or file
    '''
    def __init__(self, level="d", file_path=None, fmt = '%(asctime)s - [%(levelname)s]: %(message)s'):
        pass

    def d(self, *args):
        print(args)

    def i(self, *args):
        print(args)

    def w(self, *args):
        print(args)

    def e(self, *args):
        print(args)


if __name__ == "__main__":
    import os
    log = Logger(file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.log"))
    log.d("debug", "hello")
    log.i("info:", 1)
    log.w("warning")
    log.e("error")



