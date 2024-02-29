# mrt2mmdb
Convert a mrt file into a maxmind database file 

## Usage
usage: make_mmdb.py [-h] [--mrt [MRT]] [--mmdb [MMDB]] [--target [TARGET]] [--prefixes [PREFIXES]] [--quiet]

optional arguments:

  -h, --help            show this help message and exit
  
  --mrt [MRT]           Filename of mrt dump
  
  --mmdb [MMDB]         Filename of Maxmind mmdb file for prefixes lookup and return description/ASN
  
  --target [TARGET]     Filename of new target mmdb file generated from mrt file
  
  --prefixes [PREFIXES]
                        Number of prefixes to process in mrt file (default:all)
                        
  --quiet               Turn off verbose (default:verbose)
