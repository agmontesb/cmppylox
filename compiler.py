from scanner import initScanner, scanToken, TokenType


def lox_compile(source: str):
    initScanner(source)
    line = -1
    while True:
        token = scanToken()
        if token.line != line:
            print(f"{token.line:4d} ", end='')
            line = token.line
        else:
            print("   | ", end='')
        print(f"{token.token_type.value:2d} {token.token_type.name:20s} '{token.lexeme}'")
        if token.token_type == TokenType.TOKEN_EOF:
            break
        pass

