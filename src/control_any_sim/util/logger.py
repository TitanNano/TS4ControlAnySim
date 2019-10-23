from os import path


def get_logfile_name():
    dir_name = path.dirname(path.abspath(__file__))
    log_dir = path.normpath(path.join(dir_name, '../../../'))

    return path.join(log_dir, 'debug.log')


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
