#!/usr/bin/env python
"""
This module returns the file creation time for injestion by prometheus
"""
import os
import time
import sys


def file_create(fname, logger):
    """return the file create on time in epoch time. If file is missing, return a value of zero"""
    if os.path.isfile(fname):
        etime = os.path.getmtime(fname)
        logger.debug(f"[File]: {fname} -> {time.ctime(etime)} ({etime:.0f})")
    else:
        etime = 0
        logger.debug(f"[File]: {fname} -> file does not exist")
    return etime


def all_files_create(files, logger):
    """return the files creation time"""
    return [file_create(f, logger) for f in files]


def arguments_filename(parser, logger):
    """Sanitize the filename obtain from the arguments,exit and print
    help menu if the file does not exist"""
    args = parser.parse_args()
    if not os.path.isfile(args.mrt):
        logger.warning("\nerror: unable to locate mrt file\n")
        file_error(parser)
    if not os.path.isfile(args.mmdb) and not args.custom_lookup_only:
        if os.path.isfile(args.lookup_file):
            args.mmdb = ""
            logger.debug(
                f"set mmdb filename to empty string as mmdb file is not needed\
                  {args.lookup_file} is the only lookup file"
            )
        else:
            logger.warning("\nerror: unable to locate mmdb file\n")
            file_error(parser)
    if not os.path.isfile(args.lookup_file) and args.lookup_file != "":
        logger.warning("\nerror: unable to locate lookup file (csv,tsv)\n")
        file_error(parser)
    if args.custom_lookup_only:
        args.mmdb = ""
    return args


def file_error(parser):
    """exit routine when error is reported. Please help menu"""
    parser.print_help(sys.stderr)
    sys.exit(1)


def main():
    """
    main function define the workflow to make a ASN dict->Load the
    corresponding mrt->convert the mrt into mmda
    """
    return 0


if __name__ == "__main__":
    main()
