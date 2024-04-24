import sys

from chunk import Chunk, init_chunk, write_code, free_chunk, addConstant
from debug import disassembleChunk
from vm import initVm, freeVM, interpret


opCode = sys.modules['chunk']


def main():
    initVm()

    chunk = Chunk()
    init_chunk(chunk)

    constant = addConstant(chunk, 1.2)
    write_code(chunk, opCode.OP_CONSTANT, 123)
    write_code(chunk, constant, 123)

    constant = addConstant(chunk, 3.4)
    write_code(chunk, opCode.OP_CONSTANT, 123)
    write_code(chunk, constant, 123)

    write_code(chunk, opCode.OP_ADD, 123)

    constant = addConstant(chunk, 5.6)
    write_code(chunk, opCode.OP_CONSTANT, 123)
    write_code(chunk, constant, 123)

    write_code(chunk, opCode.OP_DIVIDE, 123)
    write_code(chunk, opCode.OP_NEGATE, 123)

    write_code(chunk, opCode.OP_RETURN, 123)

    disassembleChunk(chunk, 'test_chunk')
    interpret(chunk)

    freeVM()
    free_chunk(chunk)


if __name__ == '__main__':
    main()