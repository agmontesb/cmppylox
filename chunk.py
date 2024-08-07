from enum import Enum

from parcel import Parcel

class opCode(Enum):
    OP_RETURN = 0x01
    OP_CONSTANT = 0x02
    OP_NIL = 0x08
    OP_TRUE = 0x09
    OP_FALSE = 0x0A
    OP_EQUAL = 0x0C
    OP_GREATER = 0x0D
    OP_LESS = 0x0E
    OP_ADD = 0x03
    OP_SUBTRACT = 0x04
    OP_MULTIPLY = 0x05
    OP_DIVIDE = 0x06
    OP_NOT = 0x0B
    OP_NEGATE = 0x07
    OP_PRINT = 0x0F
    OP_POP = 0x10
    OP_DEFINE_GLOBAL = 0x11
    OP_GET_LOCAL = 0x14
    OP_GET_GLOBAL = 0x12
    OP_SET_LOCAL = 0x15
    OP_SET_GLOBAL = 0x13
    OP_JUMP = 0x17
    OP_JUMP_IF_FALSE = 0x16
    OP_LOOP = 0x18


class Chunk:
    def __init__(self):
        self.code = None
        self.constants = None
        self.lines = None
    pass


def init_chunk(chunk):
    chunk.code = Parcel()
    chunk.constants = []
    chunk.lines = []


def free_chunk(chunk):
    chunk.code = None
    chunk.constants = None
    init_chunk(chunk)


def write_code(chunk: Chunk, byte: int, line: int):
    npos = chunk.code.dataPosition()
    chunk.code.writeByte(byte)
    if npos == len(chunk.lines):
        chunk.lines.append(line)
    else:
        chunk.lines[npos] = line


def addConstant(chunk, value):
    pos = len(chunk.constants)
    chunk.constants.append(value)
    return pos
