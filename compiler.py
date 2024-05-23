from _ctypes import POINTER, pointer
from ctypes import cast
from enum import Enum
from typing import Callable

from chunk import Chunk, OP_RETURN, OP_CONSTANT, addConstant, OP_NEGATE, OP_ADD, OP_SUBTRACT, OP_MULTIPLY, OP_DIVIDE, \
    write_code, OP_FALSE, OP_NIL, OP_TRUE, OP_NOT, OP_EQUAL, OP_GREATER, OP_LESS
from common import DEBUG_PRINT_CODE
from debug import disassembleChunk
from loxobject import copyString, LoxObj
from scanner import initScanner, scanToken, TokenType
from value import NUMBER_VAL, Value, OBJ_VAL


class Parser:

    def __init__(self):
        self.current = None
        self.previous = None
        self.hadError = False
        self.panicMode = False


class Precedence(Enum):
    PREC_NONE = 0
    PREC_ASSIGNMENT = 1     # =
    PREC_OR = 2             # or
    PREC_AND = 3            # and
    PREC_EQUALITY = 4       # == !=
    PREC_COMPARISON = 5     # < > <= >=
    PREC_TERM = 6           # + -
    PREC_FACTOR = 7         # * /
    PREC_UNARY = 8          # ! -
    PREC_CALL = 9           # . ()
    PREC_PRIMARY = 10


parseFn = Callable[[], None]


class ParseRule:
    def __init__(self, prefix: parseFn | None, infix: parseFn | None, precedence: Precedence):
        self.prefix = prefix
        self.infix = infix
        self.precedence = precedence


parser = Parser()

compilingChunk: Chunk | None = None


def currentChunk():
    return compilingChunk


def errorAt(token, message: str):
    if parser.panicMode:
        return
    parser.panicMode = True
    if token.token_type == TokenType.TOKEN_EOF:
        print(f"[line {token.line}] Error at end: {message}")
    else:
        print(f"[line {token.line}] Error at '{token.lexeme}': {message}")
    parser.hadError = True


def error(message: str):
    errorAt(parser.previous, message)


def errorAtCurrent(message: str):
    errorAt(parser.current, message)


def advance():
    parser.previous = parser.current

    while True:
        parser.current = scanToken()
        if parser.current.token_type != TokenType.TOKEN_ERROR:
            break
        errorAtCurrent(parser.current.lexeme)


def consume(token_type: TokenType, message: str):
    if parser.current.token_type == token_type:
        advance()
        return
    errorAtCurrent(message)


def emitByte(byte: int):
    write_code(currentChunk(), byte, parser.previous.line)


def emitBytes(byte1: int, byte2: int):
    emitByte(byte1)
    emitByte(byte2)


def emitReturn():
    emitByte(OP_RETURN)


def makeConstant(value: Value):
    constant = addConstant(currentChunk(), value)
    if constant > 0xff:
        error("Too many constants in one chunk.")
        return 0
    return constant


def emitConstant(value: Value):
    emitBytes(OP_CONSTANT, makeConstant(value))


def endCompiler():
    emitReturn()

    if DEBUG_PRINT_CODE:
        if not parser.hadError:
            disassembleChunk(currentChunk(), "code")


def binary():
    # Remember the operator.
    operatorType = parser.previous.token_type

    # Compile the right operand.
    rule = getRule(operatorType)
    parsePrecedence(Precedence(rule.precedence.value + 1))

    # Emit the operator instruction.
    match operatorType:
        case TokenType.TOKEN_BANG_EQUAL:
            emitBytes(OP_EQUAL, OP_NOT)
        case TokenType.TOKEN_EQUAL_EQUAL:
            emitByte(OP_EQUAL)
        case TokenType.TOKEN_GREATER:
            emitByte(OP_GREATER)
        case TokenType.TOKEN_GREATER_EQUAL:
            emitBytes(OP_LESS, OP_NOT)
        case TokenType.TOKEN_LESS:
            emitByte(OP_LESS)
        case TokenType.TOKEN_LESS_EQUAL:
            emitBytes(OP_GREATER, OP_NOT)
        case TokenType.TOKEN_PLUS:
            emitByte(OP_ADD)
        case TokenType.TOKEN_MINUS:
            emitByte(OP_SUBTRACT)
        case TokenType.TOKEN_STAR:
            emitByte(OP_MULTIPLY)
        case TokenType.TOKEN_SLASH:
            emitByte(OP_DIVIDE)
        case _: # Unreachable.
            pass


