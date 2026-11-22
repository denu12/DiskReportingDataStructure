"""Retry an inconclusive correctness check on a bounded subset of the same input."""

import struct


def bounded_fixture(source, target, max_points=50_000):
    with source.open("rb") as stream:
        magic = stream.read(8)
        if magic == b"SQUARE1\0":
            dimension, n, queries = struct.unpack("<IQQ",stream.read(20))
            header = lambda count: struct.pack("<8sIQQ",magic,dimension,count,queries+1)
        elif magic == b"ESA2D01\0":
            dimension=2
            n,queries=struct.unpack("<QQ",stream.read(16))
            header = lambda count: struct.pack("<8sQQ",magic,count,queries+1)
        else:
            stream.seek(0)
            dimension,n,queries=struct.unpack("<IQQ",stream.read(20))
            header = lambda count: struct.pack("<IQQ",dimension,count,queries+1)
        if n<=max_points:
            return False
        offset=stream.tell()
        size=dimension*4
        points=stream.read(max_points*size)
        if len(points)!=max_points*size:
            raise ValueError(f"Truncated fixture: {source}")
        stream.seek(offset+n*size)
        tail=stream.read()
        query_size = dimension*8 if magic==b"SQUARE1\0" else dimension*4+16
        if len(tail)!=queries*query_size:
            raise ValueError(f"Truncated fixture queries: {source}")
    # Ensure at least one positive query even when all original queries miss the subset.
    first_point=points[:size]
    anchor=first_point if magic==b"SQUARE1\0" else bytes(16)
    target.write_bytes(header(max_points)+points+tail+first_point+anchor)
    return True


def admit(path, retry_path, run, record, previous=None, retry=None):
    row=previous
    if row is None:
        row=run(path,False)
        record(row)
    if row["status"]!="timeout":
        return row
    if retry is not None:
        return retry
    if bounded_fixture(path,retry_path):
        row=run(retry_path,True)
        record(row)
    return row
