import collections
import sys
from _ctypes import sizeof
from ctypes import c_int
from enum import Enum
import operator

from chunk import Chunk, init_chunk, free_chunk
from common import DEBUG_TRACE_EXECUTION
from compiler import lox_compile
from debug import disassembleInstruction
from value import printValue, Value, IS_NUMBER, NUMBER_VAL, AS_NUMBER, NIL_VAL, BOOL_VAL, IS_NIL, IS_BOOL, AS_BOOL, \
    valuesEqual

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


def resetStack():
    vm.stack.clear()


def runtimeError(format_str: str, *args):
    print(format_str.format(*args))
    print(f"[line {vm.chunk.lines[vm.ip]}] in script")
    resetStack()
    return InterpretResult.INTERPRET_RUNTIME_ERROR


def push(value):
    vm.stack.append(value)


def pop():
    return vm.stack.pop()


def peek(distance: int):
    return vm.stack[-1 - distance]


def isFalsey(value):
    return IS_NIL(value) or (IS_BOOL(value) and not AS_BOOL(value))


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
        value_size = sizeof(c_int) + sizeof(Value)
        constant_offset = value_size * vm.chunk.code.readByte()
        vm.ip = vm.chunk.code.dataPosition()
        vm.chunk.constants.setDataPosition(constant_offset)
        return vm.chunk.constants.readTypedObject(Value())

    def binary_op(value_type, op):
        if not IS_NUMBER(peek(0)) or not IS_NUMBER(peek(1)):
            runtimeError("Operands must be numbers.")
            return InterpretResult.INTERPRET_RUNTIME_ERROR
        b = AS_NUMBER(pop())
        a = AS_NUMBER(pop())
        push(value_type(op(a, b)))


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
            case opCode.OP_NIL:
                push(NIL_VAL())
            case opCode.OP_TRUE:
                push(BOOL_VAL(True))
            case opCode.OP_FALSE:
                push(BOOL_VAL(False))
            case opCode.OP_EQUAL:
                b = pop()
                a = pop()
                push(BOOL_VAL(valuesEqual(a, b)))
            case opCode.OP_GREATER:
                binary_op(BOOL_VAL, operator.gt)
            case opCode.OP_LESS:
                binary_op(BOOL_VAL, operator.lt)
            case opCode.OP_ADD:
                binary_op(NUMBER_VAL, operator.add)
            case opCode.OP_SUBTRACT:
                binary_op(NUMBER_VAL, operator.sub)
            case opCode.OP_MULTIPLY:
                binary_op(NUMBER_VAL, operator.mul)
            case opCode.OP_DIVIDE:
                binary_op(NUMBER_VAL, operator.truediv)
            case opCode.OP_NOT:
                push(BOOL_VAL(isFalsey(pop())))
            case opCode.OP_NEGATE:
                if not IS_NUMBER(peek(0)):
                    runtimeError("Operand must be a number.")
                    return InterpretResult.INTERPRET_RUNTIME_ERROR
                push(NUMBER_VAL(-AS_NUMBER(pop())))
            case opCode.OP_RETURN:
                printValue(pop())
                return InterpretResult.INTERPRET_OK
            case _:
                print("Unknown opcode")
                return InterpretResult.INTERPRET_RUNTIME_ERROR
        pass
    pass