import sys
from _ctypes import POINTER, pointer, Structure
from ctypes import cast
from enum import Enum
from functools import total_ordering
from typing import Callable

from chunk import Chunk, addConstant, write_code, opCode
from common import DEBUG_PRINT_CODE, UINT8_COUNT
from debug import disassembleChunk
from loxobject import copyString, LoxObj
from scanner import initScanner, scanToken, TokenType, Token
from value import NUMBER_VAL, Value, OBJ_VAL


class Parser:

    def __init__(self):
        self.current = None
        self.previous = None
        self.hadError = False
        self.panicMode = False

@total_ordering
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

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value


parseFn = Callable[[bool], None]


class ParseRule:
    def __init__(self, prefix: parseFn | None, infix: parseFn | None, precedence: Precedence):
        self.prefix = prefix
        self.infix = infix
        self.precedence = precedence


class Local(Structure):
    _fields_ = [
        ("name", Token),
        ("depth", int),
    ]


class Compiler(Structure):
    _fields_ = [
        ("locals", (Local * UINT8_COUNT)()),
        ("localCount", int),
        ("scopeDepth", int),
    ]



parser = Parser()

current: Compiler | None = None

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


def check(token_type: TokenType):
    return parser.current.token_type == token_type


def match(token_type: TokenType):
    if not check(token_type):
        return False
    advance()
    return True


def emitByte(byte: int | opCode):
    try:
        int_byte = byte.value
    except AttributeError:
        int_byte = byte
    write_code(currentChunk(), int_byte, parser.previous.line)


def emitBytes(byte1: int | opCode, byte2: int | opCode):
    emitByte(byte1)
    emitByte(byte2)


def emitReturn():
    emitByte(opCode.OP_RETURN)


def makeConstant(value: Value):
    constant = addConstant(currentChunk(), value)
    if constant > 0xff:
        error("Too many constants in one chunk.")
        return 0
    return constant


def emitConstant(value: Value):
    emitBytes(opCode.OP_CONSTANT, makeConstant(value))


def initCompiler(compiler: Compiler):
    global current
    compiler.localCount = 0
    compiler.scopeDepth = 0
    current = compiler


def endCompiler():
    emitReturn()

    if DEBUG_PRINT_CODE:
        if not parser.hadError:
            disassembleChunk(currentChunk(), "code")


def beginScope():
    current.scopeDepth += 1


def endScope():
    current.scopeDepth -= 1
    while current.localCount > 0 and current.locals[current.localCount - 1].depth > current.scopeDepth:
        emitByte(opCode.OP_POP)
        current.localCount -= 1


def binary(canAssign: bool):
    # Remember the operator.
    operatorType = parser.previous.token_type

    # Compile the right operand.
    rule = getRule(operatorType)
    parsePrecedence(Precedence(rule.precedence.value + 1))

    # Emit the operator instruction.
    match operatorType:
        case TokenType.TOKEN_BANG_EQUAL:
            emitBytes(opCode.OP_EQUAL, opCode.OP_NOT)
        case TokenType.TOKEN_EQUAL_EQUAL:
            emitByte(opCode.OP_EQUAL)
        case TokenType.TOKEN_GREATER:
            emitByte(opCode.OP_GREATER)
        case TokenType.TOKEN_GREATER_EQUAL:
            emitBytes(opCode.OP_LESS, opCode.OP_NOT)
        case TokenType.TOKEN_LESS:
            emitByte(opCode.OP_LESS)
        case TokenType.TOKEN_LESS_EQUAL:
            emitBytes(opCode.OP_GREATER, opCode.OP_NOT)
        case TokenType.TOKEN_PLUS:
            emitByte(opCode.OP_ADD)
        case TokenType.TOKEN_MINUS:
            emitByte(opCode.OP_SUBTRACT)
        case TokenType.TOKEN_STAR:
            emitByte(opCode.OP_MULTIPLY)
        case TokenType.TOKEN_SLASH:
            emitByte(opCode.OP_DIVIDE)
        case _: # Unreachable.
            pass


def literal(canAssign: bool):
    match parser.previous.token_type:
        case TokenType.TOKEN_FALSE:
            emitByte(opCode.OP_FALSE)
        case TokenType.TOKEN_NIL:
            emitByte(opCode.OP_NIL)
        case TokenType.TOKEN_TRUE:
            emitByte(opCode.OP_TRUE)
        case _:
            return


