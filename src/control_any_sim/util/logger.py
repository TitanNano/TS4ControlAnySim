import os


def get_logfile_name():
    log_dir = os.path.abspath(__file__)
    log_dir = os.path.dirname(dir)
    log_dir = os.path.dirname(dir)
    log_dir = os.path.dirname(dir)

    return log_dir + '/debug.log'


class Logger:
    PRODUCTION = False

    handler = open(get_logfile_name(), "a")

    @classmethod
    def log(cls, message):
        if cls.PRODUCTION:
            return

        cls.handler.write(message + '\n')
        cls.handler.flush()

    @classmethod
    def error(cls, message):
        cls.handler.write('ERROR: ' + message + '\n')
        cls.handler.flush()
