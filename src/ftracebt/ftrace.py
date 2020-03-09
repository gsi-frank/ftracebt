import time
import random
from helper import Helpers


class ParsingBufferHeadError(Exception):
    pass


class CheckingMarkerPagesError(Exception):
    pass


class CheckingEntriesOrderError(Exception):
    pass


class CompareTraceFiles(Exception):
    pass


class BufferInternals:
    def __init__(self, config):
        self.config = config

    def get_nr_readable_pages(self, cpu):
        filename = self.config['nr_readable_pages_file']
        return Helpers.read_int_from_file(filename.format(cpu))

    def get_nr_entries_commit_page(self, cpu):
        filename = self.config['nr_entries_commit_page_file']
        return Helpers.read_int_from_file(filename.format(cpu))

    def get_commit_page_commit(self, cpu):
        filename = self.config['commit_page_commit_file']
        return Helpers.read_int_from_file(filename.format(cpu))

    def get_info(self, cpu):
        return {
            'nr_readable_pages': self.get_nr_readable_pages(cpu),
            'nr_entries_commit_page': self.get_nr_entries_commit_page(cpu),
            'commit_page_commit': self.get_commit_page_commit(cpu)
        }

    def print_info(self, cpu):
        info = self.get_info(cpu)
        print('CPU#: {:03}\tnr_readable_pages: {:13}'.format(
            cpu, info['nr_readable_pages']))
        print('CPU#: {:03}\tnr_entries_commit_page: {:8}'.format(
            cpu, info['nr_entries_commit_page']))
        print('CPU#: {:03}\tcommit_page_commit: {:12}'.format(
            cpu, info['commit_page_commit']))


class WriteBuffer:
    head_entry_beginning = 'CPU#-PAGE_ID#-ENTRY#              PAGE_ID:'
    def __init__(self, config):
        self.config = config

    @staticmethod
    def generate_entry(cpu, page_id, entry_nr):
        return '{:03}-{:08}-{:03}'.format(cpu, page_id, entry_nr)

    @staticmethod
    def generate_page_header_entry(page_id):
        return '{}{:08}'.format(WriteBuffer.head_entry_beginning, page_id)

    def write_string(self, s):
        filename = self.config['marker_file']
        return Helpers.append2file(filename, s)

    def write_entry(self, cpu, page_id, entry_nr):
        return self.write_string(WriteBuffer.generate_entry(cpu, page_id, entry_nr))

    def write_page(self, cpu, page_id, entries_per_page, delay=0):
        self.write_string(WriteBuffer.generate_page_header_entry(page_id))
        for entry_nr in range(1, entries_per_page):
            if delay:
                time.sleep(random.randint(0, delay) / 1000000)
            self.write_entry(cpu, page_id, entry_nr)

    def write_pages(self, nr_pages, cpu, entries_per_page, first_page_id=1, delay=0):
        for i in range(0, nr_pages):
            self.write_page(cpu, first_page_id + i, entries_per_page, delay)


class ReadBuffer:
    def __init__(self, config):
        self.config = config

    def complete_read_nc(self, trace_filename):
        return open(trace_filename, 'r').readlines()

    def is_empty(self):
        lines = self.complete_read_nc(self.config['trace'][0])
        return lines[0].startswith('# tracer: ') and len(lines) == 11

    def get_entries_noheader_nc(self, trace_filename, nr_entries=None):
        lines = self.complete_read_nc(trace_filename)
        entries_to_ignore = 0
        nr_lines = len(lines)
        while lines[entries_to_ignore].find(WriteBuffer.head_entry_beginning) == -1:
            entries_to_ignore += 1
            if entries_to_ignore == nr_lines:
                raise ParsingBufferHeadError("Error while trying to ignore the buffer header. No first entry pattern found.") 
        return lines[entries_to_ignore:nr_entries]


class FtraceManager:
    def __init__(self, config):
        self.config = config

    def set_tracer(self, tracer_name):
        Helpers.write2file(self.config['current_tracer'], tracer_name)

    def clear_buffer(self):
        Helpers.write2file(self.config['trace'][0], ' ')

    def set_tracing_on(self):
        Helpers.write2file(self.config['tracing_on'], '1')

    def set_tracing_off(self):
        Helpers.write2file(self.config['tracing_on'], '0')

    def set_events_on(self):
        Helpers.write2file(self.config['events'], '1')

    def set_events_off(self):
        Helpers.write2file(self.config['events'], '0')

    def activate_tracer(self, tracer_name, duration):
        if tracer_name in ['function', 'function_graph']:
            self.set_tracing_on()
            self.set_tracer(tracer_name)
            time.sleep(duration/1000)
            self.set_tracing_off()
        elif tracer_name == 'events':
            self.set_tracer('nop')
            self.set_tracing_on()
            self.set_events_on()
            time.sleep(duration/1000)
            self.set_events_off()
            self.set_tracing_off()


