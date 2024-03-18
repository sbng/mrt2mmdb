#!/usr/bin/env python
"""
This module returns the file creation time for injestion by prometheus
"""
import os
from args import get_args


def file_create(fname):
    """return the file creation time in epoch time"""
    return os.path.getmtime(fname)


def all_files_create(files):
    """return the files creation time"""
    return [file_create(f) for f in files]


def main():
    """
    main function define the workflow to make a ASN dict->Load the
    corresponding mrt->convert the mrt into mmda
    """
    parser = get_args(
        target=True,
        mrt=True,
        mmdb=True,
    )
    args = parser.parse_args()
    print(args)
    return 0


if __name__ == "__main__":
    main()
