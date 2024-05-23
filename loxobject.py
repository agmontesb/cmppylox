from _ctypes import Structure, sizeof, POINTER, pointer
from ctypes import c_int, c_char_p, cast


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
    ]


def allocateObject(size: int, _type: int) -> bytes:
    from vm import vm

    cobj = bytearray(b'\0' * size)
    lobj = LoxObj.from_buffer(cobj)
    lobj._type = _type
    lobj.next = vm.objects
    vm.objects = pointer(lobj)
    return cobj


def allocateString(chars: str, length: int) -> ObjString:
    lobj = allocateObject(sizeof(ObjString), ObjType.OBJ_STRING)
    string = ObjString.from_buffer_copy(lobj)
    string.length = length
    string.chars = c_char_p(chars.encode('utf-8') + b'\0')
    return string


def copyString(chars: str) -> ObjString:
    return allocateString(chars, len(chars))


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

