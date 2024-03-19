#!/usr/bin/env python
"""
This module returns the file creation time for injestion by prometheus
"""
import os
import time


def file_create(fname, logger):
    """return the file creati on time in epoch time"""
    etime = os.path.getmtime(fname)
    logger.debug(f"[File]: {fname} -> {time.ctime(etime)} ({etime:.0f})")
    return etime


def all_files_create(files, logger):
    """return the files creation time"""
    return [file_create(f, logger) for f in files]


def main():
    """
    main function define the workflow to make a ASN dict->Load the
    corresponding mrt->convert the mrt into mmda
    """
    return 0


if __name__ == "__main__":
    main()
