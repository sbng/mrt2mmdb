#!/usr/bin/env python
"""
This module get the arguments for the various founction for processing
Any new argument can be added to this file to consolidate and reuse all possible
arguments used. Use need to add the boolean keyword of the new argument and use the 
boolean variable to capture the argument needed when this module is called.
"""
import argparse


def get_args(
    mrt=False,
    mmdb=False,
    target=False,
    prefix=False,
    quiet=False,
    ipaddress=False,
    asn=False,
):
    # pylint: disable=too-many-arguments
    """
    Input: keywords boolean of the desire argument
    Output: The argument obtained from the command line
    Caveat: Boolean variable allows the desired argument to be captured
    """
    parser = argparse.ArgumentParser()
    if mrt:
        parser.add_argument(
            "--mrt",
            metavar="",
            type=str,
            help="Filename of mrt dump",
            default="data/mrt-dump.ams.202402171710.gz",
        )
    if mmdb:
        parser.add_argument(
            "--mmdb",
            metavar="",
            type=str,
            help="Filename of Maxmind mmdb file for prefixes lookup and return description/ASN",
            default="data/GeoLite2-ASN.mmdb",
        )
    if target:
        parser.add_argument(
            "--target",
            metavar="",
            type=str,
            help="Filename of new target mmdb file generated from mmrt file",
            default="out.mmdb",
        )
    if prefix:
        parser.add_argument(
            "--prefixes",
            metavar="",
            type=int,
            help="Number of prefixes to process in mrt file (default:all)",
            default=None,
        )
    if quiet:
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Turn off verbose (default:verbose)",
            default=False,
        )
    if ipaddress:
        parser.add_argument(
            "--ipaddress", metavar="", type=str, help="IP address lookup", default=""
        )
    if asn:
        parser.add_argument(
            "--asn", metavar="", type=str, help="ASN lookup", default=""
        )
    return parser.parse_args()


def main():
    """
    main function define the workflow to make a ASN dict->Load the
    corresponding mrt->convert the mrt into mmda
    """
    args = get_args(
        mrt=True,
        mmdb=True,
        target=True,
        prefix=True,
        ipaddress=True,
        asn=True,
        quiet=True,
    )
    print(args)
    return 0


if __name__ == "__main__":
    main()
