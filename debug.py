import sys

from chunk import Chunk
from value import printValue

opCode = sys.modules['chunk']


def disassembleChunk(chunk: Chunk, name: str):
    print(f"== {name} ==")
    offset = 0
    while offset < chunk.code.dataSize():
        offset = disassembleInstruction(chunk, offset)
    pass


def disassembleInstruction(chunk: Chunk, offset: int):
    print(f"{offset:04d} ", end="")

    chunk.code.setDataPosition(offset)
    if offset > 0 and chunk.lines[offset] == chunk.lines[offset - 1]:
        print("   | ", end="")
    else:
        print(f"{chunk.lines[offset]:04d} ", end="")

    instruction = chunk.code.readByte()
    
    match instruction:
        case opCode.OP_CONSTANT:
            return constantInstruction("OP_CONSTANT", chunk, offset)
        case opCode.OP_RETURN:
            return simpleInstruction("OP_RETURN", offset)
        case _:
            print("Unknown opcode")
            return offset + 1


def constantInstruction(name: str, chunk: Chunk, offset: int):
    constant_offset = chunk.code.readByte()
    chunk.constants.setDataPosition(constant_offset)
    constant = constant_offset // 8
    print(f"{name} {constant} ", end="")
    printValue(chunk.constants.readDouble())
    return offset + 2

def simpleInstruction(name: str, offset: int):
    print(name)
    return offset + 1
    pass
