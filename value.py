from _ctypes import Structure, Union, sizeof
from ctypes import c_double, c_bool, c_int
from enum import Enum


class ValueType(Structure):
    VAL_BOOL = 0x0001
    VAL_NIL = 0x0001
    VAL_NUMBER = 0x0002
    # VAL_OBJ = 3


class Value(Structure):
    _fields_ = [
        ("_type", c_int),
        ('padding', c_int),
        ("_as", type('_As', (Union,), {'_fields_': [('boolean', c_bool), ('number', c_double),]})),
    ]

    def writeToParcel(self, dest, flags):
        """
        Flatten this object in to a Parcel.
        :param dest: Parcel: The Parcel in which the object should be written.
        :param flags: int: Additional flags about how the object should be
        written. May be 0 or Parcelable.PARCELABLE_WRITE_RETURN_VALUE.
        """
        dest.writeInt(self._type)
        dest.writeInt(self.padding)
        dest.writeDouble(self._as.number)

    def createFromParcel(self, source):
        """
        Read and return a new object from the parcel at the current dataPosition.
        :param source: Parcel: The Parcel to read the object's data from.
        """
        self._type = source.readInt()
        self.padding = source.readInt()
        self._as.number = source.readDouble()
        return self



def IS_BOOL(value: Value) -> bool:
    return value._type == ValueType.VAL_BOOL


def IS_NIL(value: Value) -> bool:
    return value._type == ValueType.VAL_NIL


def IS_NUMBER(value: Value) -> bool:
    return value._type == ValueType.VAL_NUMBER


def AS_BOOL(value: Value) -> bool:
    return value._as.boolean


def AS_NUMBER(value: Value) -> float:
    return value._as.number


def BOOL_VAL(value: bool) -> Value:
    val = Value()
    val._type = ValueType.VAL_BOOL
    val._as.boolean = value
    return val


def NIL_VAL() -> Value:
    val = Value()
    val._type = ValueType.VAL_NIL
    val._as.number = 0
    return val


def NUMBER_VAL(value: float) -> Value:
    val = Value()
    val._type = ValueType.VAL_NUMBER
    val._as.number = value
    return val


def printValue(value: Value, end='\n'):
    if IS_BOOL(value):
        print('true' if AS_BOOL(value) else 'false', end=end)
    elif IS_NIL(value):
        print('nil', end=end)
    elif IS_NUMBER(value):
        print(f"'{AS_NUMBER(value)}'", end=end)


def valuesEqual(a: Value, b: Value) -> bool:
    if a._type != b._type:
        return False
    if IS_BOOL(a):
        return AS_BOOL(a) == AS_BOOL(b)
    if IS_NIL(a):
        return True
    if IS_NUMBER(a):
        return AS_NUMBER(a) == AS_NUMBER(b)
    return False


