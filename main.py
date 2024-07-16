import sys

from vm import initVm, freeVM, interpret

opCode = sys.modules['chunk']


def repl():
    while True:
        line = input("> ")
        if not line:
            print('')
            break
        interpret(line + '\n')


def readFile(path: str):
    try:
        with open(path, 'r') as file:
            source = file.read()
    except FileNotFoundError:
        print(f"Could not open file '{path}'.")
        exit(74)
    else:
        return source


def runFile(path: str):
    source = readFile(path)
    result = interpret(source)
    match result:
        case opCode.INTERPRET_OK:
            pass
        case opCode.INTERPRET_COMPILE_ERROR:
            exit(65)
        case opCode.INTERPRET_RUNTIME_ERROR:
            exit(70)


def main():
    initVm()

    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        runFile(sys.argv[1])
    else:
        print("Usage: clox [path]")
        exit(64)

    freeVM()


if __name__ == '__main__':
    main()