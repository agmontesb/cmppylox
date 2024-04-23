from chunk import Chunk, init_chunk, write_code, free_chunk, addConstant
from chunk import OP_RETURN, OP_CONSTANT
from debug import disassembleChunk


def main():
    chunk = Chunk()
    init_chunk(chunk)

    constant = addConstant(chunk, 1.2)
    write_code(chunk, OP_CONSTANT, 123)
    write_code(chunk, constant, 123)

    write_code(chunk, OP_RETURN, 123)

    disassembleChunk(chunk, 'test_chunk')
    free_chunk(chunk)


if __name__ == '__main__':
    main()