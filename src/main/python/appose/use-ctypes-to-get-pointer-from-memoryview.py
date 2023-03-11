# Trying to get a pointer from a SharedMemory block.
# segfaults. :-(

import ctypes
from ctypes import *
from multiprocessing.shared_memory import SharedMemory

shm = SharedMemory(create=True, size=1234567)

c_ssize_p = POINTER(c_ssize_t)

class Py_buffer(ctypes.Structure):
    _fields_ = [
        ('buf', c_void_p),
        ('obj', py_object),
        ('len', c_ssize_t),
        ('itemsize', c_ssize_t),
        ('readonly', c_int),
        ('ndim', c_int),
        ('format', c_char_p),
        ('shape', c_ssize_p),
        ('strides', c_ssize_p),
        ('suboffsets', c_ssize_p),
        ('internal', c_void_p)
    ]

b = shm.buf.tobytes()

result = Py_buffer()


import _testbuffer # HACK

print("-----------")
#pythonapi.PyObject_GetBuffer(bytes(shm.buf), result, _testbuffer.PyBUF_ANY_CONTIGUOUS)
#pythonapi.PyObject_GetBuffer(b, result, _testbuffer.PyBUF_ANY_CONTIGUOUS)
#pythonapi.PyObject_GetBuffer(shm, result, _testbuffer.PyBUF_ANY_CONTIGUOUS)
pythonapi.PyObject_GetBuffer(shm.buf, result, _testbuffer.PyBUF_ANY_CONTIGUOUS)
#pythonapi.PyObject_GetBuffer(shm.buf.obj, result, _testbuffer.PyBUF_ANY_CONTIGUOUS)

print("-----------")
print(result)
print("-----------")
