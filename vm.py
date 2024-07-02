import collections
import sys
from _ctypes import sizeof, pointer, POINTER
from ctypes import c_int, cast
from enum import Enum
import operator

from chunk import Chunk, init_chunk, free_chunk, opCode
from common import DEBUG_TRACE_EXECUTION
from compiler import lox_compile
from debug import disassembleInstruction
from loxobject import IS_STRING, AS_STRING, copyString, ObjType, ObjString, LoxObj
from table import Table, initTable, freeTable, tableSet, tableGet, tableDelete
from value import printValue, Value, IS_NUMBER, NUMBER_VAL, AS_NUMBER, NIL_VAL, BOOL_VAL, IS_NIL, IS_BOOL, AS_BOOL, \
    valuesEqual, OBJ_VAL

STACK_MAX = 256


class VM:

    def __init__(self):
        self.chunk = None
        self.stack = collections.deque([], maxlen=STACK_MAX)
        self._ip = 0
        self.objects = cast(None, POINTER(LoxObj))
        self.strings = Table()
        self.globals = Table()


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
    vm.objects = cast(None, POINTER(LoxObj))
    initTable(vm.globals)
    initTable(vm.strings)
    pass


def freeVM():
    freeTable(vm.globals)
    freeTable(vm.strings)
    freeObjects()


def freeObjects():
    lobj = vm.objects.contents
    while lobj:
        next = lobj.next.contents
        freeObj(lobj)
        lobj = next


def freeObj(lobj):
    match lobj._type:
        case ObjType.OBJ_STRING:
            string = cast(pointer(lobj), POINTER(ObjString)).contents
            del string



def resetStack():
    vm.stack.clear()


def runtimeError(format_str: str, *args):
    print(format_str.format(*args), end='')
    print(f" [line {vm.chunk.lines[vm.ip]}] in script")
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


def concatenate():
    b = AS_STRING(pop())
    a = AS_STRING(pop())
    chars = a.chars + b.chars
    string = copyString(chars.decode('utf-8'))
    lobj = cast(pointer(string), POINTER(LoxObj)).contents
    push(OBJ_VAL(lobj))


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

    def READ_STRING():
        return AS_STRING(read_constant())

    def read_byte():
        vm.chunk.code.setDataPosition(vm.ip)
        vm.ip += 1
        instruction = vm.chunk.code.readByte()
        try:
            return opCode(instruction)
        except:
            return None

    def read_constant():
        constant_pos = vm.chunk.code.readByte()
        vm.ip = vm.chunk.code.dataPosition()
        return vm.chunk.constants[constant_pos]

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
            case opCode.OP_POP:
                pop()
            case opCode.OP_GET_GLOBAL:
                name = READ_STRING()
                value = Value()
                if not tableGet(vm.globals, name, value):
                    runtimeError("Undefined variable '{}'.", name.chars)
                    return InterpretResult.INTERPRET_RUNTIME_ERROR
                push(value)
            case opCode.OP_DEFINE_GLOBAL:
                name = READ_STRING()
                tableSet(vm.globals, name, peek(0))
                pop()
            case opCode.OP_SET_GLOBAL:
                name = READ_STRING()
                if tableSet(vm.globals, name, peek(0)):
                    tableDelete(vm.globals, name)
                    runtimeError("Undefined variable '{}'.", name.chars.decode('utf-8'))
                    return InterpretResult.INTERPRET_RUNTIME_ERROR
            case opCode.OP_EQUAL:
                b = pop()
                a = pop()
                push(BOOL_VAL(valuesEqual(a, b)))
            case opCode.OP_GREATER:
                binary_op(BOOL_VAL, operator.gt)
            case opCode.OP_LESS:
                binary_op(BOOL_VAL, operator.lt)
            case opCode.OP_ADD:
                if IS_STRING(peek(0)) and IS_STRING(peek(1)):
                    concatenate()
                elif IS_NUMBER(peek(0)) and IS_NUMBER(peek(1)):
                    b = AS_NUMBER(pop())
                    a = AS_NUMBER(pop())
                    push(NUMBER_VAL(a + b))
                else:
                    runtimeError("Operands must be two numbers or two strings.")
                    return InterpretResult.INTERPRET_RUNTIME_ERROR
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
            case opCode.OP_PRINT:
                printValue(pop())
            case opCode.OP_RETURN:
                return InterpretResult.INTERPRET_OK
            case _:
                print("Unknown opcode")
                return InterpretResult.INTERPRET_RUNTIME_ERROR
        pass
    pass