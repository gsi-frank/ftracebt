import pytest
from subprocess import Popen
from ftrace import CheckingMarkerPagesError
from writer import marker_writer_names


class WriterProcessError(Exception):
    pass


@pytest.fixture
def reset_rb(ftrace_manager, readbuffer):
    def _reset_rb():
        ftrace_manager.set_tracer('nop')
        ftrace_manager.clear_buffer()
        ftrace_manager.set_tracing_on()
        if not readbuffer.is_empty():
            pytest.fail("We couldn't clear the buffer.")
    _reset_rb()
    return _reset_rb


@pytest.fixture
def check_writing_n_pages(config, max_writes_delay, writebuffer, readbuffer, buffercheck):
    def _read_and_check_n_pages(config, entries_per_page, cpu, pages_written):
        nr_pages, first_page_id = buffercheck.get_nr_pages_and_first_page_id(config, pages_written)
        for trace_filename in config['trace']:
            content_no_header = readbuffer.get_entries_noheader_nc(trace_filename)
            try:
                buffercheck.exact_marker_pages(content_no_header, entries_per_page, cpu, nr_pages, first_page_id)
            except CheckingMarkerPagesError as err:
                pytest.fail(str(err))

    def _check_writing_n_pages(nr_pages, cpu, entries_per_page):
        writebuffer.write_pages(nr_pages, cpu, entries_per_page, delay=max_writes_delay)
        _read_and_check_n_pages(config, entries_per_page, cpu, nr_pages)
        return True

    return _check_writing_n_pages


@pytest.fixture
def check_multiple_cpus(config, readbuffer, buffercheck, cpus_to_use, marker_entries_per_page):
    def _check_multiple_cpus(writer_name):
        for trace_filename in config['trace']:
            try:
                content_no_header = readbuffer.get_entries_noheader_nc(trace_filename)
                buffercheck.per_cpu_content(config, writer_name, content_no_header, cpus_to_use, marker_entries_per_page)
                buffercheck.merged_buffers(content_no_header)
            except Exception as err:
                pytest.fail('Error while testing with marker and multiple cpus. Writer name: "{}". Trace filename: "{}". Details: {}'.format(writer_name, trace_filename, str(err)))

    return _check_multiple_cpus


class TestWithMarker:
    @staticmethod
    def write_processes(config, write_name, cpus_to_use, max_writes_delay, cwd):
        process = []
        for cpu in cpus_to_use:
            write_cmd = config['writer_command'].format(cpu, write_name, cpu, max_writes_delay)
            p = Popen(write_cmd.split(), cwd=cwd)
            process.append(p)
        for p in process:
            if p.wait():
                raise WriterProcessError('Error while trying to execute the command: {}'.format(' '.join(p.args)))

    @pytest.mark.usefixtures('reset_rb')
    def test_write_one_page(self, check_writing_n_pages, default_cpu, marker_entries_per_page):
        assert check_writing_n_pages(1, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_write_two_page(self, check_writing_n_pages, default_cpu, marker_entries_per_page):
        assert check_writing_n_pages(2, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_write_three_page(self, check_writing_n_pages, default_cpu, marker_entries_per_page):
        assert check_writing_n_pages(3, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_write_four_page(self, check_writing_n_pages, default_cpu, marker_entries_per_page):
        assert check_writing_n_pages(4, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_fillup_buffer(self, config, check_writing_n_pages, default_cpu, marker_entries_per_page):
        nr_pages = config['nr_pages_to_fillup_buffer']
        assert check_writing_n_pages(nr_pages, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_fillup_plus_one_page(self, config, check_writing_n_pages, default_cpu, marker_entries_per_page):
        nr_pages = config['nr_pages_to_fillup_buffer']
        assert check_writing_n_pages(nr_pages + 1, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_fillup_plus_two_page(self, config, check_writing_n_pages, default_cpu, marker_entries_per_page):
        nr_pages = config['nr_pages_to_fillup_buffer']
        assert check_writing_n_pages(nr_pages + 2, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_fillup_plus_three_page(self, config, check_writing_n_pages, default_cpu, marker_entries_per_page):
        nr_pages = config['nr_pages_to_fillup_buffer']
        assert check_writing_n_pages(nr_pages + 3, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_fillup_plus_four_page(self, config, check_writing_n_pages, default_cpu, marker_entries_per_page):
        nr_pages = config['nr_pages_to_fillup_buffer']
        assert check_writing_n_pages(nr_pages + 4, default_cpu, marker_entries_per_page)

    @pytest.mark.usefixtures('reset_rb')
    def test_marker_multiple_cpus(self, check_multiple_cpus, config, cpus_to_use, max_writes_delay, cwd, reset_rb):
        for writer_name in marker_writer_names:
            print('\nExecuting test on CPUS: {}. Test name: {}. '.format(str(cpus_to_use), writer_name), end='')
            TestWithMarker.write_processes(config, writer_name, cpus_to_use, max_writes_delay, cwd)
            check_multiple_cpus(writer_name)
            print('PASSED', end='')
            reset_rb()
        print('')
        assert 1

    @pytest.mark.usefixtures('reset_rb')
    def test_with_the_tracers(self, config, ftrace_manager, reset_rb, buffercheck, readbuffer):
        if not ('/sys/kernel/debug/tracing/persistent' in config['trace'] and len(config['trace']) > 1):
            print('\nIgnoring "test_with_the_tracers" test because we don\'t have two files (normally "trace" and "persistent") to compare.')
            return
        for tracer_name in config['test_with_tracers']:
            for t in config['tracers_tests_times']:
                try:
                    print('\nExecuting tracer test. Tracer: "{}". Tracer was on: {} milliseconds. '.format(tracer_name, t), end='')
                    ftrace_manager.activate_tracer(tracer_name, t)
                    content1 = readbuffer.complete_read_nc(config['trace'][0])
                    content2 = readbuffer.complete_read_nc(config['trace'][1])
                    buffercheck.content_trace_files(content1, content2)
                    print('PASSED ', end='')
                    reset_rb()
                except Exception as err:
                    pytest.fail('\nExecuting tracer test. Tracer: "{}". Tracer was on: {} millisecondsi. Details: {}'.format(tracer_name, t, str(err)))

