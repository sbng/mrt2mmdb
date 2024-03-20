#!/usr/bin/env python
"""
This module parse a cvs or tsv flat file while returning the 
values a in dictionary for further processing
"""
import csv
from tqdm import tqdm


def parse_flatfile(fname, quiet):
    """process a csv or tsv file and convert the file into a dictionary for asn lookup"""
    result = {}
    with open(fname, newline="\n", encoding="utf-8") as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        message = "Making custom ASN table using lookup file"
        with tqdm(
            desc=f" {message:<40} ",
            unit=" prefixes",
            disable=quiet,
        ) as pb:
            for row in reader:
                # tsv file missing the country information on the last column
                # add the country as empty string. csv handle the country correctly
                # so length of cvs row is equal to 4
                # if len(row) < 4:
                #    row.append('')
                result[row[0]] = str(row[2])
                pb.update(1)
        return result


def main():
    """
    main function test the flat file parsing into a dictionary
    """
    r = parse_flatfile("data/asn_rir_org_country.csv", False)
    del r
    return 0


if __name__ == "__main__":
    main()
