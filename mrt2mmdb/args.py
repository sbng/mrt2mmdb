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
    lookup_file=False,
    prefix=False,
    quiet=False,
    ipaddress=False,
    asn=False,
    bgpscan=False,
    display=False,
    prometheus=False,
    database_type=False,
    show_db_type=False,
    log_level=False,
):
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
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
    if lookup_file:
        parser.add_argument(
            "--lookup_file",
            metavar="",
            type=str,
            help="Filename of csv,tsv file for custom ASN lookup",
            default="",
            #            default="data/asn_rir_org_country.csv",
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
    if bgpscan:
        parser.add_argument(
            "--bgpscan",
            action="store_true",
            help="Using faster bgpscanner to parse mrt file",
            default=False,
        )
    if display:
        parser.add_argument(
            "--display",
            action="store_true",
            help="Display the database",
            default=False,
        )
    if prometheus:
        parser.add_argument(
            "--prometheus",
            action="store_true",
            help="Output statistics for prometheus injestion",
            default=False,
        )
    if database_type:
        parser.add_argument(
            "--database_type",
            metavar="",
            type=str,
            help="Type pf mmdb database (default: mrt2mmdb)",
            default="mrt2mmdb",
        )
    if show_db_type:
        parser.add_argument(
            "--show_db_type",
            action="store_true",
            help="Show the mmdb database type",
            default=False,
        )
    if log_level:
        parser.add_argument(
            "--log_level",
            metavar="",
            type=str,
            help="logging level [CRITICAL|WARNING|INFO|DEBUG](default: WARNING)",
            default="WARNING",
        )
    return parser


def main():
    """
    main function define to test the function before integeration
    """
    parser = get_args(
        mmdb=True,
        mrt=True,
        target=True,
        bgpscan=True,
        prometheus=True,
        prefix=True,
        display=True,
    )
    args = parser.parse_args()
    del args
    return 0


if __name__ == "__main__":
    main()
