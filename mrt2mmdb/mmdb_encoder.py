# coding: utf-8
# This module is a copy of mmdb_writer https://github.com/vimt/MaxMind-DB-Writer-python.git
# Only the Encoder class were kept as the extra classes are not required for filter.py
# To avoid conflict with the installed mmdb_writer module, this module is created for the sole
# need to encode mmdb data.
 
__version__ = "0.1.1"

import logging
import math
import struct
import time
from typing import Union

from netaddr import IPSet, IPNetwork
from weakref import WeakKeyDictionary

MMDBType = Union[dict, list, str, bytes, int, bool]

logger = logging.getLogger(__name__)

METADATA_MAGIC = b"\xab\xcd\xefMaxMind.com"


class Encoder(object):

    def __init__(self, cache=True):
        self.data_cache = {}
        self.pointer_cache = {}
        self.data_list = []
        self.data_pointer = 0

        self.cache = cache

    def _encode_pointer(self, value):
        pointer = value
        if pointer >= 134744064:
            res = struct.pack(">BI", 0x38, pointer)
        elif pointer >= 526336:
            pointer -= 526336
            res = struct.pack(
                ">BBBB",
                0x30 + ((pointer >> 24) & 0x07),
                (pointer >> 16) & 0xFF,
                (pointer >> 8) & 0xFF,
                pointer & 0xFF,
            )
        elif pointer >= 2048:
            pointer -= 2048
            res = struct.pack(
                ">BBB",
                0x28 + ((pointer >> 16) & 0x07),
                (pointer >> 8) & 0xFF,
                pointer & 0xFF,
            )
        else:
            res = struct.pack(">BB", 0x20 + ((pointer >> 8) & 0x07), pointer & 0xFF)

        return res

    def _encode_utf8_string(self, value):
        encoded_value = value.encode("utf-8")
        res = self._make_header(2, len(encoded_value))
        res += encoded_value
        return res

    def _encode_bytes(self, value):
        return self._make_header(4, len(value)) + value

    def _encode_uint(self, type_id, max_len):
        def _encode_unsigned_value(value):
            res = b""
            while value != 0 and len(res) < max_len:
                res = struct.pack(">B", value & 0xFF) + res
                value = value >> 8
            return self._make_header(type_id, len(res)) + res

        return _encode_unsigned_value

    def _encode_map(self, value):
        res = self._make_header(7, len(value))
        for k, v in list(value.items()):
            # Keys are always stored by value.
            res += self.encode(k)
            res += self.encode(v)
        return res

    def _encode_array(self, value):
        res = self._make_header(11, len(value))
        for k in value:
            res += self.encode(k)
        return res

    def _encode_boolean(self, value):
        return self._make_header(14, 1 if value else 0)

    def _encode_pack_type(self, type_id, fmt):
        def pack_type(value):
            res = struct.pack(fmt, value)
            return self._make_header(type_id, len(res)) + res

        return pack_type

    _type_decoder = None

    @property
    def type_decoder(self):
        if self._type_decoder is None:
            self._type_decoder = {
                1: self._encode_pointer,
                2: self._encode_utf8_string,
                3: self._encode_pack_type(3, ">d"),  # double,
                4: self._encode_bytes,
                5: self._encode_uint(5, 2),  # uint16
                6: self._encode_uint(6, 4),  # uint32
                7: self._encode_map,
                8: self._encode_pack_type(8, ">i"),  # int32
                9: self._encode_uint(9, 8),  # uint64
                10: self._encode_uint(10, 16),  # uint128
                11: self._encode_array,
                14: self._encode_boolean,
                15: self._encode_pack_type(15, ">f"),  # float,
            }
        return self._type_decoder

    def _make_header(self, type_id, length):
        if length >= 16843036:
            raise Exception("length >= 16843036")

        elif length >= 65821:
            five_bits = 31
            length -= 65821
            b3 = length & 0xFF
            b2 = (length >> 8) & 0xFF
            b1 = (length >> 16) & 0xFF
            additional_length_bytes = struct.pack(">BBB", b1, b2, b3)

        elif length >= 285:
            five_bits = 30
            length -= 285
            b2 = length & 0xFF
            b1 = (length >> 8) & 0xFF
            additional_length_bytes = struct.pack(">BB", b1, b2)

        elif length >= 29:
            five_bits = 29
            length -= 29
            additional_length_bytes = struct.pack(">B", length & 0xFF)

        else:
            five_bits = length
            additional_length_bytes = b""

        if type_id <= 7:
            res = struct.pack(">B", (type_id << 5) + five_bits)
        else:
            res = struct.pack(">BB", five_bits, type_id - 7)

        return res + additional_length_bytes

    _python_type_id = {float: 15, bool: 14, list: 11, dict: 7, bytes: 4, str: 2}

    def python_type_id(self, value):
        value_type = type(value)
        type_id = self._python_type_id.get(value_type)
        if type_id:
            return type_id
        if value_type is int:
            if value > 0xFFFFFFFFFFFFFFFF:
                return 10
            elif value > 0xFFFFFFFF:
                return 9
            elif value > 0xFFFF:
                return 6
            elif value < 0:
                return 8
            else:
                return 5
        raise TypeError("unknown type {value_type}".format(value_type=value_type))

    def _freeze(self, value):
        if isinstance(value, dict):
            return tuple((k, self._freeze(v)) for k, v in value.items())
        elif isinstance(value, list):
            return tuple(self._freeze(v) for v in value)
        return value

    def encode_meta(self, meta):
        res = self._make_header(7, len(meta))
        meta_type = {
            "node_count": 6,
            "record_size": 5,
            "ip_version": 5,
            "binary_format_major_version": 5,
            "binary_format_minor_version": 5,
            "build_epoch": 9,
        }
        for k, v in list(meta.items()):
            # Keys are always stored by value.
            res += self.encode(k)
            res += self.encode(v, meta_type.get(k))
        return res

    def encode(self, value, type_id=None):
        if self.cache:
            try:
                cache_key = self._freeze(value)
                return self.data_cache[cache_key]
            except KeyError:
                pass

        if not type_id:
            type_id = self.python_type_id(value)

        try:
            encoder = self.type_decoder[type_id]
        except KeyError:
            raise ValueError("unknown type_id={type_id}".format(type_id=type_id))
        res = encoder(value)

        if self.cache:
            # add to cache
            if type_id == 1:
                self.data_list.append(res)
                self.data_pointer += len(res)
                return res
            else:
                self.data_list.append(res)
                pointer_position = self.data_pointer
                self.data_pointer += len(res)
                pointer = self.encode(pointer_position, 1)
                self.data_cache[cache_key] = pointer
                return pointer
        return res 


def bits_rstrip(n, length=None, keep=0):
    return map(int, bin(n)[2:].rjust(length, "0")[:keep])
