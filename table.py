from _ctypes import Structure, POINTER, pointer, sizeof
from ctypes import c_int, cast, memmove

from loxobject import ObjString
from value import Value, NIL_VAL, BOOL_VAL, IS_NIL

TABLE_MAX_LOAD = 0.75


class Entry(Structure):
    _fields_ = [
        ("key", POINTER(ObjString)),
        ("value", Value),
    ]


class Table(Structure):
    _fields_ = [
        ("count", c_int),
        ("capacity", c_int),
        ("entries", POINTER(Entry)),
    ]


def initTable(table: Table):
    table.count = 0
    table.capacity = 0
    table.entries = None


def freeTable(table: Table):
    del table.entries.contents
    initTable(table)


def tableGet(table: Table, key: ObjString, value: Value) -> bool:
    if table.count == 0:
        return False

    entry = findEntry(table.entries, table.capacity, key)
    if entry.key is None:
        return False

    memmove(pointer(value), pointer(entry.value), sizeof(Value))
    # value._type = entry.value._type
    # value._as.loxobj = entry.value._as.loxobj
    return True


def findEntry(entries: Entry, capacity: int, key: ObjString) -> Entry:
    index = key.hash % capacity
    tombstone = None
    while True:
        entry = entries[index]
        try:
            string = entry.key.contents
            if string.chars == key.chars and string.length == key.length and string.hash == key.hash:
                return entry
        except ValueError:
            if IS_NIL(entry.value):
                return tombstone or entry
            else:
                if tombstone is None:
                    tombstone = entry

        index = (index + 1) % capacity


def ALLOCATE(type, count):
    return (type * count)()


def adjustCapacity(table: Table, capacity: int):
    entries = ALLOCATE(Entry, capacity)
    for i in range(capacity):
        entries[i].key = cast(None, POINTER(ObjString))
        entries[i].value = NIL_VAL()

    table.count = 0
    for i in range(table.capacity):
        entry = table.entries[i]
        try:
            string = entry.key.contents
        except ValueError:
            continue

        dest = findEntry(entries, capacity, string)
        dest.key = entry.key
        dest.value = entry.value
        table.count += 1

    # del table.entries.contents
    table.entries = entries
    table.capacity = capacity


def tableSet(table: Table, key: ObjString, value: Value) -> bool:
    if table.count + 1 > table.capacity * TABLE_MAX_LOAD:
        capacity = 2 * table.capacity if table.capacity else 8
        adjustCapacity(table, capacity)

    entry = findEntry(table.entries, table.capacity, key)
    try:
        _ = entry.key.contents
        wasNewKey = False
    except ValueError:
        wasNewKey = True

    if wasNewKey and IS_NIL(entry.value):
        table.count += 1

    entry.key = pointer(key)
    entry.value = value
    return wasNewKey


def tableDelete(table: Table, key: ObjString) -> bool:
    if table.count == 0:
        return False

    entry = findEntry(table.entries, table.capacity, key)
    if entry.key is None:
        return False

    entry.key = cast(None, POINTER(ObjString))
    entry.value = BOOL_VAL(True)
    return True


def tableAddAll(fromTable: Table, toTable: Table):
    for i in range(fromTable.capacity):
        entry = fromTable.entries[i]
        if entry.key is not None:
            tableSet(toTable, entry.key, entry.value)


def tableFindString(table: Table, chars: str, length: int, hash: int) -> ObjString | None:
    if table.count == 0:
        return None

    index = hash % table.capacity
    while True:
        entry = table.entries[index]
        try:
            string = entry.key.contents
            if string.length == length and string.hash == hash and string.chars == chars.encode('utf-8'):
                return string
        except ValueError:
            if IS_NIL(entry.value):
                return None

        index = (index + 1) % table.capacity