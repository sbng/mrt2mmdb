#!/usr/bin/env python
"""
utility to help lookup on description of network base on IP address or ASN
"""
import os
import sys
import maxminddb
from args import get_args

args = get_args(mmdb=True, ipaddress=True, asn=True)

if not os.path.isfile(args.mmdb):
    args.print_help(sys.stderr)
    sys.exit(1)


def lookup(fname, ipadd):
    """
    lookup base on IP address. The description is returned.
    """
    with maxminddb.open_database(fname) as mreader:
        return mreader.get(ipadd)


def lookup_asn(fname, asn):
    """
    lookup base on ASN. The description is returned.
    """
    result = {}
    with maxminddb.open_database(fname) as mreader:
        for prefix, data in mreader:
            try:
                del prefix
                if str(data["autonomous_system_number"]) == asn:
                    result = data
            except KeyError:
                print("ASN not found")
                result = {}
    return result


def main():
    """
    main function for the workflow
    """
    if args.ipaddress != "":
        print(lookup(args.mmdb, args.ipaddress))
    if args.asn != "":
        print(lookup_asn(args.mmdb, args.asn))


if __name__ == "__main__":
    main()
