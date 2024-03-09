#!/usr/bin/env python
"""
This module convert a mrt to mmdb format. This conversion also enrich the
new mmdb file with network description whereby a more rich and complete 
information can be obtained from a routing prefix.
"""
import os
import sys
import subprocess
import itertools


def sanitize(text):
    """search and replace string in dict 'condition'"""
    condition = {"{": "", "}": "", ",": " "}
    for i, j in condition.items():
        text = text.replace(i, j)
    return text


def parse_bgpscanner(fname, pb, result, num_prefix):
    """
    For future optimization and improvement using bgpscanner external
    process to speed up the mrt loading process
        ['/usr/bin/env','LD_LIBRARY_PATH="./lib"','bin/bgpscanner', fname],
    """
    count = 0
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "lib"
    with subprocess.Popen(
        ["bin/bgpscanner", fname],
        stdout=subprocess.PIPE,
        text=True,
        env=my_env,
        bufsize=1,
        universal_newlines=True,
    ) as process:
        for line in itertools.islice(process.stdout, num_prefix):
            pb.update(1)
            count += 1
            val = line.split("|")
            prefix = val[1]
            aspath = sanitize(val[2])
            result[prefix] = [aspath.split(), prefix]
            sys.stdout.flush()
    return result, count


def main():
    """main function for bgpscanner.py"""
    return 0


if __name__ == "__main__":
    main()
