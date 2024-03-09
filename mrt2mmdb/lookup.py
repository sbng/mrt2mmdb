#!/usr/bin/env python
"""
utility to help lookup on description of network base on IP address or ASN
"""
import os
import sys
import json
import maxminddb
from args import get_args

parser = get_args(mmdb=True, ipaddress=True, asn=True, display=True)
args = parser.parse_args()

if not os.path.isfile(args.mmdb):
    parser.print_help(sys.stderr)
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
    result = []
    with maxminddb.open_database(fname) as mreader:
        for prefix, data in mreader:
            try:
                del prefix
                if str(data["autonomous_system_number"]) == asn:
                    result.append(data)
            except KeyError:
                print("ASN not found")
                result = {}
    return result


def show_db(fname):
    """
    display and pritn the entire mmdb
    """
    result = []
    with maxminddb.open_database(fname) as mreader:
        for prefix, data in mreader:
            try:
                result.append((prefix.compressed, data))
            except KeyError as e:
                print(f"Error {e}")
    return result


def main():
    """
    main function for the workflow
    """
    if args.ipaddress != "":
        print(json.dumps(lookup(args.mmdb, args.ipaddress), indent=1))
    if args.asn != "":
        print(json.dumps(lookup_asn(args.mmdb, args.asn), indent=1))
    if args.display:
        print(json.dumps(show_db(args.mmdb), indent=1))


if __name__ == "__main__":
    main()
