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

def decode_byte(byte_pointer: bytes, reader):
    # check what type of pointer by extracting first first of the input
    mask = int('00011000', 2) 
    mask_pointer = int('00000111', 2)
    cp = byte_pointer[0] & mask
    
    print ("byte pointer: ",byte_pointer.hex(), "CP: ",cp)

    if cp == 0:
        res = ((byte_pointer[0] & mask_pointer) << 8) | byte_pointer[1]
    if cp == 1:
        res = ((byte_pointer[0] & mask_pointer) << 16) | (byte_pointer[1] << 8) | byte_pointer[2] + 2048,
    if cp == 2:
        res =((byte_pointer[0] & mask_pointer) << 24) | (byte_pointer[1] << 16) | (byte_pointer[2] << 8) | byte_pointer[3]  + 526336,
    if cp == 3:
        res = (byte_pointer[1] << 24) | (byte_pointer[2] << 16) | (byte_pointer[3] << 8) | byte_pointer[4],

    return struct.pack('>I', res + reader._metadata.node_count + 16)


def decode_pointer(res, reader):
    if len(res) == 5:
        _, pointer = struct.unpack('>BI', res)
    elif len(res) == 4:
        b0, b1, b2, b3 = struct.unpack('>BBBB', res)
        pointer = (b0 & 0x07) << 24 | b1 << 16 | b2 << 8 | b3
        pointer += 526336
    elif len(res) == 3:
        b0, b1, b2 = struct.unpack('>BBB', res)
        pointer = (b0 & 0x07) << 16 | b1 << 8 | b2
        pointer += 2048
    elif len(res) == 2:
        b0, b1 = struct.unpack('>BB', res)
        pointer = (b0 & 0x07) << 8 | b1
    else:
        raise ValueError("Invalid encoded pointer")
    return struct.pack('>I', pointer + reader._metadata.node_count + 16)

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

def load_db(fname):
    """
    display and print the entire mmdb
    Return a list of prefix/dictionaries
    using python generator
    """
    result = []
    mreader = maxminddb.open_database(fname)
    res = (((prefix.compressed),filter_dict(data)) for prefix, data in mreader)
    mreader.close
    return (res)

def rewrite(fname, dic_data):
    shutil.copyfile(fname, fname+".trim")
    fh = open(fname+".trim", 'r+b')
    with Reader(fname) as reader:
        metadata = reader.metadata()
        treesize = int(((metadata.record_size * 2)/8) * metadata.node_count)
        data_section_start = treesize + 16
        resolved = data_section_start
        data_section_end = reader._buffer.rfind(reader._METADATA_START_MARKER, max(0, reader._buffer_size - 128 * 1024))
        metadata_cache = reader._buffer[data_section_end:]
        encode_record = Encoder(cache=True)
        for prefix,record in dic_data:
            a = prefix.split('/')[0]
            address = bytearray(ipaddress.ip_address(a).packed)
            pack = encode_record.encode(record)
            pack_pointer = decode_pointer(pack, reader)
            end_marker = resolved + len(encode_record.data_list)
            """
            Update the search tree leaf node with the pointer of the data for this node
            using the custom find_address_in_tree_loc function from Decoder module. The 
            function return -> the address of the location of leaf node. 
            Result :      Tuple of location of leaf node (loc) and the pointer 
                          (data_pointer) to the data. 
            """
            ((data_pointer, loc), prefix_length) = reader._find_address_in_tree_loc(address)
            fh.seek(loc)
            fh.write(pack_pointer)
            """
            write the buf onto the file and clear the encoding data_list in the encoder
            This will prevent overloading the memory
            """
            buff = encode_record.data_list
            encode_record.data_list = []
            print (b''.join([bytes_obj for bytes_obj in buff]))
            fh.seek(resolved)
            fh.write((b''.join([bytes_obj for bytes_obj in buff])))
            resolved = end_marker

        #pack_list = (b''.join([bytes_obj for bytes_obj in encode_record.data_list]))
        #fh.seek(data_section_start)
        #fh.write(pack_list)
        fh.seek(resolved)
        fh.write(metadata_cache)
    fh.close()

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

if __name__ == "__main__":
    main()
    fname = args.mmdb
    db = load_db(fname)
    rewrite(fname, db)
    
