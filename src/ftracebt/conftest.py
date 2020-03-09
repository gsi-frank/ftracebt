import pytest
import pathlib
from helper import ArgumentError
from helper import Helpers
from ftrace import FtraceManager
from ftrace import ReadBuffer
from ftrace import WriteBuffer
from ftrace import Check


def pytest_addoption(parser):
    parser.addoption("--config-file",
                     default="test_buffer.ini",
                     help="Configuration file.")
    parser.addoption("--default-cpu",
                     type=int,
                     default=0,
                     help="CPU were to run the test when we are testing just on one CPU.")
    parser.addoption("--max-writes-delay",
                     type=int,
                     default=0,
                     help="Max amount of microsecods to wait between the writting of entries in a CPU buffer.")
    parser.addoption("--cpus-to-use",
                     default='0',
                     help="List of cpus numbers that the test will use to write in their ftrace's buffer. e.g. --cpu 0,1,3,5")

@pytest.fixture(scope='session')
def cwd(request):
    return pathlib.Path(__file__).parent

@pytest.fixture(scope='session')
def config_filename(request):
    return request.config.getoption("--config-file")


@pytest.fixture(scope='session')
def default_cpu(request):
    return request.config.getoption("--default-cpu")


@pytest.fixture(scope='session')
def max_writes_delay(request):
    return request.config.getoption("--max-writes-delay")


@pytest.fixture(scope='session')
def cpus_to_use(request):
    try:
        return [int(cpu.strip()) for cpu in request.config.getoption("--cpus-to-use").split(',')]
    except Exception as err:
        raise ArgumentError('Error in argument "--cpus-to-uses". Details: {}'.format(str(err)))


@pytest.fixture(scope='session')
def config(config_filename):
    return Helpers.get_config(config_filename)


@pytest.fixture(scope='session')
def writebuffer(config):
    return WriteBuffer(config)


@pytest.fixture(scope='session')
def buffercheck(config):
    return Check


@pytest.fixture(scope='session')
def readbuffer(config):
    return ReadBuffer(config)


@pytest.fixture(scope='session')
def ftrace_manager(config):
    return FtraceManager(config)


@pytest.fixture(scope='session')
def marker_entries_per_page(config):
    return int(config['marker_entries_per_page'])