def grouping(canAssign: bool):
    expression()
    consume(TokenType.TOKEN_RIGHT_PAREN, "Expect ')' after expression.")


def number(canAssign: bool):
    value = float(parser.previous.lexeme)
    emitConstant(NUMBER_VAL(value))


def string(canAssign: bool):
    objstring = copyString(parser.previous.lexeme[1:-1])
    lobj = cast(pointer(objstring), POINTER(LoxObj)).contents
    return emitConstant(OBJ_VAL(lobj))


def namedVariable(name: Token, canAssign: bool):
    arg = resolveLocal(current, name)
    if arg != -1:
        getOp, setOp = opCode.OP_GET_LOCAL, opCode.OP_SET_LOCAL
    else:
        arg = identifierConstant(name)
        getOp, setOp = opCode.OP_GET_GLOBAL, opCode.OP_SET_GLOBAL
    if canAssign and match(TokenType.TOKEN_EQUAL):
        expression()
        emitBytes(setOp, arg)
    else:
        emitBytes(getOp, arg)


def variable(canAssign: bool):
    namedVariable(parser.previous, canAssign)


def unary(canAssign: bool):
    operatorType = parser.previous.token_type
    parsePrecedence(Precedence.PREC_UNARY)
    match operatorType:
        case TokenType.TOKEN_BANG:
            emitByte(opCode.OP_NOT)
        case TokenType.TOKEN_MINUS:
            emitByte(opCode.OP_NEGATE)
            return
        case _:
            return


rules: dict[TokenType, ParseRule] = {
    TokenType.TOKEN_LEFT_PAREN: ParseRule(grouping, None, Precedence.PREC_NONE),
    TokenType.TOKEN_RIGHT_PAREN: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_LEFT_BRACE: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_RIGHT_BRACE: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_COMMA: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_DOT: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_MINUS: ParseRule(unary, binary, Precedence.PREC_TERM),
    TokenType.TOKEN_PLUS: ParseRule(None, binary, Precedence.PREC_TERM),
    TokenType.TOKEN_SEMICOLON: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_SLASH: ParseRule(None, binary, Precedence.PREC_FACTOR),
    TokenType.TOKEN_STAR: ParseRule(None, binary, Precedence.PREC_FACTOR),
    TokenType.TOKEN_NUMBER: ParseRule(number, None, Precedence.PREC_NONE),
    TokenType.TOKEN_IDENTIFIER: ParseRule(variable, None, Precedence.PREC_NONE),
    TokenType.TOKEN_STRING: ParseRule(string, None, Precedence.PREC_NONE),
    TokenType.TOKEN_BANG: ParseRule(unary, None, Precedence.PREC_NONE),
    TokenType.TOKEN_BANG_EQUAL: ParseRule(None, binary, Precedence.PREC_EQUALITY),
    TokenType.TOKEN_EQUAL: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_EQUAL_EQUAL: ParseRule(None, binary, Precedence.PREC_EQUALITY),
    TokenType.TOKEN_GREATER: ParseRule(None, binary, Precedence.PREC_COMPARISON),
    TokenType.TOKEN_GREATER_EQUAL: ParseRule(None, binary, Precedence.PREC_COMPARISON),
    TokenType.TOKEN_LESS: ParseRule(None, binary, Precedence.PREC_COMPARISON),
    TokenType.TOKEN_LESS_EQUAL: ParseRule(None, binary, Precedence.PREC_COMPARISON),
    TokenType.TOKEN_AND: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_CLASS: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_ELSE: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_FALSE: ParseRule(literal, None, Precedence.PREC_NONE),
    TokenType.TOKEN_FOR: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_FUN: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_IF: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_NIL: ParseRule(literal, None, Precedence.PREC_NONE),
    TokenType.TOKEN_OR: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_PRINT: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_RETURN: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_SUPER: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_THIS: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_TRUE: ParseRule(literal, None, Precedence.PREC_NONE),
    TokenType.TOKEN_VAR: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_WHILE: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_ERROR: ParseRule(None, None, Precedence.PREC_NONE),
    TokenType.TOKEN_EOF: ParseRule(None, None, Precedence.PREC_NONE)
}


def parsePrecedence(precedence: Precedence):
    advance()
    prefixrule = getRule(parser.previous.token_type).prefix
    if prefixrule is None:
        error("Expect expression.")
        return
    canAssign = precedence <= Precedence.PREC_ASSIGNMENT
    prefixrule(canAssign)
    while precedence <= getRule(parser.current.token_type).precedence:
        advance()
        infixrule = getRule(parser.previous.token_type).infix
        infixrule(canAssign)
    if canAssign and match(TokenType.TOKEN_EQUAL):
        error("Invalid assignment target.")


