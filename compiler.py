from enum import Enum
from typing import Callable

from chunk import Chunk, OP_RETURN, OP_CONSTANT, addConstant, OP_NEGATE, OP_ADD, OP_SUBTRACT, OP_MULTIPLY, OP_DIVIDE, \
    write_code
from common import DEBUG_PRINT_CODE
from debug import disassembleChunk
from scanner import initScanner, scanToken, TokenType

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


def makeConstant(value: float):
    constant = addConstant(currentChunk(), value)
    if constant > 0xff:
        error("Too many constants in one chunk.")
        return 0
    return constant


def emitConstant(value: float):
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


def grouping():
    expression()
    consume(TokenType.TOKEN_RIGHT_PAREN, "Expect ')' after expression.")


def number():
    value = float(parser.previous.lexeme)
    emitConstant(value)


def unary():
    operatorType = parser.previous.token_type
    parsePrecedence(Precedence.PREC_UNARY)
    match operatorType:
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
rules[TokenType.TOKEN_STRING.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_IDENTIFIER.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_AND.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_CLASS.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_ELSE.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_FALSE.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_FOR.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_FUN.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_IF.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_NIL.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_OR.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_PRINT.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_RETURN.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_SUPER.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_THIS.value] = ParseRule(None, None, Precedence.PREC_NONE)
rules[TokenType.TOKEN_TRUE.value] = ParseRule(None, None, Precedence.PREC_NONE)
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

