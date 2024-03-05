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
from netaddr import IPSet, IPNetwork
from mmdb_writer import MMDBWriter
from tqdm import tqdm
import maxminddb
import mrtparse
from args import get_args

args = get_args(mrt=True, mmdb=True, prefix=True, target=True, quiet=True)

if not (os.path.isfile(args.mrt)) or not os.path.isfile(args.mmdb):
    args.print_help(sys.stderr)
    sys.exit(1)


def make_asn(fname):
    """
    Input:  A complete mmdb file that contains prefixes with ASN and description
    Output: Return a ASN lookup dictionary that provides a description for each ASN
            The ASN dictionary discard the prefix information. This dictionary
            is a direct ASN->Description relationship.
            Print the progress while processing each prefixes
    Workflow: Iterate over the mmdb entries to create the desire dictionary
    """
    asn = {}
    message = "Making ASN table for description lookup"
    with maxminddb.open_database(fname) as mreader:
        with tqdm(
            desc=f" {message:<40}  ",
            unit=" prefixes",
            disable=args.quiet,
        ) as pb:
            for prefix, data in mreader:
                try:
                    del prefix
                    asn[str(data["autonomous_system_number"])] = data[
                        "autonomous_system_organization"
                    ]
                    pb.update(1)
                except KeyError:
                    pass
    return asn


def make_dict(i, result):
    """
    Input: One mrt entry and a aggregated entries (result). This aggregated entries
           (dictionary) allow quick lookup of a prefix (key) and fetch the values
           (AS_PATH and the prefix).
    Output: Aggregated mrt entries in dictionary (prefix-> AS_PATH/PREFIX)
    Workflow: Check the mmrt entry for "rib_entries" as this branch contains the
              required routing information such as AS_PATH. This information are
              used to forma mrt entry in dictionary then return back to the caller.
    """
    if ("rib_entries" in i.data) and (
        len(i.data["rib_entries"][0]["path_attributes"][1]["value"]) > 0
    ):
        prefix = str(i.data["prefix"]) + "/" + str(i.data["length"])
        aspath = i.data["rib_entries"][0]["path_attributes"][1]["value"][0]["value"]
        result[prefix] = [aspath, prefix]
    return result


def load_mrt(fname):
    """
    Input: file of the mrt file.
    Output: Aggregated mrt entries in dictionary (prefix-> AS_PATH/PREFIX)
            Print the progress while processing each entry.
    Workflow: Iterate over the mrt entries (parsed by mrtparse module) to
              form the output dictionary
    """
    num = args.prefixes
    result = {}
    mrt = mrtparse.Reader(fname)
    message = "Loading mrt data into dictionary"
    with tqdm(
        desc=f" {message:<40}  ",
        unit=" prefixes",
        disable=args.quiet,
    ) as pb:
        for i in itertools.islice(mrt, num):
            result = make_dict(i, result)
            pb.update(1)
    return result


def convert_mrt_mmdb(fname, mrt, asn):
    """
    Input: Filename of the target mmdb file.
           Dictionary of the prefix->AS_PATH/PREFIX derive from previous mrt file
           Dictionary of the ASN->Decsription
    Output: Create a mmdb file on the target path
            Report any missing description as some ASN inside the mrt may not exist
            in the ASN->Decsription dictionary. This must be reported as missing
            entries.
            Print the progress of the process.
    Workflow: Iterate over the dictionary (prefix->AS_PATH/PREFIX) and derive the
              ASN of destination using AS_PATH. Using this ASN of destionation, do
              a lookup via the Dictionary of the ASN->Decsription. With all these
              data we can form a mmdb entry and using writer.insert_network to
              populate the mmdb. After the completion of the iteration, write
              all mmdb entries into the target file.
    """
    missing = []
    writer = MMDBWriter(ip_version=6, ipv4_compatible=True)
    message = "Converting mrt into mmda"
    with tqdm(
        desc=f" {message:<40}  ",
        unit=" prefixes",
        disable=args.quiet,
    ) as pb:
        for prefix, val in mrt.items():
            if str(val[0][-1]) in asn:
                org_desc = asn[str(val[0][-1])]
            else:
                missing.append(str(val[0][-1]))
                org_desc = ""
            writer.insert_network(
                IPSet(IPNetwork(prefix)),
                {
                    "autonomous_system_number": int(val[0][-1]),
                    "autonomous_system_organization": org_desc,
                    "organization": str(prefix),
                    "isp": " ".join(val[0]),
                },
            )
            pb.update(1)
        writer.to_db_file(fname)
    return missing


def load_bgpscanner(fname):
    """
    For future optimization and improvement using bgpscanner external
    process to speed up the mrt loading process
    """
    result = subprocess.run(
        ["/home/sbng/bin/bgpscanner", fname],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    new = result.stdout.split("=")
    print(new)


def main():
    """
    main function define the workflow to make a ASN dict->Load the
    corresponding mrt->convert the mrt into mmda
    """
    asn = make_asn(args.mmdb)
    prefixes_mrt = load_mrt(args.mrt)
    missing = convert_mrt_mmdb(args.target, prefixes_mrt, asn)
    message = "Prefixes without description"
    print(f" {message:<40}  :", len(missing), " prefixes")
    return 0


if __name__ == "__main__":
    main()
