#!/usr/bin/env python
"""
utility to help lookup on description of network base on IP address or ASN
"""
import os
import sys
import json
import maxminddb
import ipaddress
import struct
import shutil
from netaddr import IPSet, IPNetwork

from maxminddb.const import MODE_AUTO, MODE_MMAP, MODE_FILE, MODE_MEMORY, MODE_FD
from maxminddb.errors import InvalidDatabaseError
from maxminddb.file import FileBuffer
from maxminddb.types import Record
from os import PathLike
from typing import Any, AnyStr, IO, Optional, Tuple, Union, cast, Dict, List, Tuple, Union

from mmdb_writer import Encoder
from maxminddb.reader import Reader
from maxminddb.decoder import Decoder

from args import (
    get_args,
    mmdb_arg,
    ipaddress_arg,
    asn_arg,
    display_arg,
    show_db_type_arg,
    trim_arg,
)

# pylint: disable=global-statement
args = {}

class update(Reader, Encoder):
    _data_start = 0 
    _pointer_base = 0
    _data_stop = 0
    _seeker = 0
    _next_data = 0
    _decode_bytes = bytearray()
    _pointer_test = []
    _pointer_base = 0

    def __init__(
        self, database: Union[AnyStr, int, PathLike, IO], mode: int = MODE_AUTO
    ) -> None:
        Reader.__init__(self, database, mode)
        self._data_start = self.data_section_start
        self._seeker = self.data_section_start
        self._data_stop = self.data_section_stop
        self._next_data = self.next_pointer
        self._pointer_base = self._data_start
        self._encode = Encoder(cache=False)
        #self._encode = Encoder()
        self._filename = database
        shutil.copyfile(database, database+".trim")
        self._fh = open(database+".trim", 'r+b')
        self.data_cache = {}

    @property
    def data_section_start(self) -> int:
        metadata = self.metadata()
        treesize = int(((metadata.record_size * 2)/8) * metadata.node_count)
        _ptr = treesize + 16
        return _ptr 

    @property
    def data_section_stop(self) -> int:
        return self._buffer.rfind(
                self._METADATA_START_MARKER, max(0, self._buffer_size - 128 * 1024)
        )
    
    @property
    def seeker(self) -> int:
        return self._seeker
    
    @property
    def next_pointer(self) -> int:
        (_, self._next_data) = self.decode(self._seeker)
        return self._next_data
    
    @property
    def show_data(self):
        (content, _) = self.decode(self._seeker)
        return content

    @property
    def next_data(self) -> int:
        self._seeker = self._next_data
        self.next_pointer
        (content, _) = self.decode(self._seeker)
        if self.next_pointer == self._data_stop:
            self._seeker = self._data_start
            self._next_data = self._data_start
        return content

    def decode(self, offset: int) -> Tuple[Record, int]:
        return self._decoder.decode(offset)

    def encode(self, value, type_id=None):
        res = self._encode.encode(value)
        print (self._encode.data_cache)
        return res

    def extract(self, start_marker: int, end_marker: int) -> list:
        if end_marker == 0:
            return self._buffer[start_marker:]
        else:
            return self._buffer[start_marker:end_marker]

    def decode_byte(self, byte_pointer: bytes):
        # check what type of pointer by extracting first first of the input
        mask = int('00011000', 2)
        mask_pointer = int('00000111', 2)
        cp = byte_pointer[0] & mask
        
        if cp == 0:
            res = ((byte_pointer[0] & mask_pointer) << 8) | byte_pointer[1]
        if cp == 1:
            res = ((byte_pointer[0] & mask_pointer) << 16) | (byte_pointer[1] << 8) | byte_pointer[2] + 2048,
        if cp == 2:
            res =((byte_pointer[0] & mask_pointer) << 24) | (byte_pointer[1] << 16) | (byte_pointer[2] << 8) | byte_pointer[3]  + 526336,
        if cp == 3:
            res = (byte_pointer[1] << 24) | (byte_pointer[2] << 16) | (byte_pointer[3] << 8) | byte_pointer[4],
    

        return struct.pack('>I', res + self._metadata.node_count + 16)

def filter_dict(raw):
    """
    filter and remove keys from dictionary. The keys to be removed are store in ignore_keys and ignore_lang
    list
    """
    ignore_keys = ["geoname_id","confidence","organization","accuracy_radius","time_zone","isp","domain","postal","metro_code"]
    ignore_lang = ["de","es","fr","ja","pt-BR","ru","zh-CN"]
    rem_keys = ignore_keys + ignore_lang
    fnc = lambda sub: [
        fnc(item) if isinstance(item, dict) else item
        for item in sub
        if isinstance(sub, list)
    ] if isinstance(sub, list) else {
        key1: fnc(val1) if isinstance(val1, (dict, list)) else val1
        for key1, val1 in sub.items()
        if key1 not in rem_keys
    }
    return fnc(raw)

def show_db(fname):
    """
    display and print the entire mmdb
    Return a list of prefix/dictionaries 
    """
    result = []
    mreader = maxminddb.open_database(fname)
    res = (((prefix.compressed),filter_dict(data)) for prefix, data in mreader)
    mreader.close
    rewrite(fname, res)
    return (res)

def rewrite(fname, dic_data):
    with update(fname) as reader:
        metadata_cache = reader.extract(reader.data_section_stop,0)
        resolved = reader.data_section_start
        encode_record = Encoder(cache=True)
        for prefix,record in dic_data:
            a = prefix.split('/')[0]
            address = bytearray(ipaddress.ip_address(a).packed)
            ((data_pointer, loc),_) = reader._find_address_in_tree_loc(address)
            pack = encode_record.encode(record)
            pack_pointer = reader.decode_byte(pack)
            """
            Update the search tree leaf node with the pointer of the data for this node
            pointer_loc : Tuple of location of leaf node (loc) and the pointer 
                          (data_pointer) to the data. 
            """
            reader._fh.seek(loc)
            reader._fh.write(pack_pointer)
        pack_list = (b''.join([bytes_obj for bytes_obj in encode_record.data_list]))
        reader._fh.seek(reader.data_section_start)
        reader._fh.write(pack_list)
        reader._fh.write(metadata_cache)

def main():
    """
    main function for the workflow
    """
    parser = get_args([mmdb_arg, ipaddress_arg, asn_arg, display_arg, show_db_type_arg, trim_arg])
    global args
    args = parser.parse_args()
    if not os.path.isfile(args.mmdb):
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.ipaddress != "":
        print(json.dumps(lookup(args.mmdb, args.ipaddress), indent=1))
    if args.asn != "":
        print(json.dumps(lookup_asn(args.mmdb, args.asn), indent=1))
    if args.display:
         show_db(args.mmdb)
    if args.trim:
         show_db(args.mmdb)
    if args.show_db_type:
         print(json.dumps(db_type(args.mmdb), indent=1))


if __name__ == "__main__":
    main()
