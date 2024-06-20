from _ctypes import Structure, sizeof, POINTER, pointer
from ctypes import c_int, c_char_p, cast, c_uint32


class ObjType(c_int):
    OBJ_STRING = 0x0001
    # OBJ_FUNCTION = 0x0002
    # OBJ_NATIVE = 0x0003
    # OBJ_CLOSURE = 0x0004
    # OBJ_UPVALUE = 0x0005
    # OBJ_CLASS = 0x0006
    # OBJ_INSTANCE = 0x0007
    # OBJ_BOUND_METHOD = 0x0008


class LoxObj(Structure):
    pass


LoxObj._fields_ = [
        ("_type", c_int),
        ("next", POINTER(LoxObj)),
    ]


class ObjString(Structure):
    _fields_ = [
        ("obj", LoxObj),
        ("length", c_int),
        ("chars", c_char_p),
        ("hash", c_uint32),
    ]


def allocateObject(size: int, _type: int) -> bytes:
    cobj = bytearray(b'\0' * size)
    lobj = LoxObj.from_buffer(cobj)
    lobj._type = _type

    try:
        from vm import vm
    except ImportError:
        lobj.next = cast(None, POINTER(LoxObj))
    else:
        lobj.next = vm.objects
        vm.objects = pointer(lobj)
    return cobj


def allocateString(chars: str, length: int, hash: int) -> ObjString:
    from vm import vm
    from table import tableSet
    from value import NIL_VAL

    lobj = allocateObject(sizeof(ObjString), ObjType.OBJ_STRING)
    string = ObjString.from_buffer_copy(lobj)
    string.length = length
    string.chars = c_char_p(chars.encode('utf-8') + b'\0')
    string.hash = hash
    tableSet(vm.strings, string, NIL_VAL())
    return string


def takeString(chars: str, length: int) -> ObjString:
    from table import tableFindString
    from vm import vm

    hash = hashString(chars, length)
    interned = tableFindString(vm.strings, chars, length, hash)
    if interned is not None:
        return interned
    return allocateString(chars, length, hash)


def hashString(chars: str, length: int) -> int:
    key = chars.encode('utf-8')
    hash = c_uint32(2166136261)
    for i in range(length):
        hash.value ^= key[i]
        hash.value *= 16777619
    return hash.value


def copyString(chars: str) -> ObjString:
    from vm import vm
    from table import tableFindString

    length = len(chars)
    hash = hashString(chars, length)
    interned = tableFindString(vm.strings, chars, length, hash)
    if interned:
        return interned
    return allocateString(chars, length, hash)


def printObject(value: 'Value', end='\n'):
    match OBJ_TYPE(value):
        case ObjType.OBJ_STRING:
            print(f"{AS_CSTRING(value)}", end=end)
        case _:
            print("Unknown object type", end=end)


def isObjType(value: 'Value', vtype: ObjType) -> bool:
    from value import AS_OBJ, IS_OBJ
    return IS_OBJ(value) and AS_OBJ(value)._type == vtype


def OBJ_TYPE(value: 'Value') -> ObjType:
    from value import AS_OBJ
    return AS_OBJ(value)._type


def IS_STRING(value: 'Value') -> bool:
    return isObjType(value, ObjType.OBJ_STRING)


def AS_STRING(value: 'Value') -> ObjString:
    from value import AS_OBJ
    lobj = AS_OBJ(value)
    return cast(pointer(lobj), POINTER(ObjString)).contents


def AS_CSTRING(value: 'Value') -> str:
    return AS_STRING(value).chars.decode('utf-8')

