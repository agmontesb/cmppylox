import collections
import sys
from enum import Enum
import operator

from chunk import Chunk, init_chunk, free_chunk
from common import DEBUG_TRACE_EXECUTION
from compiler import lox_compile
from debug import disassembleInstruction
from value import printValue

opCode = sys.modules['chunk']
STACK_MAX = 256


class VM:

    def __init__(self):
        self.chunk = None
        self.stack = collections.deque([], maxlen=STACK_MAX)
        self._ip = 0

    @property
    def ip(self):
        # return self.chunk.code.dataPosition()
        return self._ip

    @ip.setter
    def ip(self, value: int):
        # self.chunk.code.setDataPosition(value)
        self._ip = value


vm = VM()


class InterpretResult(Enum):
    INTERPRET_OK = 0
    INTERPRET_COMPILE_ERROR = 1
    INTERPRET_RUNTIME_ERROR = 2


def initVm():
    vm.stack.clear()
    pass


def freeVM():
    pass


def push(value):
    vm.stack.append(value)


def pop():
    return vm.stack.pop()


def interpret(source: str) -> InterpretResult:
    chunk = Chunk()
    init_chunk(chunk)

    if not lox_compile(source, chunk):
        free_chunk(chunk)
        return InterpretResult.INTERPRET_COMPILE_ERROR

    vm.chunk = chunk
    vm.ip = 0
    result: InterpretResult = run()

    free_chunk(chunk)
    return result


def run() -> InterpretResult:
    def read_byte():
        vm.chunk.code.setDataPosition(vm.ip)
        vm.ip += 1
        return vm.chunk.code.readByte()

    def read_constant():
        constant_offset = vm.chunk.code.readByte()
        vm.ip = vm.chunk.code.dataPosition()
        vm.chunk.constants.setDataPosition(constant_offset)
        return vm.chunk.constants.readDouble()

    def binary_op(op):
        b = pop()
        a = pop()
        push(op(a, b))


    while True:
        if DEBUG_TRACE_EXECUTION:
            print("          ")
            if not vm.stack:
                print("[]")
            for x in vm.stack:
                print("[ ", end="")
                printValue(x, end="")
                print(" ]")
            disassembleInstruction(vm.chunk, vm.ip)
        instruction = read_byte()
        match instruction:
            case opCode.OP_CONSTANT:
                constant = read_constant()
                push(constant)
            case opCode.OP_ADD:
                binary_op(operator.add)
            case opCode.OP_SUBTRACT:
                binary_op(operator.sub)
            case opCode.OP_MULTIPLY:
                binary_op(operator.mul)
            case opCode.OP_DIVIDE:
                binary_op(operator.truediv)
            case opCode.OP_NEGATE:
                push(-pop())
            case opCode.OP_RETURN:
                printValue(pop())
                return InterpretResult.INTERPRET_OK
            case _:
                print("Unknown opcode")
                return InterpretResult.INTERPRET_RUNTIME_ERROR
        pass
    pass