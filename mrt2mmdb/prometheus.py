#!/usr/bin/env python
""" This module output prometheus formated text for prometheus injestion. 
Require statistic from various sources to include in the prometheus output.
"""


def output_prometheus(
    asn_stats, prefix_stats, convert_stats, missing_stats, files_stats
):
    """Return the prometheus format output using a f-string templating"""
    return f"""#
# durations are seconds
mrt2mmdb_description_asn_prefixes {asn_stats[0]}
mrt2mmdb_description_asn_prefixes_duration {asn_stats[1]:.0f}
mrt2mmdb_description_asn_prefixes_per_second {asn_stats[0]/asn_stats[1]:.2f}
#
mrt2mmdb_dictionary_load_prefixes {prefix_stats[0]}
mrt2mmdb_dictionary_load_prefixes_duration {prefix_stats[1]:.0f}
mrt2mmdb_dictionary_load_prefixes_per_second {prefix_stats[0]/prefix_stats[1]:.2f}
#
mrt2mmdb_conversions {convert_stats[0]}
mrt2mmdb_conversions_duration {convert_stats[1]:.0f}
mrt2mmdb_conversions_per_second {convert_stats[0]/convert_stats[1]:.2f}
#
# How many prefixes were not found in the Maxmind template file that we’re using as a source for names?
#
mrt2mmdb_prefixes_no_description {len(missing_stats)} 
mrt2mmdb_asn_no_description {len(set(missing_stats))}
#
# When did this instance of the process start? Unix epoch seconds.
#
mrt2mmdb_lastrun_timestamp {files_stats[0]:.0f} 
#
# This is the creationtime of the MRT file that is being parsed
# Unix epoch seconds.  This is what we can use to see if somehow
# our MRT file collection pipeline is “stuck” and not being updated.
#
mrt2mmdb_mrt_file_creation_timestamp {files_stats[1]:.0f} 
#
# This is the creationtime of the template MMDB file that is being parsed
# Unix epoch seconds.  This is what we can use to see if somehow
# our template MMDB file collection pipeline is “stuck” and not being updated.
#
mrt2mmdb_template_mmdb_file_creation_timestamp {files_stats[2]:.0f} 
#
# Keep a version number so we can track behaviors of different variations
# MUST BE NUMERIC ONLY, with a single decimal point.
#
mrt2mmdb_version 1.0
"""


def main():
    """
    main function define the workflow to make a ASN dict->Load the
    corresponding mrt->convert the mrt into mmda
    """
    return 0


if __name__ == "__main__":
    main()
