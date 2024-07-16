from _ctypes import Structure
from ctypes import c_int
from enum import IntEnum


class TokenType(IntEnum):
    # Single-character tokens.
    TOKEN_LEFT_PAREN = 1
    TOKEN_RIGHT_PAREN = 2
    TOKEN_LEFT_BRACE = 3
    TOKEN_RIGHT_BRACE = 4
    TOKEN_COMMA = 5
    TOKEN_DOT = 6
    TOKEN_MINUS = 7
    TOKEN_PLUS = 8
    TOKEN_SEMICOLON = 9
    TOKEN_SLASH = 10
    TOKEN_STAR = 11

    # One or two character tokens.
    TOKEN_BANG = 12
    TOKEN_BANG_EQUAL = 13
    TOKEN_EQUAL = 14
    TOKEN_EQUAL_EQUAL = 15
    TOKEN_GREATER = 16
    TOKEN_GREATER_EQUAL = 17
    TOKEN_LESS = 18
    TOKEN_LESS_EQUAL = 19

    # Literals.
    TOKEN_IDENTIFIER = 20
    TOKEN_STRING = 21
    TOKEN_NUMBER = 22

    # Keywords.
    TOKEN_AND = 23
    TOKEN_CLASS = 24
    TOKEN_ELSE = 25
    TOKEN_FALSE = 26
    TOKEN_FUN = 27
    TOKEN_FOR = 28
    TOKEN_IF = 29
    TOKEN_NIL = 30
    TOKEN_OR = 31
    TOKEN_PRINT = 32
    TOKEN_RETURN = 33
    TOKEN_SUPER = 34
    TOKEN_THIS = 35
    TOKEN_TRUE = 36
    TOKEN_VAR = 37
    TOKEN_WHILE = 38

    TOKEN_ERROR = 39
    TOKEN_EOF = 40


class Token(Structure):
    _fields_ = [
        ('token_type_value', c_int),
        ('start', c_int),
        ('length', c_int),
        ('line', c_int)
    ]

    def __init__(self, token_type: TokenType, start: int, length: int, line: int):
        token_type_value = token_type.value
        super(Token, self).__init__(token_type_value, start, length, line)

    @property
    def token_type(self) -> TokenType:
        return TokenType(self.token_type_value)

    @token_type.setter
    def token_type(self, value: TokenType):
        self.token_type_value = value.value

    @property
    def lexeme(self):
        return scanner.source[self.start:self.start + self.length]

    @lexeme.deleter
    def lexeme(self):
        pass


class Scanner:
    def __init__(self, source: str = ''):
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1


scanner = Scanner()


def initScanner(source: str):
    scanner.source = source + '\0'
    scanner.start = 0
    scanner.current = 0
    scanner.line = 1


def isAlpha(c: str) -> bool:
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '_'


def isDigit(c: str) -> bool:
    return '0' <= c <= '9'


def isAtEnd() -> bool:
    pos = scanner.current
    return scanner.source[pos] == '\0'


def advance() -> str:
    scanner.current += 1
    return scanner.source[scanner.current - 1]


def peek() -> str:
    return scanner.source[scanner.current]


def peekNext() -> str:
    if isAtEnd():
        return '\0'
    return scanner.source[scanner.current + 1]


def match(expected: str) -> bool:
    if isAtEnd():
        return False
    if scanner.source[scanner.current] != expected:
        return False
    scanner.current += 1
    return True


def errorToken(message: str) -> Token:
    EToken = type('EToken', (Token,), {'lexeme': f'{message}'})
    token = EToken(
        TokenType.TOKEN_ERROR,
        0,
        len(message),
        scanner.line
    )
    return token


def skipWhitespace():
    while True:
        c = peek()
        if c in (' ', '\r', '\t'):
            advance()
        elif c == '\n':
            scanner.line += 1
            advance()
        elif c == '/':
            if peekNext() == '/':
                while peek() != '\n' and not isAtEnd():
                    advance()
            else:
                return
        else:
            return


def checkKeyword(start: int, length: int, rest: str, token_type: TokenType) -> TokenType:
    lexeme = scanner.source[scanner.start:scanner.current]
    if scanner.current - scanner.start == start + length and lexeme[start: start + length] == rest:
        return token_type
    return TokenType.TOKEN_IDENTIFIER


