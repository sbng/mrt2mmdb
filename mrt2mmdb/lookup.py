#!/usr/bin/env python

import os
import sys
import argparse
import maxminddb
import mrtparse
import subprocess
import multiprocessing
from netaddr import IPSet, IPNetwork
from ipaddress import ip_address, IPv4Address

parser = argparse.ArgumentParser()
parser.add_argument(
    "--mmdb",
    type=str,
    help="Filename of Maxmind mmdb file for prefixes lookup and return description/ASN",
    nargs="?",
    default="GeoLite2-ASN.mmdb",
)
parser.add_argument(
    "--ipaddress", type=str, help="IP address lookup", nargs="?", default=""
)
parser.add_argument("--asn", type=str, help="ASN lookup", nargs="?", default="")
parser.add_argument(
    "--mrt",
    type=str,
    help="Lookup using MRT file instead of mmdb",
    nargs="?",
    default="",
)
args = parser.parse_args()

if (not (os.path.isfile(args.mmdb))):
    parser.print_help(sys.stderr)
    sys.exit(1)

def lookup(fname, ipadd):
    with maxminddb.open_database(fname) as mreader:
        return mreader.get(ipadd)


def lookup_asn(fname, asn):
    with maxminddb.open_database(fname) as mreader:
        for prefix, data in mreader:
            try:
                if str(data["autonomous_system_number"]) == asn:
                    return data
            except:
                pass

    pool = multiprocessing.Pool(os.cpu_count())
    mrt = mrtparse.Reader(fname)
    print(fname, ipadd)
    return


def main():
    if (args.ipaddress != "") and (args.mrt == ""):
        print(lookup(args.mmdb, args.ipaddress))
    if (args.asn != "") and (args.mrt == ""):
        print(lookup_asn(args.mmdb, args.asn))


if __name__ == "__main__":
    main()
