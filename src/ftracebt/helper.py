import configparser
import os


class ArgumentError(Exception):
    pass


class IntFromFileError(Exception):
    def __init__(self, filename, nested_err):
        super().__init__(
            'Error reading Integer from file: "{}"'.format(filename))
        self.nested_err = nested_err


class ConfigError(Exception):
    def __init__(self, filename):
        super().__init__(
            'Error reading configuration file: "{}"'.format(filename))

class FileWriteError(Exception):
    def __init__(self, filename, mode, text, nested_err):
        super().__init__(
                'Error writing file. Filename: "{}". Mode: "{}". String to write: "{}"'.format(filename, mode, text))
        self.nested_err = nested_err


class Helpers:
    @staticmethod
    def get_config(filename):
        config = configparser.ConfigParser()
        if not config.read(filename):
            raise ConfigError(filename)
        config = dict(config['GLOBAL'])

        config['nr_pages_to_fillup_buffer'] = int(config['nr_pages_to_fillup_buffer'])
        config['trace'] = [x.strip() for x in config['trace'].split(',') if x]
        config['test_with_tracers'] = [x.strip() for x in config['test_with_tracers'].split(',') if x]
        config['tracers_tests_times'] = [int(x.strip()) for x in config['tracers_tests_times'].split(',') if x]

        return config

    @staticmethod
    def read_int_from_file(filename):
        try:
            with open(filename) as f:
                i = int(open(filename, 'r').readline())
            return i
        except Exception as err:
            raise IntFromFileError(filename, err)

    @staticmethod
    def _filewrite(filename, mode, text):
        try:
            with open(filename, mode) as f:
                r = f.write(text)
                f.flush()
                return r
        except Exception as err:
            raise FileWriteError(filename, mode, text, err)

    @staticmethod
    def write2file(filename, text):
        return Helpers._filewrite(filename, 'w', text)

    @staticmethod
    def append2file(filename, text):
        return Helpers._filewrite(filename, 'a', text)