def literal():
    match parser.previous.token_type:
        case TokenType.TOKEN_FALSE:
            emitByte(OP_FALSE)
        case TokenType.TOKEN_NIL:
            emitByte(OP_NIL)
        case TokenType.TOKEN_TRUE:
            emitByte(OP_TRUE)
        case _:
            return


def grouping():
    expression()
    consume(TokenType.TOKEN_RIGHT_PAREN, "Expect ')' after expression.")


def number():
    value = float(parser.previous.lexeme)
    emitConstant(NUMBER_VAL(value))


def string():
    objstring = copyString(parser.previous.lexeme[1:-1])
    lobj = cast(pointer(objstring), POINTER(LoxObj)).contents
    return emitConstant(OBJ_VAL(lobj))


def unary():
    operatorType = parser.previous.token_type
    parsePrecedence(Precedence.PREC_UNARY)
    match operatorType:
        case TokenType.TOKEN_BANG:
            emitByte(OP_NOT)
        case TokenType.TOKEN_MINUS:
            emitByte(OP_NEGATE)
            return
        case _:
            return


max_value = max(x.value for x in TokenType) + 1
rules: list[ParseRule] = max_value * [None]
rules[TokenType.TOKEN_LEFT_PAREN.value] = ParseRule(grouping, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_RIGHT_PAREN.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_LEFT_BRACE.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_RIGHT_BRACE.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_COMMA.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_DOT.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_MINUS.value] = ParseRule(unary, binary, Precedence.PREC_TERM)
rules[TokenType.TOKEN_PLUS.value] = ParseRule(None, binary, Precedence.PREC_TERM)
rules[TokenType.TOKEN_SEMICOLON.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_SLASH.value] = ParseRule(None, binary, Precedence.PREC_FACTOR)
rules[TokenType.TOKEN_STAR.value] = ParseRule(None, binary, Precedence.PREC_FACTOR)
rules[TokenType.TOKEN_NUMBER.value] = ParseRule(number, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_STRING.value] = ParseRule(string, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_BANG.value] = ParseRule(unary, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_BANG_EQUAL.value] = ParseRule(None, binary, Precedence.PREC_EQUALITY)
rules[TokenType.TOKEN_EQUAL_EQUAL.value] = ParseRule(None, binary, Precedence.PREC_EQUALITY)
rules[TokenType.TOKEN_GREATER.value] = ParseRule(None, binary, Precedence.PREC_COMPARISON)
rules[TokenType.TOKEN_GREATER_EQUAL.value] = ParseRule(None, binary, Precedence.PREC_COMPARISON)
rules[TokenType.TOKEN_LESS.value] = ParseRule(None, binary, Precedence.PREC_COMPARISON)
rules[TokenType.TOKEN_LESS_EQUAL.value] = ParseRule(None, binary, Precedence.PREC_COMPARISON)
rules[TokenType.TOKEN_AND.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_CLASS.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_ELSE.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_FALSE.value] = ParseRule(literal, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_FOR.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_FUN.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_IF.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_NIL.value] = ParseRule(literal, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_OR.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_PRINT.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_RETURN.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_SUPER.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_THIS.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_TRUE.value] = ParseRule(literal, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_VAR.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_WHILE.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_ERROR.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_EOF.value] = ParseRule(None, None, Precedence.PREC_NONE)


def parsePrecedence(precedence: Precedence):
    advance()
    prefixrule = getRule(parser.previous.token_type).prefix
    if prefixrule is None:
        error("Expect expression.")
        return
    prefixrule()
    while precedence.value <= getRule(parser.current.token_type).precedence.value:
        advance()
        infixrule = getRule(parser.previous.token_type).infix
        infixrule()


def getRule(tokenType: TokenType) -> ParseRule:
    return rules[tokenType.value]


def expression():
    parsePrecedence(Precedence.PREC_ASSIGNMENT)
    pass


def lox_compile(source: str, chunk: Chunk) -> bool:
    global compilingChunk

    compilingChunk = chunk

    parser.hadError = False
    parser.panicMode = False

    initScanner(source)
    advance()
    expression()
    consume(TokenType.TOKEN_EOF, "Expect end of expression.")
    endCompiler()
    return not parser.hadError

