import sys

from chunk import Chunk, opCode
from value import printValue


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

    instrution = chunk.code.readByte()
    try:
        opcode = opCode(instrution)
    except:
        opcode = None
    
    match opcode:
        case opCode.OP_ADD:
            return simpleInstruction("OP_ADD", offset)
        case opCode.OP_SUBTRACT:
            return simpleInstruction("OP_SUBTRACT", offset)
        case opCode.OP_MULTIPLY:
            return simpleInstruction("OP_MULTIPLY", offset)
        case opCode.OP_DIVIDE:
            return simpleInstruction("OP_DIVIDE", offset)
        case opCode.OP_NOT:
            return simpleInstruction("OP_NOT", offset)
        case opCode.OP_NEGATE:
            return simpleInstruction("OP_NEGATE", offset)
        case opCode.OP_CONSTANT:
            return constantInstruction("OP_CONSTANT", chunk, offset)
        case opCode.OP_NIL:
            return simpleInstruction("OP_NIL", offset)
        case opCode.OP_TRUE:
            return simpleInstruction("OP_TRUE", offset)
        case opCode.OP_FALSE:
            return simpleInstruction("OP_FALSE", offset)
        case opCode.OP_POP:
            return simpleInstruction("OP_POP", offset)
        case opCode.OP_GET_GLOBAL:
            return constantInstruction("OP_GET_GLOBAL", chunk, offset)
        case opCode.OP_DEFINE_GLOBAL:
            return constantInstruction("OP_DEFINE_GLOBAL", chunk, offset)
        case opCode.OP_SET_GLOBAL:
            return constantInstruction("OP_SET_GLOBAL", chunk, offset)
        case opCode.OP_EQUAL:
            return simpleInstruction("OP_EQUAL", offset)
        case opCode.OP_GREATER:
            return simpleInstruction("OP_GREATER", offset)
        case opCode.OP_LESS:
            return simpleInstruction("OP_LESS", offset)
        case opCode.OP_PRINT:
            return simpleInstruction("OP_PRINT", offset)
        case opCode.OP_RETURN:
            return simpleInstruction("OP_RETURN", offset)
        case _:
            print("Unknown opcode")
            return offset + 1


def constantInstruction(name: str, chunk: Chunk, offset: int):
    constant_pos = chunk.code.readByte()
    print(f"{name} {constant_pos} ", end="")
    value = chunk.constants[constant_pos]
    printValue(value)
    return offset + 2

def simpleInstruction(name: str, offset: int):
    print(name)
    return offset + 1
    pass
