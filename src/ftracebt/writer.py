import argparse
from helper import Helpers
from ftrace import WriteBuffer


marker_writer_names = ['write_one_page', 'write_two_pages', 'write_three_pages', 'write_four_pages', 'fillup_buffer', 'fillup_plus_one_page', 'fillup_plus_two_page', 'fillup_plus_three_page', 'fillup_plus_four_page']


def parse_args():
    parser = argparse.ArgumentParser(description='Write to the ftrace ring buffer.')
    parser.add_argument('--write-name', choices=marker_writer_names,
                        help="The name of what will be written to the ftrace's buffer.", required=True)
    parser.add_argument("--config-file", default="test_buffer.ini", help="Configuration file.")
    parser.add_argument("--cpu", type=int,
            help="The CPU where to write the entries. This parameter has meaning just for a few 'write-name' values.")
    parser.add_argument("--entries-per-page", type=int, default=101,
            help="The number of entries to write per page. This could vary depending on the page size. For 4k page size the default value fills up one page. This parameter has meaning just for a few 'write-name' values.")
    parser.add_argument("--max-delay", type=int,
            help="The max amount of microseconds to wait between the writing of entries. The delay will be picked randomly from 0 to this value. This parameter has meaning just for a few 'write-name' values.")
    return parser.parse_args()


def write_with_marker(args):
    config = Helpers.get_config(args.config_file)
    writebuffer = WriteBuffer(config)

    if args.write_name == 'write_one_page':
        writebuffer.write_pages(1, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'write_two_pages':
        writebuffer.write_pages(2, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'write_three_pages':
        writebuffer.write_pages(3, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'write_four_pages':
        writebuffer.write_pages(4, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'fillup_buffer':
        nr_pages = config['nr_pages_to_fillup_buffer']
        writebuffer.write_pages(nr_pages, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'fillup_plus_one_page':
        nr_pages = config['nr_pages_to_fillup_buffer']
        writebuffer.write_pages(nr_pages + 1, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'fillup_plus_two_page':
        nr_pages = config['nr_pages_to_fillup_buffer']
        writebuffer.write_pages(nr_pages + 2, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'fillup_plus_three_page':
        nr_pages = config['nr_pages_to_fillup_buffer']
        writebuffer.write_pages(nr_pages + 3, args.cpu, args.entries_per_page, delay=args.max_delay)
    elif args.write_name == 'fillup_plus_four_page':
        nr_pages = config['nr_pages_to_fillup_buffer']
        writebuffer.write_pages(nr_pages + 4, args.cpu, args.entries_per_page, delay=args.max_delay)


def main():
    args = parse_args()
    if args.write_name in marker_writer_names:
        write_with_marker(args)
    else:
        #TODO Add error handling here.
        pass


if __name__ == "__main__":
    # execute only if run as a script
    main()
