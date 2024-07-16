# -*- coding: utf-8 -*-
"""https://developer.android.com/reference/android/os/Parcel"""
import array
import importlib
import struct
import ctypes

from androidobjects import overload, Object
# from Android.interface.IParcelable import IParcelable


class Parcel(Object):

    def __init__(self):
        super(Parcel, self).__init__()
        self.block = block = 50
        self._data_pointer = 0
        self._data_size = 0
        self._buffer = array.array('B')
        self.setDataCapacity(block)
        self.primitives = {}
        pass

    def _isCtypePrimitive(self, value):
        return isinstance(value, ctypes._SimpleCData)

    def _isCtypeArray(self, value):
        return isinstance(value, ctypes.Array)

    def _isCtypeArrayPrimitive(self, value):
        return self._isCtypeArray(value) and self._isCtypePrimitive(value[0])

    def _getfullclassname(self, obj):
        classname = obj.__class__.__name__
        modulename = obj.__module__
        if modulename != '__main__':
            classname = modulename + '.' + classname
        return classname

    def _incrementDataCapacity(self, length):
        dataSize = self.dataSize()
        delta = self.dataCapacity() - dataSize
        if delta < length:
            n = (length - delta) // self.block
            if (length - delta) % self.block:
                n += 1
            size = self.dataCapacity() + n*self.block
            self.setDataCapacity(size)

    def _writePrimitive(self, cTypeValue):
        dataType = cTypeValue._type_
        s = self.primitives.setdefault(dataType, struct.Struct(dataType))
        bytesToWrite = s.size
        self._incrementDataCapacity(bytesToWrite)
        dataSize = self.dataSize()
        pos = self.dataPosition()
        s.pack_into(self._buffer, pos, cTypeValue.value)
        self.setDataPosition(pos + bytesToWrite)
        self.setDataSize(dataSize + bytesToWrite)

    def _writePrimitiveArray(self, cType, val):
        # s = self.primitives[dataType]
        # bytesToWrite = s.size
        # size = bytesToWrite*len(val)
        if val is None:
            self.writeInt(-1)
            return
        size = len(val)
        self.writeInt(size)
        self._incrementDataCapacity(size)
        map(lambda x: self._writePrimitive(cType(x)), val)

    def _readPrimitive(self, cType):
        dataType = cType._type_
        s = self.primitives.setdefault(dataType, struct.Struct(dataType))
        bytesToRead = s.size
        if self.dataAvail() < bytesToRead:
            return None
        pos = self.dataPosition()
        self.setDataPosition(pos + bytesToRead)
        return s.unpack_from(self._buffer, pos)[0]

    def _readPrimitiveArray(self, cType, out=None):
        size = self.readInt()
        if size < 0: return None
        if out and size != len(out):
            raise Exception('bad array lengths')
        lista = []
        map(lambda x: lista.append(self._readPrimitive(cType)), range(size))
        if out is None: return (size*cType)(*lista)
        out[:size] = lista

    def appendFrom(self, parcel, offset, length):
        """
        :param parcel: Parcel
        :param offset: int
        :param length: int
        """
        self._incrementDataCapacity(length)
        dataSize = self.dataSize()
        pos = self.dataPosition()
        parcelStr = parcel.marshall()[offset: offset + length]
        self._buffer[pos:pos + length] = array.array('B', str(parcelStr))
        self.setDataPosition(pos + length)
        self.setDataSize(dataSize + length)
        pass

    # def createBinderArray(self):
    #     """
    #     :return: IBinder[].
    #     """
    #     pass

    # def createBinderArrayList(self):
    #     """
    #     Read and return a new ArrayList containing IBinder objects from the
    #     parcel that was written with writeBinderList(List) at the current
    #     dataPosition().  Returns null if the previously written list object
    #     was null.
    #     :return: ArrayList<IBinder>. A newly created ArrayList containing
    #     strings with the same data as those that were previously written.
    #     See also: writeBinderList(List)
    #     """
    #     pass

    def createBooleanArray(self):
        """
        :return: boolean[].
        """
        return self._readPrimitiveArray(ctypes.c_bool)

    def createByteArray(self):
        """
        Read and return a byte[] object from the parcel.
        :return: byte[].
        """
        return self._readPrimitiveArray(ctypes.c_byte)

    def createCharArray(self):
        """
        :return: char[].
        """
        val = self._readPrimitiveArray(ctypes.c_byte)
        return (len(val)*ctypes.c_char)(*map(chr, val))

    def createDoubleArray(self):
        """
        :return: double[].
        """
        return self._readPrimitiveArray(ctypes.c_double)

    def createFloatArray(self):
        """
        :return: float[].
        """
        return self._readPrimitiveArray(ctypes.c_float)

    def createIntArray(self):
        """
        :return: int[].
        """
        return self._readPrimitiveArray(ctypes.c_int32)

    def createLongArray(self):
        """
        :return: long[].
        """
        return self._readPrimitiveArray(ctypes.c_int64)

    def createStringArray(self):
        """
        :return: String[].
        """
        return self.createStringArrayList()

    def createStringArrayList(self):
        """
        Read and return a new ArrayList containing String objects from the
        parcel that was written with writeStringList(List) at the current
        dataPosition().  Returns null if the previously written list object
        was null.
        :return: ArrayList<String>. A newly created ArrayList containing
        strings with the same data as those that were previously written.
        See also: writeStringList(List)
        """
        size = self.readInt()
        if size < 0: return
        return map(lambda x: self.readString(), range(size))

    def createTypedArray(self, c):
        """
        Read and return a new array containing a particular object type from
        the parcel at the current dataPosition().  Returns null if the
        previously written array was null.  The array must have previously
        been written via writeTypedArray(T[], int) with the same object type.
        :param c: Creator
        :return: T[]. A newly created array containing objects with the same
        data as those that were previously written.
        See also: writeTypedArray(T[], int)
        """
        # size = self.readInt()
        # if size < 0: return
        # answArray = c.newArray(size)
        # answArray[:size] = map(lambda x: self.readTypedObject(c), range(size))
        # return answArray
        return self.createTypedArrayList(c)

    def createTypedArrayList(self, c):
        """
        Read and return a new ArrayList containing a particular object type
        from the parcel that was written with writeTypedList(List) at the
        current dataPosition().  Returns null if the previously written list
        object was null.  The list must have previously been written via
        writeTypedList(List) with the same object type.
        :param c: Creator
        :return: ArrayList<T>. A newly created ArrayList containing objects
        with the same data as those that were previously written.
        See also: writeTypedList(List)
        """
        size = self.readInt()
        if size >= 0:
            return map(lambda x: self.readTypedObject(c), range(size))

    def dataAvail(self):
        """
        Returns the amount of data remaining to be read from the parcel.  That
        is, dataSize()-dataPosition().
        :return: int.
        """
        return self.dataSize() - self.dataPosition()

    def dataCapacity(self):
        """
        Returns the total amount of space in the parcel.  This is always >=
        dataSize().  The difference between it and dataSize() is the amount of
        room left until the parcel needs to re-allocate its data buffer.
        :return: int.
        """
        return len(self._buffer)

    def dataPosition(self):
        """
        Returns the current position in the parcel data.  Never more than
        dataSize().
        :return int:
        """
        return self._data_pointer

    def dataSize(self):
        """
        Returns the total amount of data contained in the parcel.
        :return int:
        """
        return self._data_size

    # def enforceInterface(self, interfaceName):
    #     """
    #     :param interfaceName: String
    #     """
    #     pass

    # def hasFileDescriptors(self):
    #     """
    #     Report whether the parcel contains any marshalled file descriptors.
    #     :return: boolean.
    #     """
    #     pass

    def marshall(self):
        """
        Returns the raw bytes of the parcel.  The data you retrieve here must
        not be placed in any kind of persistent storage (on local disk, across
        a network, etc).  For that, you should use standard serialization or
        another kind of general serialization mechanism.  The Parcel
        marshalled representation is highly optimized for local IPC, and as
        such does not attempt to maintain compatibility with data created in
        different versions of the platform.
        :return: byte[].
        """
        return bytearray(self._buffer)

    @classmethod
    def obtain(cls):
        """
        Retrieve a new Parcel object from the pool.
        :return Parcel:
        """
        return cls()

    def readArray(self, loader):
        """
        Read and return a new Object array from the parcel at the current
        dataPosition().  Returns null if the previously written array was
        null.  The given class loader will be used to load any enclosed
        Parcelables.
        :param loader: ClassLoader
        :return: Object[].
        """
        return self.readArrayList(loader)

    def readArrayList(self, loader):
        """
        Read and return a new ArrayList object from the parcel at the current
        dataPosition().  Returns null if the previously written list object
        was null.  The given class loader will be used to load any enclosed
        Parcelables.
        :param loader: ClassLoader
        :return: ArrayList.
        """
        size = self.readInt()
        if size < 0:
            return
        return map(lambda x: self.readValue(loader), range(size))

    def readBinderArray(self, val):
        """
        :param val: IBinder
        """
        pass

    def readBinderList(self, list):
        """
        Read into the given List items IBinder objects that were written with
        writeBinderList(List) at the current dataPosition().
        :param list: List
        See also: writeBinderList(List)
        """
        pass

    def readBooleanArray(self, val):
        """
        :param val: boolean
        """
        self._readPrimitiveArray(ctypes.c_bool, val)

    # @overload
    # def readBundle(self):
    #     """
    #     Read and return a new Bundle object from the parcel at the current
    #     dataPosition().  Returns null if the previously written Bundle object
    #     was null.
    #     :return: Bundle.
    #     """
    #     return self.readBundle('Android.Os.Bundle.Bundle')

    # @readBundle.adddef('str')
    # def readBundle(self, loader):
    #     """
    #     Read and return a new Bundle object from the parcel at the current
    #     dataPosition(), using the given class loader to initialize the class
    #     loader of the Bundle for later retrieval of Parcelable objects.
    #     Returns null if the previously written Bundle object was null.
    #     :param loader: String
    #     :return: Bundle.
    #     """
    #     classname = loader
    #     try:
    #         modulename, classname = classname.rsplit('.', 1)
    #     except ValueError:
    #         modulename = '__main__'
    #     modulename = importlib.import_module(modulename)
    #     loader = getattr(modulename, classname)
    #     return self.readTypedObject(loader.CREATOR)

    def readByte(self):
        """
        Read a byte value from the parcel at the current dataPosition().
        :return byte:
        """
        return self._readPrimitive(ctypes.c_byte)

    def readByteArray(self, val):
        """
        Read a byte[] object from the parcel and copy it into the given byte
        array.
        :param val: byte
        """
        return self._readPrimitiveArray(ctypes.c_byte, val)

    def readCharArray(self, val):
        """
        :param val: char
        """
        return self._readPrimitiveArray(ctypes.c_char, val)

    def readDouble(self):
        """
        Read a double precision floating point value from the parcel at the
        current dataPosition().
        :return: double.
        """
        return self._readPrimitive(ctypes.c_double)

    def readDoubleArray(self, val):
        """
        :param val: double
        """
        return self._readPrimitiveArray(ctypes.c_double, val)

    # @overload
    # def readException(self):
    #     """
    #     Special function for reading an exception result from the header of a
    #     parcel, to be used after receiving the result of a transaction.  This
    #     will throw the exception for you if it had been written to the Parcel,
    #     otherwise return and let you read the normal result data from the
    #     Parcel.
    #     See also: writeException(Exception)writeNoException()
    #     """
    #     pass

    # @readException.adddef('int', 'String')
    # def readException(self, code, msg):
    #     """
    #     Throw an exception with the given message. Not intended for use
    #     outside the Parcel class.
    #     :param code: int: Used to determine which exception class to throw.
    #     :param msg: String: The exception message.
    #     """
    #     pass

    # def readFileDescriptor(self):
    #     """
    #     Read a FileDescriptor from the parcel at the current dataPosition().
    #     :return: ParcelFileDescriptor.
    #     """
    #     pass

    def readFloat(self):
        """
        Read a floating point value from the parcel at the current
        dataPosition().
        :return: float.
        """
        return self._readPrimitive(ctypes.c_float)

    def readFloatArray(self, val):
        """
        :param val: float
        """
        return self._readPrimitiveArray(ctypes.c_float, val)

    # def readHashMap(self, loader):
    #     """
    #     Please use readBundle(ClassLoader) instead (whose data must have been
    #     written with writeBundle(Bundle).  Read and return a new HashMap
    #     object from the parcel at the current dataPosition(), using the given
    #     class loader to load any enclosed Parcelables.  Returns null if the
    #     previously written map object was null.
    #     :param loader: ClassLoader
    #     :return: HashMap.
    #     """
    #     pass

    def readInt(self):
        """
        Read an integer value from the parcel at the current dataPosition().
        :return: int.
        """
        return self._readPrimitive(ctypes.c_int32)

    def readIntArray(self, val):
        """
        :param val: int
        """
        return self._readPrimitiveArray(ctypes.c_int32, val)

    def readList(self, outVal, loader):
        """
        Read into an existing List object from the parcel at the current
        dataPosition(), using the given class loader to load any enclosed
        Parcelables.  If it is null, the default class loader is used.
        :param outVal: List
        :param loader: ClassLoader
        """
        answ = self.readArrayList(loader)
        if not answ: return
        size = len(answ)
        if size != len(outVal):
            raise Exception('bad list lengths')
        outVal[:size] = answ

    def readLong(self):
        """
        Read a long integer value from the parcel at the current
        dataPosition().
        :return: long.
        """
        return self._readPrimitive(ctypes.c_int64)

    def readLongArray(self, val):
        """
        :param val: long
        """
        return self._readPrimitiveArray(ctypes.c_int64, val)

    def readMap(self, outVal, loader):
        """
        Please use readBundle(ClassLoader) instead (whose data must have been
        written with writeBundle(Bundle).  Read into an existing Map object
        from the parcel at the current dataPosition().
        :param outVal: Map
        :param loader: ClassLoader
        """
        if self.readInt() >= 0:
            keys = self.createStringArrayList()
            values = self.readArray(loader)
            outVal.update(zip(keys, values))

    # def readParcelable(self, loader):
    #     """
    #     Read and return a new Parcelable from the parcel.  The given class
    #     loader will be used to load any enclosed Parcelables.  If it is null,
    #     the default class loader will be used.
    #     :param loader: ClassLoader: A ClassLoader from which to instantiate
    #     the Parcelable object, or null for the default class loader.
    #     :return: T. Returns the newly created Parcelable, or null if a null
    #     object has been written.
    #     :raises: BadParcelableExceptionThrows BadParcelableException if there
    #     was an error trying to instantiate the Parcelable.
    #     """
    #     classname = self.readString()
    #     if classname == 'NoneType':
    #         return None
    #     classname = loader or classname
    #     try:
    #         modulename, classname = classname.rsplit('.', 1)
    #     except ValueError:
    #         modulename = '__main__'
    #     modulename = importlib.import_module(modulename)
    #     loader = getattr(modulename, classname)
    #     creator = loader.CREATOR
    #     return creator.createFromParcel(self)

    # def readParcelableArray(self, loader):
    #     """
    #     Read and return a new Parcelable array from the parcel. The given
    #     class loader will be used to load any enclosed Parcelables.
    #     :param loader: ClassLoader
    #     :return: Parcelable[]. the Parcelable array, or null if the array is
    #     null
    #     """
    #     size = self.readInt()
    #     if size < 0: return
    #     return map(lambda x: self.readParcelable(loader), range(size))

    # @overload
    # def readPersistableBundle(self):
    #     """
    #     Read and return a new Bundle object from the parcel at the current
    #     dataPosition().  Returns null if the previously written Bundle object
    #     was null.
    #     :return: PersistableBundle.
    #     """
    #     return self.readPersistableBundle('Android.Os.PersistableBundle.PersistableBundle')

    # @readPersistableBundle.adddef('str')
    # def readPersistableBundle(self, loader):
    #     """
    #     Read and return a new Bundle object from the parcel at the current
    #     dataPosition(), using the given class loader to initialize the class
    #     loader of the Bundle for later retrieval of Parcelable objects.
    #     Returns null if the previously written Bundle object was null.
    #     :param loader: String
    #     :return: PersistableBundle.
    #     """
    #     classname = loader
    #     try:
    #         modulename, classname = classname.rsplit('.', 1)
    #     except ValueError:
    #         modulename = '__main__'
    #     modulename = importlib.import_module(modulename)
    #     loader = getattr(modulename, classname)
    #     return self.readTypedObject(loader.CREATOR)

    def readSerializable(self):
        """
        Read and return a new Serializable object from the parcel.
        :return: Serializable. the Serializable object, or null if the
        Serializable name wasn't found in the parcel.
        """
        pass

    # def readSize(self):
    #     """
    #     Read a Size from the parcel at the current dataPosition().
    #     :return: Size.
    #     """
    #     pass

    # def readSizeF(self):
    #     """
    #     Read a SizeF from the parcel at the current dataPosition().
    #     :return: SizeF.
    #     """
    #     pass

    # def readSparseArray(self, loader):
    #     """
    #     Read and return a new SparseArray object from the parcel at the
    #     current dataPosition().  Returns null if the previously written list
    #     object was null.  The given class loader will be used to load any
    #     enclosed Parcelables.
    #     :param loader: ClassLoader
    #     :return: SparseArray.
    #     """
    #     pass

    # def readSparseBooleanArray(self):
    #     """
    #     Read and return a new SparseBooleanArray object from the parcel at the
    #     current dataPosition().  Returns null if the previously written list
    #     object was null.
    #     :return: SparseBooleanArray.
    #     """
    #     pass

    def readString(self):
        """
        Read a string value from the parcel at the current dataPosition().
        :return: String.
        """
        pos = self.dataPosition()
        size = self._buffer[pos:].index('\0')
        ret = self._buffer[pos:pos + size]
        self.setDataPosition(pos + size + 1)
        return ret.tostring()

    def readStringArray(self, val):
        """
        :param val: String
        """
        self.readStringList(val)

    def readStringList(self, lista):
        """
        Read into the given List items String objects that were written with
        writeStringList(List) at the current dataPosition().
        :param lista: List
        See also:
        writeStringList(List)
        """
        answ = self.createStringArrayList()
        if answ:
            size = len(answ)
            if size != len(lista):
                raise Exception('bad list lenghts')
            lista[:size] = answ

    # def readStrongBinder(self):
    #     """
    #     Read an object from the parcel at the current dataPosition().
    #     :return: IBinder.
    #     """
    #     pass

    def readTypedArray(self, val, c):
        """
        :param val: T
        :param c: Creator
        """
        answ = self.createTypedArray(c)
        if answ:
            size = len(answ)
            if size != len(val):
                raise Exception('bad array lengths')
            val[:size] = answ

    def readTypedList(self, lista, c):
        """
        Read into the given List items containing a particular object type
        that were written with writeTypedList(List) at the current
        dataPosition().  The list must have previously been written via
        writeTypedList(List) with the same object type.
        :param lista: List
        :param c: Creator
        :return: void. A newly created ArrayList containing objects with the
        same data as those that were previously written.
        See also:
        writeTypedList(List)
        """
        answ = self.createTypedArrayList(c)
        if answ:
            size = len(answ)
            if size != len(lista):
                raise Exception('bad list lengths')
            lista[:size] = answ

    def readTypedObject(self, c):
        """
        Read and return a typed Parcelable object from a parcel. Returns null
        if the previous written object was null. The object must have previous
        been written via writeTypedObject(T, int) with the same object type.
        :param c: Creator
        :return: T. A newly created object of the type that was previously
        written.
        See also:
        writeTypedObject(T, int)
        """
        if self.readInt():
            return c.createFromParcel(self)

    def readValue(self, loader):
        """
        Read a typed object from a parcel.  The given class loader will be
        used to load any enclosed Parcelables.  If it is null, the default
        class loader will be used.
        :param loader: ClassLoader
        :return: Object.
        """
        valueType = self.readInt()
        if valueType == -1:
            return
        elif valueType == 1:
            ctype = getattr(ctypes, self.readString())
            return self._readPrimitive(ctype)
        elif valueType == 5:
            return self.readString()
        elif valueType == 6:
            aMap = {}
            self.readMap(aMap, loader)
            return aMap
        elif valueType == 7:
            return self.readArrayList(loader)
        elif valueType == 2:
            ctype = getattr(ctypes, self.readString())
            return self._readPrimitiveArray(ctype)
        # elif valueType == 3:
        #     return self.readParcelable(loader)
        # elif valueType == 4:
        #     return self.readParcelableArray(loader)
        pass

    # def recycle(self):
    #     """
    #     Put a Parcel object back into the pool.  You must not touch the object
    #     after this call.
    #     """
    #     pass

    def setDataCapacity(self, size):
        """
        Change the capacity (current available space) of the parcel.
        :param size: int: The new capacity of the parcel, in bytes.  Can not
        be less than dataSize() -- that is, you can not drop existing data
        with this method.
        """
        datasize = self.dataSize()
        if size > datasize:
            delta = size - datasize
            self._buffer = self._buffer[:datasize] + array.array('B', [0] * delta)
        pass

    def setDataPosition(self, pos):
        """
        Move the current read/write position in the parcel.
        :param pos: int: New offset in the parcel; must be between 0 and
        dataSize().
        """
        self._data_pointer = pos

    def setDataSize(self, size):
        """
        Change the amount of data in the parcel.  Can be either smaller or
        larger than the current size.  If larger than the current capacity,
        more memory will be allocated.
        :param size: int: The new number of bytes in the Parcel.
        """
        self._data_size = size

    def unmarshall(self, data, offset, length):
        """
        Set the bytes in data to be the raw bytes of this Parcel.
        :param data: byte
        :param offset: int
        :param length: int
        """
        raw = data[offset:offset+length]
        rawString = str(raw)
        self._buffer = array.array('B', rawString)
        self.setDataPosition(length)
        self.setDataSize(length)

    def writeArray(self, val):
        """
        Flatten an Object array into the parcel at the current dataPosition(),
        growing dataCapacity() if needed.  The array values are written using
        writeValue(Object) and must follow the specification there.
        :param val: Object
        """
        if val is None:
            return self.writeInt(-1)
        size = len(val)
        self.writeInt(size)
        map(self.writeValue, val)
        pass

    def writeBinderArray(self, val):
        """
        :param val: IBinder
        """
        pass

    def writeBinderList(self, val):
        """
        Flatten a List containing IBinder objects into the parcel, at the
        current dataPosition() and growing dataCapacity() if needed.  They can
        later be retrieved with createBinderArrayList() or
        readBinderList(List).
        :param val: List: The list of strings to be written.
        See also: createBinderArrayList()readBinderList(List)
        """
        pass

    def _writeBoolean(self, val):
        """
        :param val: boolean
        """
        self._writePrimitive(ctypes.c_bool(val))

    def writeBooleanArray(self, val):
        """
        :param val: boolean
        """
        self._writePrimitiveArray(ctypes.c_bool, val)

    # def writeBundle(self, val):
    #     """
    #     Flatten a Bundle into the parcel at the current dataPosition(),
    #     growing dataCapacity() if needed.
    #     :param val: Bundle
    #     """
    #     self.writeTypedObject(val, 0)

    def writeByte(self, val):
        """
        Write a byte value into the parcel at the current dataPosition(),
        growing dataCapacity() if needed.
        :param val: byte
        """
        self._writePrimitive(ctypes.c_byte(val))

    @overload('list')
    def writeByteArray(self, b):
        """
        Write a byte array into the parcel at the current dataPosition(),
        growing dataCapacity() if needed.
        :param b: byte: Bytes to place into the parcel.
        """
        self._writePrimitiveArray(ctypes.c_byte, b)
        pass

    @writeByteArray.adddef('bytearray', 'int', 'int')
    def writeByteArray(self, b, offset, len):
        """
        Write a byte array into the parcel at the current dataPosition(),
        growing dataCapacity() if needed.
        :param b: byte: Bytes to place into the parcel.
        :param offset: int: Index of first byte to be written.
        :param len: int: Number of bytes to write.
        """
        val = b[offset:offset + len]
        self._writePrimitiveArray(ctypes.c_byte, val)
        pass

    def writeCharArray(self, val):
        """
        :param val: char
        """
        self._writePrimitiveArray(ctypes.c_byte, bytearray(val))
        pass

    def writeDouble(self, val):
        """
        Write a double precision floating point value into the parcel at the
        current dataPosition(), growing dataCapacity() if needed.
        :param val: double
        """
        self._writePrimitive(ctypes.c_double(val))

    def writeDoubleArray(self, val):
        """
        :param val: double
        """
        self._writePrimitiveArray(ctypes.c_double, val)
        pass

    # def writeException(self, e):
    #     """
    #     Special function for writing an exception result at the header of a
    #     parcel, to be used when returning an exception from a transaction.
    #     Note that this currently only supports a few exception types; any
    #     other exception will be re-thrown by this function as a
    #     RuntimeException (to be caught by the system's last-resort exception
    #     handling when dispatching a transaction).  The supported exception
    #     types are:
    #
    #     BadParcelableExceptionIllegalArgumentExceptionIllegalStateExceptionNullPointerExceptionSecurityExceptionUnsupportedOperationExceptionNetworkOnMainThreadException
    #     :param e: Exception: The Exception to be written.
    #     See also: writeNoException()readException()
    #     """
    #     pass

    # def writeFileDescriptor(self, val):
    #     """
    #     Write a FileDescriptor into the parcel at the current dataPosition(),
    #     growing dataCapacity() if needed.  The file descriptor will not be
    #     closed, which may result in file descriptor leaks when objects are
    #     returned from Binder calls.  Use
    #     ParcelFileDescriptor.writeToParcel(Parcel, int) instead, which accepts
    #     contextual flags and will close the original file descriptor if
    #     Parcelable.PARCELABLE_WRITE_RETURN_VALUE is set.
    #     :param val: FileDescriptor
    #     """
    #     pass

    def writeFloat(self, val):
        """
        Write a floating point value into the parcel at the current
        dataPosition(), growing dataCapacity() if needed.
        :param val: float
        """
        self._writePrimitive(ctypes.c_float(val))

    def writeFloatArray(self, val):
        """
        :param val: float
        """
        self._writePrimitiveArray(ctypes.c_float, val)
        pass

    def writeInt(self, val):
        """
        Write an integer value into the parcel at the current dataPosition(),
        growing dataCapacity() if needed.
        :param val: int
        """
        self._writePrimitive(ctypes.c_int32(val))

    def writeIntArray(self, val):
        """
        :param val: int
        """
        self._writePrimitiveArray(ctypes.c_int32, val)
        pass

    def writeInterfaceToken(self, interfaceName):
        """
        Store or read an IBinder interface token in the parcel at the current
        dataPosition().  This is used to validate that the marshalled
        transaction is intended for the target interface.
        :param interfaceName: String
        """
        pass

    def writeList(self, val):
        """
        Flatten a List into the parcel at the current dataPosition(), growing
        dataCapacity() if needed.  The List values are written using
        writeValue(Object) and must follow the specification there.
        :param val: List
        """
        self.writeArray(val)

    def writeLong(self, val):
        """
        Write a long integer value into the parcel at the current
        dataPosition(), growing dataCapacity() if needed.
        :param val: long
        """
        self._writePrimitive(ctypes.c_int64(val))

    def writeLongArray(self, val):
        """
        :param val: long
        """
        self._writePrimitiveArray(ctypes.c_int64, val)
        pass

    def writeMap(self, val):
        """
        Please use writeBundle(Bundle) instead.  Flattens a Map into the
        parcel at the current dataPosition(), growing dataCapacity() if
        needed.  The Map keys must be String objects. The Map values are
        written using writeValue(Object) and must follow the specification
        there.  It is strongly recommended to use writeBundle(Bundle) instead
        of this method, since the Bundle class provides a type-safe API that
        allows you to avoid mysterious type errors at the point of marshalling.
        :param val: Map
        """
        if val is None:
            self.writeInt(-1)
        else:
            self.writeInt(0)
            keys, values = zip(*val.items())
            self.writeStringList(keys)
            self.writeArray(values)

    def writeNoException(self):
        """
        Special function for writing information at the front of the Parcel
        indicating that no exception occurred.
        See also:
            writeException(Exception)
            readException()
        """
        pass

    def writeParcelable(self, p, parcelableFlags):
        """
        Flatten the name of the class of the Parcelable and its contents into
        the parcel.
        :param p: Parcelable: The Parcelable object to be written.
        :param parcelableFlags: int: Contextual flags as per
        Parcelable.writeToParcel().
        """
        if p is None:
            classname = 'NoneType'
            self.writeString(classname)
            return
        classname = p.__module__ + '.' + p.__class__.__name__
        self.writeString(classname)
        p.writeToParcel(self, parcelableFlags)
        pass

    def writeParcelableArray(self, value, parcelableFlags):
        """
        Write a heterogeneous array of Parcelable objects into the Parcel.
        Each object in the array is written along with its class name, so that
        the correct class can later be instantiated.  As a result, this has
        significantly more overhead than writeTypedArray(T[], int), but will
        correctly handle an array containing more than one type of object.
        :param value: T: The array of objects to be written.
        :param parcelableFlags: int: Contextual flags as per
        Parcelable.writeToParcel().
        See also: writeTypedArray(T[], int)
        """
        if value is None:
            self.writeInt(-1)
        else:
            size = len(value)
            self.writeInt(size)
            map(lambda x: self.writeParcelable(x, parcelableFlags), value)
        pass

    def writePersistableBundle(self, val):
        """
        Flatten a PersistableBundle into the parcel at the current
        dataPosition(), growing dataCapacity() if needed.
        :param val: PersistableBundle
        """
        self.writeTypedObject(val, 0)

    def writeSerializable(self, s):
        """
        Write a generic serializable object in to a Parcel.  It is strongly
        recommended that this method be avoided, since the serialization
        overhead is extremely large, and this approach will be much slower
        than using the other approaches to writing data in to a Parcel.
        :param s: Serializable
        """
        pass

    def writeSize(self, val):
        """
        Flatten a Size into the parcel at the current dataPosition(), growing
        dataCapacity() if needed.
        :param val: Size
        """
        pass

    def writeSizeF(self, val):
        """
        Flatten a SizeF into the parcel at the current dataPosition(), growing
        dataCapacity() if needed.
        :param val: SizeF
        """
        pass

    def writeSparseArray(self, val):
        """
        Flatten a generic SparseArray into the parcel at the current
        dataPosition(), growing dataCapacity() if needed.  The SparseArray
        values are written using writeValue(Object) and must follow the
        specification there.
        :param val: SparseArray
        """
        pass

    def writeSparseBooleanArray(self, val):
        """
        :param val: SparseBooleanArray
        """
        pass

    def writeString(self, val):
        """
        Write a string value into the parcel at the current dataPosition(),
        growing dataCapacity() if needed.
        :param val: String
        """
        val = val or ''
        size = len(val) + 1
        self._incrementDataCapacity(size)
        pos = self.dataPosition()
        self._buffer[pos:pos+size] = array.array('B', val + '\0')
        self.setDataPosition(pos + size)
        self.setDataSize(pos + size)
        pass

    def writeStringArray(self, val):
        """
        :param val: String
        """
        self.writeStringList(val)

    def writeStringList(self, val):
        """
        Flatten a List containing String objects into the parcel, at the
        current dataPosition() and growing dataCapacity() if needed.  They can
        later be retrieved with createStringArrayList() or
        readStringList(List).
        :param val: List: The list of strings to be written.
        See also:
        createStringArrayList()
        readStringList(List)
        """
        if val is None:
            self.writeInt(-1)
        else:
            self.writeInt(len(val))
            map(self.writeString, val)
        pass

    def writeStrongBinder(self, val):
        """
        Write an object into the parcel at the current dataPosition(), growing
        dataCapacity() if needed.
        :param val: IBinder
        """
        pass

    def writeStrongInterface(self, val):
        """
        Write an object into the parcel at the current dataPosition(), growing
        dataCapacity() if needed.
        :param val: IInterface
        """
        pass

    def writeTypedArray(self, val, parcelableFlags):
        """
        Flatten a homogeneous array containing a particular object type into
        the parcel, at the current dataPosition() and growing dataCapacity()
        if needed.  The type of the objects in the array must be one that
        implements Parcelable. Unlike the writeParcelableArray(T[], int)
        method, however, only the raw data of the objects is written and not
        their type, so you must use readTypedArray(T[], Parcelable.Creator)
        with the correct corresponding Parcelable.Creator implementation to
        unmarshall them.
        :param val: T: The array of objects to be written.
        :param parcelableFlags: int: Contextual flags as per
        Parcelable.writeToParcel().
        See also:
        readTypedArray(T[], Parcelable.Creator)
        writeParcelableArray(T[], int)
        Parcelable.Creator
        """
        if val is None:
            self.writeInt(-1)
        else:
            self.writeInt(len(val))
            map(lambda x: self.writeTypedObject(x, parcelableFlags), val)
        pass

    def writeTypedList(self, val):
        """
        Flatten a List containing a particular object type into the parcel, at
        the current dataPosition() and growing dataCapacity() if needed.  The
        type of the objects in the list must be one that implements
        Parcelable. Unlike the generic writeList() method, however, only the
        raw data of the objects is written and not their type, so you must use
        the corresponding readTypedList() to unmarshall them.
        :param val: List: The list of objects to be written.
        See also:
        createTypedArrayList(Parcelable.Creator)
        readTypedList(List, Parcelable.Creator)
        Parcelable
        """
        self.writeTypedArray(val, 0)
        pass

    def writeTypedObject(self, val, parcelableFlags):
        """
        Flatten the Parcelable object into the parcel.
        :param val: T: The Parcelable object to be written.
        :param parcelableFlags: int: Contextual flags as per
        Parcelable.writeToParcel().
        See also:
        readTypedObject(Parcelable.Creator)
        """
        if val is None:
            self.writeInt(0)
        else:
            self.writeInt(1)
            val.writeToParcel(self, parcelableFlags)
        pass

    def writeValue(self, value):
        """
        Flatten a generic object in to a parcel.  The given Object value may
        currently be one of the following types:  null String Byte Short
        Integer Long Float Double Boolean String[] boolean[] byte[] int[]
        long[] Object[] (supporting objects of the same type defined here).
        Bundle Map (as supported by writeMap(Map)). Any object that implements
        the Parcelable protocol. Parcelable[] CharSequence (as supported by
        TextUtils.writeToParcel(CharSequence, Parcel, int)). List (as
        supported by writeList(List)). SparseArray (as supported by
        writeSparseArray(SparseArray)). IBinder Any object that implements
        Serializable (but see writeSerializable(Serializable) for caveats).
        Note that all of the previous types have relatively efficient
        implementations for writing to a Parcel; having to rely on the generic
        serialization approach is much less efficient and should be avoided
        whenever possible. Parcelable objects are written with
        Parcelable.writeToParcel(Parcel, int) using contextual flags of 0.
        When serializing objects containing ParcelFileDescriptors, this may
        result in file descriptor leaks when they are returned from Binder
        calls (where Parcelable.PARCELABLE_WRITE_RETURN_VALUE should be used).
        :param value: Object
        """
        v = value
        if isinstance(v, bool):
            v = ctypes.c_bool(v)
        elif isinstance(v, int):
            v = ctypes.c_int32(v)
        elif isinstance(v, float):
            v = ctypes.c_float(v)

        if v is None:
            self.writeInt(-1)
        elif self._isCtypePrimitive(v):
            self.writeInt(1)
            self.writeString(v.__class__.__name__)
            self._writePrimitive(v)
        elif isinstance(v, str):
            self.writeInt(5)
            self.writeString(v)
        elif self._isCtypeArrayPrimitive(v):
            self.writeInt(2)
            ctype = v._type_
            self.writeString(ctype.__name__)
            self._writePrimitiveArray(ctype, v)
        elif isinstance(v, dict):
            self.writeInt(6)
            self.writeMap(v)
        elif isinstance(v, list):
            self.writeInt(7)
            self.writeList(v)
        # elif isinstance(v, IParcelable):
        #     self.writeInt(3)
        #     self.writeParcelable(v)
        # elif self._isCtypeArray(v) and isinstance(v[0], IParcelable):
        #     self.writeInt(4)
        #     self.writeParcelableArray(v, 0)
        pass

    # def finalize(self):
    #     """
    #     Called by the garbage collector on an object when garbage collection
    #     determines that there are no more references to the object. A subclass
    #     overrides the finalize method to dispose of system resources or to
    #     perform other cleanup.  The general contract of finalize is that it is
    #     invoked if and when the Java&trade; virtual machine has determined
    #     that there is no longer any means by which this object can be accessed
    #     by any thread that has not yet died, except as a result of an action
    #     taken by the finalization of some other object or class which is ready
    #     to be finalized. The finalize method may take any action, including
    #     making this object available again to other threads; the usual purpose
    #     of finalize, however, is to perform cleanup actions before the object
    #     is irrevocably discarded. For example, the finalize method for an
    #     object that represents an input/output connection might perform
    #     explicit I/O transactions to break the connection before the object is
    #     permanently discarded.  The finalize method of class Object performs
    #     no special action; it simply returns normally. Subclasses of Object
    #     may override this definition.  The Java programming language does not
    #     guarantee which thread will invoke the finalize method for any given
    #     object. It is guaranteed, however, that the thread that invokes
    #     finalize will not be holding any user-visible synchronization locks
    #     when finalize is invoked. If an uncaught exception is thrown by the
    #     finalize method, the exception is ignored and finalization of that
    #     object terminates.  After the finalize method has been invoked for an
    #     object, no further action is taken until the Java virtual machine has
    #     again determined that there is no longer any means by which this
    #     object can be accessed by any thread that has not yet died, including
    #     possible actions by other objects or classes which are ready to be
    #     finalized, at which point the object may be discarded.  The finalize
    #     method is never invoked more than once by a Java virtual machine for
    #     any given object.  Any exception thrown by the finalize method causes
    #     the finalization of this object to be halted, but is otherwise ignored.
    #     :raises: Throwable
    #     """
    #     pass

    def __getitem__(self, item):
        return self._buffer[item]