class Check:
    @staticmethod
    def marker_page(buffer_content, entries_per_page, cpu, page_id):
        if len(buffer_content) < entries_per_page:
            raise CheckingMarkerPagesError('Not enough entries. CPU: {} PAGE_ID: {} Entries expected: {} Entries in this page: {}'.format(cpu, page_id, entries_per_page, len(buffer_content)))
        if buffer_content[0].find(WriteBuffer.generate_page_header_entry(page_id)) == -1:
            raise CheckingMarkerPagesError('First line do not match. PAGE_ID: {} Line: {}'.format(page_id, buffer_content[0]))
        for entry_nr in range (1, entries_per_page):
            if buffer_content[entry_nr].find(WriteBuffer.generate_entry(cpu, page_id, entry_nr)) == -1:
                raise CheckingMarkerPagesError('Line do not match. CPU: {} PAGE_ID: {} ENTRY: {}. Line: {}'.format(cpu, page_id, entry_nr, buffer_content[entry_nr]))
        return (entries_per_page, page_id + 1)

    @staticmethod
    def exact_marker_pages(content_no_header, entries_per_page, cpu, nr_pages, first_page_id=1, extra_entries=0):
        begin = 0
        if extra_entries: raise NotImplementedError('Parameter "extra_entries" is not supported yet.')
        next_page_id = first_page_id
        for i in range(1, nr_pages + 1):
            entries, next_page_id = Check.marker_page(content_no_header[begin:], entries_per_page, cpu, next_page_id)
            begin += entries
        if content_no_header[begin:]:
            raise CheckingMarkerPagesError('There is extra entries. First extra entry: {}'.format(content_no_header[begin]))
        return True

    
    @staticmethod
    def _get_nr_pages_from(config, writer_name):
        nr_pages_to_fillup_buffer = config['nr_pages_to_fillup_buffer']
        writer_names_nr_pages = {'write_one_page': 1, 'write_two_pages': 2, 'write_three_pages': 3, 'write_four_pages': 4, 'fillup_buffer': nr_pages_to_fillup_buffer, 'fillup_plus_one_page': nr_pages_to_fillup_buffer + 1, 'fillup_plus_two_page': nr_pages_to_fillup_buffer + 2, 'fillup_plus_three_page': nr_pages_to_fillup_buffer + 3, 'fillup_plus_four_page': nr_pages_to_fillup_buffer + 4}
        return writer_names_nr_pages[writer_name]

    @staticmethod
    def get_nr_pages_and_first_page_id(config, pages_written):
        nr_pages_to_fillup_buffer = config['nr_pages_to_fillup_buffer']
        if pages_written > nr_pages_to_fillup_buffer:
                first_page_id = pages_written - nr_pages_to_fillup_buffer + 1
                nr_pages = nr_pages_to_fillup_buffer
        else:
            nr_pages = pages_written
            first_page_id = 1
        return (nr_pages, first_page_id)

    @staticmethod
    def per_cpu_content(config, writer_name, content_no_header, cpus_to_use, entries_per_page):
        for cpu in cpus_to_use:
            filtered_content = [x for x in content_no_header if x.find(' [{:03}] '.format(cpu)) != -1]
            pages_written = Check._get_nr_pages_from(config, writer_name)
            nr_pages, first_page_id = Check.get_nr_pages_and_first_page_id(config, pages_written)
            Check.exact_marker_pages(filtered_content, entries_per_page, cpu, nr_pages, first_page_id)

    @staticmethod
    def merged_buffers(content_no_header):
        prev_time = [-1,-1]
        prev_line = None
        for line in content_no_header:
            if line.find(' buffer started ####') != -1: continue
            try:
                current_time = list(int(x) for x in line.split()[3].strip(':').split('.'))
            except Exception as err:
                raise CheckingEntriesOrderError('Error while trying to get time stamp of line: {}'.format(line))
            if current_time < prev_time:
                raise CheckingEntriesOrderError('Entries out of order. Entry x: {}. Entry x+1: {}'.format(prev_line, line))
            prev_line = line
            prev_time = current_time

    @staticmethod
    def content_trace_files(trace_content, persistent_content):
        i2 = 0
        for i1, trace_line in enumerate(trace_content):
            try:
                if trace_line.find('# entries-in-buffer/entries-written: ') != -1 and i1 == 2:
                    i2 += 1
                    continue
                if trace_line.find(' buffer started ####') != -1: continue
                if trace_line != persistent_content[i2]:
                    raise CompareTraceFiles('Error while comparing trace and persistent content. A line doesn\'t match. Line index at trace content: {}. Line index at persistent content: {}. Line of trace content: "{}". Line of persistent content: "{}".'.format(i1, i2, trace_line, persistent_content[i2]))
                i2 += 1
            except IndexError:
                raise CompareTraceFiles('Error while comparing trace content and persistent content. Trace content is longer than persistent content. First extra line index: {}. Line content: "{}"'.format(i1, trace_line))
        if len(persistent_content) > i2:
            raise CompareTraceFiles('Error while comparing trace content and and persistent content. Persistent content is longer than trace content. First extra line index: {}. Line content: "{}"'.format(i2, persistent_content[i2]))

