"""Reader for the witness-timestream .bin files written for the CUORE vibrational tests.

Format first inferred from the bytes (2026-10-31, orchestrator), then confirmed field-for-field
against Vivek's writer, ~/WriteContinuousDataToBinary.cpp (struct ContinuousBinaryHeader, packed).
Little-endian throughout:

    offset  type       meaning
    0       char[4]    magic "VCTS"
    4       uint32     version, reserved, written as 0
    8       int32      run number
    12      int32      DAQ channel number
    16      float64    t_start_sec, the requested start (0.0 in every file seen)
    24      float64    t_end_requested_sec, -1.0 = "through the natural end of the run"
    32      float64    sample_rate_hz             (1000.0, hard-coded in the writer)
    40      uint64     n_samples
    48      int32[n]   samples, raw ADC counts (the RDCF QVectorI integer type)

ADC counts are converted to mV with the factor used by $VIBES
(WriteTimestreamsFromDAQ.cpp): 8.0108642578125e-02 mV/count.
"""
import struct
import numpy as np

ADC2MV = 8.0108642578125e-02
HEADER = 48


def read_header(path):
    with open(path, "rb") as fh:
        b = fh.read(HEADER)
    magic, ver, run, ch, t0, tend, rate, n = struct.unpack("<4sIiidddQ", b)
    if magic != b"VCTS":
        raise ValueError(f"{path}: magic {magic!r}, expected b'VCTS'")
    return dict(magic=magic.decode(), version=ver, run=run, channel=ch,
                t0=t0, tend=tend, rate=rate, n_samples=n)


def read(path, mv=True):
    """(header, samples). Samples in mV if mv else raw ADC counts (int32)."""
    h = read_header(path)
    x = np.fromfile(path, dtype="<i4", offset=HEADER)
    if len(x) != h["n_samples"]:
        raise ValueError(f"{path}: header says {h['n_samples']} samples, file holds {len(x)}")
    return h, (x * ADC2MV if mv else x)