def identifierConstant(name: Token) -> int:
    return makeConstant(
        OBJ_VAL(
            cast(pointer(
                copyString(name.lexeme)), POINTER(LoxObj)
            ).contents
        )
    )


def identifierEqual(a: Token, b: Token) -> bool:
    if a.length != b.length:
        return False
    return a.lexeme == b.lexeme


def resolveLocal(compiler: Compiler, name: Token) -> int:
    for i in range(compiler.localCount - 1, -1, -1):
        local = compiler.locals[i]
        if identifierEqual(name, local.name):
            if local.depth == -1:
                error("Cannot read local variable in its own initializer.")
            return i
    return -1


def addLocal(name: Token):
    if current.localCount == UINT8_COUNT:
        error("Too many local variables in function.")
        return
    local = current.locals[current.localCount]
    local.name = name
    local.depth = -1
    current.localCount += 1


def declareVariable():
    if current.scopeDepth == 0:
        return
    name = parser.previous
    for i in range(current.localCount - 1, -1, -1):
        local = current.locals[i]
        if local.depth != -1 and local.depth < current.scopeDepth:
            break
        if identifierEqual(name, local.name):
            error("Variable with this name already declared in this scope.")
    addLocal(name)


def parseVariable(error_message: str) -> int:
    consume(TokenType.TOKEN_IDENTIFIER, error_message)
    declareVariable()
    if current.scopeDepth > 0:
        return 0
    return identifierConstant(parser.previous)


def getRule(tokenType: TokenType) -> ParseRule:
    return rules[tokenType]


def expression():
    parsePrecedence(Precedence.PREC_ASSIGNMENT)
    pass


def block():
    while not check(TokenType.TOKEN_RIGHT_BRACE) and not check(TokenType.TOKEN_EOF):
        declaration()
    consume(TokenType.TOKEN_RIGHT_BRACE, "Expect '}' after block.")


def markInitialized():
    current.locals[current.localCount - 1].depth = current.scopeDepth


def defineVariable(lox_global: int):
    if current.scopeDepth > 0:
        markInitialized()
        return
    emitBytes(opCode.OP_DEFINE_GLOBAL, lox_global)


def varDeclaration():
    lox_global = parseVariable("Expect variable name.")
    if match(TokenType.TOKEN_EQUAL):
        expression()
    else:
        emitByte(opCode.OP_NIL)
    consume(TokenType.TOKEN_SEMICOLON, "Expect ';' after variable declaration.")
    defineVariable(lox_global)


def expressionStatement():
    expression()
    consume(TokenType.TOKEN_SEMICOLON, "Expect ';' after expression.")
    emitByte(opCode.OP_POP)


def printStatement():
    expression()
    consume(TokenType.TOKEN_SEMICOLON, "Expect ';' after value.")
    emitByte(opCode.OP_PRINT)


def synchronize():
    parser.panicMode = False
    while parser.current.token_type != TokenType.TOKEN_EOF:
        if parser.previous.token_type == TokenType.TOKEN_SEMICOLON:
            return

        match parser.current.token_type:
            case (TokenType.TOKEN_CLASS,
                  TokenType.TOKEN_FUN,
                  TokenType.TOKEN_VAR,
                  TokenType.TOKEN_FOR,
                  TokenType.TOKEN_IF,
                  TokenType.TOKEN_WHILE,
                  TokenType.TOKEN_PRINT,
                  TokenType.TOKEN_RETURN):
                return

        advance()


def declaration():
    if match(TokenType.TOKEN_VAR):
        varDeclaration()
    else:
        statement()


def statement():
    if match(TokenType.TOKEN_PRINT):
        printStatement()
    elif match(TokenType.TOKEN_LEFT_BRACE):
        beginScope()
        block()
        endScope()
    else:
        expressionStatement()


def lox_compile(source: str, chunk: Chunk) -> bool:
    global compilingChunk

    parser.hadError = False
    parser.panicMode = False

    initScanner(source)
    compiler = Compiler()
    initCompiler(compiler)
    compilingChunk = chunk

    advance()

    while not match(TokenType.TOKEN_EOF):
        declaration()
        if parser.panicMode:
            synchronize()

    endCompiler()
    return not parser.hadError

