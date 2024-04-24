
from parcel import Parcel


# OpCode
OP_RETURN = 0x01
OP_CONSTANT = 0x02
OP_ADD = 0x03
OP_SUBTRACT = 0x04
OP_MULTIPLY = 0x05
OP_DIVIDE = 0x06
OP_NEGATE = 0x07


class Chunk:
    def __init__(self):
        self.code = None
        self.constants = None
        self.lines = None
    pass


def init_chunk(chunk):
    chunk.code = Parcel()
    chunk.constants = Parcel()
    chunk.lines = []


def free_chunk(chunk):
    chunk.code = None
    chunk.constants = None
    init_chunk(chunk)


def write_code(chunk: Chunk, byte: bytes, line: int):
    npos = chunk.code.dataPosition()
    chunk.code.writeByte(byte)
    if npos == len(chunk.lines):
        chunk.lines.append(line)
    else:
        chunk.lines[npos] = line


def addConstant(chunk, value):
    pos = chunk.constants.dataPosition()
    chunk.constants.writeDouble(1.0 * value)
    return pos
