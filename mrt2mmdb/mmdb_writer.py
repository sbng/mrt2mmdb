__version__ = "0.2.2"

import logging
import math
import struct
import time
from decimal import Decimal
from enum import IntEnum
from typing import Dict, List, Literal, Union

from netaddr import IPNetwork, IPSet


class MmdbBaseType:
    def __init__(self, value):
        self.value = value


# type hint
class MmdbF32(MmdbBaseType):
    def __init__(self, value: float):
        super().__init__(value)


class MmdbF64(MmdbBaseType):
    def __init__(self, value: Union[float, Decimal]):
        super().__init__(value)


class MmdbI32(MmdbBaseType):
    def __init__(self, value: int):
        super().__init__(value)


class MmdbU16(MmdbBaseType):
    def __init__(self, value: int):
        super().__init__(value)


class MmdbU32(MmdbBaseType):
    def __init__(self, value: int):
        super().__init__(value)


class MmdbU64(MmdbBaseType):
    def __init__(self, value: int):
        super().__init__(value)


class MmdbU128(MmdbBaseType):
    def __init__(self, value: int):
        super().__init__(value)


MMDBType = Union[
    dict,
    list,
    str,
    bytes,
    int,
    bool,
    MmdbF32,
    MmdbF64,
    MmdbI32,
    MmdbU16,
    MmdbU32,
    MmdbU64,
    MmdbU128,
]

logger = logging.getLogger(__name__)

METADATA_MAGIC = b"\xab\xcd\xefMaxMind.com"


class MMDBTypeID(IntEnum):
    POINTER = 1
    STRING = 2
    DOUBLE = 3
    BYTES = 4
    UINT16 = 5
    UINT32 = 6
    MAP = 7
    INT32 = 8
    UINT64 = 9
    UINT128 = 10
    ARRAY = 11
    DATA_CACHE = 12
    END_MARKER = 13
    BOOLEAN = 14
    FLOAT = 15


UINT16_MAX = 0xFFFF
UINT32_MAX = 0xFFFFFFFF
UINT64_MAX = 0xFFFFFFFFFFFFFFFF



IntType = Union[
    Literal[
        "auto",
        "u16",
        "u32",
        "u64",
        "u128",
        "i32",
        "uint16",
        "uint32",
        "uint64",
        "uint128",
        "int32",
    ],
    MmdbU16,
    MmdbU32,
    MmdbU64,
    MmdbU128,
    MmdbI32,
]
FloatType = Union[Literal["f32", "f64", "float32", "float64"], MmdbF32, MmdbF64]