def identifierType() -> TokenType:
    match scanner.source[scanner.start]:
        case 'a': return checkKeyword(1, 2, "nd", TokenType.TOKEN_AND)
        case 'c': return checkKeyword(1, 4, "lass", TokenType.TOKEN_CLASS)
        case 'e': return checkKeyword(1, 3, "lse", TokenType.TOKEN_ELSE)
        case 'f':
            if scanner.current - scanner.start > 1:
                match scanner.source[scanner.start + 1]:
                    case 'a': return checkKeyword(2, 3, "lse", TokenType.TOKEN_FALSE)
                    case 'o': return checkKeyword(2, 1, "r", TokenType.TOKEN_FOR)
                    case 'u': return checkKeyword(2, 1, "n", TokenType.TOKEN_FUN)
        case 'i': return checkKeyword(1, 1, "f", TokenType.TOKEN_IF)
        case 'n': return checkKeyword(1, 2, "il", TokenType.TOKEN_NIL)
        case 'o': return checkKeyword(1, 1, "r", TokenType.TOKEN_OR)
        case 'p': return checkKeyword(1, 4, "rint", TokenType.TOKEN_PRINT)
        case 'r': return checkKeyword(1, 5, "eturn", TokenType.TOKEN_RETURN)
        case 's': return checkKeyword(1, 5, "uper", TokenType.TOKEN_SUPER)
        case 't':
            if scanner.current - scanner.start > 1:
                match scanner.source[scanner.start + 1]:
                    case 'h': return checkKeyword(2, 2, "is", TokenType.TOKEN_THIS)
                    case 'r': return checkKeyword(2, 2, "ue", TokenType.TOKEN_TRUE)
        case 'v': return checkKeyword(1, 2, "ar", TokenType.TOKEN_VAR)
        case 'w': return checkKeyword(1, 4, "hile", TokenType.TOKEN_WHILE)

    return TokenType.TOKEN_IDENTIFIER


def identifier() -> Token:
    while isAlpha(peek()) or isDigit(peek()):
        advance()

    return makeToken(identifierType())


def number() -> Token:
    while isDigit(peek()):
        advance()

    if peek() == '.' and isDigit(peekNext()):
        advance()
        while isDigit(peek()):
            advance()
    return makeToken(TokenType.TOKEN_NUMBER)


def string() -> Token:
    while peek() != '"' and not isAtEnd():
        if peek() == '\n':
            scanner.line += 1
        advance()

    if isAtEnd():
        return errorToken("Unterminated string.")

    advance()
    return makeToken(TokenType.TOKEN_STRING)


def makeToken(token_type: TokenType) -> Token:
    return Token(
        token_type,
        scanner.start,
        scanner.current - scanner.start,
        scanner.line
    )


def scanToken() -> Token:
    skipWhitespace()
    scanner.start = scanner.current

    if isAtEnd():
        return makeToken(TokenType.TOKEN_EOF)

    c = advance()
    if isAlpha(c): return identifier()
    if isDigit(c): return number()

    match c:
        case '(': return makeToken(TokenType.TOKEN_LEFT_PAREN)
        case ')': return makeToken(TokenType.TOKEN_RIGHT_PAREN)
        case '{': return makeToken(TokenType.TOKEN_LEFT_BRACE)
        case '}': return makeToken(TokenType.TOKEN_RIGHT_BRACE)
        case ';': return makeToken(TokenType. TOKEN_SEMICOLON)
        case ',': return makeToken(TokenType.TOKEN_COMMA)
        case '.': return makeToken(TokenType.TOKEN_DOT)
        case '-': return makeToken(TokenType.TOKEN_MINUS)
        case '+': return makeToken(TokenType.TOKEN_PLUS)
        case '/': return makeToken(TokenType.TOKEN_SLASH)
        case '*': return makeToken(TokenType.TOKEN_STAR)
        case '!':
            return makeToken(TokenType.TOKEN_BANG_EQUAL if match('=') else TokenType.TOKEN_BANG)
        case '=':
            return makeToken(TokenType.TOKEN_EQUAL_EQUAL if match('=') else TokenType.TOKEN_EQUAL)
        case '<':
            return makeToken(TokenType.TOKEN_LESS_EQUAL if match('=') else TokenType.TOKEN_LESS)
        case '>':
            return makeToken(TokenType.TOKEN_GREATER_EQUAL if match('=') else TokenType.TOKEN_GREATER)
        case '"': return string()

    return errorToken("Unexpected character.")


