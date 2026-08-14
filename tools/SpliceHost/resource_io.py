"""Source 2 compiled resource (vmdl_c) block reader/writer."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import keyvalues3 as kv3


@dataclass
class Block:
    typ: bytes  # 4-byte type
    data: bytes


def read_resource(path: str | Path) -> tuple[int, int, list[Block]]:
    raw = Path(path).read_bytes()
    file_size, hdr, ver, block_off, count = struct.unpack_from("<IHHII", raw, 0)
    if hdr != 12:
        raise ValueError(f"unexpected header version {hdr}")
    pos = 16 + (block_off - 8)
    blocks: list[Block] = []
    for _ in range(count):
        typ_i, rel, size = struct.unpack_from("<III", raw, pos)
        abs_off = (pos + 4) + rel
        blocks.append(Block(struct.pack("<I", typ_i), raw[abs_off : abs_off + size]))
        pos += 12
    return hdr, ver, blocks


def write_resource(path: str | Path, ver: int, blocks: list[Block], hdr: int = 12) -> None:
    count = len(blocks)
    dir_size = count * 12
    # header: 16 bytes, directory immediately after (block_off=8)
    header = bytearray()
    header += struct.pack("<IHHII", 0, hdr, ver, 8, count)
    header += b"\x00" * dir_size

    payload = bytearray()
    dir_entries: list[tuple[int, int, int]] = []  # type, rel_offset, size

    # After header+dir, align first block to 16
    cursor = 16 + dir_size

    def align16(buf: bytearray, abs_pos: int) -> int:
        pad = (16 - (abs_pos % 16)) % 16
        if pad:
            buf += b"\x00" * pad
        return abs_pos + pad

    for i, block in enumerate(blocks):
        cursor = align16(payload, cursor)
        dir_field_pos = 16 + i * 12 + 4  # position of offset field
        rel = cursor - dir_field_pos
        dir_entries.append((struct.unpack("<I", block.typ)[0], rel, len(block.data)))
        payload += block.data
        cursor += len(block.data)

    file_size = 16 + dir_size + len(payload)
    out = bytearray()
    out += struct.pack("<IHHII", file_size, hdr, ver, 8, count)
    for typ_i, rel, size in dir_entries:
        out += struct.pack("<III", typ_i, rel, size)
    out += payload
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(out)


def kv3_read_block(data: bytes):
    return kv3.read(BytesIO(data))


def kv3_write_block(value) -> bytes:
    if isinstance(value, kv3.KV3File):
        value = value.value
    buf = BytesIO()
    kv3.write(value, buf, encoding=kv3.ENCODING_BINARY_UNCOMPRESSED, format=kv3.FORMAT_GENERIC)
    return buf.getvalue()


def find_blocks(blocks: list[Block], typ: bytes) -> list[int]:
    return [i for i, b in enumerate(blocks) if b.typ == typ]