class Encoder:
    def __init__(
        self, cache=True, int_type: IntType = "auto", float_type: FloatType = "f64"
    ):
        self.cache = cache
        self.int_type = int_type
        self.float_type = float_type

        self.data_cache = {}
        self.data_list = []
        self.data_pointer = 0
        self._python_type_id = {
            float: MMDBTypeID.DOUBLE,
            bool: MMDBTypeID.BOOLEAN,
            list: MMDBTypeID.ARRAY,
            dict: MMDBTypeID.MAP,
            bytes: MMDBTypeID.BYTES,
            str: MMDBTypeID.STRING,
            MmdbF32: MMDBTypeID.FLOAT,
            MmdbF64: MMDBTypeID.DOUBLE,
            MmdbI32: MMDBTypeID.INT32,
            MmdbU16: MMDBTypeID.UINT16,
            MmdbU32: MMDBTypeID.UINT32,
            MmdbU64: MMDBTypeID.UINT64,
            MmdbU128: MMDBTypeID.UINT128,
        }

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
        res = self._make_header(MMDBTypeID.STRING, len(encoded_value))
        res += encoded_value
        return res

    def _encode_bytes(self, value):
        return self._make_header(MMDBTypeID.BYTES, len(value)) + value

    def _encode_uint(self, type_id, max_len):
        value_max = 2 ** (max_len * 8)

        def _encode_unsigned_value(value):
            if value < 0 or value >= value_max:
                raise ValueError(
                    f"encode uint{max_len * 8} fail: "
                    f"{value} not in range(0, {value_max})"
                )
            res = b""
            while value != 0 and len(res) < max_len:
                res = struct.pack(">B", value & 0xFF) + res
                value = value >> 8
            return self._make_header(type_id, len(res)) + res

        return _encode_unsigned_value

    def _encode_map(self, value):
        res = self._make_header(MMDBTypeID.MAP, len(value))
        for k, v in list(value.items()):
            # Keys are always stored by value.
            res += self.encode(k)
            res += self.encode(v)
        return res

    def _encode_array(self, value):
        res = self._make_header(MMDBTypeID.ARRAY, len(value))
        for k in value:
            res += self.encode(k)
        return res

    def _encode_boolean(self, value):
        return self._make_header(MMDBTypeID.BOOLEAN, 1 if value else 0)

    def _encode_pack_type(self, type_id, fmt):
        def pack_type(value):
            res = struct.pack(fmt, value)
            return self._make_header(type_id, len(res)) + res

        return pack_type

    _type_encoder = None

    @property
    def type_encoder(self):
        if self._type_encoder is None:
            self._type_encoder = {
                MMDBTypeID.POINTER: self._encode_pointer,
                MMDBTypeID.STRING: self._encode_utf8_string,
                MMDBTypeID.DOUBLE: self._encode_pack_type(MMDBTypeID.DOUBLE, ">d"),
                MMDBTypeID.BYTES: self._encode_bytes,
                MMDBTypeID.UINT16: self._encode_uint(MMDBTypeID.UINT16, 2),
                MMDBTypeID.UINT32: self._encode_uint(MMDBTypeID.UINT32, 4),
                MMDBTypeID.MAP: self._encode_map,
                MMDBTypeID.INT32: self._encode_pack_type(MMDBTypeID.INT32, ">i"),
                MMDBTypeID.UINT64: self._encode_uint(MMDBTypeID.UINT64, 8),
                MMDBTypeID.UINT128: self._encode_uint(MMDBTypeID.UINT128, 16),
                MMDBTypeID.ARRAY: self._encode_array,
                MMDBTypeID.BOOLEAN: self._encode_boolean,
                MMDBTypeID.FLOAT: self._encode_pack_type(MMDBTypeID.FLOAT, ">f"),
            }
        return self._type_encoder

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

    def python_type_id(self, value):
        value_type = type(value)
        type_id = self._python_type_id.get(value_type)
        if type_id:
            return type_id
        if value_type is int:
            if self.int_type == "auto":
                if value > UINT64_MAX:
                    return MMDBTypeID.UINT128
                elif value > UINT32_MAX:
                    return MMDBTypeID.UINT64
                elif value > UINT16_MAX:
                    return MMDBTypeID.UINT32
                elif value < 0:
                    return MMDBTypeID.INT32
                else:
                    return MMDBTypeID.UINT16
            elif self.int_type in ("u16", "uint16", MmdbU16):
                return MMDBTypeID.UINT16
            elif self.int_type in ("u32", "uint32", MmdbU32):
                return MMDBTypeID.UINT32
            elif self.int_type in ("u64", "uint64", MmdbU64):
                return MMDBTypeID.UINT64
            elif self.int_type in ("u128", "uint128", MmdbU128):
                return MMDBTypeID.UINT128
            elif self.int_type in ("i32", "int32", MmdbI32):
                return MMDBTypeID.INT32
            else:
                raise ValueError(f"unknown int_type={self.int_type}")
        elif value_type is float:
            if self.float_type in ("f32", "float32", MmdbF32):
                return MMDBTypeID.FLOAT
            elif self.float_type in ("f64", "float64", MmdbF64):
                return MMDBTypeID.DOUBLE
            else:
                raise ValueError(f"unknown float_type={self.float_type}")
        elif value_type is Decimal:
            return MMDBTypeID.DOUBLE
        raise TypeError(f"unknown type {value_type}")

    def encode_meta(self, meta):
        res = self._make_header(MMDBTypeID.MAP, len(meta))
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
           #if isinstance(value, dict) and self.data_pointer == 0:
           #     res = self._make_header(MMDBTypeID.MAP, len(value))
           #     self.data_list.append(res)
           #     self.data_pointer += len(res)
           try:
               return self.data_cache[id(value)]
           except KeyError:
               pass

        if not type_id:
            type_id = self.python_type_id(value)

        try:
            encoder = self.type_encoder[type_id]
        except KeyError as err:
            raise ValueError(f"unknown type_id={type_id}") from err

        if isinstance(value, MmdbBaseType):
            value = value.value
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
                self.data_cache[id(value)] = pointer
                return pointer
        return res


def bits_rstrip(n, length=None, keep=0):
    return map(int, bin(n)[2:].rjust(length, "0")[:keep])



